"""Offline, escaped tables and original-response disclosures for token studies."""

import csv
from html import escape
import json
from pathlib import Path

from .efficiency import EXTENDED, analyze
from .experiment import atomic_json


def percent(value):
    return "—" if value is None else f"{value:.1%}"


def export_efficiency(run, output):
    result = analyze(run)
    dest = Path(output)
    dest.mkdir(parents=True, exist_ok=True)
    atomic_json(dest / "analysis.json", result)
    if run["kind"] == EXTENDED:
        from .dimensions import export_dimensions
        export_dimensions(run, dest)
    headings = ["模型", "条件", "正确/返回/计划", "已知输入 token", "已知输出 token", "已知总 token", "JSON失败", "未完整输出", "请求失败"]
    rows = [[c["provider"], c["arm"], f"{c['correct']}/{c['returned']}/{c['planned']}",
             *(c["usage"][k]["known_sum"] for k in ("prompt_tokens", "completion_tokens", "total_tokens")),
             c["invalid_json"], c["incomplete"], c["errors"]] for c in result["conditions"]]
    paired_headings = ["模型", "左 → 右", "配对/缺失", "正确题数", "总token节省", "改善/退步", "缺用量配对"]
    paired_rows = [[p["provider"], p["left"] + " → " + p["right"], f"{p['paired']}/{p['missing_pairs']}",
                    f"{p['left_correct']} → {p['right_correct']}", percent(p["tokens"]["total_tokens"]["saved_fraction"]),
                    f"{p['only_right_correct']}/{p['only_left_correct']}", p["tokens"]["total_tokens"]["missing_pairs"]]
                   for p in result["comparisons"]]
    caveat = ("每个比较只使用同模型、同题、同重复中两边都返回的配对。用量缺失时仅在两边用量均已知的子集计算节省，"
              "详见 analysis.json；未知不按零计。总 token = 输入 + 输出，缓存明细保存在原始 usage 中。"
              "这些是返回用量，不是账单；失败请求可能已计费。短提示词改变了措辞，不保证语义完全等价。"
              "单次采样、小题集，结果不能推断统计显著、不劣性或普遍有效。")

    def markdown_table(headers, data):
        def safe(x):
            return str(x).replace("|", "\\|").replace("\n", " ")
        return "\n".join(["| " + " | ".join(map(safe, headers)) + " |",
                          "| " + " | ".join("---" for _ in headers) + " |"] +
                         ["| " + " | ".join(map(safe, row)) + " |" for row in data])

    text = f"# Token 效率实验\n\nRun: `{run['id']}` · {run['status']} · 请求尝试 {run['calls_attempted']}\n\n"
    text += markdown_table(headings, rows) + "\n\n## 配对比较\n\n" + markdown_table(paired_headings, paired_rows)
    text += "\n\n" + caveat + "\n"
    (dest / "analysis.md").write_text(text, encoding="utf-8")

    def cell(x):
        value = str(x)
        return "'" + value if value.startswith(("=", "+", "-", "@", "\t", "\r")) else value

    with (dest / "scores.csv").open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "case_id", "repeat", "provider", "arm", "status", "correct", "prompt_tokens", "completion_tokens", "total_tokens"])
        for r in run["records"]:
            writer.writerow([cell(r[k]) for k in ("id", "case_id", "repeat", "provider", "arm", "status")] +
                            [r.get("grade", {}).get("passed", "")] +
                            [r.get("usage", {}).get(k, "") for k in ("prompt_tokens", "completion_tokens", "total_tokens")])

    def table(headers, data):
        return '<div class="scroll"><table><thead><tr>' + ''.join(f'<th>{escape(str(x))}</th>' for x in headers) + \
               '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<td>{escape(str(x))}</td>' for x in row) + '</tr>' for row in data) + '</tbody></table></div>'

    details = []
    for c in run["cases"]:
        records = [r for r in run["records"] if r["case_id"] == c["id"]]
        body = f'<p>{escape(c["prompt"])}</p><p>参考答案：{escape(json.dumps(c["expected"], ensure_ascii=False))}</p>'
        for r in records:
            body += f'<h3>{escape(r["provider"])} · {escape(r["arm"])} · r{r["repeat"]}</h3>'
            body += '<p>' + escape(json.dumps({"status": r["status"], "grade": r.get("grade"), "usage": r.get("usage")}, ensure_ascii=False)) + '</p>'
            body += '<pre>' + escape(r.get("content", r.get("error", "Pending"))) + '</pre>'
        details.append(f'<details><summary>{escape(c["id"])} · {escape(c["title"])}</summary>{body}</details>')
    styles = 'body{margin:0;background:#f4f3ec;color:#142b36;font:16px/1.65 system-ui,sans-serif}main{max-width:1220px;margin:auto;padding:48px 24px}h1{font-size:clamp(32px,5vw,64px);line-height:1.1}h2{margin-top:42px}small{color:#506971}.tag{color:#006b56;font-weight:700;letter-spacing:.12em}.scroll{overflow:auto;background:white;border:1px solid #d7dfda;border-radius:12px}table{border-collapse:collapse;width:100%;white-space:nowrap}th,td{text-align:left;padding:12px 15px;border-bottom:1px solid #e2e7e2}th{background:#e0ebe5}details{margin:12px 0;padding:16px;background:white;border:1px solid #d7dfda;border-radius:10px}summary{cursor:pointer;font-weight:650}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f7f5;padding:16px;border-radius:8px}p{overflow-wrap:anywhere}.note{max-width:960px;color:#506971}a{color:#006b56}'
    html = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PeerLab · Token 效率实验</title><style>' + styles + '</style><main>'
    design = "三条件复测：常规解释 · 仅答案 · 先依据后答案" if run["kind"] == EXTENDED else "2 × 2 对照：提示词长度 × 是否输出解释"
    html += f'<div class="tag">PEERLAB / TOKEN EFFICIENCY</div><h1>少用 token，<br>答案还可靠吗？</h1><p>{design}</p><small>Run {escape(run["id"])} · {escape(run["status"])} · {run["calls_attempted"]} 次请求尝试</small>'
    html += '<h2>质量与用量</h2>' + table(headings, rows) + '<h2>同题配对比较</h2>' + table(paired_headings, paired_rows)
    html += '<p class="note">' + escape(caveat) + '</p><h2>逐题原始输出</h2>' + ''.join(details)
    html += '<h2>冻结的系统提示词</h2><pre>' + escape(json.dumps(run["config"]["system_prompts"], ensure_ascii=False, indent=2)) + '</pre></main></html>'
    (dest / "report.html").write_text(html, encoding="utf-8")
    return result
