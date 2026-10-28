"""Run: python3 -I skills/productivity/catch-up/scripts/test_find_sessions.py"""
import json, os, sys, tempfile, unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import find_sessions as fs


def write(path, events):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.writelines(json.dumps(e) + '\n' for e in events)


def claude_turn(cwd, text, ts):
    return {'type': 'user', 'cwd': cwd, 'timestamp': ts, 'message': {'role': 'user', 'content': text}}


def claude_reply(text, ts, bash=None):
    content = [{'type': 'text', 'text': text}]
    if bash:
        content.append({'type': 'tool_use', 'name': 'Bash', 'input': {'command': bash}})
    return {'type': 'assistant', 'timestamp': ts, 'message': {'role': 'assistant', 'content': content}}


def codex_events(sid, cwd, source='cli', reply='Done.', error=None):
    ev = [{'type': 'session_meta', 'timestamp': '2026-10-20T10:00:00Z', 'payload': {'id': sid, 'cwd': cwd, 'source': source}},
          {'type': 'response_item', 'timestamp': '2026-10-20T10:00:01Z', 'payload': {'type': 'message', 'role': 'user',
           'content': [{'type': 'input_text', 'text': '<environment_context>noise</environment_context>'},
                       {'type': 'input_text', 'text': 'Ship slice 3'}]}},
          {'type': 'response_item', 'timestamp': '2026-10-20T10:00:02Z', 'payload': {'type': 'function_call', 'name': 'exec',
           'arguments': '{"cmd": "git push && gh pr create"}'}},
          {'type': 'response_item', 'timestamp': '2026-10-20T10:00:03Z', 'payload': {'type': 'function_call_output',
           'output': 'https://github.com/o/r/pull/7'}},
          {'type': 'response_item', 'timestamp': '2026-10-20T10:00:04Z', 'payload': {'type': 'message', 'role': 'assistant',
           'content': [{'type': 'output_text', 'text': reply}]}}]
    if error:
        ev.append({'type': 'event_msg', 'timestamp': '2026-10-20T10:00:05Z', 'payload': {'type': 'error', 'message': error}})
    return ev


class FindSessions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = self.tmp.name
        self.work = os.path.realpath(os.path.join(t, 'my.repo'))
        os.makedirs(self.work)
        self.claude_root = os.path.join(t, 'claude')
        self.codex = os.path.join(t, 'codex')
        proj = os.path.join(self.claude_root, fs.claude_dir(self.work))
        write(f'{proj}/real.jsonl', [claude_turn(self.work, 'Fix the login bug', '2026-10-21T10:00:00Z'),
                                     claude_reply('Committed.', '2026-10-21T10:01:00Z', bash='git commit -m x'),
                                     claude_turn(self.work, 'Now open the PR', '2026-10-21T10:02:00Z'),
                                     claude_reply("You've hit your session limit · resets 11pm", '2026-10-21T10:03:00Z')])
        write(f'{proj}/ping.jsonl', [claude_turn(self.work, 'Reply only with Hi', '2026-10-22T10:00:00Z')])
        write(f'{proj}/me.jsonl', [claude_turn(self.work, 'where did we leave off?', '2026-10-23T10:00:00Z')])
        write(f'{self.codex}/sessions/2026/10/20/rollout-a.jsonl', codex_events('cx1', self.work, error='You have hit your usage limit.'))
        write(f'{self.codex}/sessions/2026/10/20/rollout-b.jsonl', codex_events('cx2', self.work, source={'subagent': 'review'}))
        write(f'{self.codex}/sessions/2026/10/20/rollout-c.jsonl', codex_events('cx3', '/elsewhere'))
        write(f'{self.codex}/session_index.jsonl', [{'id': 'cx1', 'thread_name': 'Slice 3'}])

    def tearDown(self):
        self.tmp.cleanup()

    def run_find(self):
        return fs.find(self.work, 5, {'me'}, claude_root=self.claude_root, homes=[self.codex])[1]

    def test_keeps_real_sessions_and_skips_pings_subagents_self_and_other_dirs(self):
        self.assertEqual(sorted(r['id'] for r in self.run_find()), ['cx1', 'real'])

    def test_claude_session_summary(self):
        r = next(r for r in self.run_find() if r['id'] == 'real')
        self.assertEqual(r['user'], ['Fix the login bug', 'Now open the PR'])
        self.assertEqual(r['ended'], 'hit a usage limit')
        self.assertEqual(r['actions'], {'commit': 1})

    def test_codex_session_summary(self):
        r = next(r for r in self.run_find() if r['id'] == 'cx1')
        self.assertEqual(r['user'], ['Ship slice 3'])
        self.assertEqual(r['title'], 'Slice 3')
        self.assertEqual(r['said'], 'Done.')
        self.assertEqual(r['ended'], 'hit a usage limit')
        self.assertEqual(r['actions'], {'push': 1, 'pr_create': 1})
        self.assertEqual(r['prs'], {'https://github.com/o/r/pull/7'})

    def test_render_lists_turns_and_prs(self):
        out = fs.render(next(r for r in self.run_find() if r['id'] == 'cx1'), 4)
        self.assertIn('1. Ship slice 3', out)
        self.assertIn('https://github.com/o/r/pull/7', out)


if __name__ == '__main__':
    unittest.main()
