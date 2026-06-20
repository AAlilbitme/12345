#!/usr/bin/env python3
"""
run.py  --  run tamarin-prover on the project's .spthy files, print a
            per-lemma verified / failed / incomplete table, AND the run
            time per file.

Each file is proved in a single `tamarin-prover --prove` invocation (so
[reuse] lemmas are derived once and shared). One OOM-killed file does not
stop the others.

IMPORTANT -- per-file search strategy:
  --stop-on-trace=seqdfs RESCUES multihop's heavy exists-traces (without it
  Multihop_Payment_Possible OOM-kills), but it HANGS cltv_blocks.spthy's nat
  arithmetic and gaps.spthy's linear-token lemmas.
  So seqdfs is applied to every file EXCEPT the ones in NO_SEQDFS below.

Usage:
    python3 run.py                  # all files in the FILES list below
    python3 run.py multihop.spthy   # only the files you name
    python3 run.py --timeout 1200   # per-file wall-clock cap (default 900s)

Exit code is 0 only if every lemma in every file verified.
"""

import argparse
import os
import re
import subprocess
import sys
import time

# --- the project's theory files, in reading order -------------------------
FILES = [
    "cltv_blocks.spthy",
    "PaymentChannels.spthy",
    "value_conservation.spthy",
    "gaps.spthy",
    "t2b_attack.spthy",
    "multihop.spthy",
]

# Files that must NOT use --stop-on-trace=seqdfs.
# cltv_blocks: nat-arithmetic lemmas hang under seqdfs.
# gaps: linear channel token makes heavy lemmas (No_HTLC_After_Close, 218 steps)
#       pathological under seqdfs.
# value_conservation: simple model, default strategy is faster.
NO_SEQDFS = {"cltv_blocks.spthy", "gaps.spthy", "value_conservation.spthy"}

# tamarin prints e.g.  "  Multihop_Payment_Possible (exists-trace): verified (67 steps)"
LINE_RE = re.compile(
    r"^\s*(?P<name>\w+)\s*\((?P<kind>[^)]+)\):\s*(?P<status>verified|falsified|analysis incomplete)"
    r"(?:\s*\((?P<steps>\d+)\s*steps?\))?"
)

USE_COLOR = sys.stdout.isatty()
def c(code, s):
    return f"\033[{code}m{s}\033[0m" if USE_COLOR else s
GREEN  = lambda s: c("32", s)
RED    = lambda s: c("31", s)
YELLOW = lambda s: c("33", s)
BOLD   = lambda s: c("1",  s)


def fmt_time(seconds):
    if seconds < 60:
        return f"{seconds:.1f}s"
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s:02d}s"


def build_cmd(path):
    cmd = [
        "tamarin-prover", path,
        "--prove",
        "--heuristic=c",
        "--derivcheck-timeout=0",
    ]
    if path not in NO_SEQDFS:
        cmd.append("--stop-on-trace=seqdfs")
    return cmd


def run_file(path, timeout):
    cmd = build_cmd(path)
    print("   $ " + " ".join(cmd), flush=True)
    env = dict(os.environ, LANG="C.utf8", LC_ALL="C.utf8")

    start = time.monotonic()
    try:
        proc = subprocess.run(
            cmd, env=env, capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        return [], f"wall-clock timeout after {timeout}s", time.monotonic() - start
    except FileNotFoundError:
        return [], "tamarin-prover not found on PATH", time.monotonic() - start
    elapsed = time.monotonic() - start

    out = proc.stdout + proc.stderr
    lemmas = []
    for line in out.splitlines():
        m = LINE_RE.match(line)
        if m:
            lemmas.append({
                "name":   m.group("name"),
                "kind":   m.group("kind"),
                "status": "incomplete" if m.group("status") == "analysis incomplete"
                          else m.group("status"),
                "steps":  m.group("steps") or "",
            })

    if not lemmas:
        tail = out.strip().splitlines()[-1] if out.strip() else "(no output)"
        reason = "process killed (likely OOM)" if proc.returncode and proc.returncode < 0 \
                 else f"no result lines; last output: {tail[:80]}"
        return [], reason, elapsed

    return lemmas, None, elapsed


def print_table(path, lemmas, error, elapsed):
    print(BOLD(f"\n=== {path} ===") + f"  [{fmt_time(elapsed)}]")
    if error:
        print(RED(f"  !! {error}"))
        return (0, 0)

    name_w = max((len(l["name"]) for l in lemmas), default=4)
    n_ok = n_bad = 0
    for l in lemmas:
        if l["status"] == "verified":
            tag, n_ok = GREEN("verified  "), n_ok + 1
        elif l["status"] == "falsified":
            tag, n_bad = RED("FALSIFIED "), n_bad + 1
        else:
            tag, n_bad = YELLOW("incomplete"), n_bad + 1
        steps = f"({l['steps']} steps)" if l["steps"] else ""
        print(f"  {l['name']:<{name_w}}  {tag}  {steps}")
    print(f"  -> {GREEN(str(n_ok)+' ok')}" + (f", {RED(str(n_bad)+' not ok')}" if n_bad else "")
          + f"  in {fmt_time(elapsed)}")
    return (n_ok, n_bad)


def main():
    ap = argparse.ArgumentParser(description="Prove the project's .spthy files.")
    ap.add_argument("files", nargs="*", help="specific .spthy files (default: built-in list)")
    ap.add_argument("--timeout", type=int, default=900,
                    help="per-file wall-clock cap in seconds (default 900)")
    args = ap.parse_args()

    files = args.files or FILES

    print(BOLD(f"Will process {len(files)} file(s): ") + ", ".join(files), flush=True)
    missing = [f for f in files if not os.path.exists(f)]
    if missing:
        print(YELLOW(f"Warning: listed but not found on disk: {', '.join(missing)}"), flush=True)

    total_ok = total_bad = 0
    total_time = 0.0
    failed_files = []
    timings = []

    for path in files:
        if not os.path.exists(path):
            print(RED(f"\n=== {path} ===\n  !! file not found"))
            failed_files.append(path)
            continue
        print(f"\n… proving {path} …", flush=True)
        lemmas, error, elapsed = run_file(path, args.timeout)
        n_ok, n_bad = print_table(path, lemmas, error, elapsed)
        total_ok += n_ok
        total_bad += n_bad
        total_time += elapsed
        timings.append((path, elapsed))
        if error or n_bad:
            failed_files.append(path)

    print(BOLD("\n--- run times ---"))
    for path, elapsed in timings:
        print(f"  {path:<32} {fmt_time(elapsed)}")
    print(f"  {'TOTAL':<32} {fmt_time(total_time)}")

    print(BOLD("\n--- summary ---"))
    print(f"  lemmas verified : {GREEN(str(total_ok))}")
    print(f"  lemmas not OK   : {(RED if total_bad else str)(str(total_bad))}")
    if failed_files:
        print(RED(f"  files with problems: {', '.join(failed_files)}"))
        print(YELLOW("  (a file with no results was likely OOM-killed; "
                     "re-run it per-lemma via the Makefile to isolate survivors)"))
        return 1
    print(GREEN("  all files fully verified."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
