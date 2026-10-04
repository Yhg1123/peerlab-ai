import hashlib
import json
from pathlib import Path
import unittest

from peerlab.analysis import analyze_run
from peerlab.efficiency import analyze
from peerlab.dimensions import diagnostics
from peerlab.factorial import factorial_diagnostics
from peerlab.native_types import type_diagnostics


class PublishedStudyTests(unittest.TestCase):
    def test_v4_raw_plan_type_results_and_missing_pairs_reproduce(self):
        root = Path(__file__).resolve().parents[1]
        folder = root / "examples/token-efficiency-v4"
        raw = (folder / "run.json").read_bytes()
        run = json.loads(raw)
        provenance = json.loads((folder / "provenance.json").read_text(encoding="utf-8"))
        plan = json.loads((root / "docs/studies/token-efficiency-v4-plan.json").read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256(raw).hexdigest(), provenance["run_json_sha256"])
        self.assertEqual({k: run["config"][k] for k in plan}, plan)
        for name, function in (("analysis", analyze), ("dimensions", diagnostics), ("types", type_diagnostics)):
            self.assertEqual(function(run), json.loads((folder / f"{name}.json").read_text(encoding="utf-8")))
        result = analyze(run)
        self.assertEqual(result["attempted"], 128)
        self.assertEqual(result["audit"]["grades_recomputed"], 126)
        self.assertEqual(result["usage"]["total_tokens"]["known_sum"], 38089)
        self.assertEqual([r["id"] for r in run["records"] if r["status"] == "error"], [66, 88])
        pairs = {p["provider"]: p for p in result["comparisons"]}
        self.assertEqual((pairs["deepseek"]["paired"], pairs["kimi"]["paired"]), (32, 30))
        self.assertEqual(pairs["kimi"]["tokens"]["total_tokens"]["left_sum"], 9820)
        self.assertEqual(pairs["kimi"]["tokens"]["total_tokens"]["right_sum"], 10796)

    def test_v3_raw_plan_missingness_and_factorial_reproduction(self):
        root = Path(__file__).resolve().parents[1]
        folder = root/"examples/token-efficiency-v3"
        raw = (folder/"run.json").read_bytes()
        run = json.loads(raw)
        provenance = json.loads((folder/"provenance.json").read_text(encoding="utf-8"))
        plan = json.loads((root/"docs/studies/token-efficiency-v3-plan.json").read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256(raw).hexdigest(), provenance["run_json_sha256"])
        self.assertEqual({k:run["config"][k] for k in plan}, plan)
        for name, function in (("analysis", analyze), ("dimensions", diagnostics), ("factorial", factorial_diagnostics)):
            self.assertEqual(function(run), json.loads((folder/f"{name}.json").read_text(encoding="utf-8")))
        result = analyze(run)
        self.assertEqual(result["attempted"], 256)
        self.assertEqual(result["audit"]["grades_recomputed"], 255)
        self.assertEqual(result["usage"]["total_tokens"]["known_sum"], 72608)
        self.assertEqual([r["id"] for r in run["records"] if r["status"] == "error"], [235])
        effects = factorial_diagnostics(run)["interactions"]
        self.assertEqual([(p["complete_blocks"],p["missing_blocks"]) for p in effects], [(32,0),(31,1)])
        self.assertEqual([p["estimate"]["accuracy"] for p in effects], [.40625,0])

    def test_evidence_matches_preregistered_plan_and_saved_analysis(self):
        root = Path(__file__).resolve().parents[1]
        folder = root/"examples"/"review-study-v1"
        raw = (folder/"run.json").read_bytes()
        run = json.loads(raw)
        provenance = json.loads((folder/"provenance.json").read_text(encoding="utf-8"))
        plan = json.loads((root/"docs"/"studies"/"review-study-v1-plan.json").read_text(encoding="utf-8"))
        saved = json.loads((folder/"analysis.json").read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256(raw).hexdigest(), provenance["run_json_sha256"])
        self.assertEqual(run["dataset_sha256"],plan["dataset_sha256"])
        for field in ("seed", "repeats", "protocol", "arms", "planned_calls"):
            self.assertEqual(run["config"][field],plan[field])
        self.assertEqual([c["id"] for c in run["cases"]],plan["cases"])
        for provider in run["providers"]:
            self.assertEqual(provider["max_tokens"],plan["max_output_tokens_per_call"])
        self.assertEqual(analyze_run(run),saved)

    def test_token_study_preserves_plan_raw_bytes_and_paired_denominators(self):
        root = Path(__file__).resolve().parents[1]
        folder = root / "examples" / "token-efficiency-v1"
        raw = (folder / "run.json").read_bytes()
        run = json.loads(raw)
        provenance = json.loads((folder / "provenance.json").read_text(encoding="utf-8"))
        plan = json.loads((root / "docs/studies/token-efficiency-v1-plan.json").read_text(encoding="utf-8"))
        saved = json.loads((folder / "analysis.json").read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256(raw).hexdigest(), provenance["run_json_sha256"])
        self.assertEqual({k: run["config"][k] for k in plan}, plan)
        self.assertEqual(analyze(run), saved)
        self.assertEqual(saved["audit"]["grades_recomputed"], 95)
        comparisons = {p["provider"]: p for p in saved["comparisons"] if p["comparison"] == "combined"}
        self.assertEqual(comparisons["deepseek"]["paired"], 11)
        self.assertEqual(comparisons["kimi"]["paired"], 12)
        self.assertEqual(comparisons["deepseek"]["tokens"]["total_tokens"]["left_sum"], 2631)
        self.assertEqual(comparisons["kimi"]["tokens"]["total_tokens"]["right_sum"], 1485)

    def test_v2_evidence_matches_plan_dimensions_and_contract_counts(self):
        root = Path(__file__).resolve().parents[1]
        folder = root / "examples" / "token-efficiency-v2"
        raw = (folder / "run.json").read_bytes()
        run = json.loads(raw)
        provenance = json.loads((folder / "provenance.json").read_text(encoding="utf-8"))
        plan = json.loads((root / "docs/studies/token-efficiency-v2-plan.json").read_text(encoding="utf-8"))
        self.assertEqual(hashlib.sha256(raw).hexdigest(), provenance["run_json_sha256"])
        self.assertEqual({k:run["config"][k] for k in plan}, plan)
        saved = json.loads((folder / "analysis.json").read_text(encoding="utf-8"))
        dims = json.loads((folder / "dimensions.json").read_text(encoding="utf-8"))
        self.assertEqual(analyze(run), saved)
        self.assertEqual(diagnostics(run), dims)
        self.assertEqual(saved["audit"]["grades_recomputed"], 288)
        self.assertEqual(saved["usage"]["total_tokens"]["known_sum"], 62837)
        groups = {g["provider"]:g for g in dims["conditions"] if g["scope"]=="all" and g["arm"]=="compact_evidence"}
        self.assertEqual((groups["deepseek"]["correct"],groups["deepseek"]["contract_and_correct"]),(40,27))
        self.assertEqual((groups["kimi"]["correct"],groups["kimi"]["contract_and_correct"]),(22,10))
