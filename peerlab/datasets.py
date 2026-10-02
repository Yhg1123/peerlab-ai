"""Seeded numeric tasks with Fraction-based reference answers, never LLM-generated."""

from fractions import Fraction
from itertools import product
import json
from pathlib import Path
import random


def reference(kind, parameters):
    """Compute from integer inputs, without parsing or executing model output."""
    if kind == "bayes":
        if set(parameters) != {"prevalence_bp", "sensitivity_bp", "false_positive_bp"}:
            raise ValueError("Bayes oracle requires exactly three basis-point parameters.")
        if any(type(v) is not int or not 0 < v < 10000 for v in parameters.values()):
            raise ValueError("Basis-point parameters must be integers between 1 and 9999.")
        p, sensitivity, fpr = (Fraction(parameters[k], 10000) for k in
                               ("prevalence_bp", "sensitivity_bp", "false_positive_bp"))
        return p * sensitivity / (p * sensitivity + (1 - p) * fpr)
    if kind == "macro_f1":
        if set(parameters) != {"tp", "fn", "fp", "tn"}:
            raise ValueError("F1 oracle requires tp, fn, fp and tn.")
        if any(type(v) is not int or v <= 0 for v in parameters.values()):
            raise ValueError("Generated confusion-matrix cells must be positive integers.")
        tp, fn, fp, tn = (parameters[k] for k in ("tp", "fn", "fp", "tn"))
        return (Fraction(2 * tp, 2 * tp + fn + fp) + Fraction(2 * tn, 2 * tn + fn + fp)) / 2
    raise ValueError(f"Unknown oracle: {kind}")


def percent(bp):
    return f"{bp // 100}.{bp % 100:02d}".rstrip("0").rstrip(".")


def make_case(kind, parameters, index):
    expected = reference(kind, parameters)
    if kind == "bayes":
        p, tpr, fpr = (percent(parameters[k]) for k in
                       ("prevalence_bp", "sensitivity_bp", "false_positive_bp"))
        prompt = (f"某分类器识别一个占总体 {p}% 的稀有类别，真阳性率为 {tpr}%，假阳性率为 {fpr}%。"
                  "随机抽一个样本，分类器报阳性，它实际属于该类别的概率是多少？"
                  "answer 必须是0到1之间的数值，保留至少6位小数。")
        title, category = f"基准率变体 {index:03d}", "概率推理"
        formula = "p×TPR / (p×TPR + (1-p)×FPR)"
    else:
        tp, fn, fp, tn = (parameters[k] for k in ("tp", "fn", "fp", "tn"))
        prompt = (f"二分类混淆矩阵：真实正预测正{tp}、真实正预测负{fn}、真实负预测正{fp}、真实负预测负{tn}。"
                  "求两个类别各自F1的算术平均（macro-F1），不是accuracy也不是micro-F1。"
                  "answer 必须是0到1之间的数值，保留至少6位小数。")
        title, category = f"宏平均变体 {index:03d}", "机器学习"
        formula = "(2TP/(2TP+FN+FP) + 2TN/(2TN+FN+FP)) / 2"
    return {"id": f"generated-{kind}-{index:03d}", "category": category, "title": title,
            "prompt": prompt, "check": "number", "expected": float(expected), "tolerance": 0.000001,
            "rationale": f"{formula} = {expected.numerator}/{expected.denominator} ≈ {float(expected):.12f}。",
            "oracle": {"kind": kind, "parameters": parameters,
                       "exact_fraction": [expected.numerator, expected.denominator]}}


def generate_cases(kind="bayes", count=6, seed=42):
    if type(count) is not int or count < 1:
        raise ValueError("Count must be a positive integer.")
    if kind == "bayes":
        keys = ("prevalence_bp", "sensitivity_bp", "false_positive_bp")
        pool = list(product((5, 17, 25, 50, 80, 120, 200, 370, 600),
                            (8300, 9100, 9300, 9700, 9900), (13, 50, 170, 300, 500, 700, 1100)))
    elif kind == "macro_f1":
        keys = ("tp", "fn", "fp", "tn")
        pool = list(product((3, 8, 17, 29, 53), (2, 7, 11), (5, 18, 31), (37, 72, 113)))
    else:
        raise ValueError(f"Unknown family: {kind}")
    if count > len(pool):
        raise ValueError(f"This family has {len(pool)} distinct parameter sets.")
    selected = random.Random(seed).sample(pool, count)
    return [make_case(kind, dict(zip(keys, params)), i) for i, params in enumerate(selected, 1)]


def audit_cases(cases):
    """Refuse corrupted oracle-backed labels AND corrupted task wording."""
    verified = 0
    for case in cases:
        if "oracle" not in case:
            continue
        oracle = case["oracle"]
        try:
            recomputed = reference(oracle["kind"], oracle["parameters"])
            canonical = make_case(oracle["kind"], oracle["parameters"], 1)
            if (type(case["expected"]) not in (int, float) or case["expected"] != float(recomputed)
                    or case["check"] != "number" or case.get("tolerance") != canonical["tolerance"]
                    or case["prompt"] != canonical["prompt"]
                    or oracle["exact_fraction"] != [recomputed.numerator, recomputed.denominator]):
                raise ValueError("Oracle-backed prompt, reference or grading rule was modified.")
        except (KeyError, TypeError) as exc:
            raise ValueError(f"Malformed oracle for {case['id']}") from exc
        verified += 1
    return {"cases": len(cases), "oracle_verified": verified, "manual_reference": len(cases) - verified}


def write_dataset(path, cases):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as file:
        json.dump(cases, file, ensure_ascii=False, indent=2, allow_nan=False)
        file.write("\n")
