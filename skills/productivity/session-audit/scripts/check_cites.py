#!/usr/bin/env python3
"""Check findings against their digests and reconcile the chunk status file.

Usage: python3 -I check_cites.py AUDIT_DIR [--report FILE]
AUDIT_DIR holds digests/ (with status.json) and findings/. For each findings/<chunk>.md, lists S-ids that
are absent from digests/<chunk>.md (invented), with line numbers; any findings file marks its chunk done.
With --report, also lists S-ids in FILE that no findings file cites validly. Exit 1 on any problem.
Prints chunks still pending or failed: relaunch only those.
"""
import argparse, glob, json, os, re, sys


def read(path):
    with open(path) as f:
        return f.read()


def cited(text):
    ids = set(re.findall(r'\bS(\d+)\b', text))
    for a, b in re.findall(r'\bS(\d+)[–-]S?(\d+)\b', text):  # ranges like S941–S962: every id in between is cited
        ids |= {str(i) for i in range(int(a), int(b) + 1)}
    return ids


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('audit_dir')
    ap.add_argument('--report')
    a = ap.parse_args(argv)
    d, ok, valid = a.audit_dir, True, set()
    status_path = f'{d}/digests/status.json'
    status = json.loads(read(status_path)) if os.path.exists(status_path) else {}
    for f in sorted(glob.glob(f'{d}/findings/*.md')):
        name = os.path.basename(f)[:-3]
        have = set(re.findall(r'^### S(\d+)', read(f'{d}/digests/{name}.md'), re.M))
        text = read(f)
        ids = cited(text)
        bad = ids - have
        valid |= ids & have
        if text.strip():
            status[name] = 'done'  # a findings file outranks a stale failure notice
        print(f'{name}: {len(ids)} cited, {len(bad)} not in chunk')
        for n, line in enumerate(text.splitlines(), 1):
            for b in sorted(bad & cited(line), key=int):
                print(f'  {name}.md:{n}: S{b}')
        ok &= not bad
    if a.report:
        missing = cited(read(a.report)) - valid
        print(f'report: {len(missing)} S-ids with no findings file behind them', sorted(missing, key=int)[:30])
        ok &= not missing
    if status:
        with open(status_path, 'w') as f:
            json.dump(status, f, indent=1)
        print('relaunch:', ' '.join(k for k, v in status.items() if v != 'done') or 'none')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
