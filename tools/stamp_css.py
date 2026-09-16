#!/usr/bin/env python3
"""Stamp css/style.css's content hash onto every page's <link>.

Run after editing the stylesheet, before committing:

    python3 tools/stamp_css.py

GitHub Pages serves CSS with cache-control: max-age=600, so without this a
browser can pair freshly deployed HTML with 10-minute-stale CSS. That bit us
once: the mobile nav markup changed, the cached CSS still hid the link row,
and the navigation disappeared on phones.
"""

import glob
import hashlib
import os
import re

HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSS = os.path.join(HOME, "css", "style.css")

digest = hashlib.md5(open(CSS, "rb").read()).hexdigest()[:8]

changed = []
for page in sorted(glob.glob(os.path.join(HOME, "*.html"))):
    src = open(page, encoding="utf-8").read()
    out = re.sub(r'(\./css/style\.css)(\?v=[0-9a-f]+)?', r'\1?v=' + digest, src)
    if out != src:
        open(page, "w", encoding="utf-8").write(out)
        changed.append(os.path.basename(page))

print("style.css -> v=%s" % digest)
print("updated: %s" % (", ".join(changed) if changed else "(already current)"))
