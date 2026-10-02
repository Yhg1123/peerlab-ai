"""Offline, escaped tables and original-response disclosures for token studies."""

import csv
from html import escape
import json
from pathlib import Path
import re

from .efficiency import EXTENDED, FACTORIAL, analyze
from .experiment import atomic_json


def percent(value):
    return "—" if value is None else f"{value:.1%}"


def export_efficiency(run, output):
    result = analyze(run)
    dest = Path(output)
    dest.mkdir(parents=True, exist_ok=True)
    atomic_json(dest / "analysis.json", result)
    dimensions = None
    if run["kind"] in (EXTENDED, FACTORIAL):
        from .dimensions import export_dimensions
        dimensions = export_dimensions(run, dest)
    headings = ["模型", "条件", "正确/返回/计划", "已知输入 token", "已知输出 token", "已知总 token", "JSON失败", "未完整输出", "请求失败"]
    rows = [[c["provider"], c["arm"], f"{c['correct']}/{c['returned']}/{c['planned']}",
             *(c["usage"][k]["known_sum"] for k in ("prompt_tokens", "completion_tokens", "total_tokens")),
             c["invalid_json"], c["incomplete"], c["errors"]] for c in result["conditions"]]
    paired_headings = ["模型", "左 → 右", "配对/缺失", "正确次数", "总token节省", "改善/退步", "缺用量配对"]
    paired_rows = [[p["provider"], p["left"] + " → " + p["right"], f"{p['paired']}/{p['missing_pairs']}",
                    f"{p['left_correct']} → {p['right_correct']}", percent(p["tokens"]["total_tokens"]["saved_fraction"]),
                    f"{p['only_right_correct']}/{p['only_left_correct']}", p["tokens"]["total_tokens"]["missing_pairs"]]
                   for p in result["comparisons"]]
    caveat = ("每个比较只使用同模型、同题、同重复中两边都返回的配对。用量缺失时仅在两边用量均已知的子集计算节省，"
              "详见 analysis.json；未知不按零计。总 token = 输入 + 输出，缓存明细保存在原始 usage 中。"
              "这些是返回用量，不是账单；失败请求可能已计费。短提示词改变了措辞，不保证语义完全等价。"
              "有限采样、小题集，结果不能推断统计显著、不劣性或普遍有效。")

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

    extra = ''
    if run["kind"] == FACTORIAL:
        from .factorial import export_factorial
        factorial = export_factorial(run, dest)
        def decimal(value):
            return '—' if value is None else f'{value:.1f}'
        def effect_value(key, value):
            return decimal(value if key == 'total_tokens_per_block' or value is None else value * 100)
        effect_labels = {'accuracy':'正确率差（百分点）', 'common_contract_and_correct':'共同契约且正确之差（百分点）', 'total_tokens_per_block':'总token差（每区组）'}
        extra += '<h2>顺序 × 限长：共同口径</h2><p class="note">共同契约对四组都检查字段、非空依据和要求的顺序，不检查长度。本条件契约仅对限长组额外要求≤80字符；不能把去掉限制带来的合格率上升直接当作能力改善。答案类型由原判分器检查。</p>'
        extra += table(['模型','条件','返回','共同契约且正确','本条件契约且正确','≤80字符','依据长度中位数/P90'],
                       [[g['provider'],g['arm'],g['returned'],g['common_contract_and_correct'],g['arm_contract_and_correct'],g['within_80'],f"{decimal(g['median_evidence_characters'])} / {decimal(g['p90_evidence_characters'])}"] for g in factorial['conditions']])
        extra += '<h2>因素交互项</h2><p class="note">(不限长时先依据−先答案) − (限长时先依据−先答案)，仅用四组均返回的区组。正确率为比例差，token为每区组的差中之差。正负方向不等于优劣，按题聚类区间只描述这个选题集合。</p>'
        extra += table(['模型','完整/缺失区组','指标','交互估计','95%描述区间'],
                       [[p['provider'],f"{p['complete_blocks']}/{p['missing_blocks']}",effect_labels[k],effect_value(k,v),'—' if p['percentile_95pct'][k] is None else ' ～ '.join(effect_value(k,x) for x in p['percentile_95pct'][k])] for p in factorial['interactions'] for k,v in p['estimate'].items()])
    if dimensions:
        labels = {"verbose_explain": "常规解释", "compact_answer": "仅答案", "compact_evidence": "先依据后答案",
                  "answer_first_bounded": "先答案·限80字符", "evidence_first_bounded": "先依据·限80字符",
                  "answer_first_unbounded": "先答案·不限字符", "evidence_first_unbounded": "先依据·不限字符"}
        def label(arm):
            return labels.get(arm, arm)
        def ms(value):
            return '—' if value is None else f'{value:,.0f}'
        def interval(values):
            return '—' if values is None else ' ～ '.join(percent(v) for v in values)
        extra += '<h2>输出契约与耗时</h2><p class="note">合法JSON只保证可解析；契约合格还要求字段、类型以及依据的长度与顺序符合约定，仍不代表答案正确。延迟只统计返回请求，不包含失败超时，也不等于纯模型速度。</p>'
        extra += table(['模型', '回答方式', 'JSON合法/返回', '契约合格/返回', '契约合格且正确/计划', '中位延迟ms', 'P90延迟ms'],
                       [[g['provider'], label(g['arm']), f"{g['valid_json']}/{g['returned']}", f"{g['contract_ok']}/{g['returned']}", f"{g['contract_and_correct']}/{g['planned']}", ms(g['latency']['median_ms']), ms(g['latency']['p90_ms'])] for g in dimensions['conditions'] if g['scope']=='all'])
        extra += '<h2>按题型查看</h2><p class="note">每个类别样本很少；分层有助于定位问题，不适合据此排名。生成/人工参考分组和类别分组重叠，不能相加。</p>'
        for scope in dict.fromkeys(g['scope'] for g in dimensions['conditions'] if g['scope']!='all'):
            caption = scope.replace('category:', '题型：').replace('reference:generated', '程序参考题').replace('reference:manual', '人工参考题')
            extra += '<details><summary>' + escape(caption) + '</summary>'
            extra += table(['模型', '回答方式', '正确/返回/计划', 'JSON合法', '契约合格且正确', '已知总token'],
                           [[g['provider'], label(g['arm']), f"{g['correct']}/{g['returned']}/{g['planned']}", g['valid_json'], g['contract_and_correct'], g['usage']['total_tokens']['known_sum']] for g in dimensions['conditions'] if g['scope']==scope])
            extra += '</details>'
        extra += '<h2>重复采样的稳定性</h2><p class="note">分母为所有重复都返回的题目；“答案相同”只统计所有重复都可解析的题目。始终错误也可以很稳定。</p>'
        extra += table(['模型','回答方式','重复次数','完整任务','始终正确','对错变化','均可解析任务','答案完全相同'],
                       [[s['provider'],label(s['arm']),s['repeats'],s['all_repeats_returned_tasks'],s['all_repeats_correct_tasks'],s['mixed_correctness_tasks'],s['all_repeats_parseable_tasks'],s['identical_typed_answers_tasks']] for s in dimensions['stability']])
        extra += '<h2>精度敏感性</h2><p class="note">仅作诊断，不修改正式分数。计数分母是返回的数值题；格式错误和截断不会因为放宽误差而过关。</p>'
        extra += table(['模型','回答方式','数值题返回','有限数值答案','误差≤1e-6','≤1e-4','≤1e-2'],
                       [[s['provider'],label(s['arm']),s['numeric_returned'],s['finite_numeric_answers'],*s['absolute_error_thresholds'].values()] for s in dimensions['numeric_sensitivity']])
        extra += '<h2>配对变化与不确定性</h2><p class="note">按题聚类重采样2000次，保留同题所有有效重复，显示百分位95%描述区间。题目人为选取，区间不代表总体；也不做不劣性或多重检验结论。先依据后答案改变了多项要求，不能单独归因于顺序。</p>'
        extra += table(['模型','左 → 右','有效配对','正确率差','95%描述区间','总token节省','95%描述区间'],
                       [[p['provider'],label(p['left'])+' → '+label(p['right']),p['paired'],percent(p['accuracy_delta']),interval(p['cluster_bootstrap']['accuracy_delta_95pct']),percent(p['tokens']['total_tokens']['saved_fraction']),interval(p['cluster_bootstrap']['total_token_saving_95pct'])] for p in dimensions['comparisons'] if p['scope']=='all'])

    details = []
    for c in run["cases"]:
        records = [r for r in run["records"] if r["case_id"] == c["id"]]
        body = f'<p>{escape(c["prompt"])}</p><p>参考答案：{escape(json.dumps(c["expected"], ensure_ascii=False))}</p>'
        body += '<p>参考推导：' + escape(c['rationale']) + '</p>'
        for r in records:
            body += f'<h3>#{r["id"]} · {escape(r["provider"])} · {escape(r["arm"])} · r{r["repeat"]}</h3>'
            body += '<p>' + escape(json.dumps({"status": r["status"], "finish_reason": r.get("finish_reason"), "latency_ms": r.get("latency_ms"), "grade": r.get("grade"), "usage": r.get("usage")}, ensure_ascii=False)) + '</p>'
            body += '<pre>' + escape(r.get("content", r.get("error", "Pending"))) + '</pre>'
        details.append(f'<details><summary>{escape(c["id"])} · {escape(c["title"])}</summary>{body}</details>')
    styles = 'body{margin:0;background:#f4f3ec;color:#142b36;font:16px/1.65 system-ui,sans-serif}main{max-width:1220px;margin:auto;padding:48px 24px}h1{font-size:clamp(32px,5vw,64px);line-height:1.1}h2{margin-top:42px}small{color:#506971}.tag{color:#006b56;font-weight:700;letter-spacing:.12em}.scroll{overflow:auto;background:white;border:1px solid #d7dfda;border-radius:12px}table{border-collapse:collapse;width:100%;white-space:nowrap}th,td{text-align:left;padding:12px 15px;border-bottom:1px solid #e2e7e2}th{background:#e0ebe5}details{margin:12px 0;padding:16px;background:white;border:1px solid #d7dfda;border-radius:10px}summary{cursor:pointer;font-weight:650}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f7f5;padding:16px;border-radius:8px}p{overflow-wrap:anywhere}.note{max-width:960px;color:#506971}a{color:#006b56}'
    html = '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PeerLab · Token 效率实验</title><style>' + styles + '</style><main>'
    design = "三条件复测：常规解释 · 仅答案 · 先依据后答案" if run["kind"] == EXTENDED else "2 × 2 对照：提示词长度 × 是否输出解释"
    if run["kind"] == FACTORIAL:
        design = "2 × 2 对照：答案/依据顺序 × 依据是否限80字符"
        extra = extra.replace("先依据后答案改变了多项要求，不能单独归因于顺序。", "本轮在相同长度要求内比较请求的字段顺序；不能由输出顺序推断模型内部推理机制。")
    title = "答案放前，<br>还是依据放前？" if run["kind"] == FACTORIAL else "少用 token，<br>答案还可靠吗？"
    html += f'<div class="tag">PEERLAB / TOKEN EFFICIENCY</div><h1>{title}</h1><p>{design}</p><small>Run {escape(run["id"])} · {escape(run["status"])} · {run["calls_attempted"]} 次请求尝试</small>'
    html += '<h2>质量与用量</h2>' + table(headings, rows) + '<h2>同题配对比较</h2>' + table(paired_headings, paired_rows)
    html += '<p class="note">' + escape(caveat) + '</p>' + extra + '<h2>逐题原始输出</h2>' + ''.join(details)
    html += '<h2>冻结的系统提示词</h2><pre>' + escape(json.dumps(run["config"]["system_prompts"], ensure_ascii=False, indent=2)) + '</pre></main></html>'
    # Preserve provider whitespace in rendered <pre> text without introducing
    # trailing whitespace into generated HTML source tracked by Git.
    html = re.sub(r"[ \t]+(?=\r?$)", lambda m: ''.join('&#32;' if c == ' ' else '&#9;' for c in m[0]), html, flags=re.MULTILINE)
    (dest / "report.html").write_text(html, encoding="utf-8")
    return result
