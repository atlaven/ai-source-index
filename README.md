# AI Source Index

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23651937.svg)](https://doi.org/10.5281/zenodo.23651937)


Which websites do AI answer engines cite, and do they keep citing them?

Every week we ask the same 40 buyer questions to six answer engines (ChatGPT, Perplexity, Gemini, Claude, Google AI Overviews and Google AI Mode) and record every source each answer cites. This repository holds the raw rows of every published week, flat CSVs built from them, and the scripts behind our analyses, so anyone can check a number instead of trusting it.

Live index: https://promvia.app/ai-source-index

Discussion: https://www.reddit.com/r/AISourceIndex/ (each Monday's results, a question of the day from these rows, and corrections)

## What is in here

| Path | What it is |
|---|---|
| `data/raw/<week>.json` | The public API response for that week, unmodified. |
| `data/citations.csv` | One row per engine answer and cited domain. |
| `data/cited_urls.csv` | One row per engine answer and cited URL. |
| `scripts/fetch.py` | Rebuilds everything in `data/` from the API. Standard library only. |
| `analysis/persistence/` | How long a citation lasts, week over week (W36 to W41 2026): a Python analysis, an independent Node cross-check, and their outputs. |
| `analysis/persistence-2026-11/` | The same persistence analysis over eleven weekly runs (W36 to W46 2026, 3 Sep to 9 Nov): the unchanged scripts with the week list extended, the raw rows, `results.json`, `rows.csv`, `urls.csv` and both outputs (the Node recount agrees on all 168 values). |
| `analysis/question-shapes/` | Which sources each kind of buyer question cites (best, alternatives, compare, how to choose), W36 to W41 2026: `shapes.py`, an independent Node cross-check, `results.json`, a per-shape domain table and `summary.md`. |
| `analysis/aio-aimode/` | Google AI Overviews and AI Mode, W36 to W41 2026: answers with no sources, per-question switching and the overlap between the two surfaces. A Python analysis, an independent Node cross-check and their outputs. |
| `analysis/organic-vs-aio/` | Does Google's organic top 10 predict being cited by AI Overviews and AI Mode for the same question? 40 questions, runs of 28 Sep and 5 Oct 2026, organic top 10 of 6 Oct: `rows.csv`, `serp.csv`, `summary.md`. |
| `analysis/server-logs-citations/` | promvia.app's own server logs joined to ChatGPT and Perplexity citations, 26 Aug to 5 Oct 2026: what the engines' crawlers did around a citation. `rows.csv`, `recount.py`, `summary.md`. |
| `analysis/cross-engine/` | Do the six engines cite the same sources for the same question? Ten weekly runs, W36 to W45 2026: pairwise overlap, how many engines cite each domain, each engine's solo share and its week-over-week self-overlap. `cross_engine.py`, `per_week.py`, an independent Node recount and their outputs. |
| `studies/first-eight-weeks/` | The first-eight-weeks study (W36 to W43 2026): `rows.csv` (11,667 rows), `results.json` (every published number) and `recount.py`, which rebuilds the numbers and prints `ALL MATCH`. Report: https://promvia.app/ai-source-index/first-eight-weeks |

Columns in both CSVs: `week, captured_at, instrument, query_id, question, shape, engine, role, status, failure_class`, then `domain` or `url`.

- `shape` is the kind of question: `best`, `alternatives`, `compare` or `howto-buy`.
- `role` is `answer` for an answer engine and `proxy` for Bing, which stood in for Copilot in the early weeks. Leave proxy rows out of any total across engines.
- `status` is `ok` or `failed`. A failed answer is coverage, never a citation; `failure_class` says why, from a closed set.
- An answer that cited nothing (or failed) still has one row with an empty `domain` or `url`. Filter those out before counting citations; keep them when counting coverage.
- A domain is counted once per answer however many of its pages the answer cited.

## Method and limits

- **Panel.** 40 fixed English questions in every week, the same text and the same IDs: 16 best, 8 alternatives, 8 compare, 8 how-to-buy. They span consumer and business categories and are not about our own product.
- **Engines.** Checked through each engine's API or search surface, not a logged-in chat app. ChatGPT is OpenAI's API with web search. An app answer for the same question can differ.
- **One sample per engine, question and week.** AI answers vary from run to run, so a single week's citation is one draw, not a stable fact. That is the main limit of this data, and the reason our persistence analysis reports intervals.
- **Failures are kept.** Example: in W38 Claude failed 29 of 40 questions. Those rows are in the data with their failure class, not silently dropped.
- **Grounding redirects and Google search or shopping links** resolve to no domain and drop out of `domain`, which is why Google AI Mode often shows answers with no domain at all.

## Headline findings so far

From `analysis/persistence/` (six weekly runs, 3 September to 5 October 2026):

- 48.0% of the domains an engine cited for a question were cited again for the same question the next week (3,335 of 6,947; 95% interval 46.8 to 49.2%).
- A first-time citation came back the next week 27.3% of the time; after two weeks in a row, 44.5%.
- youtube.com and reddit.com were the two most cited domains in all six runs.

From `analysis/persistence-2026-11/` (eleven weekly runs, 3 September to 9 November 2026):

- 45.7% of the domains an engine cited for a question were cited again for the same question the next week (6,330 of 13,864); ten runs later, 25.6% (363 of 1,416).
- In the week the index moved ChatGPT from gpt-4o-mini to gpt-5-mini (19 to 26 October), ChatGPT cited 15 of the 255 domains it had cited the week before again: 5.9%.

From `analysis/question-shapes/`:

- YouTube was the most cited domain on head-to-head "X vs Y" questions in all six runs, in 48.6% of those answers (137 of 282), against 20 to 25% on the other shapes.
- Comparison-shaped URLs (vs, alternatives, compare) were 69.3% of the pages cited for compare questions and 2.9% for "best" questions.
- consumerreports.org was cited only for "how do I choose" questions, in every run, and never for any other shape.

Full write-up: https://promvia.app/blog/how-long-ai-citations-last

## Updating

```bash
python3 scripts/fetch.py
```

New weeks are published on the live index on Mondays. Re-running the fetch adds them and rebuilds the CSVs. A scheduled GitHub Action (`.github/workflows/weekly-fetch.yml`) does the same every Monday and Tuesday at 16:00 UTC and commits any new week, after checking that the published analyses still reproduce; the commit history is the update log.

## Licence and citation

The data is licensed under CC BY 4.0 (see `LICENSE`): use it for anything, with attribution to "Promvia AI Source Index" and a link to https://promvia.app/ai-source-index. The scripts are under the MIT licence (see `LICENSE-CODE`). `CITATION.cff` has a ready-made citation.

## Who runs it

The index is collected and published by Promvia (https://promvia.app), an AI visibility tracker made by Atlaven. We sell a product in this space; the index uses a fixed panel unrelated to our customers and is free to read, download and reuse. Questions or corrections: ops@atlaven.com.

## How to cite

Promvia (Atlaven). *AI Source Index: what six AI answer engines cited, first eight weeks (2026-W36 to W43)*, version 1.0.0. Zenodo, 2026. https://doi.org/10.5281/zenodo.23651937
