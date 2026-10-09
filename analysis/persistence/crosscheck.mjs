#!/usr/bin/env node
/**
 * SECOND DERIVATION of every headline number in summary.md, by a different code path.
 *
 * persistence.py (Python) keeps one set per (week, question, engine) cell and intersects sets.
 * This file (Node, no dependencies) never builds those sets: it flattens every citation into one
 * string key `week|question|engine|item`, keeps the ok cells as `week|question|engine`, and answers
 * each question by membership tests on those two flat Sets. It re-reads raw/*.json itself and
 * re-implements the URL normaliser, then compares every number with results.json and exits 1 on
 * any mismatch.
 *
 * Run: node crosscheck.mjs   (from this directory, after python3 persistence.py)
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const WEEKS = ["2026-W36", "2026-W37", "2026-W38", "2026-W39", "2026-W40", "2026-W41"];
const ENGINES = ["perplexity", "openai", "gemini", "claude", "aioverviews", "aimode"];

const okCell = new Set(); // "w|q|e"
const cite = new Set(); // "w|q|e|domain"
const citeUrl = new Set(); // "w|q|e|url"
const citeDb = new Set(); // database rules: domains plus google.com for Google search/shopping links
const cellsOf = new Map(); // "w" -> array of [q, e, domains[], urls[]] for ok cells
const instrument = {};
const questions = new Set();

/** Python's urlsplit + parse_qsl + urlencode, rebuilt by hand rather than through the URL class. */
function normUrl(raw) {
  const m = /^[a-zA-Z][a-zA-Z0-9+.-]*:\/\/([^/?#]*)([^?#]*)(\?[^#]*)?/.exec(raw);
  let host = (m[1].split("@").pop().split(":")[0] || "").toLowerCase();
  if (host.startsWith("www.")) host = host.slice(4);
  let path = m[2].replace(/\/+$/, "");
  if (path === "") path = "/";
  const yt = host === "youtube.com" || host === "youtu.be" || host === "m.youtube.com";
  const params = [];
  if (m[3]) {
    for (const part of m[3].slice(1).split(/[&;]/)) {
      if (part === "") continue;
      const eq = part.indexOf("=");
      const dec = (s) => decodeURIComponent(s.replace(/\+/g, " "));
      const k = dec(eq === -1 ? part : part.slice(0, eq));
      const v = eq === -1 ? "" : dec(part.slice(eq + 1));
      if (k.toLowerCase().startsWith("utm_") || k.toLowerCase() === "srsltid" || (yt && k === "t")) continue;
      params.push([k, v]);
    }
  }
  params.sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : a[1] < b[1] ? -1 : a[1] > b[1] ? 1 : 0));
  // urlencode's quote_plus: keep A-Za-z0-9 _.-~, space -> +, everything else %XX (UTF-8, upper hex)
  const enc = (s) =>
    Array.from(new TextEncoder().encode(s))
      .map((b) => {
        const c = String.fromCharCode(b);
        if (/[A-Za-z0-9_.\-~]/.test(c)) return c;
        if (c === " ") return "+";
        return "%" + b.toString(16).toUpperCase().padStart(2, "0");
      })
      .join("");
  const q = params.map(([k, v]) => `${enc(k)}=${enc(v)}`).join("&");
  return { host, key: host + path + (q ? "?" + q : "") };
}

for (const w of WEEKS) {
  const payload = JSON.parse(readFileSync(join(HERE, "raw", `${w}.json`), "utf8"));
  const week = payload.weeks[0];
  instrument[w] = week.instrument;
  const list = [];
  for (const r of week.rows) {
    if (r.role !== "answer" || r.status !== "ok") continue;
    const cell = `${w}|${r.queryId}|${r.engine}`;
    questions.add(r.queryId);
    okCell.add(cell);
    const urls = [];
    for (const d of r.domains) {
      cite.add(`${cell}|${d}`);
      citeDb.add(`${cell}|${d}`);
    }
    for (const u of r.citedUrls) {
      const { host, key } = normUrl(u);
      if (r.domains.includes(host)) {
        citeUrl.add(`${cell}|${key}`);
        if (!urls.includes(key)) urls.push(key);
      }
      if (host === "google.com") citeDb.add(`${cell}|google.com`);
    }
    list.push([r.queryId, r.engine, [...new Set(r.domains)], urls]);
  }
  cellsOf.set(w, list);
}

const isOk = (w, q, e) => okCell.has(`${w}|${q}|${e}`);
const has = (set, w, q, e, x) => set.has(`${w}|${q}|${e}|${x}`);
const itemsOf = (set, w, q, e) => {
  // Membership-only path: scan the flat Set for keys with this cell prefix (slow, deliberately dumb).
  const p = `${w}|${q}|${e}|`;
  const out = [];
  for (const k of set) if (k.startsWith(p)) out.push(k.slice(p.length));
  return out;
};
// Pre-index once so the dumb scan above is not run millions of times: same answer, built from the Set.
const index = new Map();
for (const set of [cite, citeUrl, citeDb]) {
  const m = new Map();
  for (const k of set) {
    const i = k.lastIndexOf("|", k.length);
    // keys are w|q|e|item and an item never contains "|" (checked below)
    const parts = k.split("|");
    if (parts.length !== 4) throw new Error(`unexpected key ${k} (${i})`);
    const c = parts.slice(0, 3).join("|");
    if (!m.has(c)) m.set(c, []);
    m.get(c).push(parts[3]);
  }
  index.set(set, m);
}
const items = (set, w, q, e) => index.get(set).get(`${w}|${q}|${e}`) ?? [];
// spot-check the index against the dumb scan
for (const [q, e] of cellsOf.get("2026-W38").slice(0, 25)) {
  const a = items(cite, "2026-W38", q, e).sort().join();
  const b = itemsOf(cite, "2026-W38", q, e).sort().join();
  if (a !== b) throw new Error("index disagrees with scan");
}

const Q = [...questions].sort();
const consecutive = WEEKS.slice(0, -1).map((w, i) => [w, WEEKS[i + 1]]);

function retention(pairs, engines, set = cite, { backward = false, nonemptyBoth = false } = {}) {
  let k = 0;
  let n = 0;
  for (const [a, b] of pairs)
    for (const q of Q)
      for (const e of engines) {
        if (!isOk(a, q, e) || !isOk(b, q, e)) continue;
        const from = backward ? b : a;
        const to = backward ? a : b;
        const xs = items(set, from, q, e);
        if (nonemptyBoth && (xs.length === 0 || items(set, to, q, e).length === 0)) continue;
        for (const x of xs) {
          n += 1;
          if (has(set, to, q, e, x)) k += 1;
        }
      }
  return [k, n];
}

const got = {};
got["retention.pooled.all"] = retention(consecutive, ENGINES);
for (const e of ENGINES) got[`retention.pooled.${e}`] = retention(consecutive, [e]);
got["retention.pooled.google_surfaces"] = retention(consecutive, ["aioverviews", "aimode"]);
got["retention.pooled.llm_apis"] = retention(consecutive, ["perplexity", "openai", "gemini", "claude"]);
for (const [a, b] of consecutive) got[`retention.by_pair.${a}->${b}.all`] = retention([[a, b]], ENGINES);
for (const [a, b] of consecutive)
  for (const e of ENGINES) got[`retention.by_pair.${a}->${b}.${e}`] = retention([[a, b]], [e]);
got["retention.pooled_same_instrument.all"] = retention(
  consecutive.filter(([a, b]) => instrument[a] === instrument[b]),
  ENGINES,
);
got["retention.pooled_nonempty_both.all"] = retention(consecutive, ENGINES, cite, { nonemptyBoth: true });
got["retention.pooled_nonempty_both.aimode"] = retention(consecutive, ["aimode"], cite, { nonemptyBoth: true });
got["urls.pooled.all"] = retention(consecutive, ENGINES, citeUrl);
for (let L = 1; L < WEEKS.length; L++) {
  const pairs = WEEKS.slice(0, WEEKS.length - L).map((w, i) => [w, WEEKS[i + L]]);
  got[`lag.${L}.all`] = retention(pairs, ENGINES);
}

// W36 cohort: survival as a walk over weeks per citation, not as nested all() checks
for (let kk = 1; kk < WEEKS.length; kk++) {
  let cont = 0;
  let at = 0;
  let n = 0;
  for (const q of Q)
    for (const e of ENGINES) {
      let covered = true;
      for (let j = 0; j <= kk; j++) if (!isOk(WEEKS[j], q, e)) covered = false;
      if (!covered) continue;
      for (const d of items(cite, WEEKS[0], q, e)) {
        n += 1;
        let streak = 0;
        while (streak < kk && has(cite, WEEKS[streak + 1], q, e, d)) streak += 1;
        if (streak === kk) cont += 1;
        if (has(cite, WEEKS[kk], q, e, d)) at += 1;
      }
    }
  got[`survival_w36_cohort.${kk}.continuous`] = [cont, n];
  got[`survival_w36_cohort.${kk}.present_that_week`] = [at, n];
}

// First seen in week t: walk forward from each citation's first appearance
const newPooled = {};
const cond = {};
for (let t = 1; t < WEEKS.length; t++)
  for (const q of Q)
    for (const e of ENGINES) {
      let historyOk = true;
      for (let j = 0; j <= t; j++) if (!isOk(WEEKS[j], q, e)) historyOk = false;
      if (!historyOk) continue;
      for (const d of items(cite, WEEKS[t], q, e)) {
        let seenBefore = false;
        for (let j = 0; j < t; j++) if (has(cite, WEEKS[j], q, e, d)) seenBefore = true;
        if (seenBefore) continue;
        let alive = true;
        for (let kk = 1; t + kk < WEEKS.length; kk++) {
          if (!isOk(WEEKS[t + kk], q, e)) break; // censored from here on
          if (alive) {
            // still present in every run so far: does it make one more?
            cond[kk] ??= [0, 0];
            cond[kk][1] += 1;
            if (has(cite, WEEKS[t + kk], q, e, d)) cond[kk][0] += 1;
          }
          alive = alive && has(cite, WEEKS[t + kk], q, e, d);
          newPooled[kk] ??= [0, 0];
          newPooled[kk][1] += 1;
          if (alive) newPooled[kk][0] += 1;
        }
      }
    }
for (const [kk, v] of Object.entries(newPooled)) got[`survival_new_pooled.${kk}`] = v;
for (const [kk, v] of Object.entries(cond)) got[`conditional_new.${kk}_runs_in_a_row`] = v;

// Returns after a drop
{
  let k = 0;
  let n = 0;
  let nk = 0;
  let nn = 0;
  for (let i = 0; i + 2 < WEEKS.length; i++)
    for (const q of Q)
      for (const e of ENGINES) {
        const [a, b] = [WEEKS[i], WEEKS[i + 1]];
        if (!isOk(a, q, e) || !isOk(b, q, e)) continue;
        const later = WEEKS.slice(i + 2).filter((w) => isOk(w, q, e));
        if (later.length === 0) continue;
        for (const d of items(cite, a, q, e)) {
          if (has(cite, b, q, e, d)) continue;
          n += 1;
          if (later.some((w) => has(cite, w, q, e, d))) k += 1;
          if (isOk(WEEKS[i + 2], q, e)) {
            nn += 1;
            if (has(cite, WEEKS[i + 2], q, e, d)) nk += 1;
          }
        }
      }
  got["returns.pooled_any_later_week"] = [k, n];
  got["returns.pooled_back_the_very_next_week"] = [nk, nn];
}

// One-week wonders: count weeks per triple from the flat Set directly
{
  const weeksPerTriple = new Map();
  for (const key of cite) {
    const [w, q, e, d] = key.split("|");
    if (!WEEKS.every((x) => isOk(x, q, e))) continue;
    const t = `${q}|${e}|${d}`;
    weeksPerTriple.set(t, (weeksPerTriple.get(t) ?? 0) + (w ? 1 : 0));
  }
  const vals = [...weeksPerTriple.values()];
  got["one_week_wonders.all.one_week"] = [vals.filter((v) => v === 1).length, vals.length];
  got["one_week_wonders.all.all_six"] = [vals.filter((v) => v === 6).length, vals.length];
  const slots = vals.reduce((s, v) => s + v, 0);
  got["one_week_wonders.all.slots_from_one_week"] = [vals.filter((v) => v === 1).length, slots];
}

// Top 20 domains of W36 (by answers citing them; ties alphabetical), retention in later pairs
{
  const count = new Map();
  for (const key of cite) {
    const [w, , , d] = key.split("|");
    if (w === WEEKS[0]) count.set(d, (count.get(d) ?? 0) + 1);
  }
  const top = new Set(
    [...count.entries()].sort((x, y) => y[1] - x[1] || (x[0] < y[0] ? -1 : 1)).slice(0, 20).map((x) => x[0]),
  );
  let bk = 0;
  let bn = 0;
  let ok2 = 0;
  let on = 0;
  for (const [a, b] of consecutive.slice(1))
    for (const q of Q)
      for (const e of ENGINES) {
        if (!isOk(a, q, e) || !isOk(b, q, e)) continue;
        for (const d of items(cite, a, q, e)) {
          const kept = has(cite, b, q, e, d) ? 1 : 0;
          if (top.has(d)) {
            bk += kept;
            bn += 1;
          } else {
            ok2 += kept;
            on += 1;
          }
        }
      }
  got["retention_top20_w36_later_pairs"] = [bk, bn];
  got["retention_other_w36_later_pairs"] = [ok2, on];
}

// When a domain stayed, was one of the same URLs cited again? URL keys start with the host.
{
  let k = 0;
  let n = 0;
  for (const [a, b] of consecutive)
    for (const q of Q)
      for (const e of ENGINES) {
        if (!isOk(a, q, e) || !isOk(b, q, e)) continue;
        for (const d of items(cite, a, q, e)) {
          if (!has(cite, b, q, e, d)) continue;
          n += 1;
          const mine = items(citeUrl, a, q, e).filter((u) => u.slice(0, u.indexOf("/")) === d);
          if (mine.some((u) => has(citeUrl, b, q, e, u))) k += 1;
        }
      }
  got["urls.kept_domain_same_url"] = [k, n];
}

// Non-count checks: top-10 carry-over and AI Mode's source-less answers, compared separately
const extra = {};
{
  const top10 = (w) => {
    const c = new Map();
    for (const key of cite) {
      const [ww, , , d] = key.split("|");
      if (ww === w) c.set(d, (c.get(d) ?? 0) + 1);
    }
    return [...c.entries()].sort((x, y) => y[1] - x[1] || (x[0] < y[0] ? -1 : 1)).slice(0, 10).map((x) => x[0]);
  };
  for (const [a, b] of consecutive) {
    const ta = new Set(top10(a));
    extra[`top10_overlap.${a}->${b}`] = top10(b).filter((d) => ta.has(d)).length;
  }
  for (const w of WEEKS) {
    let empty = 0;
    for (const q of Q) if (isOk(w, q, "aimode") && items(cite, w, q, "aimode").length === 0) empty += 1;
    extra[`ok_rows_without_domains.${w}.aimode`] = empty;
  }
}

// The 2026-10-05 Reddit figure: W40 -> W41, this week's domains, both answers non-empty, google.com kept
got["reddit_crosscheck.reproduced_db_rules.all"] = retention([["2026-W40", "2026-W41"]], ENGINES, citeDb, {
  backward: true,
  nonemptyBoth: true,
});
for (const e of ENGINES)
  got[`reddit_crosscheck.reproduced_db_rules.${e}`] = retention([["2026-W40", "2026-W41"]], [e], citeDb, {
    backward: true,
    nonemptyBoth: true,
  });
got["reddit_crosscheck.this_study_backward"] = retention([["2026-W40", "2026-W41"]], ENGINES, cite, { backward: true });

// ---- compare with persistence.py ------------------------------------------------------------
const results = JSON.parse(readFileSync(join(HERE, "results.json"), "utf8"));
const dig = (obj, path) => {
  // keys contain "->" and "." only as separators we chose; week keys have no dots
  let cur = obj;
  for (const part of path.split(".")) cur = cur?.[part];
  return cur;
};
/** Wilson 95% interval, written out again rather than shared with the Python. */
function wilson(k, n) {
  const z = 1.959964;
  const p = k / n;
  const den = 1 + (z * z) / n;
  const mid = (p + (z * z) / (2 * n)) / den;
  const half = (z * Math.sqrt((p * (1 - p)) / n + (z * z) / (4 * n * n))) / den;
  return [Math.max(0, mid - half), Math.min(1, mid + half)];
}
let bad = 0;
for (const [path, [k, n]] of Object.entries(got)) {
  const r = dig(results, path);
  const [lo, hi] = n ? wilson(k, n) : [null, null];
  const ciSame = !n || (Math.abs(r?.wilson_lo - lo) < 1e-9 && Math.abs(r?.wilson_hi - hi) < 1e-9);
  const same = r && r.k === k && r.n === n && ciSame;
  if (!same) bad += 1;
  const pct = n ? ((100 * k) / n).toFixed(1) : "n/a";
  console.log(`${same ? "ok  " : "DIFF"} ${path}: node ${k}/${n} (${pct}%)  python ${r ? `${r.k}/${r.n}` : "missing"}`);
}
for (const [path, v] of Object.entries(extra)) {
  const r = dig(results, path);
  if (r !== v) bad += 1;
  console.log(`${r === v ? "ok  " : "DIFF"} ${path}: node ${v}  python ${r}`);
}
const total = Object.keys(got).length + Object.keys(extra).length;
console.log(bad === 0 ? `\nAll ${total} values match (counts with their Wilson intervals, plus ${Object.keys(extra).length} plain values).` : `\n${bad} mismatches.`);
process.exit(bad === 0 ? 0 : 1);
