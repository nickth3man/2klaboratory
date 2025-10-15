#!/usr/bin/env python3
import re
import csv
import sys

src = "builds/center.md"
dst = "builds/center.csv"

with open(src, encoding="utf-8") as f:
    lines = [l.rstrip("\n") for l in f]

rows = []
for line in lines:
    m = re.search(r'\s*\d+\s*\|\s*(.*)', line)
    if m:
        rest = m.group(1)
    else:
        rest = line
    # split on tabs or sequences of 2+ spaces
    fields = re.split(r'\t+|\s{2,}', rest)
    fields = [fld.strip() for fld in fields]
    rows.append(fields)

with open(dst, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
    for r in rows:
        writer.writerow(r)

print("Wrote", dst, "rows:", max(0, len(rows) - 1))
sys.exit(0)
