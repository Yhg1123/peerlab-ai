import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from peerlab import efficiency
from peerlab.efficiency_report import export_efficiency
from peerlab.experiment import load_cases
from peerlab.grading import grade
from test_peerlab import FakeClient


class NativeTypesTests(unittest.TestCase):
    def module(self):
        self.assertIsNotNone(importlib.util.find_spec('peerlab.native_types'), 'Type diagnostics are not implemented')
        from peerlab import native_types
        return native_types

    def test_new_protocol_preserves_baseline_and_changes_only_type_instruction(self):
        self.assertTrue(hasattr(efficiency, 'NATIVE'), 'Type protocol is not implemented')
        case = load_cases()[0]
        base = efficiency.messages_for(case, 'evidence_first_unbounded')
        control = efficiency.messages_for(case, 'native_control')
        treatment = efficiency.messages_for(case, 'native_explicit')
        self.assertEqual(base, control)
        self.assertEqual(treatment[1], control[1])
        self.assertTrue(treatment[0]['content'].startswith(control[0]['content']))
        changed = dict(case, expected='SECRET_REFERENCE', rationale='SECRET_RATIONALE')
        self.assertEqual(efficiency.messages_for(changed, 'native_explicit'), treatment)
        self.assertEqual(efficiency.make_plan([case], 2, protocol=efficiency.NATIVE)['planned_calls'], 8)

    def test_types_are_not_coerced_and_invalid_or_truncated_is_not_type_success(self):
        module = self.module()
        number = {'check':'number', 'expected':10}
        array = {'check':'exact', 'expected':[1,2]}
        def row(answer, finish='stop'):
            return {'status':'ok','finish_reason':finish,'content':json.dumps({'evidence':'check','answer':answer})}
        for case, answer, expected in [(number,10,True),(number,11,True),(number,'10',False),
                                       (number,True,False),(number,None,False),(array,[1,2],True),
                                       (array,'[1,2]',False),(array,[1,'2'],True)]:
            with self.subTest(answer=answer):
                self.assertEqual(module.native_type_ok(case,row(answer)),expected)
        self.assertFalse(module.native_type_ok(number,row(10,'length')))
        bad=row(10);bad['content']='{"answer":10,"answer":11}'
        self.assertFalse(module.native_type_ok(number,bad))
        bad['content']='{"answer":1e999}'
        self.assertFalse(module.native_type_ok(number,bad))

    def test_paired_type_diagnostics_separate_arithmetic_and_missingness(self):
        module = self.module()
        cases = [c for c in load_cases() if c['id'] in ('critical-path','sql-null')]
        with tempfile.TemporaryDirectory() as directory:
            dest=Path(directory)/'run'
            run=efficiency.run_efficiency([FakeClient('deepseek'),FakeClient('kimi')],cases,dest,
                                         protocol=efficiency.NATIVE,repeats=2,max_calls=16,progress=lambda _:None)
            for r in run['records']:
                c=next(c for c in cases if c['id']==r['case_id'])
                # Type improves in all pairs, but every numerical answer remains wrong.
                r['content']=json.dumps({'evidence':'check','answer': -1 if r['arm']=='native_explicit' else '-1'})
                r['grade']=grade(c,r['content'])
            data=module.type_diagnostics(run)
            p=next(p for p in data['comparisons'] if p['provider']=='deepseek' and p['scope']=='all')
            self.assertEqual((p['paired'],p['left_type_ok'],p['right_type_ok']), (4,0,4))
            self.assertEqual(p['native_type_delta_95pct'],[1,1])
            self.assertEqual(p['task_clusters'],2)
            g=next(g for g in data['conditions'] if g['provider']=='deepseek' and g['arm']=='native_explicit' and g['scope']=='all')
            self.assertEqual(g['outcomes']['native_type_wrong_answer'],4)
            r=next(r for r in run['records'] if r['provider']=='kimi' and r['arm']=='native_explicit')
            r['status']='error';run['status']='partial'
            data=module.type_diagnostics(run)
            p=next(p for p in data['comparisons'] if p['provider']=='kimi' and p['scope']=='all')
            self.assertEqual((p['paired'],p['missing_pairs']), (3,1))
            export_efficiency(run,dest)
            self.assertTrue((dest/'types.json').exists())
            self.assertIn('原生类型', (dest/'report.html').read_text(encoding='utf-8'))

    def test_new_dataset_reproduces_with_no_prior_prompt_overlap(self):
        root=Path(__file__).resolve().parents[1]
        spec=importlib.util.spec_from_file_location('build_native_dataset',root/'scripts/build_native_dataset.py')
        builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
        saved=json.loads((root/'peerlab/data/token-efficiency-v4.json').read_text(encoding='utf-8'))
        self.assertEqual(builder.build(),saved)
        self.assertEqual(len(saved),16)
        self.assertEqual(sum('oracle' in c for c in saved),12)
        previous={c['prompt'] for name in builder.PRIOR_STUDIES for c in json.loads((root/'examples'/name/'run.json').read_text(encoding='utf-8'))['cases']}
        self.assertFalse(previous.intersection(c['prompt'] for c in saved))
        # Independently hand-checked references, not the builder's algorithm.
        expected={'v4-stable-even':[4,2,6],'v4-ranked-ids':['a','q','m'],
                  'v4-transpose':[[3,5,7],[8,1,4]],'v4-alias-copy':[[4,9],[4,9],[4,2]]}
        self.assertEqual({c['id']:c['expected'] for c in saved if 'oracle' not in c},expected)
