#!/usr/bin/env python3
"""Depth-first witness search over the Tamarin interactive server.

Usage: dfs.py <lemma> [maxdepth]
At each node apply the first proof method; order the resulting cases so that
channel-opening / direct cases come first and recycling / relay cases last;
backtrack on contradictions and when the depth bound is hit.
"""
import sys, json, re, html, urllib.request

B = "http://127.0.0.1:3011"
L = sys.argv[1]
MAXD = int(sys.argv[2]) if len(sys.argv) > 2 else 60
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
state = {"I": int(sys.argv[3]) if len(sys.argv) > 3 else 1}


def get(url):
    with opener.open(B + url, timeout=600) as r:
        return r.read().decode()


def node_text(path):
    d = json.loads(get(f"/thy/trace/{state['I']}/main/proof/{L}" + ("/" + path if path else "")))
    t = html.unescape(re.sub(r"<[^>]+>", " ", d.get("html", "")))
    return re.sub(r"\s+", " ", t)


def apply1(path):
    r = get(f"/thy/trace/{state['I']}/main/method/{L}/1" + ("/" + path if path else ""))
    m = re.search(r'"redirect":"([^"]+)"', r)
    if not m:
        return None
    state["I"] = int(re.search(r"trace/(\d+)", m.group(1)).group(1))
    return m.group(1)


def children(path):
    """Names of the direct sub-cases of `path` in the current proof tree."""
    page = get(f"/thy/trace/{state['I']}/overview/help")
    pre = f"proof/{L}/" + (path + "/" if path else "")
    kids = set()
    for p in re.findall(r'(proof/' + re.escape(L) + r'[^"\\]*)', page):
        if p.startswith(pre):
            rest = p[len(pre):]
            if rest and "/" not in rest:
                kids.add(rest)
    return kids


def rank(name):
    if name.startswith(("Intermediary_Settle", "Sender_Settle", "Fulfill_Compromised_In")):
        return 2
    if name.startswith(("Lock_Funds_And_Open", "Receiver_Fulfill_HTLC", "Sender_Offer_HTLC",
                        "Register_key", "Receiver_Create_Invoice")):
        return 0
    return 1


steps = [0]


def dfs(path, depth):
    steps[0] += 1
    t = node_text(path)
    if "Constraint System is Solved" in t or "trace found" in t.lower():
        print("TRACE FOUND", state["I"], path, flush=True)
        return True
    if "Applicable Proof Methods" not in t:
        return False
    first = re.search(r"1\.\s*(\S+)", t.split("Applicable Proof Methods", 1)[1])
    if first and first.group(1).startswith("contradiction"):
        return False
    if depth >= MAXD:
        return False
    red = apply1(path)
    if red is None:
        return False
    sub = red.split(f"/proof/{L}", 1)[1].lstrip("/")
    # sub is either path/_ (single successor) or path/<firstcase>
    parent = sub.rsplit("/", 1)[0] if "/" in sub else ""
    if parent != path:  # single successor deeper than one level? just follow it
        return dfs(sub, depth + 1)
    kids = sorted(children(path), key=lambda k: (rank(k), k))
    if not kids:
        return dfs(sub, depth + 1)
    for k in kids:
        print(f"{'  ' * min(depth, 30)}{depth}: {k}", flush=True)
        if dfs((path + "/" if path else "") + k, depth + 1):
            return True
    return False


ok = dfs("", 0)
print("RESULT", ok, "idx", state["I"], "steps", steps[0], flush=True)
