"""Offline artifacts. Model text is always rendered as text, never HTML."""

import csv
import json
from pathlib import Path

from .experiment import summarize


def export_report(run, directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    run["summary"] = summarize(run)
    template = (Path(__file__).parent / "templates" / "report.html").read_text(encoding="utf-8")
    # Prevent a model answer such as </script> from escaping the JSON script element.
    data = json.dumps(run, ensure_ascii=False, allow_nan=False).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    (directory / "report.html").write_text(template.replace("__RUN_DATA__", data), encoding="utf-8")
    lines = ["# PeerLab 实验报告", "", f"- Run: `{run['id']}`",
             f"- Mode: {run['mode']} / Status: {run['status']}",
             f"- Dataset SHA-256: `{run['dataset_sha256']}`",
             f"- 实际请求尝试: {run['calls_attempted']} / 计划: {run['config']['planned_calls']}", "",
             "正确率仅针对收到回答的样本；错误、跳过和未执行不当作错误答案，必须结合覆盖率阅读。截断回答计为未通过。", "",
             "| 模型 | 条件 | 正确 / 已返回 | 已返回 / 计划 | 修正错误 | 改错原答案 | 有效配对 |",
             "|---|---|---:|---:|---:|---:|---:|"]
    for provider in run["providers"]:
        for arm, stat in run["summary"][provider["name"]].items():
            lines.append(f"| {provider['name']} / {provider['model']} | {arm} | {stat['correct']} / {stat['completed']} | {stat['completed']} / {stat['total']} | {stat['improved']} | {stat['regressed']} | {stat['paired']} |")
    usage = [r.get("usage", {}) for r in run["records"] if r["status"] == "ok"]
    total_tokens = sum(u.get("total_tokens", 0) for u in usage if isinstance(u, dict))
    lines += ["", f"API 已返回的 total_tokens 合计：{total_tokens}。缺失用量及失败请求的费用未知，不估算账单。", "",
              "## 如何解释", "", "这是自建小题库上的探索实验，不是通用模型排行榜。一次采样不能支持显著性结论；题目可能已被模型见过。",
              "self 与 peer 都在同一 baseline 上增加一次审稿和一次修订；调用次数相同，但 token、延迟与费用并不相同。",
              "seed 仅控制本地执行顺序及展示，不保证云端模型确定性。重复样本彼此不独立，不能当成独立题目扩大样本量。",
              "客观判分只检查最终 answer，不判断解释质量。盲评是展示层匿名，页面源数据含映射，不适合对抗性评审。", ""]
    (directory / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    with (directory / "scores.csv").open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["case_id", "repeat", "provider", "stage", "status", "passed", "reason", "latency_ms", "prompt_tokens", "completion_tokens"])
        for r in run["records"]:
            if r["stage"] not in ("baseline", "self", "peer"):
                continue
            values = [r["case_id"], r["repeat"], r["provider"], r["stage"], r["status"], r.get("grade", {}).get("passed", ""),
                      r.get("grade", {}).get("reason", ""), r.get("latency_ms", ""),
                      r.get("usage", {}).get("prompt_tokens", ""), r.get("usage", {}).get("completion_tokens", "")]
            writer.writerow(["'" + v if isinstance(v, str) and v.startswith(("=", "+", "-", "@", "\t", "\r")) else v for v in values])
