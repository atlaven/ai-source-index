# AI Source Index

Which websites do AI answer engines cite, and do they keep citing them?

Every week we ask the same 40 buyer questions to six answer engines (ChatGPT, Perplexity, Gemini, Claude, Google AI Overviews and Google AI Mode) and record every source each answer cites. This repository holds the raw rows of every published week, flat CSVs built from them, and the scripts behind our analyses, so anyone can check a number instead of trusting it.

Live index: https://promvia.app/ai-source-index

## What is in here

| Path | What it is |
|---|---|
| `data/raw/<week>.json` | The public API response for that week, unmodified. |
| `data/citations.csv` | One row per engine answer and cited domain. |
| `data/cited_urls.csv` | One row per engine answer and cited URL. |
| `scripts/fetch.py` | Rebuilds everything in `data/` from the API. Standard library only. |
| `analysis/persistence/` | How long a citation lasts, week over week (W36 to W41 2026): a Python analysis, an independent Node cross-check, and their outputs. |

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

Full write-up: https://promvia.app/blog/how-long-ai-citations-last

## Updating

```bash
python3 scripts/fetch.py
```

New weeks are published on the live index on Mondays. Re-running the fetch adds them and rebuilds the CSVs.

## Licence and citation

The data is licensed under CC BY 4.0 (see `LICENSE`): use it for anything, with attribution to "Promvia AI Source Index" and a link to https://promvia.app/ai-source-index. The scripts are under the MIT licence (see `LICENSE-CODE`). `CITATION.cff` has a ready-made citation.

## Who runs it

The index is collected and published by Promvia (https://promvia.app), an AI visibility tracker made by Atlaven. We sell a product in this space; the index uses a fixed panel unrelated to our customers and is free to read, download and reuse. Questions or corrections: ops@atlaven.com.
