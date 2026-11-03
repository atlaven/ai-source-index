# Do AI engines cite the same sources? Cross-engine overlap in the AI Source Index, W36 to W45 2026

How often the six answer engines of the panel (ChatGPT, Perplexity, Gemini, Claude, Google AI Overviews, Google AI Mode) cite the same domain for the same question in the same week. Ten weekly runs, 3 September to 2 November 2026, 40 fixed questions. CC BY 4.0.

Published as a guide: https://promvia.app/blog/ai-engines-cite-different-sources (Turkish: https://promvia.app/tr/blog/yapay-zeka-motorlari-farkli-kaynaklar).

## Input

`data/raw/2026-W36.json` … `2026-W45.json` in this repository. They are the same rows as https://promvia.app/api/public/ai-source-index/rows?week=2026-W36 … W45. We checked that row for row on 2026-11-03.

## Definitions

- **Cell:** one question in one weekly run. 40 questions × 10 runs = 400 cells.
- **Taking part:** an engine takes part in a cell only if its row has `status: ok` and a non-empty `domains` list. Otherwise it is left out of that cell. It is not counted as disagreeing.
  - 37 rows failed.
  - 295 rows were ok but listed no domain. 124 of these are AI Mode, and 36 of those linked only to Google Shopping results.
  - Bing (the `proxy` role) is left out entirely.
- **Domain:** taken from `domains`. A domain counts once per row, as the index already dedupes it.
- **Pairwise overlap:** for each pair of engines, over the cells where both take part, the sum of |A∩B| divided by the sum of |A∪B|.
- **Engines citing a domain:** for each distinct domain in a cell, the number of engines taking part that cited it. This is counted over cells where at least four engines take part (385 cells). The same count is also given over cells where all six take part (177 cells).
- **Solo share:** the domains an engine cited in a cell that no other engine in that cell cited, divided by all the domains it cited there. Counted over cells with at least four engines.
- **Week over week:** the same pooled overlap for one engine, comparing a question in one run with the same question in the next run.

## Files

| File | What it is |
|---|---|
| `cross_engine.py` | The analysis (Python 3, standard library only). Run it as `python3 cross_engine.py ../../data/raw > results.json`. |
| `per_week.py` | The share for each week and the Wilson intervals of the pooled shares. Run it as `python3 per_week.py ../../data/raw > per_week.json`. |
| `recount.mjs` | An independent recount in Node, written separately from the definitions above. Run it as `node recount.mjs` (it reads `../../data/raw` and writes `recount-output.json`). |
| `results.json`, `per_week.json`, `recount-output.json` | The outputs for W36 to W45. The two scripts agree on every value. |
| `results_without_w42_w44.json`, `per_week_without_w42_w44.json` | The same Python analysis without runs W42, W43 and W44. From 15 to 28 October our data provider returned Google AI Overviews' and AI Mode's source lists cut to about three domains. To reproduce these files, copy only the other seven week files into a directory and point the scripts at it. |

## Headline numbers

- Of 10,634 domain citations (one domain, one question, one week), 8,452 came from only one engine: **79.5%**.
  - The share was between 75.2% and 82.8% in every week.
  - Over cells where all six engines took part, it was 77.0% (4,005 of 5,202).
  - Only 10 domains were cited by all six engines.
- **ChatGPT's solo share was 76.8%** (1,847 of 2,404).
  - Its pairwise overlap with each of the other engines was 3.9% to 5.4%.
- The closest pair of engines was AI Overviews and AI Mode, at **14.9%** (267 of 1,794).
- Each engine against itself one week later: **27.3% to 38.7%**.
- Without runs W42 to W44:
  - the one-engine share is 78.4% (5,847 of 7,456);
  - ChatGPT's solo share is 76.7%.

## Caveats

- **Domains, not pages.** Every overlap here is an upper bound for overlap at the level of the page.
- **ChatGPT changed model.** It ran on gpt-4o-mini until 2026-10-20 and on gpt-5-mini from 2026-10-21. Only runs W44 and W45 are on the new model.
- **One sample per cell.** Each engine answers each question once per week, through the engines' APIs and our data provider, in English, for the US.
- **The observations are not independent.** The same domains recur within a question across weeks. So the Wilson intervals in `per_week.json` are too narrow, and the guide gives the spread across the ten weeks instead.
