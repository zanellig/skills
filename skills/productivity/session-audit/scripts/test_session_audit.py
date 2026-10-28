"""Run: python3 -I skills/productivity/session-audit/scripts/test_session_audit.py"""
import contextlib, io, json, os, sys, tempfile, unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_cites, digest, extract, stats


def read(path):
    with open(path) as f:
        return f.read()


def write(path, events):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.writelines(json.dumps(e) + '\n' for e in events)


def user(text, ts, origin=None):
    e = {'type': 'user', 'cwd': '/work/app', 'timestamp': ts, 'message': {'role': 'user', 'content': text}}
    if origin:
        e['origin'] = {'kind': origin}
    return e


def reply(text, ts):
    return {'type': 'assistant', 'timestamp': ts, 'message': {'role': 'assistant', 'content': [{'type': 'text', 'text': text}]}}


class SessionAudit(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = os.path.join(self.tmp.name, 'home')
        self.out = os.path.join(self.tmp.name, 'audit', 'out')
        proj = f'{self.home}/.claude/projects/-work-app'
        head = [user('Fix the login bug', '2026-10-20T10:00:00Z'), reply('Fixed.', '2026-10-20T10:01:00Z'),
                user('Now add tests', '2026-10-20T10:02:00Z')]
        write(f'{proj}/real.jsonl', head + [
            user('<task-notification>agent finished</task-notification>', '2026-10-20T10:03:00Z', origin='task-notification'),
            user('<github-event>coderabbit[bot] commented on the PR</github-event>', '2026-10-20T10:04:00Z'),
            user('Ship it', '2026-10-20T10:05:00Z')])
        # Resumed later: replays the first two turns, then adds one of its own.
        write(f'{proj}/resumed.jsonl', head + [user('Also update the docs', '2026-10-21T09:00:00Z')])
        write(f'{proj}/ping.jsonl', [user('Reply only with Hi', '2026-10-22T10:00:00Z')])
        write(f'{proj}/greet.jsonl', [user('hola', '2026-10-22T11:00:00Z'), user('Hello Claude!', '2026-10-22T11:01:00Z')])
        write(f'{proj}/audit.jsonl', [user('# Session audit brief\n\nYou are auditing one chunk', '2026-10-22T12:00:00Z')])
        write(f'{proj}/real/subagents/agent-1.jsonl', [user('Explore the repo', '2026-10-20T10:01:00Z')])
        write(f'{proj}/sec.jsonl', [user('Review the settings page', '2026-10-23T10:00:00Z'), reply('Looking.', '2026-10-23T10:01:00Z'),
                                    user('Run a security review of the upload route', '2026-10-23T10:02:00Z')])
        write(f'{self.home}/.codex_p/sessions/2026/10/24/rollout-x.jsonl', [
            {'type': 'session_meta', 'timestamp': '2026-10-24T10:00:00Z', 'payload': {'id': 'cx1', 'cwd': '/work/app', 'source': 'cli', 'originator': 'codex_cli'}},
            {'type': 'response_item', 'timestamp': '2026-10-24T10:00:01Z', 'payload': {'type': 'message', 'role': 'user',
             'content': [{'type': 'input_text', 'text': '<environment_context>x</environment_context>'}, {'type': 'input_text', 'text': 'Plan the refactor'}]}}])
        self.env = mock.patch.dict(os.environ, {'HOME': self.home, 'CODEX_HOME': ''})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def extract(self, *args):
        with contextlib.redirect_stdout(io.StringIO()):
            extract.main([self.out, *args])
        sessions = {os.path.basename(r['path']): r for r in map(json.loads, read(f'{self.out}/sessions.jsonl').splitlines())}
        turns = {os.path.basename(d['path']): d['turns'] for d in map(json.loads, read(f'{self.out}/turns.jsonl').splitlines())}
        return sessions, turns

    def test_exclusions(self):
        s, _ = self.extract()
        kinds = {k: v['kind'] for k, v in s.items()}
        self.assertEqual(kinds['ping.jsonl'], 'healthcheck')
        self.assertEqual(kinds['greet.jsonl'], 'greeting')
        self.assertEqual(kinds['audit.jsonl'], 'self')
        self.assertEqual(kinds['agent-1.jsonl'], 'subagent')
        self.assertEqual(kinds['sec.jsonl'], 'interactive')
        self.assertEqual(kinds['rollout-x.jsonl'], 'interactive')

    def test_health_check_prompts_can_be_replaced(self):
        s, _ = self.extract('--health-check', 'Are you up')
        self.assertEqual(s['ping.jsonl']['kind'], 'interactive')

    def test_date_range(self):
        s, _ = self.extract('--since', '2026-10-22', '--until', '2026-10-23')
        self.assertEqual(sorted(s), ['audit.jsonl', 'greet.jsonl', 'ping.jsonl', 'sec.jsonl'])

    def test_machine_turns_are_marked_not_counted(self):
        s, t = self.extract()
        self.assertEqual([u['machine'] for u in t['real.jsonl']][:5], [None, None, 'task-notification', 'ci-bot', None])
        self.assertEqual(s['real.jsonl']['n_machine'], 2)
        self.assertEqual(s['real.jsonl']['first_prompt'], 'Fix the login bug')

    def test_fork_keeps_only_its_unique_tail(self):
        s, t = self.extract()
        self.assertEqual((s['resumed.jsonl']['kind'], s['resumed.jsonl']['merged_into']), ('fork', 'real'))
        self.assertNotIn('resumed.jsonl', t)
        self.assertEqual([u['text'] for u in t['real.jsonl']].count('Fix the login bug'), 1)
        self.assertEqual(t['real.jsonl'][-1]['text'], 'Also update the docs')
        self.assertEqual(s['real.jsonl']['n_user'], 4)
        self.assertEqual(stats.main(self.out)['forks_merged'], 1)

    def test_security_sessions_go_only_to_gpt_chunks(self):
        self.extract()
        dig = os.path.join(self.tmp.name, 'audit', 'digests')
        with contextlib.redirect_stdout(io.StringIO()):
            digest.main([self.out, dig])
        status = json.loads(read(f'{dig}/status.json'))
        self.assertEqual(status, {'c01-claude': 'pending', 's01-gpt': 'pending'})
        self.assertIn('security review', read(f'{dig}/s01-gpt.md'))
        self.assertNotIn('security review', read(f'{dig}/c01-claude.md'))
        self.assertIn('M[ci-bot]', read(f'{dig}/c01-claude.md'))

    def test_citations(self):
        audit = os.path.join(self.tmp.name, 'audit')
        os.makedirs(f'{audit}/findings')
        self.extract()
        with contextlib.redirect_stdout(io.StringIO()):
            digest.main([self.out, f'{audit}/digests'])
        n = len(json.loads(read(f'{self.out}/session_index.json')))
        have = [int(l.split()[1][1:]) for l in read(f'{audit}/digests/c01-claude.md').splitlines() if l.startswith('### S')]
        good, bad = have[0], n + 50
        with open(f'{audit}/findings/c01-claude.md', 'w') as f:
            f.write(f'Pattern one (S{good}).\nPattern two (S{bad}).\n')
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(check_cites.main([audit]), 1)
        self.assertIn(f'c01-claude.md:2: S{bad}', out.getvalue())
        self.assertIn('relaunch: s01-gpt', out.getvalue())
        self.assertEqual(json.loads(read(f'{audit}/digests/status.json'))['c01-claude'], 'done')
        with open(f'{audit}/findings/c01-claude.md', 'w') as f:
            f.write(f'Pattern one (S{good}).\n')
        report = os.path.join(audit, 'report.html')
        with open(report, 'w') as f:
            f.write(f'<p>S{good}</p><p>S{bad}</p>')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(check_cites.main([audit]), 0)
            self.assertEqual(check_cites.main([audit, '--report', report]), 1)


if __name__ == '__main__':
    unittest.main()
