#!/usr/bin/env python3
"""
run.py  --  run tamarin-prover on the project's .spthy files, print a
            per-lemma verified / failed / incomplete table, AND the run
            time per file.

Files listed in PER_LEMMA are proved one lemma at a time (sequential
invocations) to avoid OOM on large theories.  All other files are proved
in a single `tamarin-prover --prove` invocation so [reuse] lemmas are
shared.

IMPORTANT -- per-file search strategy:
  --stop-on-trace=seqdfs RESCUES multihop's heavy exists-traces (without it
  Multihop_Payment_Possible OOM-kills), but it HANGS cltv_blocks.spthy's nat
  arithmetic and gaps.spthy's linear-token lemmas.
  So seqdfs is applied to every file EXCEPT the ones in NO_SEQDFS below.

Usage:
    python3 run.py                  # all files in the FILES list below
    python3 run.py multihop.spthy   # only the files you name
    python3 run.py --timeout 1200   # per-lemma wall-clock cap (default 300s)

Exit code is 0 only if every lemma in every file verified.
"""

import argparse
import os
import re
import subprocess
import sys
import time
import threading

# --- the project's theory files, in reading order -------------------------
# PaymentChannels.spthy and value_conservation.spthy were retired: both are
# fully subsumed by multihop.spthy (channel layer + amounts/fees merged in,
# tested end to end -- see multihop.spthy's header). Kept in archive/ as the
# tested precedent for the signing+nat combination.
FILES = [
    "cltv_blocks.spthy",
    "gaps.spthy",
    "witnesses.spthy",
    "t2b_attack.spthy",
    "multihop.spthy",
]

# Files that must NOT use --stop-on-trace=seqdfs.
NO_SEQDFS = {"cltv_blocks.spthy", "gaps.spthy", "witnesses.spthy"}

# Files proved one lemma at a time to avoid OOM.  Each entry maps a file to
# a list of (lemma_name, use_seqdfs, timeout_override_or_None, solo) tuples.
# solo=True means the lemma runs alone (no concurrent tamarin processes) before
# the parallel batch starts.  Use for heavy exists-traces that need full CPU.
PER_LEMMA = {
    "multihop.spthy": [
        ("Multihop_Payment_Possible",          True,  300,  True),   # solo seqdfs exists-trace
        ("Refund_Possible",                    True,  600,  True),   # solo: ~70s with seqdfs
        ("state_update",                       False, None, False),
        ("delayed_funds",                      False, None, False),
        ("instant_funds",                      False, None, False),
        ("settlement_is_traceable",            False, None, False),
        ("Protocol_execution",                 False, None, False),
        ("No_Punishment_Without_Cheating",     False, None, False),
        ("Cooperative_Close_Execution",        False, None, False),
        ("Funds_Locked_Before_Update",         False, None, False),
        ("Update_Requires_Negotiation",        False, None, False),
        ("Ltk_Known_Implies_Compromised",      False, None, False),
        ("Invoice_Released_Once",              False, None, False),
        ("Distinct_Parties_Configuration",     False, None, False),
        ("Preimage_Secret_Until_Released",     False, None, False),
        ("Invoice_Has_Secret_Preimage",        False, None, False),
        ("HTLC_On_Opened_Channel",             False, None, False),
        ("Settle_Requires_Receiver_Release",   False, None, False),
        ("Forward1_Requires_Offer",            False, None, False),
        ("Forward2_Requires_Forward1",         False, None, False),
        ("Fulfill_Requires_Forward2",          False, None, False),
        ("Claim_Requires_Release",             False, None, False),
        ("Settle_Excludes_Sender_Refund",      False, None, False),
        ("Invoice_Authenticates_Settlement",   False, None, False),
        ("Forged_Invoice_Requires_Key_Compromise", False, None, False),
        ("Loss_Requires_Inaction",             False, None, False),
        ("Refund_Requires_Timeout",            False, None, False),
        ("Intermediary_Never_Loses_Under_Liveness", False, None, False),
        ("Forward1_Requires_Offer_Honest",     False, None, False),
        ("Forward2_Requires_Forward1_Honest",  False, None, False),
        ("Fulfill_Requires_Forward2_Honest",   False, None, False),
        ("Payment_Atomicity_Under_Liveness",   False, None, False),
        ("T2b_Counterexample_Blocked",         False, None, False),
        ("Fee_Conservation_Hop1",              False, None, False),
        ("Fee_Conservation_Hop2",              False, None, False),
        ("Receiver_Paid_Invoice_Amount",       False, None, False),
        ("Fees_Charged_On_Path_Possible",      False, None, False),
    ],
}

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


def base_cmd(path, seqdfs):
    cmd = [
        "tamarin-prover", path,
        "--heuristic=c",
        "--derivcheck-timeout=0",
    ]
    if seqdfs:
        cmd.append("--stop-on-trace=seqdfs")
    return cmd


def run_one(path, lemma, seqdfs, timeout, env):
    """Run a single --prove=lemma invocation; return (lemma_dict, elapsed)."""
    cmd = base_cmd(path, seqdfs) + [f"--prove={lemma}"]
    start = time.monotonic()
    try:
        proc = subprocess.run(
            cmd, env=env, capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - start
        return {"name": lemma, "kind": "?", "status": "incomplete", "steps": "",
                "error": f"timeout after {timeout}s"}, elapsed
    except FileNotFoundError:
        elapsed = time.monotonic() - start
        return {"name": lemma, "kind": "?", "status": "incomplete", "steps": "",
                "error": "tamarin-prover not found"}, elapsed

    elapsed = time.monotonic() - start
    out = proc.stdout + proc.stderr
    # Tamarin prints ALL lemma statuses even for --prove=LEMMA; filter to the
    # specific lemma we asked about so we don't grab a stale status line.
    for line in out.splitlines():
        m = LINE_RE.match(line)
        if m and m.group("name") == lemma:
            return {
                "name":   m.group("name"),
                "kind":   m.group("kind"),
                "status": "incomplete" if m.group("status") == "analysis incomplete"
                          else m.group("status"),
                "steps":  m.group("steps") or "",
                "error":  None,
            }, elapsed

    tail = out.strip().splitlines()[-1] if out.strip() else "(no output)"
    reason = "killed (OOM?)" if proc.returncode and proc.returncode < 0 \
             else f"no result; last: {tail[:60]}"
    return {"name": lemma, "kind": "?", "status": "incomplete", "steps": "",
            "error": reason}, elapsed


def run_file_bulk(path, timeout):
    """Single --prove invocation for the whole file."""
    seqdfs = path not in NO_SEQDFS
    cmd = base_cmd(path, seqdfs) + ["--prove"]
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
                "error":  None,
            })

    if not lemmas:
        tail = out.strip().splitlines()[-1] if out.strip() else "(no output)"
        reason = "process killed (likely OOM)" if proc.returncode and proc.returncode < 0 \
                 else f"no result lines; last output: {tail[:80]}"
        return [], reason, elapsed

    return lemmas, None, elapsed


def run_file_per_lemma(path, lemma_list, timeout, workers=4):
    """Run per-lemma proofs: solo lemmas first (full CPU), then the rest in parallel.

    solo=True lemmas run one at a time before the parallel batch so they get
    full CPU.  This matters for heavy exists-traces like Multihop_Payment_Possible
    which needs ~850s and OOMs or times out when competing with 3 other processes.
    """
    env = dict(os.environ, LANG="C.utf8", LC_ALL="C.utf8")
    wall_start = time.monotonic()
    print_lock = threading.Lock()

    solo   = [(i, e) for i, e in enumerate(lemma_list) if e[3]]
    batch  = [(i, e) for i, e in enumerate(lemma_list) if not e[3]]
    results = [None] * len(lemma_list)

    def run_and_record(idx, lemma, seqdfs, t):
        cmd = base_cmd(path, seqdfs) + [f"--prove={lemma}"]
        with print_lock:
            print(f"   $ " + " ".join(cmd), flush=True)
        result, elapsed = run_one(path, lemma, seqdfs, t, env)
        if result.get("error"):
            status_str = YELLOW(f"!! {result['error']}")
        elif result["status"] == "verified":
            status_str = GREEN(f"{result['name']}: verified ({result['steps']} steps)")
        else:
            status_str = RED(f"{result['name']}: {result['status']}")
        with print_lock:
            print(f"     [{fmt_time(elapsed)}] {status_str}", flush=True)
        results[idx] = result

    # Phase 1: solo lemmas, strictly sequential, full CPU each.
    for idx, (lemma, seqdfs, t_override, _) in solo:
        t = t_override if t_override is not None else timeout
        run_and_record(idx, lemma, seqdfs, t)

    # Phase 2: remaining lemmas in parallel with a bounded worker pool.
    semaphore = threading.Semaphore(workers)

    def worker(idx, lemma, seqdfs, t):
        with semaphore:
            run_and_record(idx, lemma, seqdfs, t)

    threads = []
    for idx, (lemma, seqdfs, t_override, _) in batch:
        t = t_override if t_override is not None else timeout
        th = threading.Thread(target=worker, args=(idx, lemma, seqdfs, t), daemon=True)
        threads.append(th)
    for th in threads:
        th.start()
    for th in threads:
        th.join()

    return results, None, time.monotonic() - wall_start


def print_table(path, lemmas, error, elapsed):
    print(BOLD(f"\n=== {path} ===") + f"  [{fmt_time(elapsed)}]")
    if error:
        print(RED(f"  !! {error}"))
        return (0, 0)

    name_w = max((len(l["name"]) for l in lemmas), default=4)
    n_ok = n_bad = 0
    for l in lemmas:
        err = l.get("error")
        if err:
            tag, n_bad = YELLOW(f"ERROR:{err[:30]}"), n_bad + 1
        elif l["status"] == "verified":
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
    ap.add_argument("--timeout", type=int, default=300,
                    help="per-lemma wall-clock cap in seconds (default 300)")
    ap.add_argument("--workers", type=int, default=4,
                    help="parallel tamarin processes for per-lemma files (default 4)")
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
        if path in PER_LEMMA:
            lemmas, error, elapsed = run_file_per_lemma(
                path, PER_LEMMA[path], args.timeout, workers=args.workers)
        else:
            lemmas, error, elapsed = run_file_bulk(path, args.timeout * 10)
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
        print(YELLOW("  (a lemma with no result was likely OOM-killed or timed out)"))
        return 1
    print(GREEN("  all files fully verified."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
