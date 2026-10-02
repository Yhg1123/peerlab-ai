"""Preregistered output-order x evidence-cap diagnostics for v3."""

import random
import statistics

from .dimensions import parsed_object, quantile
from .efficiency import FACTORIAL, FACTORIAL_ARMS, validate
from .experiment import atomic_json


def contract_components(row):
    obj = parsed_object(row)
    fields = obj is not None and set(obj) == {"answer", "evidence"}
    evidence = obj.get("evidence") if obj is not None else None
    nonblank = isinstance(evidence, str) and bool(evidence.strip())
    expected = ["answer", "evidence"] if row["arm"].startswith("answer_first") else ["evidence", "answer"]
    order = obj is not None and list(obj) == expected
    length = len(evidence) if isinstance(evidence, str) else None
    within = nonblank and length <= 80
    common = fields and nonblank and order
    return {"exact_fields": fields, "nonblank_evidence": nonblank, "requested_order": order,
            "evidence_characters": length, "within_80": within, "common_contract": common,
            "arm_contract": common and (within if row["arm"].endswith("_bounded") else True)}


def interaction(run, provider, samples=2000, seed=2026100301):
    """Mean [(EF-AF) unbounded - (EF-AF) bounded] on complete four-arm blocks."""
    index = {(r["case_id"], r["repeat"], r["arm"]): r for r in run["records"] if r["provider"] == provider}
    clusters = {}
    for case in run["cases"]:
        for rep in range(1, run["config"]["repeats"] + 1):
            rows = [index.get((case["id"], rep, arm)) for arm in FACTORIAL_ARMS]
            if all(r is not None and r["status"] == "ok" for r in rows):
                clusters.setdefault(case["id"], []).append(rows)
    blocks = [b for group in clusters.values() for b in group]
    tokens_known = bool(blocks) and all(r["usage"].get("total_tokens") is not None for b in blocks for r in b)

    def effect(selected, value):
        return statistics.mean(value(b[3])-value(b[2])-value(b[1])+value(b[0]) for b in selected) if selected else None

    values = {"accuracy": lambda r: int(r["grade"]["passed"]),
              "common_contract_and_correct": lambda r: int(contract_components(r)["common_contract"] and r["grade"]["passed"])}
    if tokens_known:
        values["total_tokens_per_block"] = lambda r: r["usage"]["total_tokens"]
    estimates = {k: effect(blocks, v) for k, v in values.items()}
    intervals = {k: None for k in values}
    if len(clusters) >= 2:
        rng = random.Random(seed)
        keys = sorted(clusters)
        # Precompute block effects to keep resampling inexpensive.
        effects = {k: {cid: [effect([b], v) for b in group] for cid, group in clusters.items()} for k, v in values.items()}
        draws = {k: [] for k in values}
        for _ in range(samples):
            chosen = rng.choices(keys, k=len(keys))
            for key in values:
                draws[key].append(statistics.mean(e for cid in chosen for e in effects[key][cid]))
        intervals = {k: [quantile(v, .025), quantile(v, .975)] for k, v in draws.items()}
    if not tokens_known:
        estimates["total_tokens_per_block"] = None
        intervals["total_tokens_per_block"] = None
    return {"provider": provider, "complete_blocks": len(blocks), "missing_blocks": len(run["cases"])*run["config"]["repeats"]-len(blocks),
            "task_clusters": len(clusters), "samples": samples, "seed": seed,
            "definition": "(evidence-first minus answer-first) unbounded minus bounded",
            "estimate": estimates, "percentile_95pct": intervals,
            "token_usage_complete": tokens_known}


def factorial_diagnostics(run):
    validate(run)
    if run["kind"] != FACTORIAL:
        raise ValueError("Factorial diagnostics require v3.")
    groups = []
    for provider in run["providers"]:
        for arm in FACTORIAL_ARMS:
            rows = [r for r in run["records"] if r["provider"] == provider["name"] and r["arm"] == arm and r["status"] == "ok"]
            parts = [contract_components(r) for r in rows]
            lengths = [p["evidence_characters"] for p in parts if p["evidence_characters"] is not None]
            groups.append({"provider": provider["name"], "arm": arm, "returned": len(rows),
                           **{k: sum(p[k] for p in parts) for k in ("exact_fields", "nonblank_evidence", "requested_order", "within_80", "common_contract", "arm_contract")},
                           "common_contract_and_correct": sum(p["common_contract"] and r["grade"]["passed"] for p, r in zip(parts, rows)),
                           "arm_contract_and_correct": sum(p["arm_contract"] and r["grade"]["passed"] for p, r in zip(parts, rows)),
                           "evidence_length_known": len(lengths), "median_evidence_characters": statistics.median(lengths) if lengths else None,
                           "p90_evidence_characters": quantile(lengths, .9)})
    return {"run_id": run["id"], "conditions": groups,
            "interactions": [interaction(run, p["name"]) for p in run["providers"]],
            "notes": ["Common contract: exact fields, nonblank string evidence, requested order; no length limit for any arm.",
                      "Arm contract additionally enforces 80 Unicode code points only for bounded arms; answer types are assessed by the unchanged grader.",
                      "within_80 is measured identically in all arms, not a requirement for unbounded arms.",
                      "Interaction uses complete four-arm task/repeat blocks; unknown usage suppresses its token estimate and interval.",
                      "Selected known tasks; repeated parameter variants are not independent task families. Bootstrap is descriptive, not a population claim."]}


def export_factorial(run, output):
    from pathlib import Path
    data = factorial_diagnostics(run)
    atomic_json(Path(output)/"factorial.json", data)
    text = "# 顺序 × 依据长度：分解诊断\n\n" + "\n\n".join(data["notes"]) + "\n\n"
    text += "|模型|条件|返回|共同契约且正确|本条件契约且正确|≤80字符|依据长度中位数/P90|\n|---|---|---:|---:|---:|---:|---|\n"
    for g in data["conditions"]:
        text += f"|{g['provider']}|{g['arm']}|{g['returned']}|{g['common_contract_and_correct']}|{g['arm_contract_and_correct']}|{g['within_80']}|{g['median_evidence_characters']} / {g['p90_evidence_characters']}|\n"
    text += "\n## 交互项\n\n定义：(不限长时的先依据−先答案) − (限长时的先依据−先答案)。正确率单位为比例差，总token为每个完整区组的差中之差。区间按题聚类2000次；不做显著性结论。\n\n"
    for p in data["interactions"]:
        text += f"### {p['provider']}\n\n完整区组{p['complete_blocks']}，缺失{p['missing_blocks']}，题目簇{p['task_clusters']}。\n\n"
        for key, value in p["estimate"].items():
            text += f"- {key}: {value}; 95%描述区间 {p['percentile_95pct'][key]}\n"
        text += "\n"
    (Path(output)/"factorial.md").write_text(text, encoding="utf-8")
    return data
