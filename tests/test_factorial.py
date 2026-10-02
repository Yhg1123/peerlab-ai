from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from peerlab.efficiency import FACTORIAL, FACTORIAL_ARMS, make_plan, messages_for, run_efficiency, validate
from peerlab.efficiency_report import export_efficiency
from peerlab.experiment import load_cases
from peerlab.factorial import contract_components, interaction
from peerlab.grading import grade
from test_peerlab import FakeClient


class FactorialTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/"study"
        self.cases = [c for c in load_cases() if c["id"] in ("critical-path", "sql-null")]

    def execute(self):
        run = run_efficiency([FakeClient("deepseek"), FakeClient("kimi")], self.cases, self.path,
                             protocol=FACTORIAL, repeats=2, max_calls=32, progress=lambda _: None)
        for row in run["records"]:
            case = next(c for c in self.cases if c["id"] == row["case_id"])
            # Only evidence-first/unbounded is correct: interaction = +1.
            answer = case["expected"] if row["arm"] == FACTORIAL_ARMS[3] else -1
            obj = {"answer": answer, "evidence": "check"}
            if row["arm"].startswith("evidence"):
                obj = dict(reversed(list(obj.items())))
            row["content"] = json.dumps(obj)
            row["grade"] = grade(case, row["content"])
            total = dict(zip(FACTORIAL_ARMS, (20, 30, 40, 60)))[row["arm"]]
            row["usage"] = {"prompt_tokens": 10, "completion_tokens": total-10, "total_tokens": total}
        return run

    def test_prompts_differ_only_by_preregistered_factors_and_no_labels(self):
        prompts = [messages_for(self.cases[0], a)[0]["content"] for a in FACTORIAL_ARMS]
        cap = "evidence长度不超过80个Unicode字符（包含标点和空格）。"
        self.assertEqual(prompts[0].replace(cap, ""), prompts[2])
        self.assertEqual(prompts[1].replace(cap, ""), prompts[3])
        self.assertEqual(prompts[0].replace("字段顺序为answer、evidence", "字段顺序为evidence、answer"), prompts[1])
        self.assertEqual(make_plan(self.cases, 2, protocol=FACTORIAL)["planned_calls"], 32)
        run = self.execute()
        self.assertEqual(validate(run)["grades_recomputed"], 32)
        run["records"][0]["messages"][0]["content"] += "changed"
        with self.assertRaises(ValueError):
            validate(run)

    def test_common_contract_does_not_change_when_cap_removed(self):
        def row(evidence, arm, reverse=False):
            obj = {"answer": 10, "evidence": evidence}
            if reverse:
                obj = dict(reversed(list(obj.items())))
            return {"content": json.dumps(obj), "status": "ok", "finish_reason": "stop", "arm": arm}
        bounded = contract_components(row("文"*81, FACTORIAL_ARMS[0]))
        unbounded = contract_components(row("文"*81, FACTORIAL_ARMS[2]))
        self.assertTrue(bounded["common_contract"] and unbounded["common_contract"])
        self.assertFalse(bounded["arm_contract"])
        self.assertTrue(unbounded["arm_contract"])
        self.assertFalse(contract_components(row(" ", FACTORIAL_ARMS[0]))["common_contract"])
        self.assertFalse(contract_components(row("ok", FACTORIAL_ARMS[0], True))["requested_order"])
        self.assertTrue(contract_components(row("😀"*80, FACTORIAL_ARMS[0]))["within_80"])

    def test_interaction_sign_clusters_and_missingness(self):
        run = self.execute()
        result = interaction(run, "deepseek", samples=50)
        self.assertEqual(result["complete_blocks"], 4)
        self.assertEqual(result["task_clusters"], 2)
        self.assertEqual(result["estimate"]["accuracy"], 1)
        self.assertEqual(result["percentile_95pct"]["accuracy"], [1, 1])
        self.assertEqual(result["estimate"]["total_tokens_per_block"], 10)
        self.assertEqual(result["percentile_95pct"]["total_tokens_per_block"], [10, 10])
        r = next(r for r in run["records"] if r["provider"] == "deepseek")
        r["usage"] = {}
        self.assertIsNone(interaction(run, "deepseek", samples=50)["estimate"]["total_tokens_per_block"])
        r["status"] = "error"
        result = interaction(run, "deepseek", samples=50)
        self.assertEqual(result["complete_blocks"], 3)
        self.assertEqual(result["missing_blocks"], 1)
        self.assertEqual(result["estimate"]["total_tokens_per_block"], 10)

    def test_empty_interactions_and_report(self):
        run = self.execute()
        copy = deepcopy(run)
        copy["records"] = []
        result = interaction(copy, "deepseek", samples=50)
        self.assertEqual(result["complete_blocks"], 0)
        self.assertIsNone(result["estimate"]["accuracy"])
        export_efficiency(run, self.path)
        self.assertTrue((self.path/"factorial.json").exists())
        html = (self.path/"report.html").read_text(encoding="utf-8")
        self.assertIn("因素交互项", html)
        self.assertIn("共同契约且正确", html)
        self.assertNotIn("先依据后答案改变了多项要求", html)
