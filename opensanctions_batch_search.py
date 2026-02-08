#!/usr/bin/env python3
import argparse
import csv
import html
import re
import sys
import time
import urllib.parse
import urllib.request
from typing import Iterable, List, Sequence, Tuple


BASE_SEARCH_URL = "https://www.opensanctions.org/search/?q={query}"
NO_MATCH_MARKER = "No matching entities were found."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Batch search names on OpenSanctions and export results to CSV."
    )
    parser.add_argument(
        "--name",
        action="append",
        default=[],
        help="Single name to search. Can be passed multiple times.",
    )
    parser.add_argument(
        "--input-txt",
        help="Path to TXT file with one name per line.",
    )
    parser.add_argument(
        "--input-csv",
        help="Path to CSV input file.",
    )
    parser.add_argument(
        "--name-column",
        default="",
        help="CSV column containing full name.",
    )
    parser.add_argument(
        "--first-name-column",
        default="Vorname",
        help="CSV first-name column if --name-column is not set.",
    )
    parser.add_argument(
        "--last-name-column",
        default="Nachname",
        help="CSV last-name column if --name-column is not set.",
    )
    parser.add_argument(
        "--output",
        default="opensanctions_results.csv",
        help="Output CSV path.",
    )
    parser.add_argument(
        "--max-links",
        type=int,
        default=3,
        help="Maximum number of entity links to keep per name.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="HTTP timeout in seconds.",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.5,
        help="Delay between requests in seconds.",
    )
    parser.add_argument(
        "--no-dedupe",
        action="store_true",
        help="Do not deduplicate names before searching.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit number of names to search (0 = no limit).",
    )
    return parser.parse_args()


def load_names_from_txt(path: str) -> List[str]:
    names: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            name = line.strip()
            if name:
                names.append(name)
    return names


def load_names_from_csv(
    path: str, name_col: str, first_col: str, last_col: str
) -> Tuple[List[str], List[int]]:
    names: List[str] = []
    skipped_rows: List[int] = []
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=2):
            full_name = ""
            if name_col:
                full_name = (row.get(name_col) or "").strip()
            else:
                first = (row.get(first_col) or "").strip()
                last = (row.get(last_col) or "").strip()
                full_name = " ".join(part for part in (first, last) if part).strip()

            if full_name:
                names.append(full_name)
            else:
                skipped_rows.append(i)
    return names, skipped_rows


def unique_preserve_order(values: Sequence[str]) -> List[str]:
    seen = set()
    out = []
    for value in values:
        key = value.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(value)
    return out


def fetch_search_html(name: str, timeout: float) -> Tuple[str, str]:
    query = urllib.parse.quote_plus(name)
    url = BASE_SEARCH_URL.format(query=query)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        body = response.read().decode(charset, errors="replace")
    return url, body


def extract_entities(html_text: str, max_links: int) -> List[Tuple[str, str]]:
    pattern = re.compile(r'<a[^>]+href="(/entities/[^"]+)"[^>]*>(.*?)</a>', re.DOTALL)
    entities: List[Tuple[str, str]] = []
    seen = set()
    for rel_url, raw_title in pattern.findall(html_text):
        abs_url = "https://www.opensanctions.org" + rel_url
        title = html.unescape(re.sub(r"<[^>]+>", "", raw_title)).strip()
        key = (abs_url, title.lower())
        if key in seen:
            continue
        seen.add(key)
        entities.append((title, abs_url))
        if len(entities) >= max_links:
            break
    return entities


def build_name_list(args: argparse.Namespace) -> Tuple[List[str], List[str]]:
    names: List[str] = []
    notices: List[str] = []

    if args.name:
        names.extend(name.strip() for name in args.name if name.strip())

    if args.input_txt:
        names.extend(load_names_from_txt(args.input_txt))

    if args.input_csv:
        csv_names, skipped = load_names_from_csv(
            args.input_csv, args.name_column, args.first_name_column, args.last_name_column
        )
        names.extend(csv_names)
        if skipped:
            notices.append(
                f"Skipped {len(skipped)} empty row(s) in CSV: "
                + ", ".join(str(x) for x in skipped[:10])
                + (" ..." if len(skipped) > 10 else "")
            )

    if not args.no_dedupe:
        names = unique_preserve_order(names)

    return names, notices


def write_results(
    path: str, rows: Iterable[Tuple[str, str, int, str, str, str]]
) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "query_name",
                "status",
                "match_count",
                "search_url",
                "entity_results",
                "error",
            ]
        )
        writer.writerows(rows)


def main() -> int:
    args = parse_args()
    names, notices = build_name_list(args)

    if not names:
        print(
            "No names provided. Use --name, --input-txt or --input-csv.",
            file=sys.stderr,
        )
        return 2

    if args.limit > 0:
        names = names[: args.limit]

    result_rows: List[Tuple[str, str, int, str, str, str]] = []

    for i, name in enumerate(names, start=1):
        try:
            search_url, page = fetch_search_html(name, args.timeout)
            if NO_MATCH_MARKER in page:
                result_rows.append((name, "no_match", 0, search_url, "", ""))
            else:
                entities = extract_entities(page, args.max_links)
                if entities:
                    entity_str = " | ".join(
                        f"{title} ({url})" if title else url for title, url in entities
                    )
                    result_rows.append(
                        (name, "match", len(entities), search_url, entity_str, "")
                    )
                else:
                    result_rows.append(
                        (
                            name,
                            "unknown",
                            0,
                            search_url,
                            "",
                            "Search page returned without parseable entity links.",
                        )
                    )
        except Exception as exc:
            query = urllib.parse.quote_plus(name)
            search_url = BASE_SEARCH_URL.format(query=query)
            result_rows.append((name, "error", 0, search_url, "", str(exc)))

        if args.sleep > 0 and i < len(names):
            time.sleep(args.sleep)

    write_results(args.output, result_rows)

    for notice in notices:
        print(f"Notice: {notice}", file=sys.stderr)

    total = len(result_rows)
    matches = sum(1 for row in result_rows if row[1] == "match")
    no_match = sum(1 for row in result_rows if row[1] == "no_match")
    errors = sum(1 for row in result_rows if row[1] == "error")
    print(
        f"Done. Output: {args.output} | total={total}, match={matches}, "
        f"no_match={no_match}, error={errors}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
