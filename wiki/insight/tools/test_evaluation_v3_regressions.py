#!/usr/bin/env python3
"""Regression checks for publication decisions, legacy evaluations and retries."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

import test_evaluation_tools as fixtures
from evaluation_state import latest_evaluations
from evaluation_validator import CURRENT_RUBRIC_VERSION as V, validate_text

HERE = Path(__file__).resolve().parent


class ValidatorRegressionTest(unittest.TestCase):
    def test_partial_exemption_empty_gate_and_ambiguous_actions_rejected(self):
        base = fixtures.ev()
        variants = [
            base.replace('| 観点 | 状態 | 根拠 |\n', ''),
            base.replace('| 事実基盤 | 十分 |', '| 事実基盤 | 対象外 |'),
            base.replace('- R1: a', '- R1:'),
            base.replace('## 対応項目', '| 未知観点 | 十分 | 根拠 |\n## 対応項目'),
            fixtures.ev(actions='- なし\n' + fixtures.action('任意改善')),
            fixtures.ev(actions=fixtures.action('任意改善') + '\n- 種別: 修正必須'),
            base.replace('- reusability_gate: 合格', '- reusability_gate: 合格\n- pass: はい'),
        ]
        for body in variants:
            with self.subTest(body=body):
                result = validate_text(body)
                self.assertFalse(result['valid'])
                self.assertFalse(result['pass'])

    def test_required_research_validates_and_missing_or_blank_question_rejected(self):
        states = {d: '十分' for d in fixtures.D}
        states['事実基盤'] = '要対応'
        fields = '\n- 確認対象: 主張の支持\n- 必要な理由: 採否を決める\n- 調査先: 原典\n- 結果ごとの対応: 支持なら維持、非支持なら修正、確認不能なら保留'
        body = fixtures.ev(states, fixtures.action('調査必須', '事実基盤', fields))
        result = validate_text(body)
        self.assertTrue(result['valid'], result['errors'])
        self.assertFalse(result['pass'])
        self.assertEqual(result['research_count'], 1)
        self.assertEqual(result['decision'], '要対応')
        self.assertFalse(validate_text(body.replace('- 確認対象: 主張の支持', '- 確認対象:'))['valid'])

    def test_dimension_and_action_must_match_both_directions(self):
        states = {d: '十分' for d in fixtures.D}
        states['事実基盤'] = '要対応'
        self.assertFalse(validate_text(fixtures.ev(states))['valid'])
        self.assertFalse(validate_text(fixtures.ev(actions=fixtures.action()))['valid'])


class StateRegressionTest(unittest.TestCase):
    def setUp(self):
        helper = fixtures.StateCliTest()
        self.helper = helper
        self.temp, self.root, self.pages = helper.setup()
        self.addCleanup(self.temp.cleanup)
        self.tool = lambda *args, **kwargs: helper.tool(self.root, *args, **kwargs)
        self.manifest = helper.init_next(self.root, self.pages)
        self.body = self.root / 'body.md'
        self.body.write_text(fixtures.ev())
        self.evaluations = self.root / fixtures.EVALS

    def save(self, check=True):
        return self.tool('save', '--manifest', str(self.manifest), '--slug', 'sample',
                         '--body', str(self.body), '--evaluated-at', '2026-01-02T00:00:00Z',
                         '--evaluation-run-id', 'abcdefgh', check=check)

    def test_hash_change_while_running_rejects_save(self):
        page = self.pages / 'sample.md'
        page.write_text(page.read_text().replace('# t', '# changed'))
        result = self.save(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('target changed since', result.stderr)
        self.assertFalse((self.evaluations / 'sample/article.md').exists())
        self.assertEqual(json.loads(self.manifest.read_text())['items'][0]['status'], 'running')

    def test_failed_save_keeps_the_previous_evaluation(self):
        self.save()
        article = self.evaluations / 'sample/article.md'
        before = article.read_text()
        self.tool('init', '--manifest', str(self.manifest), '--rubric-version', str(V), '--pages-dir', str(self.pages))
        self.tool('next', '--manifest', str(self.manifest))
        self.body.write_text(fixtures.ev().replace('- R1: a', '- R1:'))
        self.assertNotEqual(self.save(check=False).returncode, 0)
        self.assertEqual(article.read_text(), before)
        self.assertEqual(sorted(p.name for p in article.parent.iterdir()), ['article.md', 'design.md'])

    def test_retry_limit_and_resume_preserve_pending_work(self):
        for expected in ('retry', 'retry', 'failed'):
            self.tool('fail', '--manifest', str(self.manifest), '--slug', 'sample', '--error', 'invalid')
            item = json.loads(self.manifest.read_text())['items'][0]
            self.assertEqual(item['status'], expected)
            if expected != 'failed':
                self.tool('next', '--manifest', str(self.manifest))
        self.assertIn('EVALUATION_NEXT none', self.tool('next', '--manifest', str(self.manifest)).stdout)
        self.assertEqual(json.loads(self.manifest.read_text())['items'][0]['attempts'], 3)

    def test_resume_and_batch_cap(self):
        self.tool('resume', '--manifest', str(self.manifest))
        self.assertEqual(json.loads(self.manifest.read_text())['items'][0]['status'], 'retry')
        for slug in ('alpha', 'bravo', 'charlie', 'delta'):
            (self.pages / f'{slug}.md').write_text((self.pages / 'sample.md').read_text())
            self.helper.add_design_pair(self.root, slug)
        self.tool('init', '--manifest', str(self.manifest), '--rubric-version', str(V), '--pages-dir', str(self.pages))
        result = self.tool('next', '--manifest', str(self.manifest))
        self.assertEqual(result.stdout.count('EVALUATION_NEXT slug='), 3)
        self.assertEqual(sum(i['status'] == 'pending' for i in json.loads(self.manifest.read_text())['items']), 2)

    def test_old_save_next_resume_refused(self):
        data = json.loads(self.manifest.read_text())
        data['rubric_version'] = V - 1
        self.manifest.write_text(json.dumps(data))
        for operation in ('next', 'resume'):
            self.assertNotEqual(self.tool(operation, '--manifest', str(self.manifest), check=False).returncode, 0)
        self.assertNotEqual(self.save(check=False).returncode, 0)

    def test_article_init_and_resume_refuse_missing_design_claim(self):
        (self.evaluations / 'sample/design.md').unlink()
        fresh = self.root / 'without-design.json'
        rejected = self.tool('init', '--manifest', str(fresh), '--rubric-version', str(V),
                             '--target', 'sample:wiki/insight/pages/sample.md', check=False)
        self.assertNotEqual(rejected.returncode, 0)
        self.assertFalse(fresh.exists())
        data = json.loads(self.manifest.read_text())
        for key in ('design_blob', 'design_evaluation', 'design_evaluation_blob', 'design_rubric_version'):
            data['items'][0].pop(key)
        self.manifest.write_text(json.dumps(data))
        self.assertNotEqual(self.tool('resume', '--manifest', str(self.manifest), check=False).returncode, 0)

    def test_source_codes_cannot_be_hidden_in_wrong_token(self):
        page = self.pages / 'sample.md'
        page.write_text(page.read_text().replace('- S1（一次）: https://example.com — 根拠。', '外部ソース未確認。'))
        self.tool('resume', '--manifest', str(self.manifest))
        self.tool('next', '--manifest', str(self.manifest))
        states = {d: '十分' for d in fixtures.D}
        states['事実基盤'] = '要対応'
        self.body.write_text(fixtures.ev(states, fixtures.action('修正必須', '事実基盤').replace('SOURCE_MISSING', 'SOURCE_MISSING123')))
        result = self.save(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('matching mandatory', result.stderr)

    def test_legacy_evaluation_forces_full_reevaluation(self):
        self.save()
        records, invalid = latest_evaluations(self.pages, self.evaluations)
        self.assertEqual(records[0]['status'], 'current')
        self.assertEqual(records[0]['rubric_version'], V)
        self.assertFalse(invalid)
        article = self.evaluations / 'sample/article.md'
        article.write_text(article.read_text().replace(f'rubric_version: {V}\n', f'rubric_version: {V - 1}\n'))
        records, invalid = latest_evaluations(self.pages, self.evaluations)
        self.assertEqual(records[0]['status'], 'legacy')
        self.assertFalse(invalid)
        out = json.loads(self.tool('normalize', '--pages-dir', str(self.pages)).stdout)
        self.assertEqual(out['distribution']['再評価必要'], 1)
        self.assertFalse(out['improvement_queue'])
        audit = subprocess.run([sys.executable, str(HERE / 'check.py'), '--root', str(self.root)],
                               cwd=self.root, text=True, capture_output=True)
        self.assertEqual(audit.returncode, 0, audit.stderr)
        self.assertIn('scope=all', audit.stdout)
        self.assertIn('reason=rubric', audit.stdout)

    def test_orphan_records_are_reported(self):
        (self.evaluations / 'gone').mkdir()
        evidence = self.root / 'wiki/insight/evidence'
        evidence.mkdir(parents=True)
        (evidence / 'merged.md').write_text('# 外部検証記録: merged\n')
        audit = subprocess.run([sys.executable, str(HERE / 'check.py'), '--root', str(self.root)],
                               cwd=self.root, text=True, capture_output=True)
        self.assertEqual(audit.returncode, 0, audit.stderr)
        self.assertIn('ORPHAN_RECORD severity=ERROR collection=insight slug=gone kind=evaluations', audit.stdout)
        self.assertIn('ORPHAN_RECORD severity=ERROR collection=insight slug=merged kind=evidence', audit.stdout)


if __name__ == '__main__':
    unittest.main()
