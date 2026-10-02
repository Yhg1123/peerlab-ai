"""Predefined descriptive slices, contract checks and task-cluster uncertainty."""

from collections import Counter
from html import escape
import json
import math
from pathlib import Path
import random
import re
import statistics

from .efficiency import EXTENDED, EXTENDED_COMPARISONS, arms_for, paired, usage, validate
from .experiment import atomic_json
from .grading import parse_answer


def quantile(values, q):
    if not values:
        return None
    values = sorted(values)
    pos = (len(values) - 1) * q
    lower = int(pos)
    upper = min(lower + 1, len(values) - 1)
    return values[lower] + (values[upper] - values[lower]) * (pos - lower)


def parsed_object(row):
    if row["status"] != "ok" or row["finish_reason"] != "stop":
        return None
    try:
        parse_answer(row["content"])  # Reject duplicate keys and non-finite literals first.
        text = row["content"].strip()
        fenced = re.fullmatch(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
        return json.loads(fenced.group(1) if fenced else text)
    except (ValueError, TypeError):
        return None


def contract(row):
    obj = parsed_object(row)
    if obj is None:
        return False
    if row["arm"] == "compact_answer":
        return list(obj) == ["answer"]
    if row["arm"] == "compact_evidence":
        return (list(obj) == ["evidence", "answer"] and isinstance(obj["evidence"], str)
                and 0 < len(obj["evidence"]) <= 80)
    return (set(obj) == {"answer", "explanation"} and isinstance(obj["explanation"], str)
            and bool(obj["explanation"].strip()))


def cluster_interval(run, provider, left, right, samples=2000, seed=2026100301):
    """Resample task IDs with replacement; keep all available repeats of each ID."""
    comparison = paired(run, provider, left, right)
    records = {r["id"]: r for r in run["records"]}
    clusters = {}
    for p in comparison["pairs"]:
        a, b = records[p["left_id"]], records[p["right_id"]]
        clusters.setdefault(p["case_id"], []).append((a, b))
    keys = sorted(clusters)
    if len(keys) < 2:
        return {"task_clusters": len(keys), "samples": samples, "seed": seed,
                "accuracy_delta_95pct": None, "total_token_saving_95pct": None}
    rng = random.Random(seed)
    deltas, savings = [], []
    for _ in range(samples):
        pairs = [pair for k in rng.choices(keys, k=len(keys)) for pair in clusters[k]]
        deltas.append(sum(int(b["grade"]["passed"]) - int(a["grade"]["passed"]) for a, b in pairs) / len(pairs))
        if all(a["usage"].get("total_tokens") is not None and b["usage"].get("total_tokens") is not None for a, b in pairs):
            lt = sum(a["usage"]["total_tokens"] for a, _ in pairs)
            rt = sum(b["usage"]["total_tokens"] for _, b in pairs)
            if lt:
                savings.append(1 - rt / lt)
    # Missing usage anywhere in the comparison suppresses the token interval.
    complete = comparison["tokens"]["total_tokens"]["missing_pairs"] == 0
    return {"task_clusters": len(keys), "samples": samples, "seed": seed,
            "accuracy_delta_95pct": [quantile(deltas, .025), quantile(deltas, .975)],
            "total_token_saving_95pct": [quantile(savings, .025), quantile(savings, .975)] if complete and savings else None}


def diagnostics(run):
    audit = validate(run)
    if run["kind"] != EXTENDED:
        raise ValueError("Dimensions are defined for token-efficiency-v2 only.")
    tasks = {c["id"]: c for c in run["cases"]}
    names = [p["name"] for p in run["providers"]]
    repeats = run["config"]["repeats"]
    scopes = {"all": list(tasks)}
    for category in sorted({c["category"] for c in tasks.values()}):
        scopes["category:" + category] = [c["id"] for c in tasks.values() if c["category"] == category]
    scopes["reference:generated"] = [c["id"] for c in tasks.values() if "oracle" in c]
    scopes["reference:manual"] = [c["id"] for c in tasks.values() if "oracle" not in c]
    groups, comparisons, stability, sensitivity = [], [], [], []
    for name in names:
        for arm in arms_for(run["kind"]):
            all_rows = [r for r in run["records"] if r["provider"] == name and r["arm"] == arm]
            for scope, ids in scopes.items():
                rows = [r for r in all_rows if r["case_id"] in ids]
                good = [r for r in rows if r["status"] == "ok"]
                latency = [r["latency_ms"] for r in good if type(r.get("latency_ms")) in (float, int) and math.isfinite(r["latency_ms"]) and r["latency_ms"] >= 0]
                correct = sum(r["grade"]["passed"] for r in good)
                planned = len(ids) * repeats
                groups.append({"provider": name, "arm": arm, "scope": scope, "unique_tasks": len(ids),
                               "planned": planned, "returned": len(good), "correct": correct,
                               "answer_accuracy_returned": correct / len(good) if good else None,
                               "delivered_correct_fraction": correct / planned if planned else None,
                               "valid_json": sum(parsed_object(r) is not None for r in good),
                               "contract_ok": sum(contract(r) for r in good),
                               "contract_and_correct": sum(contract(r) and r["grade"]["passed"] for r in good),
                               "failure_reasons": dict(sorted(Counter(r["grade"]["reason"] for r in good if not r["grade"]["passed"]).items())),
                               "request_errors": sum(r["status"] == "error" for r in rows),
                               "latency": {"known_calls": len(latency), "missing_calls": len(good)-len(latency),
                                           "median_ms": statistics.median(latency) if latency else None,
                                           "p90_ms": quantile(latency, .9)}, "usage": usage(rows)})
            by_case = {cid: [r for r in all_rows if r["case_id"] == cid and r["status"] == "ok"] for cid in tasks}
            eligible = [rows for rows in by_case.values() if len(rows) == repeats]
            parseable = [rows for rows in eligible if all(parsed_object(r) is not None for r in rows)]
            stability.append({"provider": name, "arm": arm, "repeats": repeats,
                              "all_repeats_returned_tasks": len(eligible), "missing_task_clusters": len(tasks)-len(eligible),
                              "all_repeats_correct_tasks": sum(all(r["grade"]["passed"] for r in rows) for rows in eligible),
                              "mixed_correctness_tasks": sum(0 < sum(r["grade"]["passed"] for r in rows) < repeats for rows in eligible),
                              "all_repeats_parseable_tasks": len(parseable),
                              "identical_typed_answers_tasks": sum(len({json.dumps(parsed_object(r)["answer"], ensure_ascii=False, sort_keys=True) for r in rows}) == 1 for rows in parseable)})
            numerical = [r for r in all_rows if tasks[r["case_id"]]["check"] == "number" and r["status"] == "ok"]
            errors = []
            for r in numerical:
                obj = parsed_object(r)
                value = obj["answer"] if obj is not None else None
                try:
                    if type(value) in (int, float) and math.isfinite(value):
                        errors.append(abs(value - tasks[r["case_id"]]["expected"]))
                except OverflowError:
                    pass
            sensitivity.append({"provider": name, "arm": arm, "numeric_returned": len(numerical),
                                "finite_numeric_answers": len(errors), "median_absolute_error": statistics.median(errors) if errors else None,
                                "absolute_error_thresholds": {str(t): sum(e <= t for e in errors) for t in (1e-6, 1e-4, 1e-2)},
                                "note": "Sensitivity only; original per-task grading is unchanged. Invalid/truncated outputs never pass."})
        for label, left, right in EXTENDED_COMPARISONS:
            for scope, ids in scopes.items():
                subset = {**run, "cases": [tasks[i] for i in ids]}
                entry = {"comparison": label, "scope": scope, **paired(subset, name, left, right)}
                if scope == "all":
                    entry["cluster_bootstrap"] = cluster_interval(run, name, left, right)
                comparisons.append(entry)
    return {"audit": audit, "run_id": run["id"], "conditions": groups, "comparisons": comparisons,
            "stability": stability, "numeric_sensitivity": sensitivity,
            "notes": ["Percentile bootstrap resamples task clusters, not independent repeats; 2000 draws, fixed seed 2026100301.",
                      "Intervals describe this selected task set, are not adjusted for multiple comparisons and do not establish noninferiority.",
                      "Latency covers returned responses only; timeout durations and server load/cache are uncontrolled.",
                      "Contract checks field structure and evidence length/order, not semantic truth of explanations.",
                      "Scope rows overlap; categories/reference groups cannot be summed together."]}


def export_dimensions(run, output):
    data = diagnostics(run)
    dest = Path(output)
    dest.mkdir(parents=True, exist_ok=True)
    atomic_json(dest / "dimensions.json", data)
    def fmt(value):
        return "—" if value is None else f"{value:.1f}"
    def table(headers, rows):
        return "\n".join(["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"] +
                         ["| " + " | ".join(str(x).replace("|", "\\|") for x in row) + " |" for row in rows])
    text = "# 多维度分析\n\n" + "\n\n".join(data["notes"]) + "\n\n## 按任务类别\n\n"
    text += table(["模型", "条件", "范围", "正确/返回/计划", "契约合格且正确", "延迟中位数ms", "延迟P90ms"],
                  [[g["provider"], g["arm"], g["scope"], f"{g['correct']}/{g['returned']}/{g['planned']}", g["contract_and_correct"], fmt(g["latency"]["median_ms"]), fmt(g["latency"]["p90_ms"])] for g in data["conditions"]])
    text += "\n\n## 两次采样的稳定性\n\n" + table(["模型", "条件", "完整任务", "始终正确", "对错变化", "均可解析任务", "答案完全相同"],
                 [[s[k] for k in ("provider", "arm", "all_repeats_returned_tasks", "all_repeats_correct_tasks", "mixed_correctness_tasks", "all_repeats_parseable_tasks", "identical_typed_answers_tasks")] for s in data["stability"]])
    text += "\n\n## 数值误差敏感性（不改原判分）\n\n" + table(["模型", "条件", "数值题返回", "有限数值答案", "误差≤1e-6", "≤1e-4", "≤1e-2", "绝对误差中位数"],
                [[s["provider"], s["arm"], s["numeric_returned"], s["finite_numeric_answers"], *s["absolute_error_thresholds"].values(), s["median_absolute_error"]] for s in data["numeric_sensitivity"]])
    text += "\n\n## 整体配对与任务聚类区间\n\n" + table(["模型", "比较", "有效/缺失", "改善/退步", "正确率差", "95%描述区间", "总token节省", "95%描述区间"],
                [[p["provider"], p["comparison"], f"{p['paired']}/{p['missing_pairs']}", f"{p['only_right_correct']}/{p['only_left_correct']}", p["accuracy_delta"], p["cluster_bootstrap"]["accuracy_delta_95pct"], p["tokens"]["total_tokens"]["saved_fraction"], p["cluster_bootstrap"]["total_token_saving_95pct"]] for p in data["comparisons"] if p["scope"] == "all"])
    text += "\n\n各题型的完整配对、输入/输出token与缺失数见 dimensions.json。区间不是总体能力估计；不能据区间覆盖0宣称等价。\n"
    (dest / "dimensions.md").write_text(text, encoding="utf-8")
    return data
