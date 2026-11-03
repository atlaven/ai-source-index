import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const here = path.dirname(fileURLToPath(import.meta.url));
const RAW = process.argv[2] ?? path.join(here, '..', '..', 'data', 'raw');
const ENGINES = ['openai','perplexity','gemini','claude','aioverviews','aimode'];
const ES = new Set(ENGINES);
const r6 = x => Math.round(x*1e6)/1e6;

const diag = { files: 0, weekMismatch: [], duplicateRows: 0, rowsWithDupDomains: 0, rowsWithCaseOrWwwVariants: 0,
  rowsOtherEngineOrRole: 0, otherEngineRoleStatus: {}, statusValues: {}, okEmptyWithCitedUrls: 0, weeksSeen: [] };
const cellsMap = new Map(); // week -> Map(queryId -> Map(engine -> Set))
const notOkByEngine = {}; const okEmptyByEngine = {};
let notOk = 0;

for (const f of fs.readdirSync(RAW).filter(f => f.endsWith('.json')).sort()) {
  diag.files++;
  const d = JSON.parse(fs.readFileSync(path.join(RAW, f), 'utf8'));
  for (const w of d.weeks) {
    if (w.week + '.json' !== f) diag.weekMismatch.push({ file: f, week: w.week });
    if (!cellsMap.has(w.week)) cellsMap.set(w.week, new Map());
    const wm = cellsMap.get(w.week);
    const seenRow = new Set();
    for (const r of w.rows) {
      if (!ES.has(r.engine) || r.role !== 'answer') {
        diag.rowsOtherEngineOrRole++;
        const k = `${r.engine}:${r.role}:${r.status}`;
        diag.otherEngineRoleStatus[k] = (diag.otherEngineRoleStatus[k]||0)+1;
        continue;
      }
      // a cell = every (week, queryId) with at least one in-scope (answer-role, known-engine) row
      if (!wm.has(r.queryId)) wm.set(r.queryId, new Map());
      const k = r.queryId + '|' + r.engine;
      if (seenRow.has(k)) diag.duplicateRows++;
      seenRow.add(k);
      diag.statusValues[r.status] = (diag.statusValues[r.status]||0)+1;
      if (r.status !== 'ok') { notOk++; notOkByEngine[r.engine] = (notOkByEngine[r.engine]||0)+1; continue; }
      const doms = Array.isArray(r.domains) ? r.domains : [];
      if (doms.length === 0) {
        okEmptyByEngine[r.engine] = (okEmptyByEngine[r.engine]||0)+1;
        if ((r.citedUrls||[]).length) diag.okEmptyWithCitedUrls++;
        continue;
      }
      const s = new Set(doms);
      if (s.size !== doms.length) diag.rowsWithDupDomains++;
      const norm = new Set(doms.map(x => String(x).toLowerCase().replace(/^www\./,'')));
      if (norm.size !== s.size) diag.rowsWithCaseOrWwwVariants++;
      const cell = wm.get(r.queryId);
      if (cell.has(r.engine)) { for (const x of s) cell.get(r.engine).add(x); } else cell.set(r.engine, s);
    }
  }
}
const weeks = [...cellsMap.keys()].sort();
diag.weeksSeen = weeks;

const cells = [];
for (const wk of weeks) for (const [q, m] of cellsMap.get(wk)) cells.push({ week: wk, queryId: q, eng: m });

// A
const A = { cells: cells.length, rowsExcludedStatusNotOk: notOk, rowsExcludedStatusNotOkByEngine: notOkByEngine,
  rowsExcludedOkButEmptyDomainsByEngine: Object.fromEntries(ENGINES.map(e => [e, okEmptyByEngine[e]||0])),
  rowsExcludedOkButEmptyDomainsTotal: Object.values(okEmptyByEngine).reduce((a,b)=>a+b,0),
  cellsByPresentEngineCount: {} };
for (const c of cells) A.cellsByPresentEngineCount[c.eng.size] = (A.cellsByPresentEngineCount[c.eng.size]||0)+1;

const inter = (a, b) => { let n = 0; for (const x of a) if (b.has(x)) n++; return n; };

// B
const B = {};
for (let i = 0; i < ENGINES.length; i++) for (let j = i+1; j < ENGINES.length; j++) {
  const a = ENGINES[i], b = ENGINES[j]; let I = 0, U = 0, n = 0;
  for (const c of cells) if (c.eng.has(a) && c.eng.has(b)) {
    const sa = c.eng.get(a), sb = c.eng.get(b); const k = inter(sa, sb);
    I += k; U += sa.size + sb.size - k; n++;
  }
  B[`${a}|${b}`] = { cells: n, sumIntersection: I, sumUnion: U, pooledJaccard: U ? r6(I/U) : null };
}

function hist(filter) {
  const h = {1:0,2:0,3:0,4:0,5:0,6:0}; let n = 0;
  for (const c of cells) if (filter(c)) {
    n++;
    const cnt = new Map();
    for (const s of c.eng.values()) for (const d of s) cnt.set(d, (cnt.get(d)||0)+1);
    for (const v of cnt.values()) h[v]++;
  }
  const tot = Object.values(h).reduce((a,b)=>a+b,0);
  return { cells: n, distinctDomainCellPairs: tot, histogram: h, shareExactlyOne: tot ? r6(h[1]/tot) : null };
}
const C = hist(c => c.eng.size >= 4);
const D = hist(c => c.eng.size === 6);

// E
const E = {};
for (const e of ENGINES) {
  let tot = 0, uniq = 0, n = 0;
  for (const c of cells) if (c.eng.size >= 4 && c.eng.has(e)) {
    n++;
    for (const d of c.eng.get(e)) {
      tot++;
      let other = false;
      for (const [e2, s2] of c.eng) if (e2 !== e && s2.has(d)) { other = true; break; }
      if (!other) uniq++;
    }
  }
  E[e] = { cells: n, totalDomains: tot, citedByNoOtherEngine: uniq, shareUnique: tot ? r6(uniq/tot) : null };
}

// F
const F = {};
for (const e of ENGINES) {
  let I = 0, U = 0, n = 0;
  for (let wi = 0; wi + 1 < weeks.length; wi++) {
    const cur = cellsMap.get(weeks[wi]), nxt = cellsMap.get(weeks[wi+1]);
    for (const [q, m] of cur) {
      if (!m.has(e)) continue;
      const m2 = nxt.get(q); if (!m2 || !m2.has(e)) continue;
      const a = m.get(e), b = m2.get(e); const k = inter(a, b);
      I += k; U += a.size + b.size - k; n++;
    }
  }
  F[e] = { pairs: n, sumIntersection: I, sumUnion: U, pooledJaccard: U ? r6(I/U) : null };
}

// G
const gc = new Map(); let gCells = 0;
for (const c of cells) {
  if (c.eng.size < 4) continue;
  const cnt = new Map();
  for (const s of c.eng.values()) for (const d of s) cnt.set(d, (cnt.get(d)||0)+1);
  let any = false;
  for (const [d, v] of cnt) if (v >= 4) { gc.set(d, (gc.get(d)||0)+1); any = true; }
  if (any) gCells++;
}
const G = { cellsWithAnyConsensusDomain: gCells, distinctConsensusDomains: gc.size,
  top10: [...gc.entries()].sort((a,b) => b[1]-a[1] || a[0].localeCompare(b[0])).slice(0,10).map(([domain, cells]) => ({ domain, cells })) };

const out = { weeks, engines: ENGINES, A, B, C, D, E, F, G, diagnostics: diag };
fs.writeFileSync(path.join(here, 'recount-output.json'), JSON.stringify(out, null, 2));
console.log(JSON.stringify(out, null, 2));
