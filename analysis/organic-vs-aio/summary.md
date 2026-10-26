# Google organic top 10 vs AI Overviews / AI Mode citations, by question shape

Promvia AI Source Index panel (40 fixed English buyer questions, global market → Google US, English). AI citations from the weekly panel runs of 2026-09-28 and 2026-10-05; Google organic top 10 fetched 2026-10-06 through DataForSEO (one live call per question). Every row behind every number is in `rows.csv` (one line per question × engine × run × cited domain) and `serp.csv` (the organic top 10 per question).

**Question:** does ranking in Google's organic top 10 predict being cited by Google's own AI surfaces for the same question?

## Definitions

- **(a) cited → top 10:** of the domains an AI answer cited, the share that also ranks in Google's organic top 10 for the same question. Unit: one (question, engine, run, cited domain).
- **(b) top 10 → cited:** of the distinct domains in the organic top 10, the share the AI answer cited. Unit: one (question, engine, run, top-10 domain), over every answer the surface gave — an answer with no sources counts (it cited none of them); a question where the surface showed nothing is excluded.
- **(c) cited → top 3:** as (a), restricted to organic ranks 1–3.
- A domain is the lowercase host with a leading `www.` removed — the rule that builds `cited_domains` — so `www.x.com` = `x.com`, but subdomains stay distinct (`blog.x.com` ≠ `x.com`) on both sides. A domain counts once per answer however many of its URLs were cited; its organic rank is its best rank in the top 10. Google's own shopping/result links (`google.com/search?…ibp=oshop`) are dropped as non-sources, as the published index does.
- Rates are `k/n = %` with a 95% Wilson interval `[low–high]` where n ≥ 10. The two runs are pooled, so n counts (question × run) observations: the same question appears up to twice per engine, which makes the intervals somewhat narrower than independent samples would.
- In `rows.csv`, `in_top10`, `organic_rank` and `in_top3` are EMPTY when that question's SERP call failed (see caveat 5): unknown, not "not ranked". `organic_rank` is also empty for a cited domain that is not on page one. Zero-citation answers have no line in `rows.csv`; they are counted in the tables below.
- Answers columns: **answers** = checks with status ok and a usable SERP; **no AI answer** = the surface showed nothing; **answer, no sources** = text without a single citation. Both are zero-citation answers.

## AI Overviews — both runs pooled

| shape | questions | answers | no AI answer | answer, no sources | (a) cited → top 10 | (b) top 10 → cited | (c) cited → top 3 | answers with ≥1 cited domain in top 10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| best | 14 | 27 | 5 | 4 | 18/77 = 23.4% [15.3–34.0] | 18/170 = 10.6% [6.8–16.1] | 10/77 = 13.0% [7.2–22.3] | 10/18 |
| alternatives | 8 | 16 | 2 | 0 | 26/96 = 27.1% [19.2–36.7] | 26/105 = 24.8% [17.5–33.8] | 12/96 = 12.5% [7.3–20.6] | 11/14 |
| compare | 8 | 16 | 1 | 3 | 21/87 = 24.1% [16.4–34.1] | 21/109 = 19.3% [13.0–27.7] | 9/87 = 10.3% [5.5–18.5] | 9/12 |
| howto-buy | 8 | 16 | 1 | 1 | 25/103 = 24.3% [17.0–33.4] | 25/116 = 21.6% [15.0–29.9] | 13/103 = 12.6% [7.5–20.4] | 13/14 |
| **all** | 38 | 75 | 9 | 8 | 90/363 = 24.8% [20.6–29.5] | 90/500 = 18.0% [14.9–21.6] | 44/363 = 12.1% [9.2–15.9] | 43/58 |

## AI Mode — both runs pooled

| shape | questions | answers | no AI answer | answer, no sources | (a) cited → top 10 | (b) top 10 → cited | (c) cited → top 3 | answers with ≥1 cited domain in top 10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| best | 14 | 28 | 1 | 8 | 19/110 = 17.3% [11.3–25.4] | 19/202 = 9.4% [6.1–14.2] | 6/110 = 5.5% [2.5–11.4] | 9/19 |
| alternatives | 8 | 16 | 3 | 2 | 5/33 = 15.2% [6.7–30.9] | 5/96 = 5.2% [2.2–11.6] | 3/33 = 9.1% [3.1–23.6] | 3/11 |
| compare | 8 | 16 | 0 | 1 | 15/64 = 23.4% [14.7–35.1] | 15/116 = 12.9% [8.0–20.2] | 10/64 = 15.6% [8.7–26.4] | 10/15 |
| howto-buy | 8 | 16 | 0 | 11 | 11/24 = 45.8% [27.9–64.9] | 11/124 = 8.9% [5.0–15.2] | 7/24 = 29.2% [14.9–49.2] | 4/5 |
| **all** | 38 | 76 | 4 | 22 | 50/231 = 21.6% [16.8–27.4] | 50/538 = 9.3% [7.1–12.0] | 26/231 = 11.3% [7.8–16.0] | 26/50 |

## Both surfaces together — both runs pooled

| shape | questions | answers | no AI answer | answer, no sources | (a) cited → top 10 | (b) top 10 → cited | (c) cited → top 3 | answers with ≥1 cited domain in top 10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| best | 14 | 55 | 6 | 12 | 37/187 = 19.8% [14.7–26.1] | 37/372 = 9.9% [7.3–13.4] | 16/187 = 8.6% [5.3–13.4] | 19/37 |
| alternatives | 8 | 32 | 5 | 2 | 31/129 = 24.0% [17.5–32.1] | 31/201 = 15.4% [11.1–21.1] | 15/129 = 11.6% [7.2–18.3] | 14/25 |
| compare | 8 | 32 | 1 | 4 | 36/151 = 23.8% [17.7–31.2] | 36/225 = 16.0% [11.8–21.4] | 19/151 = 12.6% [8.2–18.8] | 19/27 |
| howto-buy | 8 | 32 | 1 | 12 | 36/127 = 28.3% [21.2–36.7] | 36/240 = 15.0% [11.0–20.1] | 20/127 = 15.7% [10.4–23.1] | 17/19 |
| **all** | 38 | 151 | 13 | 30 | 140/594 = 23.6% [20.3–27.1] | 140/1038 = 13.5% [11.5–15.7] | 70/594 = 11.8% [9.4–14.6] | 69/108 |

## Time gap: (a) per run

The SERPs are from 2026-10-06; the AI citations from 2026-09-28 and 2026-10-05 — a gap of 1 and 8 days. If the organic top 10 drifted enough in a week to matter, (a) should be visibly lower for the older run.

| run | engine | best | alternatives | compare | howto-buy | **all** |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-09-28 | AI Overviews | 8/42 = 19.0% [10.0–33.3] | 12/52 = 23.1% [13.7–36.1] | 4/44 = 9.1% [3.6–21.2] | 11/47 = 23.4% [13.6–37.2] | 35/185 = 18.9% [13.9–25.2] |
| 2026-09-28 | AI Mode | 12/35 = 34.3% [20.8–50.8] | 1/16 = 6.3% [1.1–28.3] | 7/32 = 21.9% [11.0–38.8] | 9/19 = 47.4% [27.3–68.3] | 29/102 = 28.4% [20.6–37.8] |
| 2026-09-28 | both | 20/77 = 26.0% [17.5–36.7] | 13/68 = 19.1% [11.5–30.0] | 11/76 = 14.5% [8.3–24.1] | 20/66 = 30.3% [20.6–42.2] | 64/287 = 22.3% [17.9–27.5] |
| 2026-10-05 | AI Overviews | 10/35 = 28.6% [16.3–45.1] | 14/44 = 31.8% [20.0–46.6] | 17/43 = 39.5% [26.4–54.4] | 14/56 = 25.0% [15.5–37.7] | 55/178 = 30.9% [24.6–38.0] |
| 2026-10-05 | AI Mode | 7/75 = 9.3% [4.6–18.0] | 4/17 = 23.5% [9.6–47.3] | 8/32 = 25.0% [13.3–42.1] | 2/5 = 40.0% (n<10) | 21/129 = 16.3% [10.9–23.6] |
| 2026-10-05 | both | 17/110 = 15.5% [9.9–23.4] | 18/61 = 29.5% [19.6–41.9] | 25/75 = 33.3% [23.7–44.6] | 16/61 = 26.2% [16.8–38.4] | 76/307 = 24.8% [20.3–29.9] |

## Sensitivity

- **Subdomains collapsed** to the registrable domain on both sides (`blog.x.com` = `x.com`, a last-two-labels rule with a short list of two-part suffixes): (a) 142/594 = 23.9% [20.7–27.5] vs 140/594 = 23.6% [20.3–27.1] with the codebase rule; (c) 71/594 = 12.0% [9.6–14.8] vs 70/594 = 11.8% [9.4–14.6].
- **Google shopping links kept as a cited domain** (`google.com`, never an organic result): adds 20 cited-domain observations to the denominator of (a), all misses — (a) would read 140/614 = 22.8% [19.7–26.3].

## The SERPs

| shape | SERPs ok | with an ai_overview item | of which a deferred placeholder | organic results (mean, min–max) | distinct top-10 domains (mean) |
| --- | --- | --- | --- | --- | --- |
| best | 14/16 | 13 | 10 | 8.2 (6–9) | 7.5 |
| alternatives | 8/8 | 6 | 6 | 8.1 (7–9) | 7.5 |
| compare | 8/8 | 8 | 8 | 7.6 (7–8) | 7.3 |
| howto-buy | 8/8 | 8 | 7 | 7.9 (7–9) | 7.8 |
| **all** | 38/40 | 35 | 31 | 8.0 (6–9) | 7.5 |

Called without `load_async_ai_overview` (production's AI Overviews engine sets it): the presence count is what Google put in the first response, so it can undercount AI Overviews that load late. Total DataForSEO cost reported by the responses: $0.1000, including 10 failed attempt(s) that were re-bought.

**"Top 10" is page one.** One call returns one Google page, which held 6–9 organic results here (the rest of the page is AI Overview, People also ask, forums, video, products). "Top 10" in this write-up means the organic results ranked ≤ 10 that the call returned; no SERP had ten.

## Caveats

1. **Time gap.** Organic results fetched 2026-10-06; citations from 2026-09-28 and 2026-10-05. See the per-run table above for how much that matters.
2. **One sample each.** One SERP per question and one AI answer per engine per question per run. Google personalises and rotates both; a single fetch is a snapshot, not a distribution.
3. **Location.** The panel is "global"; DataForSEO needs a location, so both the panel's AI checks and these SERPs use Google US in English (`location_code` 2840).
4. **Partial run.** The 2026-10-05 run is marked partial. For these two engines it lost 1 check(s): AI Overviews — "Best credit card for airline miles with no foreign transaction fee" (2026-10-05). A failed check is left out, never counted as "cited nothing".
5. **SERP coverage.** 38 of 40 SERPs usable. Unusable: mkt-05 (DataForSEO (Google organic (research)) task error 40101: Internal SE Server Error.); trav-01 (DataForSEO (Google organic (research)) task error 40101: Internal SE Server Error.) — those questions are excluded from every rate.
6. **Shapes are unequal.** The panel has 16 "best" questions and 8 of each other shape, so the "best" row has twice the sample of the others.
7. **Domain, not URL.** A match means the same domain, not the same page. A domain cited for one article and ranking for another counts as overlap.
