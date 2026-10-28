#!/usr/bin/env python3
"""Deterministic aggregates over OUT_DIR/sessions.jsonl, written to OUT_DIR/stats.json (also printed).

Usage: python3 -I stats.py OUT_DIR
Counts only interactive sessions (headless ones count for entrypoints, models and subagents). Hours and
weekdays are in local time.
"""
import collections, json, os, sys
from datetime import datetime

C = collections.Counter
SRC = ('claude', 'codex')


def ts(s):
    return datetime.fromisoformat(s.replace('Z', '+00:00')).astimezone() if s else None


def proj(p):
    parts = (p or '?').replace(os.path.expanduser('~'), '~').split('/')
    return '/'.join(parts[:4])


def jsonl(path):
    with open(path) as f:
        return [json.loads(l) for l in f]


def median(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else 0


def main(out):
    rs = jsonl(f'{out}/sessions.jsonl')
    H = [r for r in rs if r['kind'] in ('interactive', 'headless')]
    I = [r for r in rs if r['kind'] == 'interactive']

    def by_src(rows, f):
        res = {}
        for src in SRC:
            c = C()
            for r in rows:
                if r['source'] == src:
                    f(r, c)
            res[src] = c.most_common(60)
        return res

    def per_src(f):
        return {src: f([r for r in I if r['source'] == src]) for src in SRC}

    def dur(r):
        a, b = ts(r['first_ts']), ts(r['last_ts'])
        return (b - a).total_seconds() / 60 if a and b else 0

    stats = {
        'kinds': {f'{k[0]}:{k[1]}': v for k, v in C((r['source'], r['kind']) for r in rs).items()},
        'entrypoints': {f'{k[0]}:{k[1]}': v for k, v in C((r['source'], r['entrypoint']) for r in H).most_common()},
        'month': {f'{k[0]}:{k[1]}': v for k, v in sorted(C((r['source'], r['first_ts'][:7]) for r in I if r['first_ts']).items())},
        'hour': sorted(C(ts(r['first_ts']).hour for r in I if r['first_ts']).items()),
        'weekday': sorted(C(ts(r['first_ts']).strftime('%a') for r in I if r['first_ts']).items()),
        'projects': C(proj(r['project']) for r in I).most_common(40),
        'lang': C(r['lang'] for r in I).most_common(),
        'turns_hist': sorted(C(min(r['n_user'], 20) for r in I).items()),
        'turns_median': median(r['n_user'] for r in I),
        'duration_median_min': median(dur(r) for r in I),
        'machine_turns': sum(r['n_machine'] for r in I),
        'forks_merged': sum(1 for r in rs if r['kind'] == 'fork'),
        'tools': by_src(I, lambda r, c: c.update(r['tools'])),
        'mcp': by_src(I, lambda r, c: c.update(r['mcp'])),
        'cmd_tags': by_src(I, lambda r, c: c.update(r['cmd_tags'])),
        'models': by_src(H, lambda r, c: c.update(r['models'])),
        'slash': by_src(I, lambda r, c: c.update(r['slash'])),
        'skills_tool': by_src(I, lambda r, c: c.update(s.split(':')[-1].strip('/ ') for s in r['skills_tool'] if s)),
        'skills_injected': by_src(I, lambda r, c: c.update(s.split(':')[-1].strip('/ ') for s in r['skills_injected'])),
        'skills_read': by_src(I, lambda r, c: c.update(set(r['skills_read']))),
        'skills_mentioned': by_src(I, lambda r, c: c.update(r['skills_mentioned'])),
        'subagents': by_src(H, lambda r, c: c.update(r['subagents'])),
        'sessions_with_any_skill': per_src(lambda rows: sum(1 for r in rows if r['skills_tool'] or r['skills_injected'] or r['skills_read'])),
        'sessions_with_subagents': per_src(lambda rows: sum(1 for r in rows if r['subagents'])),
        'sessions_with_interrupt': per_src(lambda rows: sum(1 for r in rows if r['interrupts'])),
        'interrupts': per_src(lambda rows: sum(r['interrupts'] for r in rows)),
        'images': per_src(lambda rows: sum(r['images'] for r in rows)),
        'rejections': sum(r['rejections'] for r in I),
        'compactions': sum(r['compactions'] for r in I),
        'sessions_with_cmd': {k: sum(1 for r in I if r['cmd_tags'].get(k)) for k in ('pr_create', 'commit', 'push', 'test', 'typecheck', 'worktree', 'codex_exec', 'claude_p')},
    }
    with open(f'{out}/stats.json', 'w') as f:
        json.dump(stats, f, indent=1)
    return stats


if __name__ == '__main__':
    print(json.dumps(main(sys.argv[1]))[:12000])
