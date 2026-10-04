"""Frozen top-level JSON-type diagnostics; never coerce an answer or change its grade."""

from collections import Counter
import math
from pathlib import Path

from .dimensions import cluster_interval, parsed_object
from .efficiency import NATIVE, NATIVE_ARMS, paired, validate
from .experiment import atomic_json


def native_type_ok(case, row):
    obj = parsed_object(row)
    if obj is None:
        return False
    value = obj['answer']
    if case['check'] == 'number':
        try:
            return type(value) in (int, float) and math.isfinite(value)
        except OverflowError:
            return False
    # Top-level type only. Array elements, values and shape are checked by grade().
    return type(value) is type(case['expected'])


def type_diagnostics(run):
    validate(run)
    if run['kind'] != NATIVE:
        raise ValueError('Native-type diagnostics require token-efficiency-v4.')
    cases = {c['id']:c for c in run['cases']}
    scopes = {'all':list(cases)}
    for label in ('number','array','other'):
        ids = [c['id'] for c in cases.values() if
               ('number' if c['check']=='number' else 'array' if isinstance(c['expected'],list) else 'other') == label]
        if ids:
            scopes['answer_type:'+label] = ids
    groups, comparisons = [], []
    # The original grades and evidence remain unchanged. Reuse paired accounting
    # with a separate binary endpoint after validating the original run once.
    type_run = {**run, 'records':[{**r,'grade':{'passed':native_type_ok(cases[r['case_id']],r)}} for r in run['records']]}
    for provider in run['providers']:
        name = provider['name']
        for arm in NATIVE_ARMS:
            for scope, ids in scopes.items():
                rows = [r for r in run['records'] if r['provider']==name and r['arm']==arm and r['case_id'] in ids]
                counts = Counter({k:0 for k in ('request_error','pending','not_attempted','truncated','invalid_json','wrong_native_type','native_type_wrong_answer','correct')})
                strings = []
                for r in rows:
                    if r['status'] != 'ok':
                        counts['request_error' if r['status']=='error' else 'pending'] += 1
                    elif r['finish_reason'] != 'stop':
                        counts['truncated'] += 1
                    elif parsed_object(r) is None:
                        counts['invalid_json'] += 1
                    elif not native_type_ok(cases[r['case_id']],r):
                        counts['wrong_native_type'] += 1
                        if isinstance(parsed_object(r)['answer'],str):
                            strings.append(r['id'])
                    elif not r['grade']['passed']:
                        counts['native_type_wrong_answer'] += 1
                    else:
                        counts['correct'] += 1
                planned = len(ids)*run['config']['repeats']
                counts['not_attempted'] = planned-len(rows)
                groups.append({'provider':name,'arm':arm,'scope':scope,'planned':planned,
                               'returned':sum(r['status']=='ok' for r in rows),
                               'native_type_ok':counts['native_type_wrong_answer']+counts['correct'],
                               'outcomes':dict(counts),'wrong_type_string_ids':strings})
        for scope, ids in scopes.items():
            subset = {**type_run,'cases':[cases[i] for i in ids]}
            p = paired(subset,name,*NATIVE_ARMS)
            entry = {'provider':name,'scope':scope,'paired':p['paired'],'missing_pairs':p['missing_pairs'],
                     'left_type_ok':p['left_correct'],'right_type_ok':p['right_correct'],
                     'only_left_type_ok':p['only_left_correct'],'only_right_type_ok':p['only_right_correct'],
                     'type_delta':p['accuracy_delta'],
                     'pairs':[{'case_id':x['case_id'],'repeat':x['repeat'],'left_id':x['left_id'],'right_id':x['right_id'],
                               'left_type_ok':x['left_passed'],'right_type_ok':x['right_passed']} for x in p['pairs']]}
            if scope == 'all':
                ci = cluster_interval(subset,name,*NATIVE_ARMS)
                entry.update(task_clusters=ci['task_clusters'],native_type_delta_95pct=ci['accuracy_delta_95pct'],samples=ci['samples'],seed=ci['seed'])
            comparisons.append(entry)
    return {'run_id':run['id'],'conditions':groups,'comparisons':comparisons,
            'notes':['Outcomes are mutually exclusive and sum to planned calls within each provider/arm/scope.',
                     'Native type is finite int/float excluding bool for numeric tasks, and expected top-level JSON type for exact tasks.',
                     'Array element types, shape and content remain part of strict correctness, not this top-level type endpoint.',
                     'Strings are never decoded or coerced. Invalid JSON and truncation are not native-type successes.',
                     'Type intervals use returned matched pairs and task-cluster percentile bootstrap, 2000 draws, seed 2026100301.',
                     'Fresh task parameters within known families; not new domains, population inference or equivalence evidence.']}


def export_types(run, output):
    data = type_diagnostics(run)
    dest = Path(output)
    atomic_json(dest/'types.json',data)
    text = '# JSON原生类型诊断\n\n' + '\n\n'.join(data['notes']) + '\n\n'
    text += '|模型|条件|范围|类型正确/返回/计划|类型错误|类型对但答案错|答案正确|JSON错误/截断|请求失败/待定/未尝试|\n|---|---|---|---|---:|---:|---:|---|---|\n'
    for g in data['conditions']:
        c = g['outcomes']
        text += f"|{g['provider']}|{g['arm']}|{g['scope']}|{g['native_type_ok']}/{g['returned']}/{g['planned']}|{c['wrong_native_type']}|{c['native_type_wrong_answer']}|{c['correct']}|{c['invalid_json']}/{c['truncated']}|{c['request_error']}/{c['pending']}/{c['not_attempted']}|\n"
    text += '\n## 同题类型变化\n\n|模型|范围|配对/缺失|类型正确次数|改善/退步|类型合格率差|95%描述区间（仅整体）|\n|---|---|---|---|---|---|---|\n'
    for p in data['comparisons']:
        text += f"|{p['provider']}|{p['scope']}|{p['paired']}/{p['missing_pairs']}|{p['left_type_ok']}→{p['right_type_ok']}|{p['only_right_type_ok']}/{p['only_left_type_ok']}|{p['type_delta']}|{p.get('native_type_delta_95pct','—')}|\n"
    (dest/'types.md').write_text(text,encoding='utf-8')
    return data
