#!/usr/bin/env python3
"""Resolve publication titles to DOIs via Crossref into tools/dois.json."""

import difflib
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "dois.json")
PAGE = os.path.join(os.path.dirname(HERE), "publications.html")
UA = "kai-homepage-linker/1.0 (mailto:kai.zhao@fsu.edu)"


def norm(s):
    s = html.unescape(s).lower()
    s = s.replace("’", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def query(title, field):
    url = ("https://api.crossref.org/works?query.%s=%s&rows=5"
           "&select=title,DOI,author" % (field, urllib.parse.quote(title)))
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)["message"]["items"]


def resolve(title):
    want = norm(title)
    best = (0.0, None)
    for field in ("bibliographic", "title"):
        try:
            items = query(title, field)
        except Exception as e:
            print("    ! %s: %s" % (field, e), file=sys.stderr)
            continue
        for it in items:
            got = (it.get("title") or [""])[0]
            score = difflib.SequenceMatcher(None, want, norm(got)).ratio()
            authors = " ".join(a.get("family", "") for a in it.get("author", []))
            if "Zhao" not in authors:
                score -= 0.08
            if score > best[0]:
                best = (score, it["DOI"])
        if best[0] >= 0.97:
            break
        time.sleep(1)
    return best


def main():
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    titles = re.findall(r'<p class="pub-title">(?:<a[^>]*>)?(.*?)(?:</a>)?</p>',
                        open(PAGE, encoding="utf-8").read())
    titles = [re.sub(r"<[^>]+>", "", t) for t in titles]

    hit = miss = 0
    for t in titles:
        key = norm(t)
        if key in cache:
            hit += 1 if cache[key] else 0
            continue
        score, doi = resolve(t)
        if doi and score >= 0.93:
            cache[key] = doi
            hit += 1
            print("  ok   %.2f  %s" % (score, t[:64]))
        else:
            cache[key] = None
            miss += 1
            print("  MISS %.2f  %s" % (score, t[:64]))
        json.dump(cache, open(CACHE, "w"), indent=1, sort_keys=True)
        time.sleep(1)

    print("\nresolved %d / %d  (%d unresolved)" % (hit, len(titles), len(titles) - hit))


if __name__ == "__main__":
    main()
