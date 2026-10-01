import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

from peerlab.client import APIError, Client, NoRedirect
from peerlab.experiment import load_cases, run_experiment, summarize
from peerlab.grading import grade, parse_answer
from peerlab.report import export_report


class FakeClient:
    max_tokens = 700
    timeout = 90
    base_url = "https://example.invalid"

    def __init__(self, name, fail=False):
        self.name = name
        self.model = "fake-" + name
        self.fail = fail
        self.calls = []

    def complete(self, messages):
        self.calls.append(messages)
        if self.fail:
            raise APIError("HTTP 429: Rate limited.")
        return {"content": '{"answer": 10, "explanation": "test"}', "model": self.model,
                "finish_reason": "stop", "latency_ms": 12,
                "usage": {"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18}}


class GradingTests(unittest.TestCase):
    def test_all_reference_answers_pass(self):
        for case in load_cases():
            with self.subTest(case=case["id"]):
                self.assertTrue(grade(case, json.dumps({"answer": case["expected"]}))["passed"])

    def test_numeric_reference_derivations(self):
        values = {c["id"]: c["expected"] for c in load_cases()}
        self.assertAlmostEqual(values["bayes-base-rate"], .005*.99/(.005*.99+.995*.05))
        self.assertAlmostEqual(values["metric-f1"], (16/36 + 144/164)/2)
        self.assertAlmostEqual(values["expected-draws"], 11/6)
        self.assertLess((81+192)/(87+263), (234+55)/(270+80))
        self.assertEqual(values["simpson-paradox"], "B")

    def test_no_substring_scoring_or_nonstandard_json(self):
        for content in ['some text {"answer":10}', '{"answer":NaN}', '{"answer":10,"answer":11}', '[10]']:
            with self.subTest(content=content), self.assertRaises(ValueError):
                parse_answer(content)

    def test_boolean_is_not_a_number_and_strings_are_not_coerced(self):
        case = {"check": "number", "expected": 1}
        for answer in [True, "1", None]:
            self.assertFalse(grade(case, json.dumps({"answer": answer}))["passed"])
        self.assertFalse(grade({"check":"exact", "expected":{"n":1}}, '{"answer":{"n":true}}')["passed"])

    def test_fences_and_truncation(self):
        case = {"check": "number", "expected": 10}
        self.assertTrue(grade(case, '```json\n{"answer":10}\n```')["passed"])
        self.assertFalse(grade(case, '{"answer":10}', "length")["passed"])

    def test_huge_numeric_response_is_a_failed_answer(self):
        self.assertFalse(grade({"check":"number", "expected":10}, '{"answer":'+ '9'*400+'}')["passed"])


class ExperimentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "run"
        self.cases = [next(c for c in load_cases() if c["id"] == "critical-path")]
        self.clients = [FakeClient("deepseek"), FakeClient("kimi")]

    def run_it(self, **kwargs):
        return run_experiment(self.clients, self.cases, self.path, progress=lambda x: None, **kwargs)

    def test_protocol_and_no_reference_leak(self):
        run = self.run_it(max_calls=10)
        self.assertEqual(run["status"], "complete")
        self.assertEqual(run["calls_attempted"], 10)
        for client in self.clients:
            self.assertEqual(len(client.calls), 5)
            for messages in client.calls:
                self.assertNotIn(self.cases[0]["rationale"], json.dumps(messages, ensure_ascii=False))
        for provider in ("deepseek", "kimi"):
            rows = [r for r in run["records"] if r["provider"] == provider]
            peer = next(r for r in rows if r["stage"] == "peer")
            self_review = next(r for r in rows if r["stage"] == "self_review_for_"+provider)
            self.assertEqual(json.loads(self_review["messages"][1]["content"])["candidate"], '{"answer": 10, "explanation": "test"}')
            self.assertIn("original_answer", peer["messages"][1]["content"])
        self.assertEqual(json.loads((self.path/"run.json").read_text(encoding="utf-8"))["status"], "complete")

    def test_budget_prevents_requests_and_output_creation(self):
        with self.assertRaises(ValueError):
            self.run_it(max_calls=9)
        self.assertFalse(self.path.exists())
        self.assertFalse(any(c.calls for c in self.clients))

    def test_failures_are_separate_from_incorrect_answers(self):
        self.clients[1].fail = True
        run = self.run_it(max_calls=10)
        self.assertEqual(run["status"], "partial")
        self.assertEqual(run["calls_attempted"], 5)
        self.assertEqual(run["summary"]["kimi"]["baseline"]["completed"], 0)
        self.assertIsNone(run["summary"]["kimi"]["baseline"]["accuracy"])
        self.assertEqual(run["summary"]["deepseek"]["peer"]["paired"], 0)

    def test_repeated_pairs_are_counted_separately(self):
        run = self.run_it(max_calls=20, repeats=2)
        self.assertEqual(run["summary"]["deepseek"]["peer"]["paired"], 2)

    def test_interrupt_saves_pending_attempt(self):
        with patch.object(self.clients[0], "complete", side_effect=KeyboardInterrupt):
            run = self.run_it(max_calls=10)
        self.assertEqual(run["status"], "interrupted")
        self.assertTrue(any(r["status"] == "pending" for r in run["records"]))
        self.assertTrue((self.path / "run.json").exists())

    def test_regressions_and_html_injection(self):
        run = self.run_it(max_calls=10)
        peer = next(r for r in run["records"] if r["provider"] == "deepseek" and r["stage"] == "peer")
        peer["grade"]["passed"] = False
        peer["content"] = '</script><script>alert("injected")</script>'
        self.assertEqual(summarize(run)["deepseek"]["peer"]["regressed"], 1)
        export_report(run, self.path)
        html = (self.path/"report.html").read_text(encoding="utf-8")
        self.assertNotIn(peer["content"], html)
        self.assertIn('\\u003c/script\\u003e', html)
        self.assertNotIn("innerHTML", html)
        self.assertTrue((self.path/"scores.csv").exists())

    def test_existing_output_is_not_overwritten(self):
        self.path.mkdir()
        with self.assertRaises(FileExistsError):
            self.run_it(max_calls=10)


class ClientTests(unittest.TestCase):
    def test_no_key_in_repr(self):
        client = Client("fake", "fake", "secret-value", "https://example.invalid")
        self.assertNotIn("secret-value", repr(client))

    def test_http_errors_are_sanitized(self):
        client = Client("fake", "fake", "secret-value", "https://example.invalid")
        err = urllib.error.HTTPError("https://example.invalid", 401, "secret-value", {}, None)
        with patch("urllib.request.build_opener") as opener:
            opener.return_value.open.side_effect = err
            with self.assertRaises(APIError) as raised:
                client.models()
            self.assertNotIn("secret-value", str(raised.exception))

    def test_redirect_is_blocked(self):
        with self.assertRaises(APIError):
            NoRedirect().redirect_request(None,None,302,"",{},"https://example.invalid")

    def test_bad_usage_is_a_safe_error(self):
        client = Client("fake", "fake", "secret-value", "https://example.invalid")
        response = {"choices":[{"message":{"content":"hello"},"finish_reason":"stop"}], "usage":"invalid"}
        with patch.object(client, "_request", return_value=response), self.assertRaises(APIError):
            client.complete([])


if __name__ == "__main__":
    unittest.main()
