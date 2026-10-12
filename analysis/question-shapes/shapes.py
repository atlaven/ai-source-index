#!/usr/bin/env python3
"""
Which sources does each kind of buyer question cite? Question shape x cited domain in the Promvia
AI Source Index, W36-W41 2026 (3 Sep to 5 Oct), six answer engines, 40 fixed questions.
Standard library only.

Input : ../../data/raw/2026-W36.json ... 2026-W41.json, saved unmodified from
        https://promvia.app/api/public/ai-source-index/rows?week=<week>
Output: results.json  every number, with its numerator and denominator
        shape_domain.csv  one line per (shape, domain): answers citing it, pooled and per week
Run   : python3 shapes.py            (from this directory)

Shapes (fixed per question): best (16 questions), alternatives (8), compare (8), howto-buy (8).

Units.
  Answer: one engine's answer to one question in one week, status 'ok', role 'answer' (the Bing
    proxy is dropped). A failed row is coverage, never an answer.
  Answer share: answers that cite the domain at least once / answers of that shape. A domain counts
    once per answer, as the public rows already dedupe `domains`.
  Question coverage: questions of the shape for which at least one engine cited the domain that
    week / questions of the shape (the unit quoted on Indie Hackers on 23 Sep 2026).
  Comparison-shaped URL: a cited URL whose path matches COMPARISON_PATH (vs, versus, alternative(s),
    compare, comparison), counted per cited URL.

The second, independent derivation is crosscheck.mjs (Node, different code path).
"""
import csv
import json
import math
import os
import re
import urllib.parse
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "..", "..", "data", "raw")
WEEKS = ["2026-W36", "2026-W37", "2026-W38", "2026-W39", "2026-W40", "2026-W41"]
SHAPES = ["best", "alternatives", "compare", "howto-buy"]
Z = 1.959964
COMPARISON_PATH = re.compile(r"(^|[/\-_])(vs|versus|alternatives?|compare|comparison|comparisons)([/\-_.]|$)")
SPECIALIST_MIN = 12  # pooled answer-citations a domain needs before its shape mix is reported
SPECIALIST_MIN_QUESTIONS = 3  # distinct questions: a source of ONE question is trivially "specialised"


def wilson(k, n):
    if n == 0:
        return (None, None)
    p = k / n
    den = 1 + Z * Z / n
    mid = (p + Z * Z / (2 * n)) / den
    half = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / den
    return (max(0.0, mid - half), min(1.0, mid + half))


def rate(k, n):
    lo, hi = wilson(k, n)
    return {"k": k, "n": n, "rate": (k / n if n else None), "wilson_lo": lo, "wilson_hi": hi}


def load():
    rows = []
    for w in WEEKS:
        with open(os.path.join(RAW, f"{w}.json")) as f:
            d = json.load(f)
        for wk in d["weeks"]:
            if wk["week"] != w:
                continue
            for r in wk["rows"]:
                if r.get("role") != "answer":
                    continue
                rows.append({"week": w, **r})
    return rows


def main():
    rows = load()
    questions = defaultdict(set)          # shape -> question ids
    answers = Counter()                   # (week, shape) -> ok answers
    cite = Counter()                      # (week, shape, domain) -> answers citing
    qhit = defaultdict(set)               # (week, shape, domain) -> question ids
    dq = defaultdict(set)                 # domain -> question ids, all weeks
    url_total = Counter()                 # (week, shape) -> cited URLs
    url_comp = Counter()                  # (week, shape) -> comparison-shaped cited URLs
    no_source = Counter()                 # (week, shape) -> ok answers citing no domain
    for r in rows:
        s = r["shape"]
        questions[s].add(r["queryId"])
        if r["status"] != "ok":
            continue
        answers[(r["week"], s)] += 1
        if not r["domains"]:
            no_source[(r["week"], s)] += 1
        for d in r["domains"]:
            cite[(r["week"], s, d)] += 1
            qhit[(r["week"], s, d)].add(r["queryId"])
            dq[d].add(r["queryId"])
        for u in r.get("citedUrls") or []:
            path = urllib.parse.urlsplit(u).path.lower()
            url_total[(r["week"], s)] += 1
            if COMPARISON_PATH.search(path):
                url_comp[(r["week"], s)] += 1

    out = {"weeks": WEEKS, "shapes": {}, "questions_per_shape": {s: len(questions[s]) for s in SHAPES}}
    domains = sorted({d for (_, _, d) in cite})
    pooled = {s: sum(answers[(w, s)] for w in WEEKS) for s in SHAPES}
    pooled_all = sum(pooled.values())
    dom_pooled = {(s, d): sum(cite[(w, s, d)] for w in WEEKS) for s in SHAPES for d in domains}

    for s in SHAPES:
        top = sorted(domains, key=lambda d: (-dom_pooled[(s, d)], d))[:12]
        weekly_top1 = []
        for w in WEEKS:
            best = max(domains, key=lambda d: (cite[(w, s, d)], -domains.index(d)))
            weekly_top1.append({"week": w, "domain": best, "k": cite[(w, s, best)], "n": answers[(w, s)]})
        out["shapes"][s] = {
            "answers_pooled": pooled[s],
            "answers_per_week": {w: answers[(w, s)] for w in WEEKS},
            "no_source_pooled": rate(sum(no_source[(w, s)] for w in WEEKS), pooled[s]),
            "top_domains": [{"domain": d, **rate(dom_pooled[(s, d)], pooled[s]),
                             "weeks_in_top5": sum(1 for w in WEEKS if d in sorted(domains, key=lambda x: (-cite[(w, s, x)], x))[:5])}
                            for d in top],
            "weekly_top1": weekly_top1,
            "comparison_urls_pooled": rate(sum(url_comp[(w, s)] for w in WEEKS), sum(url_total[(w, s)] for w in WEEKS)),
            "comparison_urls_per_week": {w: rate(url_comp[(w, s)], url_total[(w, s)]) for w in WEEKS},
        }

    # Platforms week by week, both units.
    plat = {}
    for d in ["youtube.com", "reddit.com", "consumerreports.org"]:
        plat[d] = {s: {"question_coverage": {w: {"k": len(qhit[(w, s, d)]), "n": len(questions[s])} for w in WEEKS},
                       "answer_share": {w: rate(cite[(w, s, d)], answers[(w, s)]) for w in WEEKS},
                       "answer_share_pooled": rate(dom_pooled[(s, d)], pooled[s])} for s in SHAPES}
    out["platforms"] = plat

    # Shape specialists: where a frequently cited domain's citations concentrate, against the shape's
    # share of all answers (best is ~40% of answers, so 40% of a domain's citations is no signal).
    spec = []
    for d in domains:
        k_all = sum(dom_pooled[(s, d)] for s in SHAPES)
        if k_all < SPECIALIST_MIN or len(dq[d]) < SPECIALIST_MIN_QUESTIONS:
            continue
        s_top = max(SHAPES, key=lambda s: dom_pooled[(s, d)])
        k_s = dom_pooled[(s_top, d)]
        lift = (k_s / pooled[s_top]) / (k_all / pooled_all)
        spec.append({"domain": d, "citations": k_all, "questions": len(dq[d]), "top_shape": s_top, "in_top_shape": k_s,
                     "concentration": k_s / k_all, "lift": lift,
                     "weeks_cited_only_in_top_shape": sum(1 for w in WEEKS if cite[(w, s_top, d)] > 0 and all(cite[(w, s, d)] == 0 for s in SHAPES if s != s_top)),
                     "weeks_cited": sum(1 for w in WEEKS if any(cite[(w, s, d)] for s in SHAPES))})
    spec.sort(key=lambda x: (-x["lift"], -x["citations"], x["domain"]))
    out["specialists"] = [x for x in spec if x["concentration"] >= 0.6 and x["lift"] >= 2][:25]
    out["specialist_threshold"] = {"min_citations": SPECIALIST_MIN, "min_questions": SPECIALIST_MIN_QUESTIONS, "min_concentration": 0.6, "min_lift": 2,
                                   "domains_considered": len(spec)}
    out["answers_pooled_all"] = pooled_all

    with open(os.path.join(HERE, "results.json"), "w") as f:
        json.dump(out, f, indent=1)
    with open(os.path.join(HERE, "shape_domain.csv"), "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["shape", "domain", "answers_citing_pooled", "answers_pooled"] + [f"answers_citing_{w}" for w in WEEKS] + [f"answers_{w}" for w in WEEKS])
        for s in SHAPES:
            for d in domains:
                if dom_pooled[(s, d)]:
                    wr.writerow([s, d, dom_pooled[(s, d)], pooled[s]] + [cite[(w, s, d)] for w in WEEKS] + [answers[(w, s)] for w in WEEKS])
    print(json.dumps({s: {"n": pooled[s], "top5": [(t["domain"], t["k"], round(100 * t["rate"], 1), t["weeks_in_top5"]) for t in out["shapes"][s]["top_domains"][:6]],
                          "top1": [x["domain"] for x in out["shapes"][s]["weekly_top1"]],
                          "comp": (out["shapes"][s]["comparison_urls_pooled"]["k"], out["shapes"][s]["comparison_urls_pooled"]["n"]),
                          "nosrc": (out["shapes"][s]["no_source_pooled"]["k"])} for s in SHAPES}, indent=0))
    for x in out["specialists"]:
        print(x["domain"], x["citations"], x["questions"], x["top_shape"], x["in_top_shape"], round(x["concentration"], 2), round(x["lift"], 1), x["weeks_cited_only_in_top_shape"], x["weeks_cited"])


if __name__ == "__main__":
    main()
