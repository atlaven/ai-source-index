"""Per-week spread of the headline shares, plus Wilson intervals for the pooled ones."""
import json, sys, os, collections, math

RAW = sys.argv[1]
ENGINES = ['openai', 'perplexity', 'gemini', 'claude', 'aioverviews', 'aimode']

def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(100 * (c - h), 1), round(100 * (c + h), 1)]

cells = collections.defaultdict(dict)
for f in sorted(os.listdir(RAW)):
    for wk in json.load(open(os.path.join(RAW, f)))['weeks']:
        for r in wk['rows']:
            if r['role'] == 'answer' and r['engine'] in ENGINES and r['status'] == 'ok' and r['domains']:
                cells[(wk['week'], r['queryId'])][r['engine']] = set(r['domains'])

per = collections.defaultdict(lambda: [0, 0, 0, 0, 0])  # one-engine, pairs, gpt-alone, gpt-own, cells
for (w, q), c in cells.items():
    if len(c) < 4:
        continue
    cnt = collections.Counter(d for s in c.values() for d in s)
    per[w][0] += sum(1 for v in cnt.values() if v == 1); per[w][1] += len(cnt); per[w][4] += 1
    if 'openai' in c:
        others = set().union(*(s for e, s in c.items() if e != 'openai'))
        per[w][2] += len(c['openai'] - others); per[w][3] += len(c['openai'])
rows = {w: {'cells': v[4], 'one_engine_pct': round(100 * v[0] / v[1], 1), 'chatgpt_alone_pct': round(100 * v[2] / v[3], 1)} for w, v in sorted(per.items())}
tot = [sum(v[i] for v in per.values()) for i in range(5)]
print(json.dumps({'per_week': rows,
                  'one_engine': [tot[0], tot[1], round(100 * tot[0] / tot[1], 1), wilson(tot[0], tot[1])],
                  'chatgpt_alone': [tot[2], tot[3], round(100 * tot[2] / tot[3], 1), wilson(tot[2], tot[3])],
                  'distinct_questions': len({q for (_, q) in cells})}, indent=1))
