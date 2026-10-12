// Independent second derivation of the headline numbers in results.json (shapes.py).
// Different code path: reads the flat CSVs in ../../data (built by scripts/fetch.py), not the raw
// JSON, derives domains from cited_urls.csv hosts for the platform shares, and compares.
// Run: node crosscheck.mjs   (from this directory)
import { readFileSync } from "node:fs";

const here = new URL(".", import.meta.url).pathname;
const parse = (path) => {
  const [head, ...lines] = readFileSync(path, "utf8").trim().split(/\r?\n/);
  const cols = head.split(",");
  return lines.map((line) => {
    // RFC 4180: fields may be quoted and contain commas or doubled quotes.
    const out = []; let cur = ""; let q = false;
    for (let i = 0; i < line.length; i++) {
      const c = line[i];
      if (q) { if (c === '"' && line[i + 1] === '"') { cur += '"'; i++; } else if (c === '"') q = false; else cur += c; }
      else if (c === '"') q = true; else if (c === ",") { out.push(cur); cur = ""; } else cur += c;
    }
    out.push(cur);
    return Object.fromEntries(cols.map((c, i) => [c, out[i] ?? ""]));
  });
};
const res = JSON.parse(readFileSync(here + "results.json", "utf8"));
// The CSVs grow every week; this study is pinned to the weeks results.json was computed on.
const inStudy = (r) => res.weeks.includes(r.week);
const urls = parse(here + "../../data/cited_urls.csv").filter((r) => inStudy(r) && r.role === "answer" && r.status === "ok");
const doms = parse(here + "../../data/citations.csv").filter((r) => inStudy(r) && r.role === "answer" && r.status === "ok");

const key = (r) => `${r.week}|${r.query_id}|${r.engine}`;
const answers = new Map(); // shape -> Set(answer key)
for (const r of doms) { if (!answers.has(r.shape)) answers.set(r.shape, new Set()); answers.get(r.shape).add(key(r)); }

const host = (u) => { try { return new URL(u).hostname.replace(/^www\./, "").toLowerCase(); } catch { return ""; } };
// The index's `domains` keep a mobile host (m.youtube.com) as its own domain; mirror that rule, and
// report the folded count separately so the difference is explained rather than hidden.
const owns = (h, base) => h === base;
const ownsFolded = (h, base) => h === base || h.endsWith("." + base) || (base === "youtube.com" && h === "youtu.be");

let bad = 0;
const check = (label, mine, theirs) => {
  const ok = mine === theirs;
  if (!ok) bad++;
  console.log(`${ok ? "ok  " : "DIFF"} ${label}: crosscheck ${mine}, shapes.py ${theirs}`);
};

for (const shape of ["best", "alternatives", "compare", "howto-buy"]) {
  const s = res.shapes[shape];
  check(`${shape} answers`, answers.get(shape).size, s.answers_pooled);
  for (const base of ["youtube.com", "reddit.com", "consumerreports.org"]) {
    const set = new Set(urls.filter((r) => r.shape === shape && r.url && owns(host(r.url), base)).map(key));
    check(`${shape} ${base} answers citing (from URLs)`, set.size, res.platforms[base][shape].answer_share_pooled.k);
  }
  const re = /(^|[/\-_])(vs|versus|alternatives?|compare|comparison|comparisons)([/\-_.]|$)/;
  const shaped = urls.filter((r) => r.shape === shape && r.url);
  const comp = shaped.filter((r) => { try { return re.test(new URL(r.url).pathname.toLowerCase()); } catch { return false; } });
  check(`${shape} comparison-shaped URLs`, `${comp.length}/${shaped.length}`, `${s.comparison_urls_pooled.k}/${s.comparison_urls_pooled.n}`);
  // Weekly #1 domain from citations.csv, ties broken alphabetically.
  const top1 = res.weeks.map((w) => {
    const c = new Map();
    for (const r of doms) if (r.week === w && r.shape === shape && r.domain) c.set(r.domain, (c.get(r.domain) ?? 0) + 1);
    const max = Math.max(...c.values());
    return [...c].filter(([, n]) => n === max).map(([d]) => d).sort().join("+");
  });
  check(`${shape} weekly #1`, top1.join(","), s.weekly_top1.map((x) => x.domain).join(","));
}
const folded = new Set(urls.filter((r) => r.shape === "compare" && r.url && ownsFolded(host(r.url), "youtube.com")).map(key)).size;
console.log(`note compare youtube.com with m.youtube.com folded in: ${folded}/${answers.get("compare").size}`);
console.log(bad ? `${bad} DIFFERENCES` : "ALL MATCH");
