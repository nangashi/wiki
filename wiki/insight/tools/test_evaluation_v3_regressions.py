#!/usr/bin/env python3
"""Regression checks for publication decisions, legacy history and retries."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

import test_evaluation_tools as fixtures
from evaluation_state import latest_evaluations
from evaluation_validator import validate_text
from test_evaluation_legacy import evaluation

HERE = Path(__file__).resolve().parent


class V3RegressionTest(unittest.TestCase):
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

    def test_legacy_requires_version_and_is_not_valid_v3(self):
        body = evaluation()
        self.assertTrue(validate_text(body, 'sample', 2)['valid'])
        self.assertFalse(validate_text(body, 'sample', 3)['valid'])
        self.assertFalse(validate_text(body, 'sample', 4)['valid'])
        self.assertFalse(validate_text(body, 'sample', 5)['valid'])
        self.assertTrue(validate_text('---\nrubric_version: 2\n---\n' + body)['valid'])


class StateRegressionTest(unittest.TestCase):
    def setUp(self):
        helper = fixtures.StateCliTest()
        self.temp, self.root, self.pages = helper.setup()
        self.addCleanup(self.temp.cleanup)
        self.tool = lambda *args, **kwargs: helper.tool(self.root, *args, **kwargs)
        refs = self.root / 'wiki/insight/references'
        refs.mkdir()
        (refs / 'article-quality-rubric.md').write_text('**rubric_version: 5**\n')
        self.manifest = helper.init_next(self.root, self.pages)
        self.body = self.root / 'body.md'
        self.body.write_text(fixtures.ev())
        self.history = self.root / 'evaluations/insight'

    def save(self, check=True):
        return self.tool('save', '--manifest', str(self.manifest), '--slug', 'sample',
                         '--body', str(self.body), '--evaluations-root', str(self.history),
                         '--evaluated-at', '2026-01-02T00:00:00Z', '--evaluation-run-id', 'abcdefgh', check=check)

    def test_hash_change_while_running_rejects_save(self):
        page = self.pages / 'sample.md'
        page.write_text(page.read_text().replace('# t', '# changed'))
        result = self.save(check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('target changed since', result.stderr)
        self.assertFalse(list(self.history.glob('sample/*.md')))
        self.assertEqual(json.loads(self.manifest.read_text())['items'][0]['status'], 'running')

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
        self.tool('init', '--manifest', str(self.manifest), '--rubric-version', '5', '--pages-dir', str(self.pages))
        result = self.tool('next', '--manifest', str(self.manifest))
        self.assertEqual(result.stdout.count('EVALUATION_NEXT slug='), 3)
        self.assertEqual(sum(i['status'] == 'pending' for i in json.loads(self.manifest.read_text())['items']), 2)

    def test_old_save_next_resume_refused(self):
        data = json.loads(self.manifest.read_text())
        data['rubric_version'] = 4
        self.manifest.write_text(json.dumps(data))
        for operation in ('next', 'resume'):
            self.assertNotEqual(self.tool(operation, '--manifest', str(self.manifest), check=False).returncode, 0)
        self.assertNotEqual(self.save(check=False).returncode, 0)

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

    def test_legacy_and_corrupt_history_do_not_override_current(self):
        self.save()
        current = next(self.history.glob('sample/*.md'))
        text = current.read_text()
        metadata = text[:text.index('\n---\n', 4) + 5]
        legacy_meta = metadata.replace('rubric_version: 5', 'rubric_version: 2').replace('2026-01-02', '2026-01-01')
        old = current.parent / '20260101T000000Z-v2-abcdefgh.md'
        old.write_text(legacy_meta + evaluation())
        (current.parent / '20260103T000000Z-v4-bcdefghi.md').write_text('bad')
        records, invalid = latest_evaluations(self.pages, self.history)
        self.assertEqual(records[0]['status'], 'current')
        self.assertEqual(records[0]['rubric_version'], 5)
        self.assertTrue(invalid)
        # A legacy-only sibling stays readable, but is excluded from v5 decisions.
        (self.pages / 'old.md').write_text((self.pages / 'sample.md').read_text())
        (self.history / 'old').mkdir()
        old_only = self.history / 'old/20260101T000000Z-v2-abcdefgh.md'
        old_only.write_text(legacy_meta.replace('pages/sample.md', 'pages/old.md') + evaluation('old'))
        records, invalid = latest_evaluations(self.pages, self.history)
        self.assertEqual(next(r for r in records if r['slug'] == 'old')['status'], 'legacy')
        out = json.loads(self.tool('normalize', '--pages-dir', str(self.pages), '--evaluations-root', str(self.history)).stdout)
        self.assertEqual(out['distribution']['再評価必要'], 1)
        self.assertFalse(out['improvement_queue'])
        cli = subprocess.run([sys.executable, str(HERE / 'evaluation_validator.py'), str(old_only)], text=True, capture_output=True)
        self.assertEqual(cli.returncode, 0, cli.stderr)
        # The shell audit must also recognize the old version, not call it malformed.
        audit = subprocess.run([sys.executable, str(HERE / 'check.py'), '--root', str(self.root)],
                               cwd=self.root, text=True, capture_output=True)
        self.assertEqual(audit.returncode, 0, audit.stderr)
        self.assertIn('scope=all', audit.stdout)
        self.assertIn('reason=rubric', audit.stdout)


if __name__ == '__main__':
    unittest.main()
