# AI Source Index: first eight weeks (2026-W36 – W43)

Every week from 3 September to 19 October 2026 (UTC), the same 40 buyer questions were put to six AI answer
engines — ChatGPT, Perplexity, Gemini, Claude, Google AI Overviews and Google AI Mode — and every source
each answer cited was recorded. 1,920 checks, 1,883 answered.

Published by [Promvia](https://promvia.app) (Atlaven, Netherlands, KvK 42199783). The report built on this data:
https://promvia.app/ai-source-index/first-eight-weeks — weekly updates and discussion: r/AISourceIndex.

## Files

| File | What it is |
|---|---|
| `rows.csv` | One row per (week, question, engine, cited domain). Failed checks are kept as rows with `status=failed` and a `failure_class`; an answered check that cited nothing has an empty `domain`. 11,667 rows. |
| `results.json` | Every number in the report, as computed from `rows.csv`. |
| `recount.py` | Python 3 stdlib script that rebuilds `results.json` from `rows.csv`: `python3 recount.py rows.csv --check results.json` prints `ALL MATCH`. |

### Columns (`rows.csv`)

`week`, `captured_at` (UTC), `instrument` (panel fingerprint; changes are noted in the report), `query_id`,
`question`, `shape` (question type: `best`, `alternatives`, `compare` ("X vs Y"), `howto-buy`), `engine` (`openai` = ChatGPT, `perplexity`, `gemini`, `claude`, `aioverviews`, `aimode`), `model` (filled from 2026-W38 for ChatGPT, Gemini and Claude; Google and Perplexity expose none),
`status` (`ok` / `failed`), `failure_class`, `domain` (registrable domain, deduplicated per answer).

## Caveats (read before quoting)

- The ChatGPT and Claude columns are API models (gpt-4o-mini, claude-haiku-4-5), not the consumer apps.
  ChatGPT moved to gpt-5-mini on 2026-10-21, after this window.
- 40 questions is a small panel; question-type comparisons rest on 8 questions per type.
- Google's own links (search, shopping, grounding redirects) are dropped by rule and resolve to no domain.
- Measurement, not causation: nothing here says why an engine cites a source.

## Licence and citation

Data: CC BY 4.0. Script: MIT.

> Promvia (2026). *AI Source Index: what six AI answer engines cited, 2026-W36 – W43.*
> https://promvia.app/ai-source-index/first-eight-weeks
