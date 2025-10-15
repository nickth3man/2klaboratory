import csv
import os
import re
import sys


def split_fields(line: str) -> list[str]:
    # line is already stripped of the leading line-number and the ' | '.
    # Use tabs when present, otherwise split on runs of 2+ spaces or tabs.
    if '\t' in line:
        parts: list[str] = [p.strip() for p in line.split('\t')]
    else:
        parts = [p.strip() for p in re.split(r'\s{2,}|\t+', line)]
    return parts


def process(src: str, dst: str) -> int:
    with open(src, 'r', encoding='utf-8') as f:
        # keep non-empty original lines (we treat blank lines as irrelevant)
        lines = [line.rstrip('\n') for line in f if line.strip() != '']
    if not lines:
        raise RuntimeError(f'Empty source: {src}')
    # header is the first line after the leading line-number and " | "
    header_line = (lines[0].split('|', 1)[1].strip()
                   if '|' in lines[0]
                   else lines[0].strip())
    headers = split_fields(header_line)
    rows: list[list[str]] = []
    for line in lines[1:]:
        if '|' in line:
            part = line.split('|', 1)[1].strip()
        else:
            part = line.strip()
        if not part:
            continue
        cells = split_fields(part)
        rows.append(cells)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, 'w', newline='', encoding='utf-8') as out:
        writer = csv.writer(out, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(headers)
        for r in rows:
            writer.writerow(r)
    return len(rows)


def verify(src: str, dst: str) -> tuple[int, int]:
    # count data rows in source (exclude header)
    with open(src, 'r', encoding='utf-8') as f:
        src_lines = [line for line in f if line.strip()]
    src_count = max(0, len(src_lines) - 1)
    # count rows in csv excluding header
    with open(dst, 'r', encoding='utf-8') as f:
        rows = list(csv.reader(f))
    csv_count = max(0, len(rows) - 1)
    return src_count, csv_count


def main() -> None:
    files = [
        ('builds/pf.md', 'builds/pf.csv'),
        ('builds/pg.md', 'builds/pg.csv'),
        ('builds/sf.md', 'builds/sf.csv'),
        ('builds/sg.md', 'builds/sg.csv'),
        ('builds/center.md', 'builds/center.csv'),
    ]
    results: list[tuple[str, int, int]] = []
    for src, dst in files:
        rows_written = process(src, dst)
        src_count, csv_count = verify(src, dst)
        if src_count != csv_count or src_count != rows_written:
            msg = (
                f'VERIFY FAIL: {src} -> {dst}: '
                f'source_rows={src_count}, '
                f'csv_rows={csv_count}, '
                f'rows_written={rows_written}'
            )
            print(msg, file=sys.stderr)
        results.append((dst, src_count, csv_count))
    for dst, s, c in results:
        print(f'{dst}\t{s}\t{c}')
    print(f'TOTAL\t{len(results)}')


if __name__ == '__main__':
    main()
