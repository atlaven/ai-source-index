# How long does an AI citation last? Eleven weekly runs (W36–W46 2026)

The 2026-10-07 study (`../2026-10-07-citation-persistence/`) re-run over eleven weekly runs of the
AI Source Index, 3 September to 9 November 2026. The two scripts are the same code with the list of
weeks extended to W46 and the printed labels corrected.

- `raw/` — the public rows, saved unmodified from
  `https://promvia.app/api/public/ai-source-index/rows?week=<week>` (CC BY 4.0).
- `persistence.py` — every number, written to `results.json`, `rows.csv`, `urls.csv`;
  printed summary in `persistence-output.txt`.
- `crosscheck.mjs` — independent Node recount; `crosscheck-output.txt` ends with
  "All 168 values match".

Legacy parts, kept so the code stays identical to the first study, not used in the article:

- section E (`one_week_wonders`): its `all_six` counts domains seen in exactly six runs, which only
  meant "every run" in the six-week study;
- `reddit_crosscheck`: reproduces the 2026-10-05 Reddit figure for the W40→W41 pair only.

Published in the guide: https://promvia.app/blog/how-long-ai-citations-last (update of 2026-11-13).
