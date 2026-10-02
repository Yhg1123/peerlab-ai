from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from peerlab.__main__ import main
from peerlab.client import APIError
from peerlab.efficiency import analyze, run_efficiency, validate
from peerlab.efficiency_report import export_efficiency
from peerlab.experiment import load_cases
from test_peerlab import FakeClient


class EfficiencyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "study"
        self.cases = [c for c in load_cases() if c["id"] in ("critical-path", "sql-null")]
        self.providers = [FakeClient("deepseek"), FakeClient("kimi")]

    def execute(self, **kwargs):
        return run_efficiency(self.providers, self.cases, self.path, max_calls=16, progress=lambda _: None, **kwargs)

    def test_budget_fails_before_side_effects_and_dry_run_is_offline(self):
        with self.assertRaises(ValueError):
            run_efficiency(self.providers, self.cases, self.path, max_calls=15)
        self.assertFalse(self.path.exists())
        self.assertFalse(any(p.calls for p in self.providers))
        output = io.StringIO()
        with patch("peerlab.__main__.clients", side_effect=AssertionError("Network initialized")), redirect_stdout(output):
            self.assertEqual(main(["efficiency", "--dry-run", "--limit", "1", "--max-calls", "8"]), 0)
        self.assertEqual(json.loads(output.getvalue())["planned_calls"], 8)

    def test_independent_prompts_never_include_references_or_other_answers(self):
        run = self.execute()
        self.assertEqual(validate(run)["grades_recomputed"], 16)
        self.assertEqual(run["calls_attempted"], 16)
        tasks = {c["id"]: c for c in self.cases}
        for r in run["records"]:
            self.assertEqual(len(r["messages"]), 2)
            self.assertEqual(r["messages"][1]["content"], tasks[r["case_id"]]["prompt"])
            self.assertNotIn(tasks[r["case_id"]]["rationale"], str(r["messages"]))

    def test_failure_is_missing_pair_not_token_saving(self):
        self.providers[0].fail = True
        run = self.execute()
        result = analyze(run)
        self.assertEqual(run["status"], "partial")
        pair = result["comparisons"][0]
        self.assertEqual(pair["paired"], 0)
        self.assertEqual(pair["missing_pairs"], 2)
        self.assertIsNone(pair["tokens"]["total_tokens"]["saved_fraction"])
        self.assertEqual(result["conditions"][0]["errors"], 2)

    def test_known_pair_quality_and_token_arithmetic(self):
        run = self.execute()
        # Hand-set a two-pair fixture: wrong->right and right->wrong.
        for r in run["records"]:
            if r["provider"] != "deepseek":
                continue
            first = r["case_id"] == "critical-path"
            compact = r["arm"] == "compact_answer"
            answer = (10 if first else 1) if compact else (9 if first else 0)
            r["content"] = json.dumps({"answer": answer})
            from peerlab.grading import grade
            r["grade"] = grade(next(c for c in self.cases if c["id"] == r["case_id"]), r["content"])
            r["usage"] = {"prompt_tokens": 10, "completion_tokens": 10 if compact else 30, "total_tokens": 20 if compact else 40}
        pair = analyze(run)["comparisons"][0]
        self.assertEqual((pair["only_left_correct"], pair["only_right_correct"]), (1, 1))
        self.assertEqual(pair["tokens"]["total_tokens"]["saved_fraction"], .5)
        self.assertEqual(pair["left_tokens_per_correct"], 80)
        self.assertEqual(pair["right_tokens_per_correct"], 40)
        self.assertEqual(pair["accuracy_delta"], 0)

    def test_unknown_usage_is_excluded_not_imputed_as_zero(self):
        run = self.execute()
        for r in run["records"]:
            if r["provider"] == "deepseek" and r["arm"] == "compact_answer":
                r["usage"] = {}
        pair = analyze(run)["comparisons"][0]
        self.assertEqual(pair["paired"], 2)
        self.assertEqual(pair["tokens"]["total_tokens"]["missing_pairs"], 2)
        self.assertIsNone(pair["tokens"]["total_tokens"]["saved_fraction"])
        self.assertIsNone(pair["right_tokens_per_correct"])

    def test_tampered_prompt_grade_order_plan_and_usage_are_rejected(self):
        run = self.execute()
        mutations = [lambda r: r["records"][0]["messages"][0].update(content="different"),
                     lambda r: r["records"][0]["grade"].update(passed=not r["records"][0]["grade"]["passed"]),
                     lambda r: r["records"].reverse(),
                     lambda r: r["config"].update(seed=0),
                     lambda r: r["records"][0]["usage"].update(total_tokens=100),
                     lambda r: r["cases"][0].update(expected=100)]
        for mutation in mutations:
            copy = deepcopy(run)
            mutation(copy)
            with self.assertRaises(ValueError):
                validate(copy)

    def test_interrupt_preserves_pending_attempt_and_does_not_retry(self):
        def interrupt(_):
            raise KeyboardInterrupt
        self.providers[0].complete = interrupt
        self.providers[1].complete = interrupt
        run = self.execute()
        self.assertEqual(run["status"], "interrupted")
        self.assertEqual(run["calls_attempted"], 1)
        self.assertEqual(run["records"][0]["status"], "pending")
        self.assertEqual(json.loads((self.path / "run.json").read_text(encoding="utf-8")), run)
        validate(run)

    def test_truncation_is_wrong_and_html_escapes_model_output(self):
        run = self.execute()
        from peerlab.grading import grade
        r = run["records"][0]
        r["content"] = '<script>alert("model output")</script>'
        r["finish_reason"] = "length"
        r["grade"] = grade(next(c for c in self.cases if c["id"] == r["case_id"]), r["content"], "length")
        result = export_efficiency(run, self.path)
        self.assertEqual(sum(c["incomplete"] for c in result["conditions"]), 1)
        html = (self.path / "report.html").read_text(encoding="utf-8")
        self.assertNotIn('<script>alert', html)
        self.assertIn('&lt;script&gt;alert', html)
