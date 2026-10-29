#!/usr/bin/env python3
"""Render kept sessions as digest chunks of about CHUNK_CHARS each, one file per delegate.

Usage: python3 -I digest.py OUT_DIR DIGEST_DIR [--chunk-chars 150000]
Chunks run in time order. Sessions whose rendered text matches SEC go only into s<NN>-gpt.md;
the rest alternate c<NN>-claude.md, c<NN>-gpt.md. Also writes OUT_DIR/session_index.json (S-id to
transcript path) and DIGEST_DIR/status.json (every chunk pending). Refuses to run when DIGEST_DIR or its sibling
findings/ already holds files: new S-ids would let old findings pass. Use a fresh audit dir.
"""
import argparse, json, os, re, sys

HOME = os.path.expanduser('~')
SEC = re.compile(r'\b(vuln\w*|CVE|exploit\w*|pentest\w*|penetration|security|seguridad|vulnerab\w*|XSS|CSRF|SSRF|injection|inyecci\w+|'
                 r'malware|payload\w*|reverse shell|privilege escalation|escalada|bypass|attack\w*|ataque\w*|adversarial\w*|phishing|'
                 r'0day|zero-day|RCE|backdoor|keylogger|brute.?force|ciberseguridad|hack\w*|crack\w*|jailbreak|AUP|safeguard\w*|cyber)\b', re.I)


def jsonl(path):
    with open(path) as f:
        return [json.loads(l) for l in f]


def clip(t, n):
    t = re.sub(r'```.*?```', lambda m: f'[code block {m.group(0).count(chr(10))} lines]', t, flags=re.S)
    t = re.sub(r'\n{3,}', '\n\n', t).replace(HOME, '~')
    t = re.sub(r'^#', r'\#', t, flags=re.M)  # a quoted '### S<n>' line would pass as a session heading
    return t if len(t) <= n else t[:n] + f' …[+{len(t) - n} chars]'


def render(i, r, turns):
    c = r['cmd_tags']
    skills = sorted(set(r['skills_tool'] + r['skills_injected'] + r['skills_read']))
    meta = [r['source'], (r['first_ts'] or '')[:16].replace('T', ' '), (r['project'] or '?').replace(HOME, '~'), r['entrypoint'] or '?',
            'models=' + ','.join(list(r['models'])[:3]), f"turns={r['n_user']}", f"machine={r['n_machine']}", f"interrupts={r['interrupts']}"]
    if r['title']:
        meta.append(f"title={r['title']!r}")
    if skills:
        meta.append('skills=' + ','.join(skills))
    if r['slash']:
        meta.append('slash=' + ','.join(r['slash'][:8]))
    if r['subagents']:
        meta.append(f"subagents={len(r['subagents'])}:" + ','.join(sorted(set(r['subagents']))[:5]))
    if c:
        meta.append('cmds=' + ','.join(f'{k}:{v}' for k, v in sorted(c.items())))
    out, n = [f'### S{i} | ' + ' | '.join(meta)], 0
    for u in turns[:40]:
        if u['machine']:
            out.append(f"  M[{u['machine']}]: {clip(u['text'], 120)}")
            continue
        n += 1
        if n > 1 and u['prev_assistant'].strip():
            out.append(f"  A> {clip(u['prev_assistant'].strip(), 200)}".replace('\n', ' '))
        out.append(f"U{n}: {clip(u['text'], 700)}" + (f" [+{u['images']} img]" if u['images'] else ''))
    if len(turns) > 40:
        out.append(f'…[{len(turns) - 40} more turns omitted]')
    return '\n'.join(out) + '\n'


def chunk(items, limit):
    """Greedy time-ordered chunks of about `limit` chars; a short last chunk joins the one before."""
    chunks, acc = [], 0
    for t in items:
        if not chunks or acc + len(t[0]) > limit:
            chunks.append([])
            acc = 0
        chunks[-1].append(t)
        acc += len(t[0])
    if len(chunks) > 1 and sum(len(t[0]) for t in chunks[-1]) < limit / 3:
        tail = chunks.pop()
        chunks[-1] += tail
    return chunks


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('out_dir')
    ap.add_argument('digest_dir')
    ap.add_argument('--chunk-chars', type=int, default=150_000)
    a = ap.parse_args(argv)
    for d in (a.digest_dir, os.path.join(os.path.dirname(os.path.abspath(a.digest_dir)), 'findings')):
        if os.path.isdir(d) and os.listdir(d):
            sys.exit(f'{d} is not empty: its findings would cite the old S-ids. Use a fresh audit dir.')
    os.umask(0o077)  # digests hold raw conversations: owner-only files and dirs
    rs = jsonl(f'{a.out_dir}/sessions.jsonl')
    turns = {d['path']: d['turns'] for d in jsonl(f'{a.out_dir}/turns.jsonl')}
    rows = sorted((r for r in rs if r['kind'] in ('interactive', 'headless')), key=lambda r: r['first_ts'] or '')
    index, items = {}, []
    for i, r in enumerate(rows, 1):
        index[f'S{i}'] = r['path']
        text = render(i, r, turns[r['path']])
        items.append((text, bool(SEC.search(text)), r['first_ts'] or ''))
    with open(f'{a.out_dir}/session_index.json', 'w') as f:
        json.dump(index, f)
    os.makedirs(a.digest_dir, exist_ok=True)
    os.chmod(a.digest_dir, 0o700)
    files = {}
    for k, ch in enumerate(chunk([t for t in items if t[1]], a.chunk_chars), 1):
        files[f's{k:02d}-gpt'] = ch
    for k, ch in enumerate(chunk([t for t in items if not t[1]], a.chunk_chars), 1):
        files[f'c{k:02d}-{"claude" if k % 2 else "gpt"}'] = ch
    for name, ch in files.items():
        span = f'{ch[0][2][:10]} to {ch[-1][2][:10]}'
        with open(f'{a.digest_dir}/{name}.md', 'w') as f:
            f.write(f'# Session digest {name} ({span}), {len(ch)} sessions\n\n' + '\n'.join(t[0] for t in ch))
        print(name, span, len(ch), 'sessions', sum(len(t[0]) for t in ch), 'chars')
    with open(f'{a.digest_dir}/status.json', 'w') as f:
        json.dump(dict.fromkeys(files, 'pending'), f, indent=1)


if __name__ == '__main__':
    main()
