# Which sources each kind of buyer question cites (W36–W41 2026)

Six weekly runs (3 Sep to 5 Oct 2026), six answer engines, the 40 fixed questions of the AI Source Index: 16 "best X", 8 "alternatives to X", 8 head-to-head "X vs Y" and 8 "how do I choose X". Every number below is in `results.json` with its numerator and denominator. `shapes.py` derives them from the raw API files; `crosscheck.mjs` derives the headline counts again from the flat CSVs by a different path, and the two agree (`crosscheck-output.txt`).

Unit: one engine's answer to one question in one run, status ok. A domain counts once per answer. Answers per shape, pooled: best 565, alternatives 282, compare 282, how-to-buy 281 (Claude failed 29 of 40 checks on 14 September; those are left out, not counted as answers).

## 1. YouTube is the head-to-head source, every week

| Share of answers citing | best | alternatives | compare | how-to-buy |
|---|---|---|---|---|
| youtube.com | 114/565 = 20.2% (17.1–23.7) | 71/282 = 25.2% (20.5–30.6) | 137/282 = 48.6% (42.8–54.4) | 71/281 = 25.3% (20.5–30.7) |
| reddit.com | 118/565 = 20.9% (17.7–24.4) | 71/282 = 25.2% (20.5–30.6) | 73/282 = 25.9% (21.1–31.3) | 44/281 = 15.7% (11.9–20.4) |

95% Wilson intervals in brackets. YouTube was the most cited domain on compare questions in all six runs, and was cited for 8 of the 8 compare questions in every run. It was also the most cited domain on how-to-buy questions in all six runs.

Two AI Overviews answers on 14 September cited `m.youtube.com`, which the index keeps as its own domain. Folding it in, YouTube's compare share is 139/282 = 49.3%.

## 2. Reddit and YouTube are level on "best" and "alternatives", and the leader changed

On best and alternatives questions the two are within a point of each other pooled. The most cited domain was YouTube in the first two runs (3 and 7 September) and Reddit in the last four, on both shapes.

Correction to what we said in public on 23 September: from the 21 September run alone (W39) we described Reddit as strong on "best" and weak on "alternatives" (15/16 best questions against 6/8 alternatives). Over six runs that does not hold: Reddit was cited for 8 of 8 alternatives questions on 3 and 7 September. Reddit's weakest shape in every run is how-to-buy (4 to 6 of 8 questions), tied with another shape in two runs.

## 3. Comparison-shaped pages are cited for comparison questions, almost never for "best"

Cited URLs whose path says vs, versus, alternative(s), compare or comparison:

- compare: 1,331 of 1,920 cited URLs, 69.3%
- alternatives: 1,091 of 2,076, 52.6%
- best: 116 of 3,964, 2.9%
- how-to-buy: 37 of 1,802, 2.1%

## 4. One true shape specialist: Consumer Reports

Among the 43 domains cited at least 12 times for at least 3 different questions, the ones whose citations sit mostly in one shape (at least 60% of their citations, at least twice that shape's share of all answers):

- consumerreports.org: 30 citations, 4 questions, 100% how-to-buy, cited in all six runs and never for any other shape.
- bankrate.com: 22 citations, 3 questions, 100% best.
- engadget.com: 23 citations, 3 questions, 91% alternatives.
- today.com 88% compare, blog.hubspot.com 80% how-to-buy, healthline.com 74% compare, kiplinger.com 70% how-to-buy, cnet.com 67% alternatives (9 questions).

The shapes are not balanced by category, so a specialist can be a category effect. Consumer Reports is the cleanest test the panel allows: it was cited for choosing a robot vacuum, a standing desk, a carry-on suitcase and a mattress, and never once for "alternatives to Dyson cordless vacuums", the best noise-cancelling headphones, the best running shoes, the best budget monitor or the best fitness tracker, which are the same kind of consumer product asked in another shape.

## 5. "How do I choose" answers cite nothing most often

Answers with no source at all: how-to-buy 69/281 = 24.6%, alternatives 30/282 = 10.6%, best 54/565 = 9.6%, compare 18/282 = 6.4%. On how-to-buy questions Google AI Mode answered without a source 36 of 48 times and Claude 25 of 41; ChatGPT once in 48 and Perplexity never.

## Limits

- One sample per engine, question and run. A two-question swing on an eight-question shape can look like a pattern for a week (see the Reddit correction above).
- 8 questions per shape (16 for best). Each shape mixes consumer, software and finance questions, but not in equal parts.
- The comparison-path rule reads URLs, not rendered pages.
