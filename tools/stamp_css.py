#!/usr/bin/env python3
"""Stamp css/style.css's content hash onto every page's <link>."""

import glob
import hashlib
import os
import re

HOME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
digest = hashlib.md5(open(os.path.join(HOME, "css", "style.css"), "rb").read()).hexdigest()[:8]

for page in sorted(glob.glob(os.path.join(HOME, "*.html"))):
    src = open(page, encoding="utf-8").read()
    out = re.sub(r'(\./css/style\.css)(\?v=[0-9a-f]+)?', r'\1?v=' + digest, src)
    if out != src:
        open(page, "w", encoding="utf-8").write(out)

print("style.css -> v=%s" % digest)
