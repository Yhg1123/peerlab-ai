from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from peerlab.analysis import analyze_run, condition_costs, export_analysis, validate_run
from peerlab.experiment import load_cases, run_experiment
from peerlab.grading import grade
from test_peerlab import FakeClient


class AnalysisTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.cases = []
        for i in range(4):
            case = deepcopy(next(c for c in load_cases() if c["id"] == "critical-path"))
            case["id"] = f"case-{i}"
            self.cases.append(case)
        self.run = run_experiment([FakeClient("deepseek"),FakeClient("kimi")], self.cases,
                                  self.path/"run", protocol="independent",max_calls=56,
                                  progress=lambda _:None)

    def make_wrong(self, case_id, arm):
        r = next(r for r in self.run["records"] if r["provider"]=="deepseek" and r["case_id"]==case_id and r["stage"]==arm)
        r["content"] = '{"answer":11}'
        r["grade"] = grade(self.cases[0],r["content"],r["finish_reason"])

    def test_four_cells_use_matched_pairs(self):
        self.make_wrong("case-1","peer_independent")
        self.make_wrong("case-2","peer")
        self.make_wrong("case-3","peer")
        self.make_wrong("case-3","peer_independent")
        result = analyze_run(self.run)["overall"][0]
        self.assertEqual([result[k] for k in ("both_correct","only_left_correct","only_right_correct","both_wrong")],[1,1,1,1])
        self.assertEqual(result["paired"],4)
        self.assertEqual(result["delta_right_minus_left"],0)

    def test_errors_reduce_coverage_not_accuracy(self):
        record = next(r for r in self.run["records"] if r["provider"]=="deepseek" and r["stage"]=="peer_independent")
        record["status"] = "error"
        self.run["status"] = "partial"
        row = analyze_run(self.run)["overall"][0]
        self.assertEqual(row["paired"],3)
        self.assertEqual(row["missing_pair"],1)
        self.assertEqual(row["right_accuracy"],1)

    def test_recomputed_grade_catches_tampering(self):
        next(r for r in self.run["records"] if "grade" in r)["grade"]["passed"] = False
        with self.assertRaisesRegex(ValueError,"recomputed grade"):
            validate_run(self.run)

    def test_hash_duplicate_and_dependency_checks(self):
        original = deepcopy(self.run)
        self.run["cases"][0]["expected"] = 99
        with self.assertRaisesRegex(ValueError,"hash"):
            validate_run(self.run)
        self.run = deepcopy(original)
        self.run["records"].append(deepcopy(self.run["records"][0]))
        with self.assertRaisesRegex(ValueError,"Duplicate call"):
            validate_run(self.run)
        self.run = original
        next(r for r in self.run["records"] if r["dependencies"])["dependencies"] = []
        with self.assertRaisesRegex(ValueError,"Dependency links"):
            validate_run(self.run)

    def test_path_costs_reuse_two_baselines_without_double_counting_total(self):
        result = analyze_run(self.run)
        costs = {r["arm"]:r for r in result["condition_costs"] if r["provider"]=="deepseek"}
        self.assertEqual(costs["baseline"]["returned_calls"],4)
        self.assertEqual(costs["peer"]["returned_calls"],12)
        self.assertEqual(costs["self"]["returned_calls"],12)
        self.assertEqual(costs["peer_independent"]["returned_calls"],16)
        self.assertEqual(result["total_usage"]["returned_calls"],56)
        self.assertEqual(result["total_usage"]["total_tokens"],56*18)

    def test_missing_usage_is_not_silently_zero(self):
        self.run["records"][0]["usage"] = {}
        result = analyze_run(self.run)
        self.assertEqual(result["total_usage"]["missing_total_tokens_calls"],1)
        self.assertEqual(result["total_usage"]["total_tokens"],55*18)

    def test_old_pilot_can_be_analyzed(self):
        path = Path(__file__).resolve().parents[1]/"examples"/"pilot"/"run.json"
        run = json.loads(path.read_text(encoding="utf-8"))
        result = analyze_run(run,"baseline","peer")
        self.assertEqual(result["audit"]["grades_recomputed"],18)
        self.assertEqual(result["overall"][0]["delta_right_minus_left"],0)

    def test_no_comparison_of_missing_or_identical_condition(self):
        with self.assertRaises(ValueError):
            analyze_run(self.run,"peer","peer")
        with self.assertRaises(ValueError):
            analyze_run(self.run,"peer","unknown")

    def test_export_reports_all_four_cells(self):
        export_analysis(self.run,self.path/"analysis")
        self.assertIn("仅右对",(self.path/"analysis"/"analysis.md").read_text(encoding="utf-8"))
        self.assertTrue((self.path/"analysis"/"analysis.json").is_file())
