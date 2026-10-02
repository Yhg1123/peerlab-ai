from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from peerlab.dimensions import cluster_interval, contract, diagnostics, parsed_object, quantile
from peerlab.efficiency import EXTENDED, make_plan, run_efficiency, validate
from peerlab.efficiency_report import export_efficiency
from peerlab.experiment import load_cases
from peerlab.grading import grade
from test_peerlab import FakeClient


class DimensionsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/"study"
        self.cases = [c for c in load_cases() if c["id"] in ("critical-path", "sql-null")]

    def execute(self):
        return run_efficiency([FakeClient("deepseek"), FakeClient("kimi")], self.cases, self.path,
                              protocol=EXTENDED, repeats=2, max_calls=24, progress=lambda _: None)

    def test_extended_plan_repeats_and_legacy_protocol(self):
        self.assertEqual(make_plan(self.cases, 2, protocol=EXTENDED)["planned_calls"], 24)
        self.assertEqual(make_plan(self.cases, 2)["planned_calls"], 32)
        run = self.execute()
        self.assertEqual(validate(run)["grades_recomputed"], 24)
        self.assertEqual(set(r["arm"] for r in run["records"]), {"verbose_explain", "compact_answer", "compact_evidence"})
        copy = deepcopy(run)
        copy["kind"] = "token-efficiency-v1"
        with self.assertRaises(ValueError):
            validate(copy)

    def test_contract_is_separate_from_answer_accuracy(self):
        def row(content, arm="compact_evidence", finish="stop"):
            return {"status": "ok", "finish_reason": finish, "content": content, "arm": arm}
        self.assertTrue(contract(row('{"evidence":"3+7=10","answer":10}')))
        for content in ['{"answer":10,"evidence":"sum"}', '{"evidence":"' + 'x'*81 + '","answer":10}', '{"evidence":"sum","answer":10,"answer":10}', '{"evidence":"sum","answer":NaN}']:
            self.assertFalse(contract(row(content)))
        self.assertFalse(contract(row('{"answer":10,"explanation":"extra"}', "compact_answer")))
        self.assertIsNone(parsed_object(row('{"answer":10}', finish="length")))
        # Syntactic evidence compliance does not validate the explanation's truth.
        self.assertTrue(contract(row('{"evidence":"wrong","answer":999}')))

    def test_cluster_bootstrap_known_constant_effect(self):
        run = self.execute()
        for r in run["records"]:
            c = next(c for c in self.cases if c["id"] == r["case_id"])
            right = r["arm"] == "compact_answer"
            r["content"] = json.dumps({"answer": c["expected"] if right else -1})
            r["grade"] = grade(c, r["content"])
            r["usage"] = {"prompt_tokens": 5, "completion_tokens": 5 if right else 15, "total_tokens": 10 if right else 20}
        ci = cluster_interval(run, "deepseek", "verbose_explain", "compact_answer", samples=50)
        self.assertEqual(ci["task_clusters"], 2)  # Four repeat pairs are NOT four clusters.
        self.assertEqual(ci["accuracy_delta_95pct"], [1, 1])
        self.assertEqual(ci["total_token_saving_95pct"], [.5, .5])
        self.assertEqual(ci, cluster_interval(run, "deepseek", "verbose_explain", "compact_answer", samples=50))

    def test_stability_missingness_and_sensitivity(self):
        run = self.execute()
        for r in run["records"]:
            if r["provider"] == "deepseek" and r["case_id"] == "critical-path" and r["arm"] == "compact_answer" and r["repeat"] == 2:
                r["content"] = '{"answer":10.00005}'
                r["grade"] = grade(self.cases[0], r["content"])
        data = diagnostics(run)
        stable = next(s for s in data["stability"] if s["provider"] == "deepseek" and s["arm"] == "compact_answer")
        self.assertEqual(stable["mixed_correctness_tasks"], 1)
        sensitive = next(s for s in data["numeric_sensitivity"] if s["provider"] == "deepseek" and s["arm"] == "compact_answer")
        self.assertEqual(sensitive["absolute_error_thresholds"], {"1e-06":1, "0.0001":2, "0.01":2})
        for r in run["records"]:
            if r["provider"] == "kimi" and r["repeat"] == 2:
                r["status"] = "error"
        run["status"] = "partial"
        data = diagnostics(run)
        stable = next(s for s in data["stability"] if s["provider"] == "kimi")
        self.assertEqual(stable["all_repeats_returned_tasks"], 0)
        self.assertEqual(stable["missing_task_clusters"], 2)

    def test_latency_and_report_export(self):
        self.assertEqual(quantile([10, 20], .9), 19)
        self.assertIsNone(quantile([], .9))
        run = self.execute()
        result = export_efficiency(run, self.path)
        self.assertEqual(len(result["conditions"]), 6)
        data = json.loads((self.path/"dimensions.json").read_text(encoding="utf-8"))
        group = next(g for g in data["conditions"] if g["scope"] == "all")
        self.assertEqual(group["latency"]["median_ms"], 12)
        self.assertIn("三条件复测", (self.path/"report.html").read_text(encoding="utf-8"))
