"""Build the frozen v4 task set without consulting any v4 model responses."""

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from peerlab.datasets import generate_cases, make_case, write_dataset

PRIOR_STUDIES = ('pilot','review-study-v1','token-efficiency-v1','token-efficiency-v2','token-efficiency-v3')


def build():
    previous = [c for name in PRIOR_STUDIES for c in json.loads((ROOT/'examples'/name/'run.json').read_text(encoding='utf-8'))['cases']]
    prompts = {c['prompt'] for c in previous}
    cases = []
    for family in ('bayes','macro_f1'):
        candidates = generate_cases(family,30,2026100401)
        chosen = [c for c in candidates if c['prompt'] not in prompts][:6]
        if len(chosen) != 6:
            raise ValueError('Insufficient novel candidates; do not silently change the seed.')
        for i,c in enumerate(chosen,1):
            new = make_case(family,c['oracle']['parameters'],i)
            new['id'] = 'v4-'+new['id']
            cases.append(new)
    manual = [
        ('stable-even','结构化输出','筛选偶数并稳定去重',
         '序列[9,4,7,4,2,9,6,2]先保留偶数，再去除重复值，保留每个值首次出现的顺序。answer必须是由整数构成的JSON数组。',
         [4,2,6],'偶数序列为[4,4,2,6,2]，按首次出现去重得[4,2,6]。'),
        ('ranked-ids','结构化输出','按分数与ID排序',
         '记录为[{"id":"m","score":3},{"id":"q","score":7},{"id":"a","score":7},{"id":"z","score":2}]。保留score至少为3的记录，先按score降序，同分按id字母升序排列。answer必须是排序后的id组成的JSON字符串数组。',
         ['a','q','m'],'z被筛掉；7分的a在q之前，然后是3分的m。'),
        ('transpose','结构化输出','二维整数数组转置',
         '矩阵的各行为[[3,8],[5,1],[7,4]]。求其转置矩阵：原矩阵的列变为新矩阵的行。answer必须是二维JSON整数数组。',
         [[3,5,7],[8,1,4]],'第一列3,5,7变为第一行；第二列8,1,4变为第二行。'),
        ('alias-copy','代码理解','引用与浅复制后的数组',
         '阅读Python代码，不执行：x=[4]; y=x; z=x[:]; x.append(9); z.append(2)。最终[x,y,z]的值是什么？answer必须是二维JSON整数数组。',
         [[4,9],[4,9],[4,2]],'x与y引用同一列表；z在追加前浅复制了元素，之后独立追加2。'),
    ]
    for cid,category,title,prompt,expected,rationale in manual:
        cases.append(dict(id='v4-'+cid,category=category,title=title,prompt=prompt,check='exact',expected=expected,rationale=rationale))
    if len(cases)!=16 or len({c['prompt'] for c in cases})!=16 or any(c['prompt'] in prompts for c in cases):
        raise ValueError('Task novelty check failed.')
    return cases


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    write_dataset(args.output,build())
    print('Wrote 16 tasks: 12 numeric oracle references, 4 manual array references; zero exact-prompt overlap with prior five studies.')
