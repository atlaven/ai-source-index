#!/usr/bin/env python3
"""Fetch every published week of the Promvia AI Source Index and rebuild the CSVs.

Standard library only. Run from the repository root:

    python3 scripts/fetch.py

Writes data/raw/<week>.json (the API response for that week, unmodified) and two flat files:
data/citations.csv (one row per engine answer and cited domain) and data/cited_urls.csv (one row
per engine answer and cited URL). A failed answer, or one that cited nothing, still gets a row
with an empty domain/url, so coverage is visible and never mistaken for a citation.
"""
import csv
import json
import pathlib
import urllib.request

API = "https://promvia.app/api/public/ai-source-index/rows"
ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

COLUMNS = ["week", "captured_at", "instrument", "query_id", "question", "shape",
           "engine", "role", "status", "failure_class"]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "ai-source-index-fetch/1"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    weeks = get(API)["weeksAvailable"]
    payloads = []
    for week in sorted(weeks):
        payload = get(f"{API}?week={week}")
        (RAW / f"{week}.json").write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n")
        payloads.append(payload)

    with open(ROOT / "data" / "citations.csv", "w", newline="") as fd, \
         open(ROOT / "data" / "cited_urls.csv", "w", newline="") as fu:
        wd, wu = csv.writer(fd), csv.writer(fu)
        wd.writerow(COLUMNS + ["domain"])
        wu.writerow(COLUMNS + ["url"])
        for payload in payloads:
            for w in payload["weeks"]:
                for r in w["rows"]:
                    base = [w["week"], w["capturedAt"], w["instrument"], r["queryId"], r["question"],
                            r["shape"], r["engine"], r["role"], r["status"], r.get("failureClass", "")]
                    for d in (r.get("domains") or [""]):
                        wd.writerow(base + [d])
                    for u in (r.get("citedUrls") or [""]):
                        wu.writerow(base + [u])
    print(f"{len(weeks)} weeks: {', '.join(sorted(weeks))}")


if __name__ == "__main__":
    main()
