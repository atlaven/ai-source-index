#!/usr/bin/env python3
"""Recount every number in "What AI engines cite: the first eight weeks of the AI Source Index".

Python 3.8+, standard library only. Report: https://promvia.app/ai-source-index/first-eight-weeks

    python3 recount.py rows.csv                      # rebuild every table from the published rows
    python3 recount.py rows.csv --check results.json # ...and compare with the published results
    python3 recount.py --raw DIR --check results.json
        # rebuild from the raw API responses instead (one file per week, as served by
        # https://promvia.app/api/public/ai-source-index/rows?week=2026-W36 ... 2026-W43)

This script is Promvia's SECOND derivation: the published results are computed by a separate
TypeScript implementation, and a number is published only when both agree exactly.

Rules (the same ones the report states):
  * Unit: one answer = one (week, question, engine) check. Answer engines only; the Bing organic
    proxy is not in the rows.
  * A failed check is coverage, never a citation. An ok answer that cited nothing is kept.
  * One domain citation = one domain in one answer (domains are already deduplicated per answer).
  * Retention: of the domains an engine cited for a question in week t, the share it cited for the
    same question in week t+1; only when both weeks' checks are ok.
  * Agreement: on (week, question) cells all six engines answered, a domain's engine count is how
    many of the six cited it; pair overlap is shared / union, summed over cells.
  * Platforms: a domain is on a platform when it equals one of its hosts or is a subdomain of one.
  * Intervals: 95% percentile bootstrap resampling the questions with replacement, 2,000 draws,
    mulberry32 seeded 20261023 afresh for every statistic. None at 0/n or n/n.
  * Percentages are rounded half up to one decimal; means to two.
"""
import csv
import json
import math
import os
import sys

WEEKS = ["2026-W%d" % w for w in range(36, 44)]
ENGINES = ["perplexity", "openai", "gemini", "claude", "aioverviews", "aimode"]
SHAPES = ["best", "alternatives", "compare", "howto-buy"]
PLATFORM_HOSTS = {"reddit": ("reddit.com",), "youtube": ("youtube.com", "youtu.be"), "wikipedia": ("wikipedia.org",)}
DRAWS, SEED, TOP = 2000, 20261023, 10
M32 = 0xFFFFFFFF


# ---- input ---------------------------------------------------------------------------------

def load_csv(path):
    answers = {}
    with open(path, newline="", encoding="utf-8") as fh:
        for rec in csv.DictReader(fh):
            k = (rec["week"], rec["query_id"], rec["engine"])
            if k not in answers:
                answers[k] = {
                    "week": rec["week"], "at": rec["captured_at"], "instrument": rec["instrument"],
                    "q": rec["query_id"], "shape": rec["shape"], "engine": rec["engine"],
                    "model": rec["model"] or None, "ok": rec["status"] == "ok",
                    "fail": rec["failure_class"] or None, "domains": set(),
                }
            if rec["domain"]:
                answers[k]["domains"].add(rec["domain"])
    return answers


def load_raw(folder):
    answers = {}
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".json"):
            continue
        with open(os.path.join(folder, name), encoding="utf-8") as fh:
            doc = json.load(fh)
        for wk in doc["weeks"]:
            if wk["week"] not in WEEKS:
                continue
            for r in wk["rows"]:
                if r["role"] != "answer":
                    continue
                answers[(wk["week"], r["queryId"], r["engine"])] = {
                    "week": wk["week"], "at": wk["capturedAt"], "instrument": wk["instrument"],
                    "q": r["queryId"], "shape": r["shape"], "engine": r["engine"],
                    "model": r.get("model"), "ok": r["status"] == "ok",
                    "fail": r.get("failureClass"),
                    "domains": set(r["domains"]) if r["status"] == "ok" else set(),
                }
    return answers


# ---- arithmetic ----------------------------------------------------------------------------

def pct(x):
    return math.floor(x * 1000 + 0.5) / 10


def two(x):
    return math.floor(x * 100 + 0.5) / 100


def imul(a, b):
    return (a * b) & M32


def rng(seed):
    state = [seed & M32]

    def nxt():
        state[0] = (state[0] + 0x6D2B79F5) & M32
        t = state[0]
        t = imul(t ^ (t >> 15), t | 1)
        t = (t ^ ((t + imul(t ^ (t >> 7), t | 61)) & M32)) & M32
        return ((t ^ (t >> 14)) & M32) / 4294967296.0
    return nxt


def interval(per_q):
    """per_q: {question: [numerator, denominator]} -> (low, high) of the ratio of sums."""
    keys = sorted(q for q, v in per_q.items() if v[1] > 0)
    nums = [per_q[q][0] for q in keys]
    dens = [per_q[q][1] for q in keys]
    m = len(keys)
    r = rng(SEED)
    out = []
    for _ in range(DRAWS):
        n = d = 0
        for _ in range(m):
            j = math.floor(r() * m)
            n += nums[j]
            d += dens[j]
        out.append(n / d)
    out.sort()
    return out[math.floor(DRAWS * 0.025)], out[math.ceil(DRAWS * 0.975) - 1]


def proportion(per_q):
    k = sum(v[0] for v in per_q.values())
    n = sum(v[1] for v in per_q.values())
    if k == 0 or k == n:
        return {"k": k, "n": n, "pct": pct(k / n), "low": None, "high": None}
    lo, hi = interval(per_q)
    return {"k": k, "n": n, "pct": pct(k / n), "low": pct(lo), "high": pct(hi)}


def bump(per_q, q, k, n):
    v = per_q.setdefault(q, [0, 0])
    v[0] += k
    v[1] += n


def on(domain, hosts):
    return any(domain == h or domain.endswith("." + h) for h in hosts)


# ---- the report ----------------------------------------------------------------------------

def recount(A):
    qs = sorted({a["q"] for a in A.values()})
    shape_of = {a["q"]: a["shape"] for a in A.values()}
    oks = [a for a in A.values() if a["ok"]]

    def got(w, q, e):
        a = A.get((w, q, e))
        return a["domains"] if a and a["ok"] else None

    week_at = {a["week"]: a["at"] for a in A.values()}
    week_instr = {a["week"]: a["instrument"] for a in A.values()}

    res = {}
    res["window"] = {"weeks": WEEKS, "capturedAt": [{"week": w, "at": week_at[w]} for w in WEEKS],
                     "first": week_at[WEEKS[0]], "last": week_at[WEEKS[-1]]}
    res["instruments"] = [{"week": w, "instrument": week_instr[w]} for w in WEEKS]
    res["panel"] = {"questions": len(qs), "byShape": {s: sum(1 for q in qs if shape_of[q] == s) for s in SHAPES},
                    "engines": len(ENGINES)}
    fails = {}
    for a in A.values():
        if not a["ok"]:
            fails[(a["week"], a["engine"], a["fail"] or "")] = fails.get((a["week"], a["engine"], a["fail"] or ""), 0) + 1
    res["coverage"] = {
        "cells": len(A), "ok": len(oks), "failed": len(A) - len(oks),
        "byEngine": {e: {"ok": sum(1 for a in oks if a["engine"] == e),
                         "failed": sum(1 for a in A.values() if a["engine"] == e and not a["ok"])} for e in ENGINES},
        "failures": [{"week": w, "engine": e, "failureClass": c, "n": n} for (w, e, c), n in sorted(fails.items())],
    }
    models = {}
    for e in ENGINES:
        groups = []
        for w in WEEKS:
            m = next((a["model"] for a in A.values() if a["week"] == w and a["engine"] == e), None)
            for g in groups:
                if g["model"] == m:
                    g["weeks"].append(w)
                    break
            else:
                groups.append({"model": m, "weeks": [w]})
        models[e] = groups
    res["models"] = models

    tally = {}
    for a in oks:
        for d in a["domains"]:
            tally[d] = tally.get(d, 0) + 1
    total = sum(tally.values())
    res["totals"] = {"domainCitations": total, "distinctDomains": len(tally),
                     "csvLines": total + sum(1 for a in A.values() if not a["domains"])}
    order = sorted(tally.items(), key=lambda kv: (-kv[1], kv[0]))
    running, half = 0, 0
    while running * 2 < total:
        running += order[half][1]
        half += 1
    once = sum(1 for _, c in order if c == 1)

    def share(n):
        k = sum(c for _, c in order[:n])
        return {"k": k, "n": total, "pct": pct(k / total)}
    res["concentration"] = {"top": [{"domain": d, "citations": c} for d, c in order[:TOP]],
                            "top1": share(1), "top2": share(2), "top10": share(TOP), "halfAt": half,
                            "citedOnce": {"k": once, "n": len(order), "pct": pct(once / len(order))}}

    # agreement
    full, hist6, only = 0, [0] * 6, {}
    pair_keys = [(ENGINES[i], ENGINES[j]) for i in range(6) for j in range(i + 1, 6)]
    pairs = {p: {} for p in pair_keys}
    for w in WEEKS:
        for q in qs:
            sets = {e: got(w, q, e) for e in ENGINES}
            if any(v is None for v in sets.values()):
                continue
            full += 1
            union = set().union(*sets.values())
            counts = {d: sum(1 for e in ENGINES if d in sets[e]) for d in union}
            for c in counts.values():
                hist6[c - 1] += 1
            bump(only, q, sum(1 for c in counts.values() if c == 1), len(union))
            for a, b in pair_keys:
                bump(pairs[(a, b)], q, len(sets[a] & sets[b]), len(sets[a] | sets[b]))
    same = {}
    for i in range(len(WEEKS) - 1):
        for q in qs:
            for e in ENGINES:
                x, y = got(WEEKS[i], q, e), got(WEEKS[i + 1], q, e)
                if x is None or y is None:
                    continue
                bump(same, q, len(x & y), len(x | y))
    pair_rows = []
    for a, b in pair_keys:
        p = proportion(pairs[(a, b)])
        pair_rows.append(dict({"a": a, "b": b}, **p))
    pair_rows.sort(key=lambda r: (-(r["k"] / r["n"]), r["a"], r["b"]))
    res["overlap"] = {"fullCells": full, "cellsOf": len(WEEKS) * len(qs), "domainCells": sum(hist6),
                      "byEngineCount": hist6, "onlyOne": proportion(only), "pairs": pair_rows,
                      "sameEngineNextWeek": proportion(same)}

    # platforms
    plats = []
    for pid, hosts in PLATFORM_HOSTS.items():
        every, per = {}, {}
        for e in ENGINES:
            m = {}
            for a in oks:
                if a["engine"] != e:
                    continue
                hit = 1 if any(on(d, hosts) for d in a["domains"]) else 0
                bump(m, a["q"], hit, 1)
                bump(every, a["q"], hit, 1)
            per[e] = proportion(m)
        plats.append({"id": pid, "byEngine": per, "all": proportion(every)})
    res["platforms"] = plats

    # retention
    pooled, same_i, per_e, prow = {}, {}, {e: {} for e in ENGINES}, []
    for i in range(len(WEEKS) - 1):
        w0, w1 = WEEKS[i], WEEKS[i + 1]
        same_instrument = week_instr[w0] == week_instr[w1]
        kk = nn = 0
        for q in qs:
            for e in ENGINES:
                x, y = got(w0, q, e), got(w1, q, e)
                if x is None or y is None:
                    continue
                kept = len(x & y)
                kk += kept
                nn += len(x)
                bump(pooled, q, kept, len(x))
                bump(per_e[e], q, kept, len(x))
                if same_instrument:
                    bump(same_i, q, kept, len(x))
        prow.append({"from": w0, "to": w1, "sameInstrument": same_instrument, "k": kk, "n": nn, "pct": pct(kk / nn)})
    ok8, hist8, one8, all8 = 0, [0] * 8, {}, {}
    for q in qs:
        for e in ENGINES:
            sets = [got(w, q, e) for w in WEEKS]
            if any(s is None for s in sets):
                continue
            ok8 += 1
            seen = {}
            for s in sets:
                for d in s:
                    seen[d] = seen.get(d, 0) + 1
            for c in seen.values():
                hist8[c - 1] += 1
            bump(one8, q, sum(1 for c in seen.values() if c == 1), len(seen))
            bump(all8, q, sum(1 for c in seen.values() if c == len(WEEKS)), len(seen))
    res["stability"] = {"pairs": prow, "pooled": proportion(pooled), "sameInstrument": proportion(same_i),
                        "byEngine": {e: proportion(per_e[e]) for e in ENGINES},
                        "eightWeeks": {"pairsOk": ok8, "pairsOf": len(qs) * len(ENGINES), "triples": sum(hist8),
                                       "hist": hist8, "onlyOne": proportion(one8), "every": proportion(all8)}}

    # question shape
    shp = []
    for s in SHAPES:
        yt, rd = {}, {}
        for a in oks:
            if a["shape"] != s:
                continue
            bump(yt, a["q"], 1 if any(on(d, PLATFORM_HOSTS["youtube"]) for d in a["domains"]) else 0, 1)
            bump(rd, a["q"], 1 if any(on(d, PLATFORM_HOSTS["reddit"]) for d in a["domains"]) else 0, 1)
        shp.append({"shape": s, "questions": res["panel"]["byShape"][s], "youtube": proportion(yt), "reddit": proportion(rd)})
    res["shapes"] = shp

    # sources per answer
    br = {}
    for e in ENGINES:
        mean, zero = {}, {}
        for a in oks:
            if a["engine"] == e:
                bump(mean, a["q"], len(a["domains"]), 1)
                bump(zero, a["q"], 1 if not a["domains"] else 0, 1)
        dom = sum(v[0] for v in mean.values())
        ans = sum(v[1] for v in mean.values())
        lo, hi = interval(mean)
        br[e] = {"answers": ans, "domains": dom, "mean": two(dom / ans), "meanLow": two(lo), "meanHigh": two(hi),
                 "zero": proportion(zero)}
    res["breadth"] = br
    return res


# ---- output and comparison -----------------------------------------------------------------

def leaves(obj, path=""):
    if isinstance(obj, dict):
        for k in obj:
            yield from leaves(obj[k], path + "." + str(k))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from leaves(v, "%s[%d]" % (path, i))
    else:
        yield path, obj


def main(argv):
    if "--raw" in argv:
        A = load_raw(argv[argv.index("--raw") + 1])
        source = "raw API snapshot"
    else:
        A = load_csv(argv[1] if len(argv) > 1 and not argv[1].startswith("--") else "rows.csv")
        source = "rows.csv"
    mine = recount(A)
    if "--check" not in argv:
        print(json.dumps(mine, indent=1))
        return 0
    with open(argv[argv.index("--check") + 1], encoding="utf-8") as fh:
        theirs = json.load(fh)
    # Fields that are metadata about the run, not counts: compared too, but listed separately.
    theirs_leaves = dict(leaves({k: v for k, v in theirs.items() if k != "bootstrap"}))
    if "window" in theirs:
        theirs_leaves.pop(".window.fetchedOn", None)
    mine_leaves = dict(leaves(mine))
    missing = sorted(set(theirs_leaves) - set(mine_leaves))
    extra = sorted(set(mine_leaves) - set(theirs_leaves))
    diff = sorted(p for p in set(theirs_leaves) & set(mine_leaves) if theirs_leaves[p] != mine_leaves[p])
    for p in missing:
        print("NOT RECOUNTED  %s = %r" % (p, theirs_leaves[p]))
    for p in extra:
        print("NOT PUBLISHED  %s = %r" % (p, mine_leaves[p]))
    for p in diff:
        print("MISMATCH       %s: published %r, recounted %r" % (p, theirs_leaves[p], mine_leaves[p]))
    same = len(set(theirs_leaves) & set(mine_leaves)) - len(diff)
    print("source: %s; %d answers" % (source, len(A)))
    print("%d of %d published values recounted and identical" % (same, len(theirs_leaves)))
    ok = not missing and not extra and not diff and theirs.get("bootstrap") == {"draws": DRAWS, "seed": SEED}
    print("ALL MATCH" if ok else "DISAGREEMENT")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
