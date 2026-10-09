# How long does an AI citation last? Week-over-week persistence, AI Source Index W36–W41 2026

Date: 2026-10-07. Every number below is a line of `results.json`, written by `persistence.py` and
re-derived independently by `crosscheck.mjs` (see "Second derivation"). Percentages are
`k / n` with a 95% Wilson interval in brackets unless stated otherwise.

## Data

- Source: the public rows of the Promvia AI Source Index,
  `https://promvia.app/api/public/ai-source-index/rows?week=<week>`, fetched 2026-10-07 for every
  week the API lists (`weeksAvailable`): 2026-W36, W37, W38, W39, W40, W41. Saved unmodified in
  `raw/`. Licence CC BY 4.0. `analysisVersion` 2.
- Panel: the same 40 fixed English buyer questions in every week (same `queryId`, same text, same
  shape: 16 best, 8 alternatives, 8 compare, 8 how-to-buy), checked against the API surfaces of six
  answer engines: Perplexity, ChatGPT (OpenAI API, gpt-4o-mini, web search), Gemini, Claude,
  Google AI Overviews, Google AI Mode. The Bing organic proxy (`role: proxy`) is not an answer
  engine and is excluded everywhere (it failed `wrong-question` in all 40 cells W36–W39 and left
  the engine set from W40).
- Runs captured (`capturedAt`): 3 Sep, 7 Sep, 14 Sep, 21 Sep, 28 Sep, 5 Oct 2026. Six weekly runs
  over 32 days; the first gap (W36→W37) is 4 days, the others 7.
- One sample per engine per question per run. The index page states this, and the run snapshots
  (`sampleTarget = 1` for every engine in all six runs) confirm it. There are no repeat samples
  inside a week, so a within-week noise floor cannot be measured from these rows.
- Failed rows: W38 Claude 29 of 40 (`other`); W41 AI Overviews 1 of 40 (`provider-error`). No other
  answer-engine row failed.
- OK rows that cited no domain at all (an answer with no linkable source, or only Google shopping
  links, which the public analysis drops): AI Mode 12, 10, 12, 14, 16, 13 of 40 in W36…W41;
  AI Overviews 3, 4, 7, 3, 8, 10; Claude 6, 7, 2, 4, 6, 7; Gemini 3, 5, 9, 3, 3, 3; ChatGPT 1 (W41).
- Domains cited per run (all six engines, counted once per answer): 1,416 / 1,414 / 1,220 / 1,575 /
  1,477 / 1,510. 2,261 distinct domains over the six runs.
- Instrument fingerprint: `v1-40-5069136b` (W36–W37), `v1-40-19f59073` (W38–W39), `v1-40-6c41eb63`
  (W40–W41). The questions did not change. The W38 change is the week the provider configuration
  started to be frozen into the fingerprint; the run snapshots show the same configuration for all
  six engines from W38 to W41, and W36–W37 predate the field, so a provider change between W37 and
  W38 cannot be ruled out from the public data. The W40 change is the Bing proxy leaving the engine
  set. `collectorVersion` is 2 for W36–W40 and 3 for W41; the v3 change concerns the Copilot lane
  only, which is excluded here. Same-instrument pairs: W36→W37, W38→W39, W40→W41.

## Method

- Unit of observation: one domain cited in one answer: (run, question, engine, domain). `domains`
  in the public rows is already deduplicated per (question, engine) and derived from `citedUrls`
  (grounding redirects and Google search/shopping links resolve to no domain and drop out).
- A (question, engine) pair enters the comparison of run a with run b only if its row is `ok` in
  BOTH runs. A failed row is not "not cited": the pair leaves that comparison's denominator.
  Exclusions per consecutive pair: W37→W38 and W38→W39 lose 29 Claude pairs each; W40→W41 loses 1
  AI Overviews pair; W36→W37 and W39→W40 lose none. An `ok` answer that cited nothing stays in: a
  domain cited in run a whose pair answered with no sources in run b counts as not retained.
- Retention (forward): of the domains cited for a question by an engine in run t, the share cited
  again for the same question by the same engine in run t+1. Pooled over the five consecutive pairs
  by summing numerators and denominators.
- Recurrence (backward, the Reddit metric): of the domains cited in run t+1, the share also cited in
  run t.
- URL level: cited URLs normalised (host lowercased without `www.`, no scheme, no trailing slash,
  `utm_*` and `srsltid` parameters dropped, YouTube's `t=` timestamp dropped, remaining parameters
  sorted), keeping only URLs whose host is one of the row's `domains` (the same exclusion rule).
- Survival, two cohorts:
  - W36 cohort: everything cited in W36 (left-censored: we cannot see when it started). Survival to
    k = present in every run W37…W36+k. Requires the pair `ok` in all runs W36…W36+k.
  - First-seen cohorts: a citation is "new" in run t (t = W37…W41) if it was absent in every earlier
    run and the pair was `ok` in all runs W36…t. Survival to k = present in every run t+1…t+k;
    a pair whose row fails later is censored from that point. Pooled across cohorts per k.
- Returns: a drop is a domain cited in run t and not in run t+1 (both `ok`). Returned = cited again
  in any later `ok` run. Only drops with at least one later run are counted.
- One-week wonders: over the 210 (question, engine) pairs `ok` in all six runs, every distinct
  (question, engine, domain) triple ever cited, by how many of the six runs it appeared in.
- Intervals: Wilson treats every domain-observation as independent. They are not: domains recur
  within a question and across runs. A cluster bootstrap that resamples the 40 questions with
  replacement (2,000 draws, seed 20261007) is reported beside the headline rates; it is the more
  honest interval. The bootstrap has a single implementation (persistence.py) and is not part of
  the second derivation.

## Results

### 1. Week-over-week retention

Pooled over five consecutive pairs, all six engines:

- **48.0%** of cited domains were cited again the next run: 3,335 / 6,947 [46.8–49.2%];
  question-cluster bootstrap [46.2–49.8%]. Equivalently, 3,612 / 6,947 = 52.0% were not cited again
  the next run (the article's "about half ... were not cited again the following week").

By pair (all engines):

| Pair | Retained | Rate | Note |
|---|---|---|---|
| W36→W37 | 782 / 1,416 | 55.2% [52.6–57.8] | 4-day gap |
| W37→W38 | 580 / 1,262 | 46.0% [43.2–48.7] | 29 Claude pairs excluded; instrument changed |
| W38→W39 | 645 / 1,220 | 52.9% [50.1–55.7] | 29 Claude pairs excluded |
| W39→W40 | 703 / 1,575 | 44.6% [42.2–47.1] | instrument changed (Bing proxy removed) |
| W40→W41 | 625 / 1,474 | 42.4% [39.9–44.9] | 1 AI Overviews pair excluded |

By engine, pooled (Wilson; bootstrap):

| Engine | Retained | Rate | Bootstrap |
|---|---|---|---|
| Claude | 563 / 1,033 | 54.5% [51.5–57.5] | [48.0–60.7] |
| Perplexity | 537 / 1,000 | 53.7% [50.6–56.8] | [50.6–56.4] |
| ChatGPT | 611 / 1,300 | 47.0% [44.3–49.7] | [43.0–51.0] |
| Gemini | 937 / 2,029 | 46.2% [44.0–48.4] | [42.4–49.7] |
| AI Overviews | 502 / 1,123 | 44.7% [41.8–47.6] | [40.3–48.9] |
| AI Mode | 185 / 462 | 40.0% [35.7–44.6] | [32.9–46.9] |

- Google's two surfaces together 687 / 1,585 = 43.3% [40.9–45.8]; the four LLM APIs together
  2,648 / 5,362 = 49.4% [48.0–50.7].
- The engine order does not hold from one pair to the next. Perplexity ranged from 65.3%
  (139/213, W36→W37) to 33.2% (69/208, W39→W40); AI Overviews from 59.9% (136/227) to 26.6%
  (68/256); Claude from 41.2% (124/301, W40→W41) to 75.0% (57/76, W38→W39, 11 pairs only).
- Same-instrument pairs only (W36→W37, W38→W39, W40→W41): 2,052 / 4,110 = 49.9% [48.4–51.5].
- Sensitivity, answers with no sources: counting only pairs where both answers cited at least one
  domain, retention is 3,335 / 6,431 = 51.9% [50.6–53.1]; AI Mode rises from 40.0% to
  185 / 377 = 49.1% [44.1–54.1]. Much of AI Mode's lower number is answers that cited nothing the
  next week, not a different source.

### 2. URL level

- Same URL cited again the next run: 3,201 / 7,739 = 41.4% [40.3–42.5]; bootstrap [39.3–43.3].
- By engine: Claude 577/1,119 = 51.6%; Perplexity 540/1,062 = 50.8%; ChatGPT 585/1,365 = 42.9%;
  AI Overviews 491/1,315 = 37.3%; Gemini 855/2,333 = 36.6%; AI Mode 153/545 = 28.1%
  (not part of the second derivation; not used in the article).
- When a domain was retained, at least one of the same URLs was cited again in 3,032 / 3,335 =
  90.9% [89.9–91.8] of cases. The churn is in which sites are cited, much less in which page of a
  site that stays.

### 3. Retention by lag (decay or noise?)

Share of domains cited in run t that are cited in run t+L (not necessarily in between), all engines:

| Lag L (runs) | Pairs pooled | Retained | Rate |
|---|---|---|---|
| 1 | 5 | 3,335 / 6,947 | 48.0% [46.8–49.2] |
| 2 | 4 | 2,322 / 5,465 | 42.5% [41.2–43.8] |
| 3 | 3 | 1,726 / 4,045 | 42.7% [41.2–44.2] |
| 4 | 2 | 1,060 / 2,825 | 37.5% [35.8–39.3] |
| 5 | 1 | 530 / 1,416 | 37.4% [34.9–40.0] |

Reading: if each week's citations were a noisy draw from a fixed pool, this curve would be flat at
the lag-1 level. It falls by about 10 points over four more runs, so there is some real drift; but
most of the loss happens at the first step and the curve then flattens, which is what heavy
run-to-run resampling looks like. The pairs pooled at each lag differ (lag 5 is W36→W41 only), so
this is indicative, not a decomposition. Without repeat samples inside a run we cannot measure the
noise floor directly.

### 4. Survival

W36 cohort (1,416 domain citations; 1,259 from k = 2 on, because Claude's W38 failures remove
those pairs):

| After k runs | Present in every run since W36 | Present in that run (gaps allowed) |
|---|---|---|
| 1 (W37) | 782 / 1,416 = 55.2% [52.6–57.8] | same |
| 2 (W38) | 410 / 1,259 = 32.6% [30.0–35.2] | 563 / 1,259 = 44.7% [42.0–47.5] |
| 3 (W39) | 311 / 1,259 = 24.7% [22.4–27.2] | 611 / 1,259 = 48.5% [45.8–51.3] |
| 4 (W40) | 197 / 1,259 = 15.6% [13.7–17.8] | 448 / 1,259 = 35.6% [33.0–38.3] |
| 5 (W41) | 139 / 1,259 = 11.0% [9.4–12.9] | 458 / 1,259 = 36.4% [33.8–39.1] |

First-seen citations (cohorts W37–W40; W41's 391 have no later run), pooled:

| Still present, every run, after | Rate |
|---|---|
| 1 run | 533 / 1,950 = 27.3% [25.4–29.4] |
| 2 runs | 193 / 1,497 = 12.9% [11.3–14.7] |
| 3 runs | 69 / 1,058 = 6.5% [5.2–8.2] |
| 4 runs | 26 / 568 = 4.6% [3.1–6.6] |

Cohort sizes: W37 632, W38 487, W39 438, W40 453, W41 391. Per-cohort "back next run": W37
170/573 = 29.7%, W38 158/487 = 32.4%, W39 106/438 = 24.2%, W40 99/452 = 21.9%. The W37 cohort has
only one earlier run behind it, so some of its "new" citations are returns from before W36.

Conditional (the longer it has lasted, the likelier it lasts), first-seen cohorts pooled:

- present in 1 run → present in the next: 533 / 1,950 = 27.3% [25.4–29.4]
- present in 2 runs in a row → a third: 193 / 434 = 44.5% [39.9–49.2]
- present in 3 in a row → a fourth: 69 / 146 = 47.3% [39.3–55.3]
- present in 4 in a row → a fifth: 26 / 39 = 66.7% [51.0–79.4] (small)

### 5. Returns after a drop

- Of domains that dropped out between two runs, 1,092 / 2,761 = 39.6% [37.7–41.4] were cited again
  in a later run of the window; 682 / 2,697 = 25.3% [23.7–27.0] were back in the very next run.
- The share grows with the number of later runs available: dropped W36→W37 (4 later runs)
  359 / 634 = 56.6%; W37→W38 (3) 309 / 682 = 45.3%; W38→W39 (2) 215 / 575 = 37.4%; W39→W40 (1)
  209 / 870 = 24.0%.

### 6. One-week wonders

Over the 210 (question, engine) pairs `ok` in all six runs (all 40 questions for Perplexity,
ChatGPT, Gemini and AI Mode; 39 for AI Overviews; 11 for Claude), 3,592 distinct
(question, engine, domain) triples were cited at least once:

- cited in exactly one of six runs: 1,781 / 3,592 = 49.6% [47.9–51.2]
- cited in all six: 139 / 3,592 = 3.9% [3.3–4.6]
- histogram (runs present: triples): 1: 1,781; 2: 717; 3: 444; 4: 292; 5: 219; 6: 139
- Weighted by citation slots (7,644 domain citations in those pairs), one-week wonders are
  1,781 / 7,644 = 23.3% of all citations and the all-six triples are 834 / 7,644 = 10.9%.
- By engine (one week only): AI Mode 201/331 = 60.7%; ChatGPT 395/782 = 50.5%; Gemini
  560/1,131 = 49.5%; AI Overviews 293/600 = 48.8%; Perplexity 233/522 = 44.6%; Claude 99/226 =
  43.8% (11 pairs). Not part of the second derivation; not used in the article.

### 7. Top domains

- Top 10 domains of each run (by the number of answers citing them, all six engines): youtube.com
  and reddit.com were first and second in all six runs; forbes.com third in all six. Carry-over
  of the top 10 between consecutive runs: 9, 9, 9, 7, 7 of 10.
- The top 20 domains of W36 (ties at 5 citations broken alphabetically) were retained at
  604 / 1,007 = 60.0% [56.9–63.0] in the later pairs (W37→W38 … W40→W41), against
  1,949 / 4,524 = 43.1% [41.6–44.5] for every other domain. (Picking the top 20 from all six runs
  and measuring the same runs gives 801/1,299 = 61.7% vs 2,534/5,648 = 44.9%, but that version is
  circular and is not used.)
- Most-cited over six runs: youtube.com 393 answer-citations, reddit.com 306, forbes.com 114,
  techradar.com 88, nerdwallet.com 68, zapier.com 68. Per-domain retention (pooled pairs):
  youtube.com 220/329 = 66.9%, reddit.com 149/250 = 59.6%, forbes.com 48/90 = 53.3%
  (not part of the second derivation; not used in the article).

## Cross-check: the 44% (631 of 1,429) quoted on Reddit on 2026-10-05

The comment said: "Same question, same engine, last week vs this week: 44% of the domains cited this
week were also cited last week (631 of 1,429). Gemini 53%, Perplexity 48%, ChatGPT 46%, Claude 41%,
AI Overviews and AI Mode both 32%."

- Week pair: W40 (28 Sep) → W41 (5 Oct). It was computed by a SQL query on the production database
  (`citation_checks.cited_domains`, the two most recent panel runs), not on the public rows.
- **It reproduces exactly from the public rows** (631 / 1,429; Perplexity 84/174 = 48.3%, ChatGPT
  119/256 = 46.5%, Gemini 207/391 = 52.9%, Claude 124/306 = 40.5%, AI Overviews 60/187 = 32.1%,
  AI Mode 37/115 = 32.2%) once two rules of that query are applied:
  1. It kept only (question, engine) pairs where BOTH runs cited at least one domain (its `pairs`
     CTE is an intersect of pairs that have domains). An answer that cited nothing in either week
     dropped out of the denominator instead of counting as "not cited".
  2. It counted `google.com` as a cited domain. The database's `cited_domains` keeps Google's own
     search/shopping links as `google.com`; the public analysis (v2) drops them. Under rule 1 this
     adds 5 AI Overviews and 30 AI Mode domain citations to the W41 denominator, and lets 4 more
     AI Mode pairs in.
- Perplexity and ChatGPT are identical under both methods; Gemini and Claude differ by rule 1
  only; AI Overviews and AI Mode need both rules. With rule 1 only (public domains):
  625 / 1,394 = 44.8%.
- Under this study's rules, the same pair is 625 / 1,510 = **41.4%** [38.9–43.9] backward (the
  comment's direction) and 625 / 1,474 = 42.4% forward. The comment's direction (share of this
  week's domains seen last week) and this study's headline direction (share of last week's domains
  seen this week) differ only in the denominator.
- The comment's engine order (Gemini most stable at 53%) is one week pair. Pooled over five pairs
  Gemini is 46.2% and fourth of six; Claude (54.5%) and Perplexity (53.7%) are highest.
- Verdict: the 44% was a correct count of the database under its own rules, but it is not the
  public-row number, and the engine ranking in that comment does not survive pooling.

## Second derivation

`crosscheck.mjs` (Node, no dependencies) re-reads `raw/*.json` and recomputes the numbers with a
different code path: every citation is flattened to one string key `run|question|engine|item` in
a single Set, `ok` cells are a second Set, and every rate is a loop of membership tests (survival is
a walk forward per citation; one-week wonders count keys per triple straight from the Set). It
re-implements the URL normaliser by hand (regex split and its own percent-encoder rather than the
URL class) and the Wilson interval, then compares each count and interval with `results.json`.

Result (`crosscheck-output.txt`): **All 98 values match**: 87 counts with their Wilson intervals
(every headline rate, all 30 per-pair × per-engine cells, the lag curve, both survival tables,
conditional survival, returns, one-week wonders, top-20 retention, URL retention, the
same-URL share, and the Reddit reproduction per engine) plus 11 plain values (top-10 carry-over,
AI Mode source-less answers per run). No mismatch had to be resolved.

A third, partial check: summing `present_next_week` in `rows.csv` gives 3,335 / 6,947 overall and
the same per-engine counts as the table above. And the Reddit reproduction is itself an outside
check of the plumbing: a SQL query on the database, written on 5 Oct for another purpose, and this
code on the public rows agree to the citation once the two rule differences are applied.

Not re-derived: the cluster-bootstrap intervals (one implementation), and the per-engine figures
marked as such above.

## Limits

- Weekly resolution. One run a week (the first gap 4 days) cannot see what happened in between: a
  domain "retained" may have dropped and returned inside the week, and a "drop" may be a
  one-day absence.
- One sample per engine per question per run. Engines are nondeterministic; a single drop may be
  noise rather than decay. With no repeat samples inside a run, the noise floor is not measured;
  the lag curve and the 25.3% next-run return rate are indirect evidence that much of the
  turnover is resampling.
- One fixed panel: 40 English buyer questions in a handful of categories, US location for the
  Google surfaces. Not a sample of all questions, languages or markets.
- API surfaces, not the consumer apps. ChatGPT is gpt-4o-mini with web search through the API;
  Gemini, Claude and Perplexity are their APIs; AI Overviews and AI Mode are read from Google
  results through a SERP provider. Consumer apps with memory, location and personalisation may
  behave differently.
- Domain counting follows the public analysis v2: subdomains stay separate (blog.x.com ≠ x.com),
  Google's own shopping/search links drop out, an answer citing only those has zero domains.
- Claude's W38 failures remove 29 of 40 Claude pairs from two week pairs and from every survival
  measure that spans W38; Claude's pooled and survival numbers rest on fewer questions.
- The instrument fingerprint changed twice (see Data). The same-instrument subset (49.9%) is close
  to the pooled figure (48.0%).
- Wilson intervals understate uncertainty because observations cluster by question; use the
  bootstrap intervals for the headline and per-engine rates.
- Six runs over 32 days. "How long a citation lasts" beyond five weeks is not observable here.

## Outside context (not comparable one-to-one)

- Profound, "The half-life of an AI citation is 11 days" (Davis McCain, 30 Sep 2026):
  883,000 pages, seven engines, 8 Sep 2025 – 8 Sep 2026, daily citation share per page smoothed
  over 14 days; half-life = days from the peak until share falls below half the peak and stays
  there 14 days. Median 11 days. Unit is a page's share of all tracked citations, not
  presence for a fixed question. No raw rows published.
  https://www.tryprofound.com/blog/the-half-life-of-an-ai-citation-is-11-days
- Profound, "Citation decay" (29 Sep 2026): product feature announcement using the same
  definitions. https://tryprofound.com/blog/citation-decay
- Writesonic, "Introducing Citation Decay in Writesonic" (Samanyou Garg, 24 Sep 2026): a product
  feature with statuses (rising, holding, declining, faded, recovering, dormant, new) and the same
  peak-to-half "half-life" definition; publishes no study numbers on decay.
  https://writesonic.com/blog/citation-decay

## Files

- `raw/2026-W36.json` … `raw/2026-W41.json`: the public rows, unmodified.
- `persistence.py`: the analysis (Python 3, standard library). Writes `results.json`, `rows.csv`,
  `urls.csv`.
- `crosscheck.mjs`: the second derivation (Node 18+). Output in `crosscheck-output.txt`.
- `rows.csv`: one line per domain observation used in a consecutive-pair comparison (6,947 lines):
  week, next_week, same_instrument, query_id, question, shape, engine, domain, present_next_week.
- `urls.csv`: the same at URL level (7,739 lines).
