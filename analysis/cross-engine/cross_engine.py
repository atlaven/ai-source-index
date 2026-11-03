"""Cross-engine source overlap in the AI Source Index, W36-W45 2026.

Unit: one (week, question). For each answer engine we take the deduped `domains` of its ok row.
An engine with a failed row, or an ok row citing no domain, is left out of that (week, question).
"""
import json, sys, itertools, collections, os

RAW = sys.argv[1]
ENGINES = ['openai', 'perplexity', 'gemini', 'claude', 'aioverviews', 'aimode']
weeks = sorted(f[:-5] for f in os.listdir(RAW) if f.endswith('.json'))

cells = {}  # (week, qid) -> {engine: set(domains)}
questions = {}
excluded = collections.Counter()
for w in weeks:
    d = json.load(open(os.path.join(RAW, w + '.json')))
    for wk in d['weeks']:
        for r in wk['rows']:
            if r['role'] != 'answer' or r['engine'] not in ENGINES:
                continue
            questions[r['queryId']] = r['question']
            if r['status'] != 'ok':
                excluded['failed'] += 1; continue
            if not r['domains']:
                excluded['ok_no_domain:' + r['engine']] += 1; continue
            cells.setdefault((wk['week'], r['queryId']), {})[r['engine']] = set(r['domains'])

out = {'weeks': weeks, 'cells': len(cells), 'excluded': dict(excluded)}

# 1. pairwise, pooled over (week, question) where both engines cited something
pair = {}
for a, b in itertools.combinations(ENGINES, 2):
    inter = union = n = 0
    for c in cells.values():
        if a in c and b in c:
            n += 1; inter += len(c[a] & c[b]); union += len(c[a] | c[b])
    pair[f'{a}|{b}'] = {'cells': n, 'shared': inter, 'union': union, 'jaccard': round(inter / union, 4) if union else None}
out['pairwise'] = pair

# 2. how many engines cite each domain, per (week, question), over cells where >= 4 engines cited something
spread = collections.Counter(); spread_cells = 0
for c in cells.values():
    if len(c) < 4:
        continue
    spread_cells += 1
    cnt = collections.Counter(dm for s in c.values() for dm in s)
    for dm, k in cnt.items():
        spread[(k, len(c))] += 1
out['spread_cells'] = spread_cells
tot = sum(spread.values())
by_k = collections.Counter()
for (k, n), v in spread.items():
    by_k[k] += v
out['domain_question_pairs'] = tot
out['engines_citing'] = {k: by_k[k] for k in sorted(by_k)}
out['share_one_engine'] = round(by_k[1] / tot, 4)
out['share_ge3'] = round(sum(v for k, v in by_k.items() if k >= 3) / tot, 4)

# 3. within-engine week-over-week, same definition, for contrast
wow = {}
for e in ENGINES:
    inter = union = 0
    for (w, q), c in cells.items():
        i = weeks.index(w)
        if i + 1 >= len(weeks) or e not in c:
            continue
        nxt = cells.get((weeks[i + 1], q), {})
        if e in nxt:
            inter += len(c[e] & nxt[e]); union += len(c[e] | nxt[e])
    wow[e] = round(inter / union, 4) if union else None
out['week_over_week_jaccard'] = wow

# 4. domains most often cited by >= 4 engines for the same question
multi = collections.Counter()
for c in cells.values():
    cnt = collections.Counter(dm for s in c.values() for dm in s)
    for dm, k in cnt.items():
        if k >= 4:
            multi[dm] += 1
out['cited_by_4plus_engines_top'] = multi.most_common(20)
# 5. robustness: only (week, question) cells where all six engines cited something
full = [c for c in cells.values() if len(c) == 6]
cnt6 = collections.Counter()
for c in full:
    for dm, k in collections.Counter(dm for s in c.values() for dm in s).items():
        cnt6[k] += 1
t6 = sum(cnt6.values())
out['all_six'] = {'cells': len(full), 'domain_question_pairs': t6, 'engines_citing': {k: cnt6[k] for k in sorted(cnt6)},
                  'share_one_engine': round(cnt6[1] / t6, 4)}

# 6. per engine: share of the domains it cites for a question that no other engine cited for that question
#    (cells where >= 4 engines cited something, so every engine has at least 3 others to agree with)
solo = {}
for e in ENGINES:
    own = alone = 0
    for c in cells.values():
        if e not in c or len(c) < 4:
            continue
        others = set().union(*(s for k, s in c.items() if k != e))
        own += len(c[e]); alone += len(c[e] - others)
    solo[e] = {'domains': own, 'cited_by_no_other': alone, 'share': round(alone / own, 4)}
out['solo_share'] = solo
json.dump(out, sys.stdout, indent=1)
