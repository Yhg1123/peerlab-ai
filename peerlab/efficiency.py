"""A frozen 2x2 prompt/output ablation with paired quality and token accounting."""

from datetime import datetime, timezone
import json
from pathlib import Path
import random
import uuid

from . import __version__
from .client import APIError
from .datasets import audit_cases
from .experiment import atomic_json, dataset_hash
from .grading import grade

PROTOCOL = "token-efficiency-v1"
PREFIXES = {
    "verbose": "你是严谨的研究助理。请认真阅读并解答用户提供的任务，遵循题目给出的条件和答案类型要求。不要自报模型或厂商。不要使用工具，也不要执行代码。",
    "compact": "解题；按题目类型作答。不自报身份，不用工具或执行代码。",
}
OUTPUTS = {
    "explain": "只输出 JSON 对象，含 answer 与简短 explanation。",
    "answer": "只输出 JSON 对象，仅含 answer，不要解释。",
}
ARMS = tuple(f"{p}_{o}" for p in PREFIXES for o in OUTPUTS)
COMPARISONS = (
    ("combined", "verbose_explain", "compact_answer"),
    ("prompt_with_explanation", "verbose_explain", "compact_explain"),
    ("prompt_without_explanation", "verbose_answer", "compact_answer"),
    ("output_with_verbose_prompt", "verbose_explain", "verbose_answer"),
    ("output_with_compact_prompt", "compact_explain", "compact_answer"),
)
METRICS = ("prompt_tokens", "completion_tokens", "total_tokens")
EXTENDED = "token-efficiency-v2"
EXTENDED_ARMS = ("verbose_explain", "compact_answer", "compact_evidence")
EVIDENCE_OUTPUT = "只输出一个 JSON 对象，先写 evidence（不超过80字的简短计算依据或核验结果），再写 answer。answer必须与evidence一致。"
EXTENDED_COMPARISONS = (
    ("combined", "verbose_explain", "compact_answer"),
    ("evidence_vs_answer", "compact_answer", "compact_evidence"),
    ("evidence_vs_baseline", "verbose_explain", "compact_evidence"),
)
FACTORIAL = "token-efficiency-v3"
FACTORIAL_ARMS = ("answer_first_bounded", "evidence_first_bounded",
                  "answer_first_unbounded", "evidence_first_unbounded")
FACTORIAL_COMPARISONS = (
    ("order_bounded", FACTORIAL_ARMS[0], FACTORIAL_ARMS[1]),
    ("order_unbounded", FACTORIAL_ARMS[2], FACTORIAL_ARMS[3]),
    ("remove_cap_answer_first", FACTORIAL_ARMS[0], FACTORIAL_ARMS[2]),
    ("remove_cap_evidence_first", FACTORIAL_ARMS[1], FACTORIAL_ARMS[3]),
)


def comparisons_for(protocol):
    return {PROTOCOL: COMPARISONS, EXTENDED: EXTENDED_COMPARISONS,
            FACTORIAL: FACTORIAL_COMPARISONS}[protocol]


def arms_for(protocol):
    if protocol == PROTOCOL:
        return ARMS
    if protocol == EXTENDED:
        return EXTENDED_ARMS
    if protocol == FACTORIAL:
        return FACTORIAL_ARMS
    raise ValueError("Unknown efficiency protocol.")


def messages_for(case, arm):
    if arm in FACTORIAL_ARMS:
        order = "answer、evidence" if arm.startswith("answer_first") else "evidence、answer"
        cap = "evidence长度不超过80个Unicode字符（包含标点和空格）。" if arm.endswith("_bounded") else ""
        suffix = (f"只输出一个JSON对象，仅含answer和evidence两个字段，字段顺序为{order}。"
                  "evidence是非空字符串，给出简短计算依据或核验结果。" + cap + "answer必须与evidence一致。")
        return [{"role": "system", "content": PREFIXES["compact"] + suffix},
                {"role": "user", "content": case["prompt"]}]
    prefix, output = arm.split("_")
    suffix = EVIDENCE_OUTPUT if output == "evidence" else OUTPUTS[output]
    return [{"role": "system", "content": PREFIXES[prefix] + suffix},
            {"role": "user", "content": case["prompt"]}]


def make_plan(cases, repeats=1, seed=42, max_tokens=700, timeout=90, protocol=PROTOCOL):
    arms = arms_for(protocol)
    if not cases or type(repeats) is not int or repeats < 1:
        raise ValueError("A nonempty dataset and positive repeats are required.")
    if len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Duplicate case IDs.")
    audit_cases(cases)
    if max_tokens < 1 or timeout < 1:
        raise ValueError("Output limit and timeout must be positive.")
    calls = len(cases) * repeats * 2 * len(arms)
    return {"protocol": protocol, "arms": list(arms),
            "system_prompts": {a: messages_for(cases[0], a)[0]["content"] for a in arms},
            "cases": [c["id"] for c in cases], "dataset_sha256": dataset_hash(cases),
            "repeats": repeats, "seed": seed, "planned_calls": calls,
            "temperature": 0.6, "thinking": "disabled", "retries": 0,
            "max_output_tokens_per_call": max_tokens, "timeout_seconds": timeout,
            "output_token_ceiling": calls * max_tokens,
            "note": "Input tokens and provider billing are not capped. Seed controls ordering, not model sampling."}


def schedule(cases, names, repeats, seed, protocol=PROTOCOL):
    rng = random.Random(seed)
    blocks = [(c["id"], rep) for rep in range(1, repeats + 1) for c in cases]
    rng.shuffle(blocks)
    jobs = []
    for case_id, rep in blocks:
        treatments = [(name, arm) for name in names for arm in arms_for(protocol)]
        rng.shuffle(treatments)
        jobs.extend((case_id, rep, name, arm) for name, arm in treatments)
    return jobs


def run_efficiency(clients, cases, output, *, repeats=1, seed=42, max_calls=24, progress=print, protocol=PROTOCOL):
    if len(clients) != 2 or len({c.name for c in clients}) != 2:
        raise ValueError("Exactly two distinct providers are required.")
    if len({(c.max_tokens, c.timeout) for c in clients}) != 1:
        raise ValueError("Providers must share output limit and timeout.")
    plan = make_plan(cases, repeats, seed, clients[0].max_tokens, clients[0].timeout, protocol)
    if plan["planned_calls"] > max_calls:
        raise ValueError(f"Planned {plan['planned_calls']} calls exceeds --max-calls={max_calls}.")
    dest = Path(output)
    dest.mkdir(parents=True, exist_ok=False)
    run = {"schema_version": 1, "kind": protocol, "peerlab_version": __version__,
           "id": uuid.uuid4().hex, "mode": "live", "status": "running",
           "started_at": datetime.now(timezone.utc).isoformat(),
           "config": {**plan, "max_calls": max_calls}, "cases": cases,
           "providers": [{"name": c.name, "model": c.model, "base_url": c.base_url,
                          "max_tokens": c.max_tokens, "timeout": c.timeout} for c in clients],
           "records": [], "calls_attempted": 0}
    by_case, by_client = {c["id"]: c for c in cases}, {c.name: c for c in clients}

    def save():
        atomic_json(dest / "run.json", run)

    save()
    try:
        for case_id, rep, name, arm in schedule(cases, list(by_client), repeats, seed, protocol):
            client, case = by_client[name], by_case[case_id]
            row = {"id": len(run["records"]) + 1, "case_id": case_id, "repeat": rep,
                   "provider": name, "arm": arm, "requested_model": client.model,
                   "messages": messages_for(case, arm), "status": "pending"}
            run["records"].append(row)
            run["calls_attempted"] += 1
            save()  # Persist before the request; a timeout can still be billed.
            progress(f"[{run['calls_attempted']}/{plan['planned_calls']}] {case_id} r{rep} · {name} · {arm}")
            try:
                row.update(client.complete(row["messages"]), status="ok")
                row["grade"] = grade(case, row["content"], row["finish_reason"])
            except APIError as exc:
                row.update(status="error", error=str(exc))
                progress(f"  {name}: {exc}")
            save()
        run["status"] = "complete" if all(r["status"] == "ok" for r in run["records"]) else "partial"
    except KeyboardInterrupt:
        run["status"] = "interrupted"
    except Exception:
        run["status"] = "failed"
        raise
    finally:
        run["finished_at"] = datetime.now(timezone.utc).isoformat()
        save()
    return run


def validate(run):
    if run.get("kind") not in (PROTOCOL, EXTENDED, FACTORIAL) or run.get("schema_version") != 1:
        raise ValueError("Unsupported efficiency evidence schema.")
    cfg, cases = run["config"], run["cases"]
    plan = make_plan(cases, cfg["repeats"], cfg["seed"], cfg["max_output_tokens_per_call"], cfg["timeout_seconds"], run["kind"])
    if any(cfg.get(k) != v for k, v in plan.items()):
        raise ValueError("Saved plan differs from the frozen protocol or dataset.")
    names = [p["name"] for p in run["providers"]]
    if len(names) != 2 or len(set(names)) != 2:
        raise ValueError("Expected two distinct providers.")
    providers = {p["name"]: p for p in run["providers"]}
    for p in providers.values():
        if p["max_tokens"] != cfg["max_output_tokens_per_call"] or p["timeout"] != cfg["timeout_seconds"]:
            raise ValueError("Provider parameters disagree with plan.")
    tasks = {c["id"]: c for c in cases}
    jobs = schedule(cases, names, cfg["repeats"], cfg["seed"], run["kind"])
    rows = run["records"]
    if len(rows) != run["calls_attempted"] or not len(rows) <= len(jobs) <= cfg["max_calls"]:
        raise ValueError("Call ledger or budget mismatch.")
    checked = 0
    for i, r in enumerate(rows):
        key = (r["case_id"], r["repeat"], r["provider"], r["arm"])
        if key != jobs[i] or type(r["id"]) is not int or r["id"] != i + 1:
            raise ValueError("Record order, identity or treatment differs from planned schedule.")
        if r["messages"] != messages_for(tasks[r["case_id"]], r["arm"]):
            raise ValueError("Prompt differs from frozen treatment; evidence cannot be compared.")
        if r["requested_model"] != providers[r["provider"]]["model"]:
            raise ValueError("Requested model mismatch.")
        if r["status"] not in ("ok", "error", "pending"):
            raise ValueError("Invalid call status.")
        if r["status"] != "ok":
            continue
        if not isinstance(r["content"], str) or not isinstance(r["usage"], dict):
            raise ValueError("Invalid answer or usage.")
        if grade(tasks[r["case_id"]], r["content"], r["finish_reason"]) != r["grade"]:
            raise ValueError("Stored grade disagrees with recomputed answer.")
        for key in METRICS:
            value = r["usage"].get(key)
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError("Invalid token usage.")
        if all(r["usage"].get(k) is not None for k in METRICS):
            if r["usage"]["total_tokens"] != r["usage"]["prompt_tokens"] + r["usage"]["completion_tokens"]:
                raise ValueError("Token usage totals disagree.")
        checked += 1
    if run["status"] == "complete" and (len(rows) != len(jobs) or checked != len(jobs)):
        raise ValueError("Complete run has missing or failed requests.")
    return {**audit_cases(cases), "call_records": len(rows), "grades_recomputed": checked,
            "plan_and_prompts_verified": True,
            "note": "Internal consistency audit, not cryptographic proof of provider authenticity."}


def usage(rows):
    good = [r for r in rows if r["status"] == "ok"]
    return {key: {"known_sum": sum(r["usage"].get(key) or 0 for r in good),
                  "known_calls": sum(r["usage"].get(key) is not None for r in good),
                  "missing_calls": sum(r["usage"].get(key) is None for r in good)} for key in METRICS}


def paired(run, provider, left, right):
    index = {(r["case_id"], r["repeat"], r["provider"], r["arm"]): r for r in run["records"]}
    pairs = []
    for c in run["cases"]:
        for rep in range(1, run["config"]["repeats"] + 1):
            a, b = (index.get((c["id"], rep, provider, arm)) for arm in (left, right))
            if a and b and a["status"] == b["status"] == "ok":
                pairs.append((a, b))
    counts = {"both_correct": 0, "only_left_correct": 0, "only_right_correct": 0, "both_wrong": 0}
    for a, b in pairs:
        ap, bp = a["grade"]["passed"], b["grade"]["passed"]
        counts["both_correct" if ap and bp else "only_left_correct" if ap else "only_right_correct" if bp else "both_wrong"] += 1
    tokens = {}
    for key in METRICS:
        known = [(a, b) for a, b in pairs if a["usage"].get(key) is not None and b["usage"].get(key) is not None]
        totals = [sum(p[side]["usage"][key] for p in known) for side in (0, 1)]
        tokens[key] = {"paired": len(known), "missing_pairs": len(pairs) - len(known),
                       "left_sum": totals[0], "right_sum": totals[1],
                       "saved_fraction": 1 - totals[1] / totals[0] if totals[0] else None}
    n = len(pairs)
    correct = [sum(p[side]["grade"]["passed"] for p in pairs) for side in (0, 1)]
    complete_usage = tokens["total_tokens"]["missing_pairs"] == 0
    per_correct = [tokens["total_tokens"][f"{side}_sum"] / count if count and complete_usage else None
                   for side, count in zip(("left", "right"), correct)]
    return {"provider": provider, "left": left, "right": right, "paired": n,
            "missing_pairs": len(run["cases"]) * run["config"]["repeats"] - n,
            **counts, "left_correct": correct[0], "right_correct": correct[1],
            "accuracy_delta": (correct[1] - correct[0]) / n if n else None,
            "tokens": tokens, "left_tokens_per_correct": per_correct[0], "right_tokens_per_correct": per_correct[1],
            "pairs": [{"case_id": a["case_id"], "repeat": a["repeat"],
                       "left_id": a["id"], "right_id": b["id"],
                       "left_passed": a["grade"]["passed"], "right_passed": b["grade"]["passed"]} for a, b in pairs]}


def analyze(run):
    audit = validate(run)
    groups, comparisons = [], []
    total = len(run["cases"]) * run["config"]["repeats"]
    for provider in run["providers"]:
        name = provider["name"]
        for arm in arms_for(run["kind"]):
            rows = [r for r in run["records"] if r["provider"] == name and r["arm"] == arm]
            good = [r for r in rows if r["status"] == "ok"]
            groups.append({"provider": name, "arm": arm, "planned": total, "returned": len(good),
                           "correct": sum(r["grade"]["passed"] for r in good),
                           "invalid_json": sum(r["grade"]["reason"] == "invalid_json_answer" for r in good),
                           "incomplete": sum(r["finish_reason"] != "stop" for r in good),
                           "errors": sum(r["status"] == "error" for r in rows), "usage": usage(rows)})
        for label, left, right in comparisons_for(run["kind"]):
            comparisons.append({"comparison": label, **paired(run, name, left, right)})
    return {"audit": audit, "run_id": run["id"], "status": run["status"],
            "attempted": run["calls_attempted"], "usage": usage(run["records"]),
            "conditions": groups, "comparisons": comparisons}
