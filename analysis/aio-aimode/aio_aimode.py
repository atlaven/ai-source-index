#!/usr/bin/env python3
"""
Google AI Overviews vs Google AI Mode in the Promvia AI Source Index, W36-W41 2026: how often each
surface answered without citing any domain, how stable that is per question across runs, how many
domains an answer cites, and how much the two surfaces' sources overlap for the same question in
the same run. Standard library only.

Input : ../2026-10-07-citation-persistence/raw/2026-W36.json ... 2026-W41.json, saved unmodified
        from https://promvia.app/api/public/ai-source-index/rows?week=<week> (CC BY 4.0)
Output: results.json   every number, as k / n with a 95% Wilson interval where it is a rate
Run   : python3 -I aio_aimode.py     (from this directory)

Rules (the public analysis v2, as in the persistence study):
  - Only engines 'aioverviews' and 'aimode' are read. A row with status != 'ok' is coverage, never
    an answer: it leaves every denominator (W41 has one failed AI Overviews row).
  - `domains` is used as published: deduplicated per (question, engine), Google's own search and
    shopping links already dropped. An ok row with empty `domains` "cited no domain". It is split by
    `citedUrls`: empty = no link at all (the public rows cannot tell "Google showed no AI answer"
    from "an answer with no sources"; both have no links); non-empty = only Google's own links.
  - Per-question stability: questions whose row is ok in all six runs.
  - Overlap: (question, run) cells where BOTH surfaces are ok and BOTH cited at least one domain.

The second, independent derivation is crosscheck.mjs (Node, a different code path); its output is
crosscheck-output.txt. Record of 2026-10-07: the first run differed on one value only, AI Mode's
"no link at all" 51 / 240 = exactly 21.25% (Python round-half-even 21.2 vs JS 21.3); fixed here by
rounding half up (`pct1`). Re-run: all 34 values match.

Numbers the guide REUSES rather than recomputes (retention per surface; page-one overlap; the
no-answer vs no-sources split for 28 Sep / 5 Oct) are quoted from
../2026-10-07-citation-persistence/summary.md and ../2026-10-06-shape-split-google/summary.md.
"""
import json
import math
import os
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "..", "2026-10-07-citation-persistence", "raw")
WEEKS = ["2026-W36", "2026-W37", "2026-W38", "2026-W39", "2026-W40", "2026-W41"]
GOOGLE = ["aioverviews", "aimode"]
Z = 1.959964


def wilson(k, n):
    if n == 0:
        return (None, None)
    p = k / n
    den = 1 + Z * Z / n
    mid = (p + Z * Z / (2 * n)) / den
    half = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / den
    return (max(0.0, mid - half), min(1.0, mid + half))


def pct1(k, n):
    """k / n as a percentage to one decimal, half rounded UP from the exact fraction (21.25 -> 21.3).
    Python's round() rounds a half to even (21.2); the first cross-check run caught that difference
    for AI Mode's 51 / 240 = 21.25%, and half-up is the rule the article prints."""
    return float((Decimal(100 * k) / Decimal(n)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def rate(k, n):
    lo, hi = wilson(k, n)
    return {"k": k, "n": n, "pct": pct1(k, n) if n else None,
            "wilson_lo": round(100 * lo, 1) if n else None, "wilson_hi": round(100 * hi, 1) if n else None}


def median(xs):
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return None
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def load():
    """cells[(week, queryId, engine)] = row, for the two Google surfaces only."""
    cells = {}
    questions = {}
    for w in WEEKS:
        with open(os.path.join(RAW, f"{w}.json"), encoding="utf-8") as fh:
            data = json.load(fh)
        week = data["weeks"][0]
        assert week["week"] == w
        for r in week["rows"]:
            if r["engine"] not in GOOGLE:
                continue
            key = (w, r["queryId"], r["engine"])
            assert key not in cells, key
            cells[key] = r
            questions[r["queryId"]] = r["question"]
    return cells, questions


def main():
    cells, questions = load()
    qids = sorted(questions)
    out = {"questions": len(qids), "weeks": WEEKS}

    # 1. Answers that cited no domain, per engine, per run and pooled.
    empty = {}
    for e in GOOGLE:
        per_run = []
        tot_ok = tot_empty = tot_nolink = tot_googleonly = tot_failed = 0
        for w in WEEKS:
            ok = nod = nolink = gonly = failed = 0
            for q in qids:
                r = cells.get((w, q, e))
                if r is None or r["status"] != "ok":
                    failed += 1
                    continue
                ok += 1
                if not r["domains"]:
                    nod += 1
                    if r.get("citedUrls"):
                        gonly += 1
                    else:
                        nolink += 1
            per_run.append({"week": w, "ok": ok, "failed": failed, "no_domain": nod,
                            "no_link_at_all": nolink, "only_google_links": gonly})
            tot_ok += ok; tot_empty += nod; tot_nolink += nolink; tot_googleonly += gonly; tot_failed += failed
        empty[e] = {
            "per_run": per_run,
            "pooled_no_domain": rate(tot_empty, tot_ok),
            "pooled_no_link_at_all": rate(tot_nolink, tot_ok),
            "pooled_only_google_links": rate(tot_googleonly, tot_ok),
            "failed_rows": tot_failed,
            "min_per_run": min(p["no_domain"] for p in per_run),
            "max_per_run": max(p["no_domain"] for p in per_run),
        }
    out["no_domain"] = empty

    # 2. Per-question stability over the six runs (questions ok in all six runs).
    stab = {}
    for e in GOOGLE:
        hist = Counter()
        n_q = 0
        for q in qids:
            rows = [cells.get((w, q, e)) for w in WEEKS]
            if any(r is None or r["status"] != "ok" for r in rows):
                continue
            n_q += 1
            hist[sum(1 for r in rows if not r["domains"])] += 1
        never = hist[0]
        always = hist[6]
        stab[e] = {
            "questions_ok_all_six": n_q,
            "histogram_runs_with_no_domain": {str(k): hist[k] for k in range(7)},
            "never_empty": rate(never, n_q),
            "always_empty": rate(always, n_q),
            "sometimes_empty": rate(n_q - never - always, n_q),
            "at_least_once_empty": rate(n_q - never, n_q),
        }
    out["per_question"] = stab

    # 3. Domains per answer, among ok answers that cited at least one domain.
    size = {}
    for e in GOOGLE:
        counts = [len(r["domains"]) for (w, q, en), r in cells.items()
                  if en == e and r["status"] == "ok" and r["domains"]]
        size[e] = {"answers": len(counts), "domains_total": sum(counts),
                   "mean": round(sum(counts) / len(counts), 2), "median": median(counts),
                   "min": min(counts), "max": max(counts)}
    out["domains_per_answer"] = size

    # 4. Same question, same run: does each surface answer with sources, and do they overlap?
    both_ok = 0
    matrix = Counter()  # (aio_has, aimode_has)
    inter = aio_dom = aimode_dom = union = 0
    cells_both = 0
    cells_any_shared = 0
    for w in WEEKS:
        for q in qids:
            a = cells.get((w, q, "aioverviews"))
            m = cells.get((w, q, "aimode"))
            if a is None or m is None or a["status"] != "ok" or m["status"] != "ok":
                continue
            both_ok += 1
            sa, sm = set(a["domains"]), set(m["domains"])
            matrix[(bool(sa), bool(sm))] += 1
            if sa and sm:
                cells_both += 1
                i = len(sa & sm)
                inter += i
                aio_dom += len(sa)
                aimode_dom += len(sm)
                union += len(sa | sm)
                if i:
                    cells_any_shared += 1
    out["same_question_same_run"] = {
        "cells_both_ok": both_ok,
        "aio_sources_aimode_sources": matrix[(True, True)],
        "aio_sources_aimode_none": matrix[(True, False)],
        "aio_none_aimode_sources": matrix[(False, True)],
        "both_none": matrix[(False, False)],
        "cells_both_cited": cells_both,
        "aimode_domains_also_in_aio": rate(inter, aimode_dom),
        "aio_domains_also_in_aimode": rate(inter, aio_dom),
        "shared_over_union": rate(inter, union),
        "cells_sharing_at_least_one_domain": rate(cells_any_shared, cells_both),
    }

    with open(os.path.join(HERE, "results.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print(json.dumps(out, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
