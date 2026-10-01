"""Strict answer grading: no LLM judge and no execution of generated code."""

import json
import math
import re


def parse_answer(content):
    text = content.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    def reject_constant(value):
        raise ValueError(f"Non-finite JSON constant: {value}")
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result
    result = json.loads(text, parse_constant=reject_constant, object_pairs_hook=unique_object)
    if not isinstance(result, dict) or "answer" not in result:
        raise ValueError("Expected a JSON object with an answer field")
    return result["answer"]


def exact(actual, expected):
    if type(actual) is not type(expected):
        return False
    if isinstance(expected, list):
        return len(actual) == len(expected) and all(exact(a, b) for a, b in zip(actual, expected))
    if isinstance(expected, dict):
        return actual.keys() == expected.keys() and all(exact(actual[k], expected[k]) for k in expected)
    return actual == expected


def grade(case, content, finish_reason="stop"):
    if finish_reason != "stop":
        return {"passed": False, "reason": f"incomplete_output:{finish_reason}", "answer": None}
    try:
        answer = parse_answer(content)
    except (ValueError, TypeError):
        return {"passed": False, "reason": "invalid_json_answer", "answer": None}
    if case["check"] == "number":
        try:
            passed = (type(answer) in (int, float) and math.isfinite(answer)
                      and math.isclose(answer, case["expected"], rel_tol=0,
                                       abs_tol=case.get("tolerance", 1e-6)))
        except OverflowError:
            passed = False
    else:
        passed = exact(answer, case["expected"])
    return {"passed": bool(passed), "reason": "correct" if passed else "wrong_answer", "answer": answer}
