"""Audit saved evidence, then compare matched answers without new API calls."""

import json
from pathlib import Path

from .datasets import audit_cases
from .experiment import PROTOCOLS, dataset_hash, planned_calls, run_arms, summarize
from .grading import grade


def validate_run(run):
    if run.get("schema_version") not in (1, 2):
        raise ValueError("Unsupported run schema.")
    cases = run["cases"]
    if not cases or len({c["id"] for c in cases}) != len(cases):
        raise ValueError("Dataset is empty or has duplicate IDs.")
    if dataset_hash(cases) != run["dataset_sha256"]:
        raise ValueError("Dataset hash does not match the saved snapshot.")
    oracle = audit_cases(cases)
    arms = run_arms(run)
    protocol = run["config"].get("protocol", "classic")
    if protocol not in PROTOCOLS or arms != PROTOCOLS[protocol]:
        raise ValueError("Protocol and recorded conditions disagree.")
    repeats = run["config"]["repeats"]
    if type(repeats) is not int or repeats < 1:
        raise ValueError("Invalid repeat count.")
    planned = planned_calls(len(cases), repeats, protocol)
    if run["config"]["planned_calls"] != planned:
        raise ValueError("Planned call count does not match the protocol.")
    names = [p["name"] for p in run["providers"]]
    if len(names) != 2 or len(set(names)) != 2:
        raise ValueError("Expected two distinct providers.")
    tasks = {c["id"]:c for c in cases}
    seen, ids, prior_records = set(), {}, {}
    checked = attempted = 0
    for record in run["records"]:
        key = (record["case_id"], record["repeat"], record["provider"], record["stage"])
        if key in seen:
            raise ValueError("Duplicate call record would double-count an observation.")
        seen.add(key)
        if key[0] not in tasks or type(key[1]) is not int or not 1 <= key[1] <= repeats or key[2] not in names:
            raise ValueError("Record does not belong to a planned task, repeat or provider.")
        valid_stages = set(arms)
        for arm in arms[1:]:
            author = record["provider"] if arm == "self" else next(n for n in names if n != record["provider"])
            valid_stages.add(f"{arm}_review_for_{author}")
        if record["stage"] not in valid_stages:
            raise ValueError("Unplanned or incorrectly attributed stage.")
        status = record["status"]
        if status not in ("ok", "error", "pending", "skipped"):
            raise ValueError("Unknown call status.")
        attempted += status != "skipped"
        if run["schema_version"] == 2:
            identifier = record.get("id")
            if type(identifier) is not int or identifier < 1 or identifier in ids:
                raise ValueError("Invalid or duplicate call ID.")
            prefix = key[:2]
            expected_keys = []
            if record["stage"] in arms[1:]:
                arm = record["stage"]
                reviewer = record["provider"] if arm == "self" else next(n for n in names if n != record["provider"])
                expected_keys = [(*prefix,record["provider"],"baseline"),
                                 (*prefix,reviewer,f"{arm}_review_for_{record['provider']}")]
            elif record["stage"] != "baseline":
                arm = next(a for a in arms[1:] if record["stage"].startswith(a+"_review_for_"))
                author = record["provider"] if arm == "self" else next(n for n in names if n != record["provider"])
                expected_keys = [(*prefix,author,"baseline")]
                if arm == "peer_independent":
                    expected_keys.append((*prefix,record["provider"],"baseline"))
            if any(k not in prior_records for k in expected_keys):
                raise ValueError("Required dependency is absent or out of order.")
            if record.get("dependencies") != [prior_records[k]["id"] for k in expected_keys]:
                raise ValueError("Dependency links do not match the recorded protocol.")
            for dependency in record.get("dependencies", []):
                prior = ids.get(dependency)
                if prior is None or (prior["case_id"],prior["repeat"]) != key[:2]:
                    raise ValueError("Dependency must be an earlier call for the same task and repeat.")
                if status == "ok" and (prior["status"] != "ok" or prior.get("finish_reason") != "stop"):
                    raise ValueError("Successful call has an unusable dependency.")
            ids[identifier] = record
        prior_records[key] = record
        if status == "ok":
            usage = record.get("usage", {})
            if not isinstance(usage, dict):
                raise ValueError("Invalid usage record.")
            for field in ("prompt_tokens", "completion_tokens", "total_tokens"):
                if field in usage and (type(usage[field]) is not int or usage[field] < 0):
                    raise ValueError("Token counts must be nonnegative integers.")
            if record["stage"] in arms:
                actual = grade(tasks[key[0]], record["content"], record["finish_reason"])
                if actual != record.get("grade"):
                    raise ValueError(f"Saved grade differs from recomputed grade: {key[0]} / {key[2]} / {key[3]}")
                checked += 1
    if attempted != run["calls_attempted"] or attempted > run["config"]["max_calls"]:
        raise ValueError("Attempt ledger does not match the recorded call budget.")
    if run["status"] == "complete" and (len(seen) != planned or any(r["status"] != "ok" for r in run["records"])):
        raise ValueError("Run marked complete has missing or failed calls.")
    return {**oracle, "call_records":len(seen), "grades_recomputed":checked,
            "dataset_hash_verified":True, "ledger_verified":True,
            "note":"Internal consistency, not a cryptographic proof that API outputs are authentic."}


def usage_summary(records):
    ok = [r for r in records if r["status"] == "ok"]
    result = {"returned_calls":len(ok), "attempted_calls":sum(r["status"] != "skipped" for r in records)}
    for field in ("prompt_tokens", "completion_tokens", "total_tokens"):
        known = [r.get("usage", {}).get(field) for r in ok]
        result[field] = sum(x for x in known if x is not None)
        result[f"missing_{field}_calls"] = sum(x is None for x in known)
    result["latency_ms_sum"] = sum(r.get("latency_ms", 0) for r in ok)
    result["missing_latency_calls"] = sum("latency_ms" not in r for r in ok)
    return result


def paired_comparison(run, provider, left, right, category=None):
    index = {(r["case_id"],r["repeat"],r["provider"],r["stage"]):r for r in run["records"]}
    tasks = [c for c in run["cases"] if category is None or c["category"] == category]
    counts = {"both_correct":0, "only_left_correct":0, "only_right_correct":0, "both_wrong":0, "missing_pair":0}
    pairs = []
    for case in tasks:
        for repeat in range(1, run["config"]["repeats"]+1):
            a, b = (index.get((case["id"],repeat,provider,arm)) for arm in (left,right))
            if not a or not b or a["status"] != "ok" or b["status"] != "ok":
                counts["missing_pair"] += 1
                continue
            ap, bp = a["grade"]["passed"], b["grade"]["passed"]
            bucket = "both_correct" if ap and bp else "only_left_correct" if ap else "only_right_correct" if bp else "both_wrong"
            counts[bucket] += 1
            pairs.append({"case_id":case["id"],"repeat":repeat,"category":case["category"],
                          "left_passed":ap,"right_passed":bp})
    n = len(pairs)
    return {"provider":provider, "left":left, "right":right, "category":category,
            "expected_pairs":len(tasks)*run["config"]["repeats"], "paired":n, **counts,
            "left_accuracy":(counts["both_correct"]+counts["only_left_correct"])/n if n else None,
            "right_accuracy":(counts["both_correct"]+counts["only_right_correct"])/n if n else None,
            "delta_right_minus_left":(counts["only_right_correct"]-counts["only_left_correct"])/n if n else None,
            "pairs":pairs}


def condition_costs(run):
    rows = run["records"]
    index = {(r["case_id"],r["repeat"],r["provider"],r["stage"]):i for i,r in enumerate(rows)}
    names = [p["name"] for p in run["providers"]]
    costs = []
    for provider in names:
        for arm in run_arms(run):
            used = set()
            outputs = [r for r in rows if r["provider"] == provider and r["stage"] == arm and r["status"] == "ok"]
            for output in outputs:
                prefix = (output["case_id"],output["repeat"])
                keys = [(*prefix,provider,arm)]
                if arm != "baseline":
                    reviewer = provider if arm == "self" else next(n for n in names if n != provider)
                    keys += [(*prefix,provider,"baseline"),(*prefix,reviewer,f"{arm}_review_for_{provider}")]
                    if arm == "peer_independent":
                        keys.append((*prefix,reviewer,"baseline"))
                for key in keys:
                    if key not in index:
                        raise ValueError("Returned answer is missing a required source call.")
                    used.add(index[key])
            costs.append({"provider":provider,"arm":arm,"completed_answers":len(outputs),
                          **usage_summary([rows[i] for i in sorted(used)])})
    return costs


def analyze_run(run, left="peer", right="peer_independent"):
    audit = validate_run(run)
    if left == right or left not in run_arms(run) or right not in run_arms(run):
        raise ValueError("Choose two distinct conditions present in this run.")
    names = [p["name"] for p in run["providers"]]
    categories = sorted({c["category"] for c in run["cases"]})
    return {"schema_version":1,"run_id":run["id"],"dataset_sha256":run["dataset_sha256"],
            "audit":audit,"summary":summarize(run),"comparison":{"left":left,"right":right},
            "overall":[paired_comparison(run,p,left,right) for p in names],
            "by_category":[paired_comparison(run,p,left,right,c) for p in names for c in categories],
            "total_usage":usage_summary(run["records"]), "condition_costs":condition_costs(run)}


def export_analysis(run, directory, left="peer", right="peer_independent"):
    analysis = analyze_run(run,left,right)
    directory = Path(directory)
    directory.mkdir(parents=True,exist_ok=True)
    (directory/"analysis.json").write_text(json.dumps(analysis,ensure_ascii=False,indent=2,allow_nan=False)+"\n",encoding="utf-8")
    lines = ["# 配对分析", "", f"Run: `{run['id']}`", "", f"比较左侧 `{left}` 与右侧 `{right}`；只使用两边均已返回答案的同题同轮配对。", "",
             f"已核验题库hash，重算 {analysis['audit']['grades_recomputed']} 个最终答案的评分；{analysis['audit']['oracle_verified']} 道参考答案通过精确算术校验。", "",
             "| 作者 | 范围 | 有效/计划配对 | 都对 | 仅左对 | 仅右对 | 都错 | 右减左（百分点） |",
             "|---|---|---:|---:|---:|---:|---:|---:|"]
    for row in analysis["overall"] + analysis["by_category"]:
        delta = row["delta_right_minus_left"]
        delta_text = f"{delta*100:+.2f}" if delta is not None else "无数据"
        lines.append(f"| {row['provider']} | {row['category'] or '全部'} | {row['paired']}/{row['expected_pairs']} | {row['both_correct']} | {row['only_left_correct']} | {row['only_right_correct']} | {row['both_wrong']} | {delta_text} |")
    total = analysis["total_usage"]
    lines += ["", "## 全程用量", "", f"请求尝试 {total['attempted_calls']} 次，返回 {total['returned_calls']} 次；已知 total_tokens={total['total_tokens']}，有 {total['missing_total_tokens_calls']} 个返回缺少该字段。",
              "失败或超时的服务端用量未知。延迟为客户端调用时长，不是模型纯推理时间。", "",
              "## 每种条件所需的调用路径", "",
              "下表只计已返回最终答案的依赖路径。先解后审包含作者与审稿者两份baseline；其余修订包含作者baseline。跨条件/作者共享的调用会在各路径重现，**不可把下表相加当作总消费**。", "",
              "| 作者 | 条件 | 已返回答案 | 路径返回调用 | 已知总Token | 缺少用量调用 | 路径耗时合计(ms) |",
              "|---|---|---:|---:|---:|---:|---:|"]
    for row in analysis["condition_costs"]:
        lines.append(f"| {row['provider']} | {row['arm']} | {row['completed_answers']} | {row['returned_calls']} | {row['total_tokens']} | {row['missing_total_tokens_calls']} | {row['latency_ms_sum']} |")
    lines += ["", "## 解释边界", "", "这是描述性配对比较，不报告p值或显著性。重复题目与相同模板会相关；两位作者的结果不能简单合并成独立样本。",
              "记录校验检查内部一致性；如果有人同时修改所有原始输出和元数据，离线工具不能证明API来源真实性。网络缺失不能假装错误答案，截断则按预设规则算未通过。", ""]
    (directory/"analysis.md").write_text("\n".join(lines),encoding="utf-8")
    return analysis
