"""Run: python3 -I skills/productivity/session-audit/scripts/test_session_audit.py"""
import contextlib, io, json, os, sys, tempfile, unittest
from unittest import mock

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_cites, digest, extract, stats


def read(path):
    with open(path) as f:
        return f.read()


def write(path, events):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.writelines(json.dumps(e) + '\n' for e in events)


def user(text, ts, origin=None, uuid=None, cwd='/work/app'):
    e = {'type': 'user', 'cwd': cwd, 'timestamp': ts, 'uuid': uuid or f'u-{ts}-{text[:20]}', 'message': {'role': 'user', 'content': text}}
    if origin:
        e['origin'] = {'kind': origin}
    return e


def reply(text, ts):
    return {'type': 'assistant', 'timestamp': ts, 'uuid': f'a-{ts}', 'message': {'role': 'assistant', 'content': [{'type': 'text', 'text': text}]}}


def bash(cmd, ts):
    return {'type': 'assistant', 'timestamp': ts, 'message': {'role': 'assistant', 'model': 'claude-x',
            'content': [{'type': 'tool_use', 'name': 'Bash', 'input': {'command': cmd}}]}}


def rollout(path, sid, cwd, turns):
    events = [{'type': 'session_meta', 'timestamp': turns[0][2], 'payload': {'id': sid, 'cwd': cwd, 'source': 'cli', 'originator': 'codex_cli'}}]
    for turn_id, text, ts in turns:
        events += [{'type': 'event_msg', 'timestamp': ts, 'payload': {'type': 'task_started', 'turn_id': turn_id}},
                   {'type': 'response_item', 'timestamp': ts, 'payload': {'type': 'message', 'role': 'user', 'content': [{'type': 'input_text', 'text': text}]}}]
    write(path, events)


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
        # Resumed later: replays the first two turns (same event uuids), then adds work of its own.
        write(f'{proj}/resumed.jsonl', head + [user('Also update the docs', '2026-10-21T09:00:00Z'),
                                               bash('git commit -m docs', '2026-10-21T09:01:00Z')])
        # Forked with --fork-session: replayed events get new uuids and point at the originals.
        write(f'{proj}/forked.jsonl', [dict(e, uuid=f'new-{i}', forkedFrom={'sessionId': 'real', 'messageUuid': e['uuid']}) for i, e in enumerate(head)]
              + [user('Try another approach', '2026-10-21T11:00:00Z')])
        # Same opening words, no shared identity: separate sessions.
        write(f'{proj}/lookalike.jsonl', [dict(e, uuid=f'other-{i}') for i, e in enumerate(head)] + [user('Different work', '2026-10-21T12:00:00Z')])
        write(f'{self.home}/.claude/projects/-work-api/elsewhere.jsonl', [user('Fix the login bug', '2026-10-20T10:00:00Z', uuid=head[0]['uuid'], cwd='/work/api'),
                                                                         user('Now add tests', '2026-10-20T10:02:00Z', uuid=head[2]['uuid'], cwd='/work/api')])
        write(f'{proj}/commit.jsonl', [user('<command-message>commit</command-message>\n<command-name>/commit</command-name>\n<command-args></command-args>', '2026-10-22T13:00:00Z')])
        write(f'{proj}/ping.jsonl', [user('Reply only with Hi', '2026-10-22T10:00:00Z')])
        write(f'{proj}/greet.jsonl', [user('hola', '2026-10-22T11:00:00Z'), user('Hello Claude!', '2026-10-22T11:01:00Z')])
        write(f'{proj}/audit.jsonl', [user('# Session audit brief\n\nYou are auditing one chunk', '2026-10-22T12:00:00Z')])
        write(f'{proj}/real/subagents/agent-1.jsonl', [user('Explore the repo', '2026-10-20T10:01:00Z')])
        write(f'{proj}/sec.jsonl', [user('Review the settings page', '2026-10-23T10:00:00Z'), reply('Looking.', '2026-10-23T10:01:00Z'),
                                    user('Run a security review of the upload route', '2026-10-23T10:02:00Z')])
        # Codex history in a home whose name gives no hint; found by its content.
        write(f'{self.home}/.work-ai/sessions/2026/10/24/rollout-x.jsonl', [
            {'type': 'session_meta', 'timestamp': '2026-10-24T10:00:00Z', 'payload': {'id': 'cx1', 'cwd': '/work/app', 'source': 'cli', 'originator': 'codex_cli'}},
            {'type': 'event_msg', 'timestamp': '2026-10-24T10:00:01Z', 'payload': {'type': 'task_started', 'turn_id': 't1'}},
            {'type': 'response_item', 'timestamp': '2026-10-24T10:00:01Z', 'payload': {'type': 'message', 'role': 'user',
             'content': [{'type': 'input_text', 'text': '<environment_context>x</environment_context>'}, {'type': 'input_text', 'text': 'Plan the refactor'}]}}])
        rollout(f'{self.home}/.work-ai/sessions/2026/10/25/rollout-fork.jsonl', 'cx2', '/work/app',
                [('t1', 'Plan the refactor', '2026-10-24T10:00:01Z'), ('t2', 'Start with the parser', '2026-10-25T10:00:00Z')])
        rollout(f'{self.home}/.work-ai/sessions/2026/10/25/rollout-same-words.jsonl', 'cx3', '/work/app',
                [('t9', 'Plan the refactor', '2026-10-25T11:00:00Z'), ('t10', 'Start with the parser', '2026-10-25T11:01:00Z')])
        self.env = mock.patch.dict(os.environ, {'HOME': self.home, 'CODEX_HOME': '', 'CLAUDE_CONFIG_DIR': '',
                                                'XDG_CONFIG_HOME': '', 'XDG_DATA_HOME': ''})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        self.tmp.cleanup()

    def extract(self, *args):
        self.printed = io.StringIO()
        with contextlib.redirect_stdout(self.printed):
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
        self.assertEqual(sorted(s), ['audit.jsonl', 'commit.jsonl', 'greet.jsonl', 'ping.jsonl', 'sec.jsonl'])

    def test_codex_replies_reach_the_next_turn(self):
        path = f'{self.home}/.work-ai/sessions/2026/10/24/rollout-x.jsonl'
        with open(path, 'a') as f:
            for e in ({'type': 'response_item', 'timestamp': '2026-10-24T10:00:02Z', 'payload': {'type': 'message', 'role': 'assistant',
                       'content': [{'type': 'output_text', 'text': 'Start with the parser.'}]}},
                      {'type': 'response_item', 'timestamp': '2026-10-24T10:00:03Z', 'payload': {'type': 'message', 'role': 'user',
                       'content': [{'type': 'input_text', 'text': 'No, the lexer first'}]}}):
                f.write(json.dumps(e) + '\n')
        _, t = self.extract()
        self.assertEqual(t['rollout-x.jsonl'][1]['prev_assistant'], 'Start with the parser.')

    def test_machine_turns_are_marked_not_counted(self):
        s, t = self.extract()
        self.assertEqual([u['machine'] for u in t['real.jsonl']][:5], [None, None, 'task-notification', 'ci-bot', None])
        self.assertEqual(s['real.jsonl']['n_machine'], 2)
        self.assertEqual(s['real.jsonl']['first_prompt'], 'Fix the login bug')

    def test_fork_keeps_only_its_unique_tail(self):
        s, t = self.extract()
        for f in ('resumed.jsonl', 'forked.jsonl'):
            self.assertEqual((s[f]['kind'], s[f]['merged_into']), ('fork', 'real'))
            self.assertNotIn(f, t)
        texts = [u['text'] for u in t['real.jsonl']]
        self.assertEqual(texts.count('Fix the login bug'), 1)
        self.assertEqual(texts[-2:], ['Also update the docs', 'Try another approach'])
        self.assertEqual(s['real.jsonl']['n_user'], 5)
        self.assertEqual((s['rollout-fork.jsonl']['kind'], s['rollout-fork.jsonl']['merged_into']), ('fork', 'cx1'))
        self.assertEqual(stats.main(self.out)['forks_merged'], 3)

    def test_fork_tail_counts_fold_into_the_kept_session(self):
        s, _ = self.extract()
        real = s['real.jsonl']
        self.assertEqual((real['cmd_tags'], real['tools'], real['models']), ({'commit': 1}, {'Bash': 1}, {'claude-x': 1}))
        self.assertEqual(real['last_ts'], '2026-10-21T11:00:00Z')

    def test_same_opening_words_without_shared_identity_stay_separate(self):
        s, _ = self.extract()
        for f in ('lookalike.jsonl', 'elsewhere.jsonl', 'rollout-same-words.jsonl'):
            self.assertEqual(s[f]['kind'], 'interactive', f)

    def test_command_only_session_is_kept(self):
        s, _ = self.extract()
        self.assertEqual((s['commit.jsonl']['kind'], s['commit.jsonl']['first_prompt']), ('interactive', '/commit'))

    def test_homes_are_found_by_content(self):
        alt = f'{self.home}/.config/claude-work/projects/-work-x'
        write(f'{alt}/alt.jsonl', [user('Port the CLI', '2026-10-26T10:00:00Z')])
        os.symlink(f'{self.home}/.work-ai', f'{self.home}/.work-ai-link')
        write(f'{self.home}/.nothing/projects/readme.txt', [])
        s, _ = self.extract('--since', '2026-10-24')
        self.assertEqual(sorted(s), ['alt.jsonl', 'rollout-fork.jsonl', 'rollout-same-words.jsonl', 'rollout-x.jsonl'])
        out = self.printed.getvalue()
        self.assertIn(f'claude {self.home}/.config/claude-work: 1 sessions, 2026-10-26 to 2026-10-26', out)
        self.assertIn(f'claude {self.home}/.claude: 0 sessions', out)
        self.assertIn(f'codex {self.home}/.work-ai: 3 sessions, 2026-10-24 to 2026-10-25', out)
        self.assertNotIn('.work-ai-link', out)
        self.assertNotIn('.nothing', out)

    def test_home_overrides(self):
        other = os.path.join(self.tmp.name, 'elsewhere')
        rollout(f'{other}/sessions/2026/10/26/rollout-o.jsonl', 'cx9', '/work/o', [('t1', 'Hello from elsewhere repo work', '2026-10-26T10:00:00Z')])
        s, _ = self.extract('--codex-home', other, '--claude-home', other)
        self.assertEqual(sorted(s), ['rollout-o.jsonl'])
        with mock.patch.dict(os.environ, {'CODEX_HOME': other}):
            s, _ = self.extract()
        self.assertIn('rollout-o.jsonl', s)
        self.assertIn('rollout-x.jsonl', s)

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

    def test_citation_ranges_check_every_id(self):
        audit = os.path.join(self.tmp.name, 'audit')
        os.makedirs(f'{audit}/digests')
        os.makedirs(f'{audit}/findings')
        with open(f'{audit}/digests/c01-claude.md', 'w') as f:
            f.write('### S1 | x\n### S3 | y\n')
        with open(f'{audit}/findings/c01-claude.md', 'w') as f:
            f.write('Pattern (S1–S3).\n')
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(check_cites.main([audit]), 1)
        self.assertIn('c01-claude.md:1: S2', out.getvalue())

    def test_quoted_headings_are_not_session_ids(self):
        audit = os.path.join(self.tmp.name, 'audit')
        write(f'{self.home}/.claude/projects/-work-app/quote.jsonl', [user('Look at this digest:\n### S999 | fake', '2026-10-26T10:00:00Z')])
        self.extract()
        with contextlib.redirect_stdout(io.StringIO()):
            digest.main([self.out, f'{audit}/digests'])
        os.makedirs(f'{audit}/findings')
        name = next(n for n in json.loads(read(f'{audit}/digests/status.json')) if 'fake' in read(f'{audit}/digests/{n}.md'))
        with open(f'{audit}/findings/{name}.md', 'w') as f:
            f.write('Pattern (S999).\n')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(check_cites.main([audit]), 1)

    def test_digests_refuse_to_overwrite_an_audit(self):
        self.extract()
        dig = os.path.join(self.tmp.name, 'audit', 'digests')
        with contextlib.redirect_stdout(io.StringIO()):
            digest.main([self.out, dig])
            with self.assertRaises(SystemExit):
                digest.main([self.out, dig])


if __name__ == '__main__':
    unittest.main()
