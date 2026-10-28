#!/usr/bin/env python3
"""Extract Claude Code and Codex history: one record per session plus its ordered user turns.

Usage: python3 -I extract.py OUT_DIR [--since YYYY-MM-DD] [--until YYYY-MM-DD]
           [--health-check PREFIX ...] [--self-prompt PREFIX ...]
Reads $HOME/.claude/projects and the Codex homes ($CODEX_HOME, ~/.codex_p, ~/.codex).
Writes OUT_DIR/sessions.jsonl (every session, with a kind) and OUT_DIR/turns.jsonl
(interactive and headless sessions: turns marked human or machine).
Kinds: interactive, headless, or one of the excluded subagent, healthcheck, self, guardian,
greeting, machine, empty, fork (merged into the session it resumed).
Dates are UTC and inclusive.
"""
import argparse, collections, glob, json, os, re

HEALTH = ('Reply only with Hi', 'Respondé únicamente DISPONIBLE')
SELF = ('# Session audit brief', '/session-audit', '$session-audit')
GUARDIAN = ('The following is the Codex agent', '>>> APPROVAL REQUEST', 'Assess the exact planned action')
SR = re.compile(r'<system-reminder>.*?</system-reminder>', re.S)
GREETING = re.compile(r'^(?:hi|hello|hey|hola|yo|buen\w*|good)(?:\s+\w+){0,2}\s*[!.?¡¿,]*$|^(?:test(?:ing)?|ping)\s*[!.?]*$', re.I)
# Injected context, not a turn: dropped.
CONTEXT = ('<local-command-stdout>', '<local-command-stderr>', 'Caveat:', '<bash-stdout>', '<bash-stderr>',
           '<environment_context>', '# AGENTS.md instructions', '<external_codex_apps', '<recommended_plugins>',
           '<in-app-browser-context', '</image>', '<image name=', '<permissions', '<user_instructions>',
           '<INSTRUCTIONS>', '<collaboration_mode>', '<apps_instructions>', '<skills_instructions>')
# Events the machine wrote into the user channel: kept, marked with a label.
HARNESS = ('<user_action>', '<goal_context>', '<codex_internal_context', '<user_shell_command>', '<command-')
MACHINE = (
    ('agent', re.compile(r'^(?:<(?:task-notification|subagent_notification|teammate-message|agent-message)\b|\[(?:message|reply) from (?:agent|subagent|teammate|thread)\b)', re.I)),
    ('ci-bot', re.compile(r'^[<\[{][^\n]{0,300}?(?:\[bot\]|github-actions|coderabbit|chatgpt-codex-connector|check_run|check_suite|workflow_run|webhook|pull_request_review)', re.I)),
    ('harness', re.compile(r'^<([\w-]+)[^>]*>.*</\1>$', re.S)),
)
MACHINE_ORIGINS = ('task-notification', 'auto-continuation')
SKILL_READ = re.compile(r'/skills/([\w.:-]+)/SKILL\.md')
CMD_TAGS = {
    'pr_create': re.compile(r'\bgh pr create\b'), 'pr_view': re.compile(r'\bgh (pr|issue|api|run)\b'),
    'commit': re.compile(r'\bgit commit\b'), 'push': re.compile(r'\bgit push\b'),
    'worktree': re.compile(r'\bgit worktree\b'),
    'test': re.compile(r'\b(vitest|pytest|jest|bun test|pnpm (run )?test|npm (run )?test|cargo test|go test|playwright test)\b'),
    'typecheck': re.compile(r'\b(tsc|typecheck|biome|eslint|oxlint|ruff|mypy|pyright)\b'),
    'deploy': re.compile(r'\bdeploy\b'),
    'codex_exec': re.compile(r'\bcodex\b[^|;&]*\bexec\b'), 'claude_p': re.compile(r'\bclaude\b[^|;&]*\s-p\b'),
    'sudo': re.compile(r'\bsudo\b'),
}


def lines(path):
    with open(path, errors='ignore') as f:
        yield from f


def events(path):
    for line in lines(path):
        try:
            yield json.loads(line)
        except ValueError:
            pass


def texts(content):
    if isinstance(content, str):
        return [content]
    return [b.get('text', '') for b in content or [] if isinstance(b, dict) and b.get('type') in ('text', 'input_text')]


def n_images(content):
    return sum(1 for b in content or [] if isinstance(b, dict) and b.get('type') in ('image', 'input_image')) if isinstance(content, list) else 0


def lang(turns):
    s = ' '.join(turns).lower()
    es = len(re.findall(r'\b(que|para|con|está|quiero|necesito|hacé|podés|también|porque|pero|esto|cómo|qué)\b', s))
    en = len(re.findall(r'\b(the|and|with|this|that|want|should|please|make|what|how|can)\b', s))
    return 'es' if es > en * 1.2 else 'en' if en > es * 1.2 else ('mixed' if es + en else '?')


def new_rec(**kw):
    r = dict(user_turns=[], tools=collections.Counter(), mcp=collections.Counter(), cmd_tags=collections.Counter(),
             skills_tool=[], skills_injected=[], skills_read=[], skills_mentioned=[], slash=[], subagents=[],
             models=collections.Counter(), interrupts=0, rejections=0, images=0, compactions=0,
             title=None, first_ts=None, last_ts=None, last_assistant='')
    r.update(kw)
    return r


def seen(r, ts):
    if ts:
        r['first_ts'] = r['first_ts'] or ts
        r['last_ts'] = ts


def tag_cmd(r, cmd):
    for k, rx in CMD_TAGS.items():
        if rx.search(cmd):
            r['cmd_tags'][k] += 1
    r['skills_read'] += SKILL_READ.findall(cmd)


def machine_label(x):
    if x.startswith(HARNESS):
        return 'harness'
    return next((label for label, rx in MACHINE if rx.search(x)), None)


def add_turn(r, x, ts, imgs, label=None):
    r['user_turns'].append({'ts': ts, 'text': x[:2000], 'prev_assistant': r['last_assistant'][-300:], 'images': imgs, 'machine': label})
    r['last_assistant'] = ''


def user_text(r, x, ts, imgs, origin=None):
    """Route one text block of a user message: drop, count, or record as a human or machine turn."""
    x = SR.sub('', x).strip()
    if not x or x.startswith(CONTEXT):
        return
    if x.startswith(('[Request interrupted', '<turn_aborted>')):
        r['interrupts'] += 1
    elif x.startswith('This session is being continued'):
        r['compactions'] += 1
    elif x.startswith('Base directory for this skill:'):
        r['skills_injected'].append(x.split('\n')[0].rsplit('/', 1)[-1])
    elif x.startswith('<skill>'):
        m = re.search(r'<name>([^<]+)</name>', x)
        r['skills_injected'].append(m.group(1) if m else '?')
    elif x.startswith('<send_user_message_question_reply>'):
        for a in re.findall(r'"answer":"((?:[^"\\]|\\.)*)"', x):
            add_turn(r, f'[answer to agent question] {a}', ts, imgs)
    elif (cm := re.search(r'<command-name>/?([^<]+)</command-name>', x)):
        r['slash'].append(cm.group(1).strip())
        args = re.search(r'<command-args>(.*?)</command-args>', x, re.S)
        if args and args.group(1).strip():
            add_turn(r, f'/{cm.group(1).strip()} {args.group(1).strip()}', ts, imgs)
    else:
        label = origin or machine_label(x)
        if not label:
            r['skills_mentioned'] += re.findall(r'(?<![\w/])[/$]([a-z][\w-]+:?[\w-]*)\b', x[:200]) if x[:1] in '/$' else []
        add_turn(r, x, ts, imgs, label)


def claude_session(path):
    r = new_rec(source='claude', path=path, id=os.path.basename(path)[:-6], project=None, entrypoint=None)
    for e in events(path):
        t, ts = e.get('type'), e.get('timestamp')
        seen(r, ts)
        r['entrypoint'] = r['entrypoint'] or e.get('entrypoint')
        r['project'] = r['project'] or e.get('cwd')
        if t == 'custom-title':
            r['title'] = e.get('customTitle')
        m = e.get('message') if isinstance(e.get('message'), dict) else {}
        if t == 'assistant':
            if m.get('model') and m['model'] != '<synthetic>':
                r['models'][m['model']] += 1
            for b in m.get('content') or []:
                if not isinstance(b, dict):
                    continue
                if b.get('type') == 'text':
                    r['last_assistant'] += b.get('text', '')
                elif b.get('type') == 'tool_use':
                    name, inp = b.get('name', ''), b.get('input') or {}
                    r['tools'][name] += 1
                    if name.startswith('mcp__'):
                        r['mcp'][name.split('__')[1]] += 1
                    if name == 'Skill':
                        r['skills_tool'].append(inp.get('skill') or inp.get('command'))
                    if name in ('Agent', 'Task'):
                        r['subagents'].append(f"{inp.get('subagent_type', '?')}/{inp.get('model', '-')}")
                    if name.endswith('delegate_task'):
                        tgt = inp.get('target') or {}
                        r['subagents'].append(f"t3:{tgt.get('provider', '?')}/{tgt.get('model', '?')}")
                    if name == 'Bash':
                        tag_cmd(r, inp.get('command', ''))
                    if name == 'Read':
                        r['skills_read'] += SKILL_READ.findall(inp.get('file_path', ''))
        elif t == 'user':
            content = m.get('content')
            for b in content if isinstance(content, list) else []:
                if isinstance(b, dict) and b.get('type') == 'tool_result':
                    c = json.dumps(b.get('content'))[:400]
                    r['rejections'] += "doesn't want to proceed" in c or 'tool use was rejected' in c
            if e.get('isMeta'):
                for x in texts(content):
                    if x.startswith('Base directory for this skill:'):
                        r['skills_injected'].append(x.split('\n')[0].rsplit('/', 1)[-1])
                continue
            kind = (e.get('origin') or {}).get('kind')
            imgs = n_images(content)
            r['images'] += imgs
            for x in texts(content):
                user_text(r, x, ts, imgs, kind if kind in MACHINE_ORIGINS else None)
    return r


def codex_session(path, names):
    r = new_rec(source='codex', path=path, id=os.path.basename(path), project=None, entrypoint=None)
    for e in events(path):
        t, p, ts = e.get('type'), e.get('payload') or {}, e.get('timestamp')
        seen(r, ts)
        if t == 'session_meta':
            r['id'], r['project'] = p.get('id') or r['id'], p.get('cwd')
            src = p.get('source')
            r['entrypoint'] = f"{p.get('originator')}|{'subagent' if isinstance(src, dict) else src}"
            r['title'] = names.get(p.get('id'))
        elif t == 'turn_context':
            r['models'][f"{p.get('model')}@{p.get('effort') or (p.get('collaboration_mode') or {}).get('settings', {}).get('reasoning_effort')}"] += 1
        elif t == 'event_msg' and p.get('type') == 'turn_aborted':
            r['interrupts'] += 1
        elif t == 'response_item':
            pt = p.get('type')
            if pt == 'message' and p.get('role') == 'assistant':
                r['last_assistant'] += ' '.join(texts(p.get('content')))
            elif pt in ('function_call', 'custom_tool_call'):
                name = p.get('name', '')
                r['tools'][name] += 1
                raw = p.get('arguments') or p.get('input') or ''
                raw = raw if isinstance(raw, str) else json.dumps(raw)
                if name.startswith('mcp__'):
                    r['mcp'][name.split('__')[1]] += 1
                tag_cmd(r, raw)
                if 'spawn' in name:
                    try:
                        a = json.loads(raw)
                        r['subagents'].append(f"{a.get('agent_type') or a.get('role') or '?'}/{a.get('model', '-')}")
                    except ValueError:
                        r['subagents'].append('?')
                if name.endswith('delegate_task'):
                    r['subagents'].append('t3:delegate')
            elif pt == 'message' and p.get('role') == 'user':
                imgs = n_images(p.get('content'))
                r['images'] += imgs
                for x in texts(p.get('content')):
                    user_text(r, x, ts, imgs)
    return r


def codex_homes(home):
    out = []
    for h in (os.environ.get('CODEX_HOME'), f'{home}/.codex_p', f'{home}/.codex'):
        if h and os.path.isdir(h) and os.path.realpath(h) not in map(os.path.realpath, out):
            out.append(h)
    return out


def session_paths(home):
    paths = [('claude', p) for p in glob.glob(f'{home}/.claude/projects/**/*.jsonl', recursive=True)]
    for h in codex_homes(home):
        paths += [('codex', p) for p in glob.glob(f'{h}/sessions/**/*.jsonl', recursive=True) + glob.glob(f'{h}/archived_sessions/*.jsonl')]
    return paths


def is_headless(r):
    ep = r['entrypoint'] or ''
    return ep == 'sdk-cli' or ep.startswith('codex_exec')


def classify(r, health, self_prompts, out_dir):
    turns = [u['text'] for u in r['user_turns']]
    human = [u['text'] for u in r['user_turns'] if not u['machine']]
    first = turns[0].lstrip() if turns else ''
    if '/subagents/' in r['path'] or '|subagent' in (r['entrypoint'] or ''):
        return 'subagent'
    if not turns:
        return 'empty'
    if all(t.lstrip().startswith(health) for t in turns):
        return 'healthcheck'
    if first.startswith(self_prompts) or any(d in first for d in out_dir):
        return 'self'
    if first.startswith(GUARDIAN):
        return 'guardian'
    if is_headless(r):
        return 'headless'
    if not human:
        return 'machine'
    if all(len(t) <= 30 and GREETING.match(t.strip()) for t in human):
        return 'greeting'
    return 'interactive'


def merge_forks(rs):
    """A resumed or forked session replays its parent's turns, so one conversation shows up several times.
    The earliest session (ties: the one that ends first) absorbs each later one's unique tail; the later one becomes kind 'fork'."""
    # ponytail: needs two shared leading turns, so a fork that shares one turn stays separate.
    by_first, full, root = {}, {}, {}
    for r in sorted((r for r in rs if r['kind'] in ('interactive', 'headless')), key=lambda r: (r['first_ts'] or '', r['last_ts'] or '')):
        texts_ = [u['text'] for u in r['user_turns']]
        full[id(r)] = texts_
        best, n = None, 0
        for p in by_first.get(texts_[0], []):
            k = next((i for i, (a, b) in enumerate(zip(full[id(p)], texts_)) if a != b), min(len(full[id(p)]), len(texts_)))
            if k > n:
                best, n = p, k
        by_first.setdefault(texts_[0], []).append(r)
        if n >= 2:
            top = root.get(id(best), best)
            root[id(r)] = top
            top['user_turns'] += r['user_turns'][n:]
            r['kind'], r['merged_into'] = 'fork', top['id']


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('out_dir')
    ap.add_argument('--since', default='')
    ap.add_argument('--until', default='')
    ap.add_argument('--health-check', nargs='+', default=list(HEALTH), help='prompt prefixes of health-check pings (replaces the defaults)')
    ap.add_argument('--self-prompt', nargs='+', default=[], help='extra first-prompt prefixes of the audit\'s own threads')
    a = ap.parse_args(argv)
    home = os.path.expanduser('~')
    out = os.path.abspath(a.out_dir)
    os.makedirs(out, exist_ok=True)
    names = {}
    for h in codex_homes(home):
        if os.path.exists(f'{h}/session_index.jsonl'):
            names.update({d['id']: d.get('thread_name') for d in events(f'{h}/session_index.jsonl') if 'id' in d})
    rs = []
    for src, p in session_paths(home):
        r = claude_session(p) if src == 'claude' else codex_session(p, names)
        day = (r['first_ts'] or '')[:10]
        if (a.since or a.until) and not day or (a.since and day < a.since) or (a.until and day > a.until):
            continue
        if is_headless(r):
            for u in r['user_turns']:
                u['machine'] = u['machine'] or 'agent-prompt'
        r['kind'] = classify(r, tuple(a.health_check), SELF + tuple(a.self_prompt), {out, out.replace(home, '~')})
        rs.append(r)
    merge_forks(rs)
    with open(f'{out}/sessions.jsonl', 'w') as so, open(f'{out}/turns.jsonl', 'w') as to:
        for r in rs:
            turns = r.pop('user_turns')
            r.pop('last_assistant')
            human = [u['text'] for u in turns if not u['machine']]
            r.update(lang=lang(human), n_user=len(human), n_machine=len(turns) - len(human), first_prompt=(human or [''])[0][:500])
            so.write(json.dumps(r) + '\n')
            if r['kind'] in ('interactive', 'headless'):
                to.write(json.dumps({'path': r['path'], 'turns': turns}) + '\n')
    print(json.dumps(collections.Counter(f"{r['source']}:{r['kind']}" for r in rs), indent=1))


if __name__ == '__main__':
    main()
