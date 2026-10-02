import hashlib
import json
from pathlib import Path
import unittest

from peerlab.analysis import analyze_run


class PublishedStudyTests(unittest.TestCase):
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
