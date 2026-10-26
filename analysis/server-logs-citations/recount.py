"""Recount every number in summary.md from rows.csv. Standard library only: python3 recount.py"""
import csv
import math
from collections import defaultdict
from datetime import datetime, timedelta
from statistics import median

ROWS = list(csv.DictReader(open(__file__.replace("recount.py", "rows.csv"))))
T = lambda s: datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ")
START, END = T("2026-08-26T00:00:00Z"), T("2026-10-06T00:00:00Z")

answers = defaultdict(lambda: {"paths": set()})
for r in ROWS:
    if r["kind"] == "citation":
        a = answers[r["answer_id"]]
        a.update(engine=r["engine"], time=T(r["check_time"]))
        a["paths"].add(r["path"])
fetches = [dict(r, t=T(r["fetch_time"]), ok=r["verified"] == "true") for r in ROWS if r["kind"] == "fetch"]

LIVE = {"chatgpt-api": "ChatGPT-User", "perplexity-api": "PerplexityBot"}
INDEX = {"chatgpt-api": "OAI-SearchBot", "perplexity-api": "PerplexityBot"}
W = timedelta(minutes=10)

print("## 1. A fetch in the 10 minutes before the stored answer")
for eng in LIVE:
    ans = [a for a in answers.values() if a["engine"] == eng]
    near = lambda a, verified: [f for f in fetches if f["crawler"] == LIVE[eng] and f["ok"] == verified and a["time"] - W <= f["t"] <= a["time"]]
    v = [a for a in ans if near(a, True)]
    vc = [a for a in ans if any(f["path"] in a["paths"] for f in near(a, True))]
    u = [a for a in ans if near(a, False)]
    uc = [a for a in ans if any(f["path"] in a["paths"] for f in near(a, False))]
    after = [a for a in ans if [f for f in fetches if f["crawler"] == LIVE[eng] and f["ok"] and a["time"] < f["t"] <= a["time"] + W]]
    print(f"{eng}: {len(ans)} answers; verified {LIVE[eng]} fetch before: {len(v)}, of a cited URL: {len(vc)}; "
          f"unverified before: {len(u)} (of a cited URL: {len(uc)}); verified fetch in the 10 minutes after: {len(after)}")

# The base rate: how often a random 10-minute window holds a verified ChatGPT-User fetch.
cu = [f for f in fetches if f["crawler"] == "ChatGPT-User" and f["ok"] and START <= f["t"] < END]
per_day = len(cu) / ((END - START).total_seconds() / 86400)
print(f"verified ChatGPT-User fetches {len(cu)} = {per_day:.1f}/day; P(>=1 in a random 10 min) = {1 - math.exp(-per_day * 10 / 1440):.1%}")
print(f"of which homepage: {sum(f['path'] == '/' for f in cu)}")

print("\n## 2. Was the cited URL fetched by the engine's index crawler before the answer?")
for eng in INDEX:
    pairs = [(a, p) for a in answers.values() if a["engine"] == eng for p in a["paths"]]
    seen = lambda a, p: any(f["crawler"] == INDEX[eng] and f["ok"] and f["path"] == p and f["t"] < a["time"] for f in fetches)
    miss = [(a["time"].date().isoformat(), p) for a, p in pairs if not seen(a, p)]
    print(f"{eng}: {len(pairs) - len(miss)}/{len(pairs)} (answer, URL) pairs crawled first; "
          f"{len({p for _, p in pairs})} distinct pages; misses: {sorted(miss)}")

print("\n## 3. Failed IP verification, Aug 26 - Oct 5")
for c in ["GPTBot", "PerplexityBot", "ChatGPT-User", "OAI-SearchBot"]:
    fs = [f for f in fetches if f["crawler"] == c and START <= f["t"] < END]
    bad = [f for f in fs if not f["ok"]]
    ours = [f for f in bad if f["note"]]
    print(f"{c}: {len(bad)}/{len(fs)} failed ({len(bad) / len(fs):.0%}); ours {len(ours)}; "
          f"not explained {len(bad) - len(ours)} of {len(fs) - len(ours)} without ours")

print("\n## 4. Revisit gap (verified, Aug 26 - Oct 5)")
for c in ["OAI-SearchBot", "PerplexityBot"]:
    by = defaultdict(list)
    for f in fetches:
        if f["crawler"] == c and f["ok"] and START <= f["t"] < END:
            by[f["path"]].append(f["t"])
    gaps, per_page = [], []
    for ts in by.values():
        ts.sort()
        g = [(b - a).total_seconds() / 3600 for a, b in zip(ts, ts[1:])]
        gaps += g
        if g:
            per_page.append(median(g))
    print(f"{c}: {sum(map(len, by.values()))} fetches of {len(by)} pages; {len(per_page)} pages fetched again; "
          f"median gap {median(gaps):.1f} h over {len(gaps)} gaps; median of per-page medians {median(per_page):.1f} h")

print("\n## 5. After the 4 Oct 18:05 UTC change to /, /pricing, /methodology, /help (rows end 7 Oct 09:00 UTC)")
CHANGE = T("2026-10-04T18:05:00Z")
for c in ["OAI-SearchBot", "PerplexityBot"]:
    for p in ["/", "/pricing", "/methodology", "/help"]:
        nxt = [f["t"] for f in fetches if f["crawler"] == c and f["ok"] and f["path"] == p and f["t"] > CHANGE]
        last = [f["t"] for f in fetches if f["crawler"] == c and f["ok"] and f["path"] == p and f["t"] <= CHANGE]
        gap = f"{(min(nxt) - CHANGE).total_seconds() / 3600:.0f} h" if nxt else "not yet"
        print(f"{c} {p}: next fetch {gap}; last fetch before the change {max(last).isoformat() if last else 'never'}")
