#!/usr/bin/env bash
#
# Render the white paper to a single PDF.
#
# Regenerates the figures first, on purpose. The figures read straight from the
# evidence TSVs and the live-extraction database, so building the PDF without
# rebuilding them is how a chart ends up disagreeing with the table under it.
#
# Output lands on the Desktop. The markdown chapters remain the source of
# record; nothing here edits them.

set -euo pipefail

SRC="/home/obsidian/AtotoCarAI_whitepaper"
OUT="${1:-$HOME/Desktop}"
STAMP="$(date +%Y%m%d)"
PDF="$OUT/Atoto_AI_Box_whitepaper_${STAMP}_EMBARGOED.pdf"

cd "$SRC"

echo "==> figures"
python3 figures/make_figures.py >/dev/null

echo "==> assembling"
python3 tools/assemble.py > /tmp/.atoto_combined.md
trap 'rm -f /tmp/.atoto_combined.md' EXIT

echo "==> pandoc + xelatex"
mkdir -p "$OUT"
pandoc /tmp/.atoto_combined.md \
    --from=markdown+pipe_tables+raw_tex+tex_math_dollars \
    --pdf-engine=xelatex \
    --resource-path="$SRC" \
    --toc --toc-depth=2 \
    --include-in-header=tools/header.tex \
    --include-before-body=tools/titlepage.tex \
    --highlight-style=tango \
    -V documentclass=article \
    -V geometry:"a4paper,top=2.4cm,bottom=2.4cm,left=2.2cm,right=2.2cm" \
    -V fontsize=10pt \
    -V mainfont="Noto Sans" \
    -V sansfont="Noto Sans" \
    -V monofont="DejaVu Sans Mono" \
    -V colorlinks=true -V linkcolor=black -V urlcolor=black -V toccolor=black \
    -o "$PDF"

echo "==> $PDF"
ls -lh "$PDF" | awk '{print "    "$5}'
pdfinfo "$PDF" 2>/dev/null | grep -E "^(Pages|Page size)" || true
