# Server logs joined to AI citations, promvia.app, 26 Aug to 5 Oct 2026

One site (promvia.app, our own), two answer APIs, four branded questions. Every number below is recomputed from `rows.csv` by `recount.py` (Python standard library, no network).

**Question:** when ChatGPT or Perplexity cites a page of ours, what did their crawlers do on our server before and around that answer?

## Sources

- **Citations.** Promvia's own tracked questions for promvia.app, asked through OpenAI's API with web search (`chatgpt-api`) and Perplexity's API (`perplexity-api`). Four questions, all branded: "Is Promvia any good?", "Promvia reviews", "Promvia vs Otterly", "What is Promvia by Atlaven?". Only answers that cited a promvia.app URL are in the file: 63 ChatGPT answers (129 answer-URL pairs, 15 pages) and 104 Perplexity answers (174 pairs, 5 pages), checked between 2026-08-26 00:00 and 2026-10-06 00:00 UTC. `check_time` is when the answer was stored, after the provider returned it.
- **Fetches.** Every request to promvia.app whose user agent claimed ChatGPT-User, OAI-SearchBot, GPTBot or PerplexityBot, from the first logged row (2026-08-25 14:34 UTC) to 2026-10-07 09:00 UTC: 1,158 rows. Perplexity-User is detected too and never appeared. `verified` is true when the source IP is inside the operator's published range for that crawler. IPs are removed.
- **Our own requests.** Two sources of unverified rows are ours and are marked in `note`: `own_weekly_probe` is Promvia's weekly crawler-access check (Mondays 13:00 UTC, the homepage, one request per crawler user agent); `own_test_address` is the address that ran the documented 2026-09-08 access test, seen again on 2026-09-24, 2026-09-30 and 2026-10-05.
- Paths are normalised: query string, fragment and trailing slash removed (`/?utm_source=openai` = `/`).

## 1. A crawler fetch in the 10 minutes before the stored answer

ChatGPT is joined to ChatGPT-User, Perplexity to PerplexityBot (and Perplexity-User, which never appeared).

| engine | answers | verified fetch in the 10 min before | of which a URL the answer cited | unverified fetch in the window |
| --- | --- | --- | --- | --- |
| ChatGPT (API) | 63 | 7 = 11.1% [5.5–21.2] | 1 | 0 |
| Perplexity (API) | 104 | 2 = 1.9% [0.5–6.7] | 0 | 8, all `own_weekly_probe`; 7 of them on `/`, which the answer cited |

Base rate: verified ChatGPT-User requests arrived 593 times in the window (14.5 a day, 561 of them the homepage). At that rate a random 10-minute window contains at least one with probability 9.6%, so 7 of 63 is what chance alone produces. In the 10 minutes after the stored answer: 14 ChatGPT answers had a verified ChatGPT-User fetch (none of a cited URL), 5 Perplexity answers a verified PerplexityBot fetch (2 of a cited URL).

## 2. Was the cited URL crawled by the engine's index crawler first?

Any earlier verified fetch of the same path, since logging began on 2026-08-25.

| engine | crawler | (answer, URL) pairs crawled first | misses |
| --- | --- | --- | --- |
| ChatGPT (API) | OAI-SearchBot | 116/129 = 89.9% [83.5–94.0] | 13, all on 27–29 Aug, within four days of the log starting |
| Perplexity (API) | PerplexityBot | 174/174 = 100% [97.8–100] | none; 5 pages: /blog/peec-ai-alternatives 60, /help 43, / 33, /blog/best-ai-visibility-tools 31, /imprint 7 |

## 3. Requests that failed IP verification, 26 Aug to 5 Oct

| crawler | failed / all | ours (`note`) | failed after removing ours |
| --- | --- | --- | --- |
| GPTBot | 16/68 = 24% | 16 | 0/52 |
| PerplexityBot | 9/34 = 26% | 9 | 0/25 |
| ChatGPT-User | 17/610 = 2.8% | 7 | 10/603 = 1.7% [0.9–3.0] |
| OAI-SearchBot | 7/390 = 1.8% | 7 | 0/383 |

## 4. Revisit gap, verified fetches, 26 Aug to 5 Oct

| crawler | fetches | pages | pages fetched more than once | median gap between fetches of the same page | median of per-page medians |
| --- | --- | --- | --- | --- | --- |
| OAI-SearchBot | 383 | 89 | 40 | 24.0 h (294 gaps) | 204 h |
| PerplexityBot | 25 | 11 | 3 | 40.7 h (14 gaps) | 89 h |

The pooled median is set by a dozen pages OAI-SearchBot fetched about once a day; the other 49 pages were fetched once in 41 days.

## 5. After a known change

On 2026-10-04 at 18:05 UTC a release changed the text of four pages: `/`, `/pricing`, `/methodology` and `/help`. As of 2026-10-07 09:00 UTC:

| crawler | `/` | `/methodology` | `/pricing` | `/help` |
| --- | --- | --- | --- | --- |
| OAI-SearchBot | 36 h later | 36 h later | not re-fetched (last: 1 Oct) | not re-fetched (last: 30 Sep) |
| PerplexityBot | not re-fetched | never fetched | never fetched | not re-fetched |

PerplexityBot's last verified request of any page was on 2026-09-26. OAI-SearchBot made no verified request between 2026-10-03 13:23 and 2026-10-06 06:04 UTC; other crawlers were logged in that gap, so it is not a logging outage.

## Caveats

1. **One site, four branded questions.** Every question names us. An engine asked about a brand by name has a reason to cite that brand's own pages; unbranded questions may behave differently.
2. **API answers, not the consumer apps.** The answers come from OpenAI's API with web search and Perplexity's API. What ChatGPT or Perplexity do for a person in their own apps may differ.
3. **`check_time` is when we stored the answer.** Some checks take two samples, so the provider was asked up to a few minutes before `check_time`; the 10-minute window covers that.
4. **The log starts on 2026-08-25.** "Not crawled before" for the earliest answers can mean "crawled before we were logging".
5. **Verification is only as good as the published ranges.** A crawler using an address outside its operator's list reads as unverified.
6. **Our own requests are identified by time and address**, from the documented probe schedule and test; the classification is in `note` so it can be disputed row by row.
