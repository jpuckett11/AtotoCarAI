#!/usr/bin/env python3
"""
Concatenate the chapter files into one markdown document on stdout.

Three things happen here that a plain `cat` would get wrong:

  * The title block at the top of chapter 00 is dropped, because titlepage.tex
    sets the title. Leaving it in prints the title twice.
  * The per-file "EMBARGOED, see front matter" reminder blockquote is dropped
    from every chapter after the first. In a single bound document it fires
    seven times; the page footer already carries it on every page.
  * Chapters are separated by a page break, so a chapter never starts three
    lines from the bottom of a page.
"""

import os
import re
import sys

SRC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CHAPTERS = [
    "00_FRONT_AND_ACQUISITION.md",
    "01_ANALYSIS_METHOD.md",
    "02_TRUST_AND_IDENTITY.md",
    "03_CONTROL_AND_COLLECTION.md",
    "04_DELIVERY_SUPPLY_AND_PROOF.md",
    "05_DISCLOSURE_AND_CLOSE.md",
    "06_APPENDICES.md",
]

EMBARGO_LINE = re.compile(r"^>\s*\**EMBARGOED\.", re.I)

# "# Chapters 9, 10 and 11" and "# Chapter 4 - Identity, and Chapter 5 - Trust"
# are artefacts of splitting the paper across files. The real chapter heading
# always follows a few lines below, so in a bound document the wrapper prints
# a heading nobody wrote. Files whose first H1 IS a real chapter heading (03,
# 06) do not match this and are left alone.
WRAPPER_H1 = re.compile(r"^#\s+Chapters\s|^#\s+Chapter\s.*,\s*and\s+Chapter\s")


def strip_leading(text, predicate):
    """Drop leading blank lines and any opening lines the predicate rejects."""
    lines = text.splitlines()
    i = 0
    while i < len(lines) and (not lines[i].strip() or predicate(lines[i])):
        i += 1
    return "\n".join(lines[i:])


def front_matter(text):
    """
    Chapter 00 only: drop the title block and the embargo blockquote.

    titlepage.tex sets both, verbatim. Leaving them in the body prints the
    title twice and the embargo notice twice on facing pages.
    """
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == "---":
            text = "\n".join(lines[i + 1:])
            break
    return strip_leading(text, lambda l: l.startswith(">") or l.strip() == "---")


def chapter(text):
    """
    Chapters 01-06: drop the wrapper H1 and the rule beneath it, then drop the
    embargo reminder wherever it sits.

    The reminder is stripped globally rather than only from the preamble
    because in two of the files it follows a real chapter heading rather than
    a wrapper, and a preamble-only rule leaves those behind. The page footer
    carries the embargo on every page regardless.
    """
    text = strip_leading(text, lambda l: WRAPPER_H1.match(l)
                         or EMBARGO_LINE.match(l) or l.strip() in ("---", ">"))
    return "\n".join(l for l in text.splitlines() if not EMBARGO_LINE.match(l))


out = []
for n, name in enumerate(CHAPTERS):
    with open(os.path.join(SRC, name), encoding="utf-8") as fh:
        body = fh.read()

    if n == 0:
        body = front_matter(body)
    else:
        body = chapter(body)
        out.append("\n\n\\newpage\n\n")

    out.append(body.rstrip() + "\n")

sys.stdout.write("".join(out))
