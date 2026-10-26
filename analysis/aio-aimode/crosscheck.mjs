// Second, independent derivation of every number in results.json (written by aio_aimode.py).
// Node 18+, no dependencies. Run: node crosscheck.mjs  (from this directory)
//
// A different code path on purpose: every row is reduced to one string record
// "week|question|engine|status|domains-joined|link-count" in a flat array, every count below is a
// filter/reduce over that array or over Sets of string keys built from it (no nested per-engine
// dicts, no per-run loop), the Wilson interval is re-implemented from the closed form, and each
// value is compared with results.json. Any difference is printed and the exit code is 1.
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const raw = join(here, "..", "2026-10-07-citation-persistence", "raw");
const weeks = [36, 37, 38, 39, 40, 41].map((n) => `2026-W${n}`);

const recs = [];
for (const w of weeks) {
  const j = JSON.parse(readFileSync(join(raw, `${w}.json`), "utf8"));
  for (const r of j.weeks[0].rows) {
    if (r.engine !== "aioverviews" && r.engine !== "aimode") continue;
    recs.push(`${w}|${r.queryId}|${r.engine}|${r.status}|${[...r.domains].sort().join(",")}|${(r.citedUrls ?? []).length}`);
  }
}
const parse = (s) => {
  const [w, q, e, st, d, links] = s.split("|");
  return { w, q, e, ok: st === "ok", doms: d === "" ? [] : d.split(","), links: Number(links) };
};
const rows = recs.map(parse);
const ok = rows.filter((r) => r.ok);

const wilson = (k, n) => {
  const z = 1.959964, p = k / n, z2 = z * z;
  const c = (p + z2 / (2 * n)) / (1 + z2 / n);
  const h = (z / (1 + z2 / n)) * Math.sqrt((p * (1 - p)) / n + z2 / (4 * n * n));
  return [Math.max(0, c - h), Math.min(1, c + h)];
};
const r1 = (x) => Math.round(x * 1000) / 10;
const rate = (k, n) => { const [lo, hi] = wilson(k, n); return { k, n, pct: r1(k / n), wilson_lo: r1(lo), wilson_hi: r1(hi) }; };

const got = {};
const put = (path, v) => { got[path] = v; };

for (const e of ["aioverviews", "aimode"]) {
  const mine = ok.filter((r) => r.e === e);
  const empty = mine.filter((r) => r.doms.length === 0);
  put(`no_domain.${e}.pooled_no_domain`, rate(empty.length, mine.length));
  put(`no_domain.${e}.pooled_no_link_at_all`, rate(empty.filter((r) => r.links === 0).length, mine.length));
  put(`no_domain.${e}.pooled_only_google_links`, rate(empty.filter((r) => r.links > 0).length, mine.length));
  put(`no_domain.${e}.failed_rows`, rows.filter((r) => r.e === e && !r.ok).length);
  const perWeek = weeks.map((w) => empty.filter((r) => r.w === w).length);
  put(`no_domain.${e}.per_run_no_domain`, perWeek);
  put(`no_domain.${e}.min_per_run`, Math.min(...perWeek));
  put(`no_domain.${e}.max_per_run`, Math.max(...perWeek));

  // Per question: questions with six ok rows; how many of the six had no domain.
  const okCount = new Map(), emptyCount = new Map();
  for (const r of mine) okCount.set(r.q, (okCount.get(r.q) ?? 0) + 1);
  for (const r of empty) emptyCount.set(r.q, (emptyCount.get(r.q) ?? 0) + 1);
  const full = [...okCount].filter(([, c]) => c === 6).map(([q]) => q);
  const hist = Array(7).fill(0);
  for (const q of full) hist[emptyCount.get(q) ?? 0]++;
  put(`per_question.${e}.questions_ok_all_six`, full.length);
  put(`per_question.${e}.histogram`, hist);
  put(`per_question.${e}.never_empty`, rate(hist[0], full.length));
  put(`per_question.${e}.always_empty`, rate(hist[6], full.length));
  put(`per_question.${e}.sometimes_empty`, rate(full.length - hist[0] - hist[6], full.length));
  put(`per_question.${e}.at_least_once_empty`, rate(full.length - hist[0], full.length));

  const sizes = mine.map((r) => r.doms.length).filter((n) => n > 0).sort((a, b) => a - b);
  const mid = sizes.length / 2;
  put(`domains_per_answer.${e}`, {
    answers: sizes.length,
    domains_total: sizes.reduce((a, b) => a + b, 0),
    mean: Math.round((sizes.reduce((a, b) => a + b, 0) / sizes.length) * 100) / 100,
    median: sizes.length % 2 ? sizes[Math.floor(mid)] : (sizes[mid - 1] + sizes[mid]) / 2,
    min: sizes[0],
    max: sizes[sizes.length - 1],
  });
}

// Same question, same run: string keys "week|question|domain" per surface.
const okKey = (e) => new Set(ok.filter((r) => r.e === e).map((r) => `${r.w}|${r.q}`));
const both = [...okKey("aioverviews")].filter((k) => okKey("aimode").has(k));
const hasSrc = (e) => new Set(ok.filter((r) => r.e === e && r.doms.length).map((r) => `${r.w}|${r.q}`));
const A = hasSrc("aioverviews"), M = hasSrc("aimode");
const cellsBoth = both.filter((k) => A.has(k) && M.has(k));
const cb = new Set(cellsBoth);
const domKeys = (e) => new Set(ok.filter((r) => r.e === e && cb.has(`${r.w}|${r.q}`)).flatMap((r) => r.doms.map((d) => `${r.w}|${r.q}|${d}`)));
const DA = domKeys("aioverviews"), DM = domKeys("aimode");
const inter = [...DA].filter((k) => DM.has(k));
const union = new Set([...DA, ...DM]);
const sharedCells = new Set(inter.map((k) => k.split("|").slice(0, 2).join("|")));
put("same.cells_both_ok", both.length);
put("same.matrix", [
  both.filter((k) => A.has(k) && M.has(k)).length,
  both.filter((k) => A.has(k) && !M.has(k)).length,
  both.filter((k) => !A.has(k) && M.has(k)).length,
  both.filter((k) => !A.has(k) && !M.has(k)).length,
]);
put("same.aimode_domains_also_in_aio", rate(inter.length, DM.size));
put("same.aio_domains_also_in_aimode", rate(inter.length, DA.size));
put("same.shared_over_union", rate(inter.length, union.size));
put("same.cells_sharing_at_least_one_domain", rate(sharedCells.size, cellsBoth.length));

// Compare with results.json.
const res = JSON.parse(readFileSync(join(here, "results.json"), "utf8"));
const want = {};
for (const e of ["aioverviews", "aimode"]) {
  const nd = res.no_domain[e];
  for (const k of ["pooled_no_domain", "pooled_no_link_at_all", "pooled_only_google_links", "failed_rows", "min_per_run", "max_per_run"])
    want[`no_domain.${e}.${k}`] = nd[k];
  want[`no_domain.${e}.per_run_no_domain`] = nd.per_run.map((p) => p.no_domain);
  const pq = res.per_question[e];
  want[`per_question.${e}.questions_ok_all_six`] = pq.questions_ok_all_six;
  want[`per_question.${e}.histogram`] = Object.values(pq.histogram_runs_with_no_domain);
  for (const k of ["never_empty", "always_empty", "sometimes_empty", "at_least_once_empty"]) want[`per_question.${e}.${k}`] = pq[k];
  want[`domains_per_answer.${e}`] = res.domains_per_answer[e];
}
const s = res.same_question_same_run;
want["same.cells_both_ok"] = s.cells_both_ok;
want["same.matrix"] = [s.aio_sources_aimode_sources, s.aio_sources_aimode_none, s.aio_none_aimode_sources, s.both_none];
for (const k of ["aimode_domains_also_in_aio", "aio_domains_also_in_aimode", "shared_over_union", "cells_sharing_at_least_one_domain"]) want[`same.${k}`] = s[k];

let bad = 0;
for (const [k, v] of Object.entries(want)) {
  const a = JSON.stringify(got[k]), b = JSON.stringify(v);
  const same = a === b;
  if (!same) bad++;
  console.log(`${same ? "match" : "MISMATCH"}  ${k}  node=${a}${same ? "" : `  python=${b}`}`);
}
console.log(bad ? `${bad} of ${Object.keys(want).length} values DIFFER` : `All ${Object.keys(want).length} values match`);
process.exit(bad ? 1 : 0);
