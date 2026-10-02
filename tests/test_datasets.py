from copy import deepcopy
from fractions import Fraction
import tempfile
from pathlib import Path
import unittest

from peerlab.datasets import audit_cases, generate_cases, reference, write_dataset
from peerlab.experiment import load_cases


class DatasetTests(unittest.TestCase):
    def test_exact_bayes_matches_enumerated_population(self):
        params = {"prevalence_bp": 50, "sensitivity_bp": 9900, "false_positive_bp": 500}
        # A population of 100,000,000 gives 495,000 TP and 4,975,000 FP.
        self.assertEqual(reference("bayes", params), Fraction(495000, 495000+4975000))

    def test_f1_reference_by_precision_recall(self):
        params = {"tp": 8, "fn": 2, "fp": 18, "tn": 72}
        positive = 2/(1/Fraction(8,26)+1/Fraction(8,10))
        negative = 2/(1/Fraction(72,74)+1/Fraction(72,90))
        self.assertEqual(reference("macro_f1", params), (positive+negative)/2)

    def test_same_seed_and_unique_parameters(self):
        for family in ("bayes", "macro_f1"):
            a = generate_cases(family, 20, 123)
            self.assertEqual(a, generate_cases(family, 20, 123))
            self.assertNotEqual(a, generate_cases(family, 20, 124))
            self.assertEqual(len({c["prompt"] for c in a}), 20)
            self.assertEqual(audit_cases(a)["oracle_verified"], 20)

    def test_catches_mislabeled_or_modified_task(self):
        original = generate_cases(count=1)
        for field, value in (("expected", .123), ("prompt", "unrelated task"), ("tolerance", 1), ("check", "exact")):
            cases = deepcopy(original)
            cases[0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                audit_cases(cases)

    def test_manual_cases_are_not_claimed_verified(self):
        stats = audit_cases(load_cases())
        self.assertEqual(stats, {"cases":12, "oracle_verified":0, "manual_reference":12})

    def test_write_roundtrip_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root)/"tasks.json"
            data = generate_cases(count=2)
            write_dataset(path, data)
            self.assertEqual(load_cases(path), data)
            with self.assertRaises(FileExistsError):
                write_dataset(path, data)

    def test_invalid_count_and_parameters(self):
        for count in (0, -1, 10000):
            with self.assertRaises(ValueError):
                generate_cases(count=count)
        with self.assertRaises(ValueError):
            reference("bayes", {"prevalence_bp":True,"sensitivity_bp":9900,"false_positive_bp":500})
