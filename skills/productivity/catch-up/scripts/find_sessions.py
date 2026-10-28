#!/usr/bin/env python3
"""List the newest Claude Code and Codex sessions for this repo (all its worktrees) or directory.

Usage: python3 -I find_sessions.py [--dir PATH] [--limit N] [--exclude ID ...]
Prints one block per session, newest first: when, where, title, how it ended,
delivery actions (commits, pushes, PRs), the last user turns and the agent's last words.
Skips health-check pings, subagent transcripts and the calling session.
"""
import argparse, glob, json, os, re, subprocess
from datetime import datetime, timezone

HOME = os.path.expanduser('~')
PING = re.compile(r'^\s*(Reply only with Hi|Respond[ée] únicamente DISPONIBLE)', re.I)
SR = re.compile(r'<system-reminder>.*?</system-reminder>', re.S)
NOISE = ('<local-command', 'Caveat:', '<task-notification>', '<command-', '<bash-', 'Base directory for this skill:',
         'This session is being continued', '<environment_context>', '# AGENTS.md instructions', '<external_codex_apps',
         '<recommended_plugins>', '<in-app-browser-context', '<subagent_notification>', '</image>', '<image name=',
         '<permissions', '<user_instructions>', '<INSTRUCTIONS>', '<collaboration_mode>', '<apps_instructions>',
         '<skills_instructions>', '<skill>', '<user_action>', '<goal_context>', '<codex_internal_context', '<turn_aborted>')
LIMIT = re.compile(r'usage limit|session limit|hit your limit|rate.?limit|resets \d', re.I)
PR_URL = re.compile(r'https://github\.com/[\w.-]+/[\w.-]+/pull/\d+')
ACTIONS = {'commit': re.compile(r'\bgit commit\b'), 'push': re.compile(r'\bgit push\b'),
           'pr_create': re.compile(r'\bgh pr create\b'), 'pr_merge': re.compile(r'\bgh pr merge\b')}


def lines(path):
    with open(path, errors='ignore') as f:
        yield from f


def texts(content):
    if isinstance(content, str):
        return [content]
    return [b.get('text', '') for b in content or [] if isinstance(b, dict) and b.get('type') in ('text', 'input_text', 'output_text')]


def clip(t, n):
    t = re.sub(r'```.*?```', lambda m: f'[code block, {m.group(0).count(chr(10))} lines]', t.strip(), flags=re.S)
    t = re.sub(r'\s*\n\s*', ' ⏎ ', t)
    return t if len(t) <= n else t[:n] + ' …'


def new(src, path, sid):
    return dict(src=src, path=path, id=sid, cwd=None, title=None, first=None, last=None, user=[], said='',
                ended='', actions={}, prs=set())


def seen(r, ts):
    if ts:
        r['first'] = r['first'] or ts
        r['last'] = ts


def act(r, cmd, out=''):
    for k, rx in ACTIONS.items():
        if rx.search(cmd):
            r['actions'][k] = r['actions'].get(k, 0) + 1
    r['prs'].update(PR_URL.findall(cmd + ' ' + out))


def user_turn(r, x):
    x = SR.sub('', x).strip()
    if not x:
        return
    if x.startswith(('[Request interrupted', '<turn_aborted>')):
        r['ended'] = 'interrupted by the user'
        return
    if x.startswith(NOISE):
        return
    r['user'].append(x)
    r['ended'] = 'waiting on the agent (no reply after the last user turn)'


def agent_said(r, text):
    if text.strip():
        r['said'] = text
        r['ended'] = 'hit a usage limit' if LIMIT.search(text[:400]) else 'agent replied'


def claude(path):
    r = new('claude', path, os.path.basename(path)[:-6])
    for line in lines(path):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        seen(r, e.get('timestamp'))
        r['cwd'] = r['cwd'] or e.get('cwd')
        t = e.get('type')
        if t in ('custom-title', 'summary'):
            r['title'] = e.get('customTitle') or e.get('summary') or r['title']
        m = e.get('message') if isinstance(e.get('message'), dict) else {}
        if t == 'assistant':
            for b in m.get('content') or []:
                if not isinstance(b, dict):
                    continue
                if b.get('type') == 'text':
                    agent_said(r, b.get('text', ''))
                elif b.get('type') == 'tool_use' and b.get('name') == 'Bash':
                    act(r, (b.get('input') or {}).get('command', ''))
        elif t == 'user' and not e.get('isMeta'):
            content = m.get('content')
            if isinstance(content, list):
                for b in content:
                    if isinstance(b, dict) and b.get('type') == 'tool_result':
                        r['prs'].update(PR_URL.findall(json.dumps(b.get('content'))))
            if (e.get('origin') or {}).get('kind') in ('task-notification', 'auto-continuation'):
                continue
            for x in texts(content):
                user_turn(r, x)
    return r


def codex_meta(path):
    with open(path, errors='ignore') as f:
        try:
            e = json.loads(f.readline())
        except ValueError:
            return None
    return e.get('payload') if e.get('type') == 'session_meta' else None


def codex(path, meta, names):
    r = new('codex', path, meta.get('id'))
    r['cwd'], r['title'] = meta.get('cwd'), names.get(meta.get('id'))
    for line in lines(path):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        seen(r, e.get('timestamp'))
        t, p = e.get('type'), e.get('payload') or {}
        if t == 'event_msg' and p.get('type') == 'turn_aborted':
            r['ended'] = 'interrupted by the user'
        elif t == 'event_msg' and p.get('type') == 'error':
            r['ended'] = 'hit a usage limit' if LIMIT.search(str(p.get('message'))) else 'stopped on an error'
        elif t == 'response_item':
            pt = p.get('type')
            if pt == 'message' and p.get('role') == 'assistant':
                agent_said(r, ' '.join(texts(p.get('content'))))
            elif pt == 'message' and p.get('role') == 'user':
                for x in texts(p.get('content')):
                    user_turn(r, x)
            elif pt in ('function_call', 'custom_tool_call'):
                raw = p.get('arguments') or p.get('input') or ''
                act(r, raw if isinstance(raw, str) else json.dumps(raw))
            elif pt in ('function_call_output', 'custom_tool_call_output'):
                r['prs'].update(PR_URL.findall(str(p.get('output'))[:20000]))
    return r


def roots(d):
    """The directory plus every worktree of its git repository."""
    try:
        out = subprocess.run(['git', '-C', d, 'worktree', 'list', '--porcelain'], capture_output=True, text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        out = ''
    paths = {l[9:] for l in out.splitlines() if l.startswith('worktree ')}
    return {os.path.realpath(p) for p in paths | {d}}


def claude_dir(path):
    # ponytail: Claude Code's own path-to-folder mangling; very long paths may be shortened by newer versions.
    return re.sub(r'[^A-Za-z0-9-]', '-', path)


def codex_homes():
    seen_homes, out = set(), []
    for h in (os.environ.get('CODEX_HOME'), f'{HOME}/.codex_p', f'{HOME}/.codex'):
        if h and os.path.isdir(h) and os.path.realpath(h) not in seen_homes:
            seen_homes.add(os.path.realpath(h))
            out.append(h)
    return out


def find(d, limit, exclude, claude_root=f'{HOME}/.claude/projects', homes=None):
    dirs = roots(os.path.realpath(d))
    found = []
    for p in dirs:
        for f in glob.glob(f'{claude_root}/{claude_dir(p)}/*.jsonl'):
            found.append((os.path.getmtime(f), 'claude', f, None))
    for h in codex_homes() if homes is None else homes:
        files = glob.glob(f'{h}/sessions/**/rollout-*.jsonl', recursive=True) + glob.glob(f'{h}/archived_sessions/*.jsonl')
        for f in sorted(files, key=os.path.getmtime, reverse=True)[:3000]:
            meta = codex_meta(f)
            src = (meta or {}).get('source')
            if meta and os.path.realpath(meta.get('cwd') or '/nonexistent') in dirs and not isinstance(src, dict):
                found.append((os.path.getmtime(f), 'codex', f, meta))
    names = {}
    for h in codex_homes() if homes is None else homes:
        for line in lines(f'{h}/session_index.jsonl') if os.path.exists(f'{h}/session_index.jsonl') else []:
            try:
                x = json.loads(line)
                names[x['id']] = x.get('thread_name')
            except (ValueError, KeyError):
                pass
    out = {'claude': [], 'codex': []}
    for _, src, f, meta in sorted(found, reverse=True):
        if len(out[src]) >= limit:
            continue
        r = claude(f) if src == 'claude' else codex(f, meta, names)
        if r['id'] in exclude or not r['user'] or all(PING.match(u) for u in r['user']):
            continue
        out[src].append(r)
    return dirs, sorted(out['claude'] + out['codex'], key=lambda r: r['last'] or '', reverse=True)


def ago(ts):
    if not ts:
        return '?'
    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
    mins = int((datetime.now(timezone.utc) - dt).total_seconds() // 60)
    rel = f'{mins} min ago' if mins < 120 else f'{mins // 60} h ago' if mins < 2880 else f'{mins // 1440} days ago'
    return f"{dt.astimezone().strftime('%Y-%m-%d %H:%M')} ({rel})"


def render(r, turns):
    acts = ', '.join(f'{k} ×{v}' for k, v in r['actions'].items()) or 'none'
    lines = [f"## {'Claude Code' if r['src'] == 'claude' else 'Codex'} session {r['id']}",
             f"- last activity: {ago(r['last'])}; started {ago(r['first'])}",
             f"- cwd: {(r['cwd'] or '?').replace(HOME, '~')}",
             f"- transcript: {r['path'].replace(HOME, '~')}"]
    if r['title']:
        lines.append(f"- title: {r['title']}")
    lines += [f"- ended: {r['ended'] or 'unknown'}", f"- delivery commands: {acts}"]
    if r['prs']:
        lines.append(f"- PRs mentioned: {', '.join(sorted(r['prs']))}")
    lines.append(f"- user turns: {len(r['user'])}; last {min(turns, len(r['user']))}:")
    lines += [f"  {i}. {clip(u, 400)}" for i, u in enumerate(r['user'][-turns:], len(r['user']) - min(turns, len(r['user'])) + 1)]
    lines.append(f"- agent's last message: {clip(r['said'], 900) or '(none)'}")
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--dir', default=os.getcwd())
    ap.add_argument('--limit', type=int, default=3, help='sessions per tool (default 3)')
    ap.add_argument('--turns', type=int, default=4, help='last user turns shown per session (default 4)')
    ap.add_argument('--exclude', nargs='*', default=[], help='session ids to skip')
    a = ap.parse_args()
    exclude = set(a.exclude) | {os.environ.get(k) for k in ('CLAUDE_CODE_SESSION_ID', 'CODEX_THREAD_ID')} - {None}
    dirs, rs = find(a.dir, a.limit, exclude)
    print('# Sessions for ' + ', '.join(sorted(p.replace(HOME, '~') for p in dirs)))
    print('\n\n'.join(render(r, a.turns) for r in rs) if rs else '\nNo sessions found for this directory.')


if __name__ == '__main__':
    main()
