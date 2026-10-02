from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from peerlab.__main__ import main
from peerlab.experiment import PROTOCOLS, load_cases, planned_calls, run_experiment
from peerlab.report import export_report
from test_peerlab import FakeClient


class IndependentReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)/"experiment"
        self.providers = [FakeClient("deepseek"), FakeClient("kimi")]
        self.cases = [next(c for c in load_cases() if c["id"] == "critical-path")]

    def execute(self, **kwargs):
        return run_experiment(self.providers, self.cases, self.path, protocol="independent",
                              max_calls=14, progress=lambda _:None, **kwargs)

    def test_budget_and_baselines_before_reviews(self):
        run = self.execute()
        self.assertEqual(run["calls_attempted"], 14)
        self.assertEqual(run["config"]["arms"], list(PROTOCOLS["independent"]))
        self.assertEqual([r["stage"] for r in run["records"][:2]], ["baseline","baseline"])
        self.assertTrue(all(len(p.calls) == 7 for p in self.providers))

    def test_reviewer_uses_own_unexposed_baseline(self):
        for provider in self.providers:
            original = provider.complete
            def tagged(messages, original=original, name=provider.name):
                result = original(messages)
                result["content"] = json.dumps({"answer":10, "explanation":name})
                return result
            provider.complete = tagged
        run = self.execute()
        by_id = {r["id"]:r for r in run["records"]}
        for review in run["records"]:
            if not review["stage"].startswith("peer_independent_review_for_"):
                continue
            candidate, independent = [by_id[i] for i in review["dependencies"]]
            data = json.loads(review["messages"][1]["content"])
            self.assertNotEqual(candidate["provider"], review["provider"])
            self.assertEqual(independent["provider"], review["provider"])
            self.assertEqual(independent["stage"], "baseline")
            self.assertEqual(data["reviewer_independent_solution"], independent["content"])
            self.assertEqual(data["candidate"], candidate["content"])
            self.assertNotIn("oracle", data)
            self.assertNotIn(self.cases[0]["rationale"], str(review["messages"]))

    def test_missing_reviewer_baseline_skips_independent_condition(self):
        original = self.providers[1].complete
        def fail_first(messages):
            if not self.providers[1].calls:
                self.providers[1].calls.append(messages)
                from peerlab.client import APIError
                raise APIError("No baseline")
            return original(messages)
        self.providers[1].complete = fail_first
        run = self.execute()
        relevant = [r for r in run["records"] if r["stage"].startswith("peer_independent")]
        self.assertTrue(all(r["status"] == "skipped" for r in relevant))

    def test_dry_run_never_initializes_api_clients(self):
        output = io.StringIO()
        with patch("peerlab.__main__.clients", side_effect=AssertionError("API initialized")), redirect_stdout(output):
            code = main(["run","--dry-run","--protocol","independent","--limit","1","--max-calls","14"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.getvalue())["planned_calls"], 14)

    def test_legacy_and_new_reports(self):
        run = self.execute()
        export_report(run, self.path)
        self.assertIn("peer_independent", (self.path/"scores.csv").read_text(encoding="utf-8-sig"))
        legacy = deepcopy(run)
        del legacy["config"]["arms"]
        del legacy["config"]["protocol"]
        legacy["records"] = [r for r in legacy["records"] if not r["stage"].startswith("peer_independent")]
        export_report(legacy, self.path/"legacy")
        self.assertNotIn("peer_independent", (self.path/"legacy"/"scores.csv").read_text(encoding="utf-8-sig"))

    def test_plan_counts(self):
        self.assertEqual(planned_calls(12, 1, "independent"), 168)
        self.assertEqual(planned_calls(12, 2, "classic"), 240)
        with self.assertRaises(ValueError):
            planned_calls(1,1,"unknown")
