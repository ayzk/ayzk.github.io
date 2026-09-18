#!/usr/bin/env python3
r"""Regenerate publications.html from cv.tex."""

import html
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DOIS = os.path.join(HERE, "dois.json")
HOME = os.path.dirname(HERE)
CV = os.path.normpath(os.path.join(HOME, "..", "cv.tex"))
OUT = os.path.join(HOME, "publications.html")

SECTIONS = [
    ("Conference Publications", "Conference Papers", "conference"),
    ("Journal", "Journal Papers", "journal"),
    ("Workshop Publications", "Workshop Papers", "workshop"),
]

AWARD_RE = re.compile(r"\((Best Paper[^)]*|Best Paper)\)", re.I)


def key(s):
    s = html.unescape(s).lower().replace("\u2019", "'").replace("\ufb01", "fi")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def strip_comments(text):
    keep = [ln for ln in text.split("\n") if not ln.lstrip().startswith("%")]
    return "\n".join(keep)


def detex(s):
    s = re.sub(r"\\textbf\{([^{}]*)\}", r"<strong>\1</strong>", s)
    s = re.sub(r"\\underline\{([^{}]*)\}", r'<span class="pub-student">\1</span>', s)
    s = re.sub(r"\\textsl\{([^{}]*)\}", r"<em>\1</em>", s)
    s = re.sub(r"\\emph\{([^{}]*)\}", r"<em>\1</em>", s)
    s = s.replace("\\%", "%").replace("\\&", "&amp;").replace("\\_", "_")
    s = s.replace("``", "\u201c").replace("''", "\u201d")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def parse_section(body):
    body = strip_comments(body)
    entries = []
    for raw in re.split(r"\\item\b", body)[1:]:
        raw = raw.split("\\end{enumerate}")[0]
        raw = raw.replace("\\vspace{0.05in}", "").strip()
        if not raw:
            continue

        m = re.match(r"\s*\\textbf\{\[(.*?)\]\}", raw, re.S)
        tag, rest = (m.group(1).strip(), raw[m.end():]) if m else ("", raw)

        award = ""
        am = AWARD_RE.search(tag)
        if am:
            award = am.group(1).strip()
            tag = AWARD_RE.sub("", tag).strip()

        tm = re.search(r"``(.*?)''", rest, re.S)
        if tm:
            authors = rest[:tm.start()]
            title = tm.group(1)
            venue = rest[tm.end():]
        else:
            authors, title, venue = rest, "", ""

        entries.append({
            "tag": detex(tag),
            "award": detex(award),
            "authors": detex(authors).rstrip(" ,"),
            "title": detex(title).rstrip(" ."),
            "venue": detex(venue).lstrip(" ,"),
        })
    return entries


def render(entries, dois):
    out = []
    for e in entries:
        out.append('                <li class="pub">')
        badge = '<span class="pub-venue">%s</span>' % html.escape(e["tag"], quote=False) if e["tag"] else ""
        award = ('<span class="pub-award">%s</span>' % html.escape(e["award"], quote=False)) if e["award"] else ""
        out.append('                    <div class="pub-tags">%s%s</div>' % (badge, award))
        out.append('                    <div class="pub-body">')
        doi = dois.get(key(e["title"]))
        title = ('<a href="https://doi.org/%s" target="_blank" rel="noopener">%s</a>' % (doi, e["title"])
                 if doi else e["title"])
        out.append('                        <p class="pub-title">%s</p>' % title)
        out.append('                        <p class="pub-authors">%s</p>' % e["authors"])
        out.append('                        <p class="pub-meta">%s</p>' % e["venue"])
        out.append("                    </div>")
        out.append("                </li>")
    return "\n".join(out)


def main():
    tex = open(CV, encoding="utf-8").read()
    dois = json.load(open(DOIS)) if os.path.exists(DOIS) else {}

    marks = [(m.start(), m.group(1)) for m in re.finditer(r"\\section\{\\mysidestyle(.*?)\}", tex, re.S)]
    marks.append((len(tex), ""))

    blocks = []
    for needle, heading, slug in SECTIONS:
        body = None
        for i, (pos, title) in enumerate(marks[:-1]):
            if needle in title:
                body = tex[pos:marks[i + 1][0]].split("\\end{enumerate}")[0]
                break
        if body is None:
            raise SystemExit("section not found in cv.tex: " + heading)
        blocks.append((heading, slug, parse_section(body)))

    parts = []
    for heading, slug, entries in blocks:
        parts.append('        <section id="%s">' % slug)
        parts.append('            <h2 class="section-title">%s <span class="count">%d</span></h2>'
                     % (heading, len(entries)))
        parts.append('            <ol class="pub-list">')
        parts.append(render(entries, dois))
        parts.append("            </ol>")
        parts.append("        </section>")
    generated = "\n".join(parts)

    page = open(OUT, encoding="utf-8").read()
    new = re.sub(
        r"(<!-- PUBS-START -->).*?(<!-- PUBS-END -->)",
        lambda _: "<!-- PUBS-START -->\n" + generated + "\n        <!-- PUBS-END -->",
        page,
        flags=re.S,
    )
    open(OUT, "w", encoding="utf-8").write(new)

    everything = [e for _, _, es in blocks for e in es]
    total = len(everything)
    TOP = ("SC", "HPDC", "ICS", "SIGMOD", "VLDB", "ICDE")
    top = sum(1 for e in everything if e["tag"].split("'")[0].strip() in TOP)
    honors = sum(1 for e in everything if e["award"])
    stats = "\n".join([
        '        <ul class="stats">',
        '            <li><span class="stat-value">%d</span><span class="stat-label">Peer-reviewed papers</span></li>' % total,
        '            <li><span class="stat-value">%d</span><span class="stat-label" title="SC, HPDC, ICS, SIGMOD, VLDB, ICDE">At CSRankings venues</span></li>' % top,
        '            <li><span class="stat-value">%d</span><span class="stat-label">Best-paper honors</span></li>' % honors,
        '        </ul>',
    ])
    page = open(OUT, encoding="utf-8").read()
    page = re.sub(r"(<!-- STATS-START -->).*?(<!-- STATS-END -->)",
                  lambda _: "<!-- STATS-START -->\n" + stats + "\n        <!-- STATS-END -->",
                  page, flags=re.S)
    open(OUT, "w", encoding="utf-8").write(page)

    for heading, _, entries in blocks:
        print("%-30s %d" % (heading, len(entries)))
    print("%-30s %d" % ("TOTAL", total))


if __name__ == "__main__":
    main()
