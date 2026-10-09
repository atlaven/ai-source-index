#!/usr/bin/env python3
"""
How long does an AI citation last? Week-over-week persistence of cited domains (and URLs) in the
Promvia AI Source Index, W36-W41 2026. Standard library only.

Input : raw/2026-W36.json ... raw/2026-W41.json, saved unmodified from
        https://promvia.app/api/public/ai-source-index/rows?week=<week>
Output: results.json  every number, with its numerator and denominator
        rows.csv      one line per (week pair, question, engine, cited domain) observation used
        urls.csv      the same at URL level
Run   : python3 persistence.py            (from this directory)

Unit of observation: one domain cited in one answer, i.e. (week, question, engine, domain). The
public rows already dedupe `domains` per (question, engine). The Bing proxy (role 'proxy') is never
an answer engine and is dropped. A (question, engine) pair enters a comparison between week a and
week b only if its row has status 'ok' in BOTH weeks; a failed or missing row removes the pair from
that comparison's denominator (it is not counted as "not cited").

The second, independent derivation of the headline numbers is crosscheck.mjs (Node, different code
path); it reads the same raw files and compares its results with results.json.
"""
import csv
import json
import math
import os
import random
import urllib.parse
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
WEEKS = ["2026-W36", "2026-W37", "2026-W38", "2026-W39", "2026-W40", "2026-W41"]
ENGINES = ["perplexity", "openai", "gemini", "claude", "aioverviews", "aimode"]
LABEL = {"perplexity": "Perplexity", "openai": "ChatGPT", "gemini": "Gemini", "claude": "Claude",
         "aioverviews": "AI Overviews", "aimode": "AI Mode"}
Z = 1.959964
BOOT_REPS = 2000
BOOT_SEED = 20261007


def wilson(k, n):
    """95% Wilson score interval for k successes out of n, as fractions."""
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


def norm_url(u):
    """Comparable form of a cited URL. Host lowercased without www., no scheme, no trailing slash,
    tracking parameters (utm_*, srsltid) dropped, YouTube's `t` timestamp dropped, the rest sorted."""
    p = urllib.parse.urlsplit(u)
    host = (p.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    path = p.path.rstrip("/") or "/"
    yt = host in ("youtube.com", "youtu.be", "m.youtube.com")
    q = [(k, v) for k, v in urllib.parse.parse_qsl(p.query, keep_blank_values=True)
         if not k.lower().startswith("utm_") and k.lower() != "srsltid" and not (yt and k == "t")]
    q.sort()
    return host, host + path + ("?" + urllib.parse.urlencode(q) if q else "")


def load():
    """obs[week][(query_id, engine)] = {'status', 'domains': set, 'urls': set, 'question', 'shape'}"""
    obs, meta = {}, {}
    for w in WEEKS:
        with open(os.path.join(HERE, "raw", f"{w}.json")) as f:
            payload = json.load(f)
        (week,) = payload["weeks"]
        assert week["week"] == w
        meta[w] = {"capturedAt": week["capturedAt"], "instrument": week["instrument"],
                   "collectorVersion": week["collectorVersion"], "promptCount": week["promptCount"],
                   "engines": [e["id"] for e in week["engines"]]}
        cells = {}
        for r in week["rows"]:
            if r["role"] != "answer":
                continue
            assert r["engine"] in ENGINES, r["engine"]
            doms = set(r["domains"])
            urls = set()
            for u in r["citedUrls"]:
                host, key = norm_url(u)
                if host in doms:  # same rule as `domains`: Google search/shopping links drop out
                    urls.add(key)
            key = (r["queryId"], r["engine"])
            assert key not in cells
            cells[key] = {"status": r["status"], "failureClass": r.get("failureClass"),
                          "domains": doms if r["status"] == "ok" else set(),
                          "urls": urls if r["status"] == "ok" else set(),
                          "question": r["question"], "shape": r["shape"]}
        obs[w] = cells
    return obs, meta


def ok(obs, w, key):
    c = obs[w].get(key)
    return c is not None and c["status"] == "ok"


def all_keys(obs):
    ks = set()
    for w in WEEKS:
        ks |= set(obs[w])
    return sorted(ks)


def pair_counts(obs, a, b, field="domains", forward=True, engines=ENGINES, nonempty_both=False,
                queries=None, extra=None):
    """Sum over (question, engine) pairs ok in both weeks of |S_a & S_b| and |S_a| (forward) or
    |S_b| (backward). `queries` (a multiset of query ids) supports the cluster bootstrap."""
    k = n = 0
    for (qid, eng) in KEYS:
        if eng not in engines:
            continue
        if not (ok(obs, a, (qid, eng)) and ok(obs, b, (qid, eng))):
            continue
        sa = obs[a][(qid, eng)][field]
        sb = obs[b][(qid, eng)][field]
        if extra:
            sa = sa | extra(obs[a][(qid, eng)])
            sb = sb | extra(obs[b][(qid, eng)])
        if nonempty_both and (not sa or not sb):
            continue
        mult = 1 if queries is None else queries.get(qid, 0)
        if mult == 0:
            continue
        inter = len(sa & sb)
        k += inter * mult
        n += (len(sa) if forward else len(sb)) * mult
    return k, n


def pooled(obs, pairs, **kw):
    k = n = 0
    for a, b in pairs:
        dk, dn = pair_counts(obs, a, b, **kw)
        k += dk
        n += dn
    return k, n


def bootstrap(obs, pairs, engines, field="domains"):
    """Cluster bootstrap over the 40 questions: resample questions with replacement, recompute the
    pooled ratio. Each question carries all its engines and weeks, so within-question correlation
    (the same domains recurring across a question's answers) is kept."""
    rng = random.Random(BOOT_SEED)
    qids = sorted({q for q, _ in KEYS})
    vals = []
    for _ in range(BOOT_REPS):
        draw = Counter(rng.choice(qids) for _ in qids)
        k, n = pooled(obs, pairs, field=field, engines=engines, queries=draw)
        if n:
            vals.append(k / n)
    vals.sort()
    return vals[int(0.025 * len(vals))], vals[int(0.975 * len(vals)) - 1]


def main():
    obs, meta = load()
    global KEYS
    KEYS = all_keys(obs)
    res = {"weeks": WEEKS, "meta": meta, "engines": ENGINES}
    consecutive = list(zip(WEEKS, WEEKS[1:]))
    same_instrument = [(a, b) for a, b in consecutive if meta[a]["instrument"] == meta[b]["instrument"]]
    res["same_instrument_pairs"] = same_instrument

    # ---- coverage: what each comparison could see -------------------------------------------
    cov = {}
    for a, b in consecutive:
        excl = defaultdict(int)
        incl = defaultdict(int)
        for (qid, eng) in KEYS:
            if ok(obs, a, (qid, eng)) and ok(obs, b, (qid, eng)):
                incl[eng] += 1
            else:
                excl[eng] += 1
        cov[f"{a}->{b}"] = {"included_pairs": dict(incl), "excluded_pairs": dict(excl),
                            "included_total": sum(incl.values()), "excluded_total": sum(excl.values())}
    res["coverage"] = cov
    res["failed_rows"] = {w: Counter(f"{c['failureClass']}:{q[1]}" for q, c in obs[w].items()
                                     if c["status"] != "ok") for w in WEEKS}
    res["ok_rows_without_domains"] = {w: Counter(q[1] for q, c in obs[w].items()
                                                 if c["status"] == "ok" and not c["domains"]) for w in WEEKS}
    res["domains_per_week"] = {w: sum(len(c["domains"]) for c in obs[w].values()) for w in WEEKS}

    # ---- A. week-over-week retention ----------------------------------------------------------
    ret = {"by_pair": {}, "pooled": {}, "pooled_same_instrument": {}, "backward_by_pair": {},
           "pooled_nonempty_both": {}}
    for a, b in consecutive:
        row = {}
        for e in ENGINES:
            row[e] = rate(*pair_counts(obs, a, b, engines=[e]))
        row["all"] = rate(*pair_counts(obs, a, b))
        ret["by_pair"][f"{a}->{b}"] = row
        brow = {e: rate(*pair_counts(obs, a, b, engines=[e], forward=False)) for e in ENGINES}
        brow["all"] = rate(*pair_counts(obs, a, b, forward=False))
        ret["backward_by_pair"][f"{a}->{b}"] = brow
    for e in ENGINES + ["all"]:
        engs = ENGINES if e == "all" else [e]
        r = rate(*pooled(obs, consecutive, engines=engs))
        r["boot_lo"], r["boot_hi"] = bootstrap(obs, consecutive, engs)
        ret["pooled"][e] = r
        ret["pooled_same_instrument"][e] = rate(*pooled(obs, same_instrument, engines=engs))
        ret["pooled_nonempty_both"][e] = rate(*pooled(obs, consecutive, engines=engs, nonempty_both=True))
    google = ["aioverviews", "aimode"]
    llm = ["perplexity", "openai", "gemini", "claude"]
    ret["pooled"]["google_surfaces"] = rate(*pooled(obs, consecutive, engines=google))
    ret["pooled"]["llm_apis"] = rate(*pooled(obs, consecutive, engines=llm))
    res["retention"] = ret

    # ---- A2. URL level -------------------------------------------------------------------------
    url = {"pooled": {}, "by_pair_all": {}}
    for e in ENGINES + ["all"]:
        engs = ENGINES if e == "all" else [e]
        r = rate(*pooled(obs, consecutive, engines=engs, field="urls"))
        if e == "all":
            r["boot_lo"], r["boot_hi"] = bootstrap(obs, consecutive, engs, field="urls")
        url["pooled"][e] = r
    for a, b in consecutive:
        url["by_pair_all"][f"{a}->{b}"] = rate(*pair_counts(obs, a, b, field="urls"))
    # Of domains that stayed, how often was at least one of the same URLs cited again?
    k = n = 0
    for a, b in consecutive:
        for key in KEYS:
            if not (ok(obs, a, key) and ok(obs, b, key)):
                continue
            ua, ub = obs[a][key]["urls"], obs[b][key]["urls"]
            for d in obs[a][key]["domains"] & obs[b][key]["domains"]:
                da = {u for u in ua if u.split("/", 1)[0] == d}
                db = {u for u in ub if u.split("/", 1)[0] == d}
                n += 1
                k += 1 if da & db else 0
    url["kept_domain_same_url"] = rate(k, n)
    res["urls"] = url

    # ---- B. retention by lag ---------------------------------------------------------------------
    lag = {}
    for L in range(1, len(WEEKS)):
        pairs = [(WEEKS[i], WEEKS[i + L]) for i in range(len(WEEKS) - L)]
        lag[str(L)] = {"pairs": len(pairs), "all": rate(*pooled(obs, pairs)),
                       **{e: rate(*pooled(obs, pairs, engines=[e])) for e in ENGINES}}
    res["lag"] = lag

    # ---- C. survival -----------------------------------------------------------------------------
    def present(w, key, d):
        return d in obs[w][key]["domains"]

    # C1: everything cited in W36 (left-censored: we do not know when it started)
    surv36 = {}
    for kk in range(1, len(WEEKS)):
        cont_k = cont_n = 0
        at_k = at_n = 0
        for key in KEYS:
            if not all(ok(obs, WEEKS[j], key) for j in range(0, kk + 1)):
                continue
            for d in obs[WEEKS[0]][key]["domains"]:
                cont_n += 1
                cont_k += 1 if all(present(WEEKS[j], key, d) for j in range(1, kk + 1)) else 0
                at_n += 1
                at_k += 1 if present(WEEKS[kk], key, d) else 0
        surv36[str(kk)] = {"continuous": rate(cont_k, cont_n), "present_that_week": rate(at_k, at_n)}
    res["survival_w36_cohort"] = surv36

    # C2: citations first seen in week t (absent in every earlier week, all earlier rows ok)
    newc = {}
    pooled_new = defaultdict(lambda: [0, 0])
    cond = defaultdict(lambda: [0, 0])
    for t in range(1, len(WEEKS)):
        cohort = []
        for key in KEYS:
            if not all(ok(obs, WEEKS[j], key) for j in range(0, t + 1)):
                continue
            for d in obs[WEEKS[t]][key]["domains"]:
                if not any(present(WEEKS[j], key, d) for j in range(0, t)):
                    cohort.append((key, d))
        entry = {"size": len(cohort), "survival": {}}
        for kk in range(1, len(WEEKS) - t):
            k = n = 0
            for key, d in cohort:
                if not all(ok(obs, WEEKS[j], key) for j in range(t + 1, t + kk + 1)):
                    continue
                n += 1
                k += 1 if all(present(WEEKS[j], key, d) for j in range(t + 1, t + kk + 1)) else 0
            entry["survival"][str(kk)] = rate(k, n)
            pooled_new[kk][0] += k
            pooled_new[kk][1] += n
        newc[WEEKS[t]] = entry
        # Conditional: of the cohort still present in runs t..t+kk (kk+1 runs in a row), how many
        # are present in run t+kk+1? kk=0 is the plain "back next week" share.
        for kk in range(0, len(WEEKS) - t - 1):
            for key, d in cohort:
                if not all(ok(obs, WEEKS[j], key) for j in range(t + 1, t + kk + 2)):
                    continue
                if not all(present(WEEKS[j], key, d) for j in range(t + 1, t + kk + 1)):
                    continue
                cond[kk][1] += 1
                cond[kk][0] += 1 if present(WEEKS[t + kk + 1], key, d) else 0
    res["survival_new_cohorts"] = newc
    res["conditional_new"] = {f"{kk + 1}_runs_in_a_row": rate(*v) for kk, v in sorted(cond.items())}
    res["survival_new_pooled"] = {str(kk): rate(*v) for kk, v in sorted(pooled_new.items())}

    # ---- D. returns after a drop -----------------------------------------------------------------
    ret_after = {}
    tot_k = tot_n = 0
    next_k = next_n = 0
    for i in range(len(WEEKS) - 2):  # a drop between i and i+1 needs at least one later week
        a, b = WEEKS[i], WEEKS[i + 1]
        k = n = 0
        for key in KEYS:
            if not (ok(obs, a, key) and ok(obs, b, key)):
                continue
            later = [w for w in WEEKS[i + 2:] if ok(obs, w, key)]
            if not later:
                continue
            for d in obs[a][key]["domains"] - obs[b][key]["domains"]:
                n += 1
                k += 1 if any(present(w, key, d) for w in later) else 0
                if ok(obs, WEEKS[i + 2], key):
                    next_n += 1
                    next_k += 1 if present(WEEKS[i + 2], key, d) else 0
        ret_after[f"dropped {a}->{b}"] = {"later_weeks": len(WEEKS) - i - 2, **rate(k, n)}
        tot_k += k
        tot_n += n
    res["returns"] = {"by_drop": ret_after, "pooled_any_later_week": rate(tot_k, tot_n),
                      "pooled_back_the_very_next_week": rate(next_k, next_n)}

    # ---- E. one-week wonders (pairs ok in all six weeks) -------------------------------------------
    full = [key for key in KEYS if all(ok(obs, w, key) for w in WEEKS)]
    hist = {e: Counter() for e in ENGINES + ["all"]}
    for key in full:
        seen = Counter()
        for w in WEEKS:
            for d in obs[w][key]["domains"]:
                seen[d] += 1
        for d, c in seen.items():
            hist[key[1]][c] += 1
            hist["all"][c] += 1
    ww = {}
    for e, h in hist.items():
        tot = sum(h.values())
        ww[e] = {"pairs_full_coverage": sum(1 for k2 in full if e == "all" or k2[1] == e),
                 "distinct_triples": tot, "weeks_present_histogram": {str(i): h[i] for i in range(1, 7)},
                 "one_week": rate(h[1], tot), "all_six": rate(h[6], tot)}
    # Same thing weighted by appearances: what share of all citation slots were one-week wonders?
    apps = sum(c * n for c, n in hist["all"].items())
    ww["all"]["slots_total"] = apps
    ww["all"]["slots_from_one_week"] = rate(hist["all"][1], apps)
    ww["all"]["slots_from_all_six"] = rate(6 * hist["all"][6], apps)
    res["one_week_wonders"] = ww

    # ---- F. top domains ---------------------------------------------------------------------------
    per_week = {w: Counter() for w in WEEKS}
    for w in WEEKS:
        for key, c in obs[w].items():
            for d in c["domains"]:
                per_week[w][d] += 1

    def top(w, n=10):
        # ties broken alphabetically so the list is reproducible
        return [d for d, _ in sorted(per_week[w].items(), key=lambda x: (-x[1], x[0]))[:n]]
    res["top10_by_week"] = {w: [(d, per_week[w][d]) for d in top(w)] for w in WEEKS}
    res["top10_overlap"] = {f"{a}->{b}": len(set(top(a)) & set(top(b))) for a, b in consecutive}
    total = Counter()
    for w in WEEKS:
        total.update(per_week[w])
    top20 = [d for d, _ in sorted(total.items(), key=lambda x: (-x[1], x[0]))[:20]]
    res["top20_overall"] = [(d, total[d]) for d in top20]
    by_dom = defaultdict(lambda: [0, 0])
    big = [0, 0]
    rest = [0, 0]
    for a, b in consecutive:
        for key in KEYS:
            if not (ok(obs, a, key) and ok(obs, b, key)):
                continue
            for d in obs[a][key]["domains"]:
                kept = 1 if d in obs[b][key]["domains"] else 0
                by_dom[d][0] += kept
                by_dom[d][1] += 1
                tgt = big if d in top20 else rest
                tgt[0] += kept
                tgt[1] += 1
    res["retention_top20_domains"] = rate(*big)
    res["retention_other_domains"] = rate(*rest)
    # The split above picks the top 20 from the same six weeks it then measures, which flatters them
    # (a domain cannot be cited often without being cited repeatedly). The non-circular version:
    # pick the top 20 from W36 alone, measure only the later pairs W37->W38 ... W40->W41.
    top20_w36 = [d for d, _ in sorted(per_week[WEEKS[0]].items(), key=lambda x: (-x[1], x[0]))[:20]]
    big2 = [0, 0]
    rest2 = [0, 0]
    for a, b in consecutive[1:]:
        for key in KEYS:
            if not (ok(obs, a, key) and ok(obs, b, key)):
                continue
            for d in obs[a][key]["domains"]:
                tgt = big2 if d in top20_w36 else rest2
                tgt[0] += 1 if d in obs[b][key]["domains"] else 0
                tgt[1] += 1
    res["top20_w36"] = [(d, per_week[WEEKS[0]][d]) for d in top20_w36]
    res["retention_top20_w36_later_pairs"] = rate(*big2)
    res["retention_other_w36_later_pairs"] = rate(*rest2)
    res["retention_by_top_domain"] = {d: rate(*by_dom[d]) for d in top20}
    res["distinct_domains_total"] = len(total)

    # ---- H. cross-check against the 2026-10-05 Reddit comment ---------------------------------------
    def google_link(cell):
        # The production DB's cited_domains keeps google.com for Google search/shopping links; the
        # public analysis (v2) drops them. Put it back to reproduce the database query.
        return {"google.com"} if any(urllib.parse.urlsplit(u).hostname in ("www.google.com", "google.com")
                                     for u in cell.get("raw_urls", [])) else set()
    # raw URLs are needed only here; reload them cheaply
    for w in WEEKS:
        with open(os.path.join(HERE, "raw", f"{w}.json")) as f:
            for r in json.load(f)["weeks"][0]["rows"]:
                if r["role"] == "answer":
                    obs[w][(r["queryId"], r["engine"])]["raw_urls"] = r["citedUrls"] if r["status"] == "ok" else []
    a, b = "2026-W40", "2026-W41"
    reddit = {"claimed": {"all": [631, 1429], "gemini": 0.53, "perplexity": 0.48, "openai": 0.46,
                          "claude": 0.41, "aioverviews": 0.32, "aimode": 0.32}}
    reddit["reproduced_db_rules"] = {e: rate(*pair_counts(obs, a, b, engines=[e], forward=False,
                                                          nonempty_both=True, extra=google_link))
                                     for e in ENGINES}
    reddit["reproduced_db_rules"]["all"] = rate(*pair_counts(obs, a, b, forward=False, nonempty_both=True,
                                                             extra=google_link))
    reddit["nonempty_only"] = rate(*pair_counts(obs, a, b, forward=False, nonempty_both=True))
    reddit["this_study_backward"] = rate(*pair_counts(obs, a, b, forward=False))
    reddit["this_study_forward"] = rate(*pair_counts(obs, a, b))
    res["reddit_crosscheck"] = reddit

    with open(os.path.join(HERE, "results.json"), "w") as f:
        json.dump(res, f, indent=1, sort_keys=False, default=lambda o: dict(o))

    # ---- rows.csv / urls.csv ----------------------------------------------------------------------
    for field, fname, col in (("domains", "rows.csv", "domain"), ("urls", "urls.csv", "url")):
        with open(os.path.join(HERE, fname), "w", newline="") as f:
            wr = csv.writer(f)
            wr.writerow(["week", "next_week", "same_instrument", "query_id", "question", "shape", "engine",
                         col, "present_next_week"])
            for a, b in consecutive:
                si = 1 if (a, b) in same_instrument else 0
                for key in KEYS:
                    if not (ok(obs, a, key) and ok(obs, b, key)):
                        continue
                    c = obs[a][key]
                    for x in sorted(c[field]):
                        wr.writerow([a, b, si, key[0], c["question"], c["shape"], key[1], x,
                                     1 if x in obs[b][key][field] else 0])
    print_summary(res)


def pct(r):
    return "n/a" if r["rate"] is None else f"{100 * r['rate']:.1f}%"


def ci(r):
    return f"[{100 * r['wilson_lo']:.1f}-{100 * r['wilson_hi']:.1f}%]"


def print_summary(res):
    p = res["retention"]["pooled"]
    print("Week-over-week domain retention, pooled over 5 consecutive pairs")
    for e in ENGINES + ["all", "google_surfaces", "llm_apis"]:
        r = p[e]
        extra = f"  bootstrap [{100 * r['boot_lo']:.1f}-{100 * r['boot_hi']:.1f}%]" if "boot_lo" in r else ""
        print(f"  {e:16s} {r['k']:5d}/{r['n']:5d} = {pct(r)} {ci(r)}{extra}")
    print("By pair (all engines):")
    for pair, row in res["retention"]["by_pair"].items():
        print(f"  {pair}: {row['all']['k']}/{row['all']['n']} = {pct(row['all'])}")
    print("Retention by lag (all):", {k: f"{v['all']['k']}/{v['all']['n']}={pct(v['all'])}" for k, v in res["lag"].items()})
    print("URL retention:", f"{res['urls']['pooled']['all']['k']}/{res['urls']['pooled']['all']['n']} = {pct(res['urls']['pooled']['all'])}")
    print("W36 cohort, continuous:", {k: f"{v['continuous']['k']}/{v['continuous']['n']}={pct(v['continuous'])}" for k, v in res["survival_w36_cohort"].items()})
    print("New cohorts pooled:", {k: f"{v['k']}/{v['n']}={pct(v)}" for k, v in res["survival_new_pooled"].items()})
    r = res["returns"]["pooled_any_later_week"]
    print("Dropped then returned (any later week):", f"{r['k']}/{r['n']} = {pct(r)}")
    w = res["one_week_wonders"]["all"]
    print("One-week wonders:", f"{w['one_week']['k']}/{w['one_week']['n']} = {pct(w['one_week'])}; all six {w['all_six']['k']} = {pct(w['all_six'])}")
    rr = res["reddit_crosscheck"]["reproduced_db_rules"]["all"]
    print("Reddit 631/1429 reproduced:", f"{rr['k']}/{rr['n']}")


KEYS = []

if __name__ == "__main__":
    main()
