#!/usr/bin/env python3
import argparse
import html
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime


BASE_SEARCH_URL = "https://www.opensanctions.org/search/?q={query}"
NO_MATCH_MARKER = "No matching entities were found."


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Interactive OpenSanctions search from terminal."
    )
    parser.add_argument(
        "--name",
        default="",
        help="Optional single name for one-shot search (non-interactive).",
    )
    parser.add_argument(
        "--max-links",
        type=int,
        default=5,
        help="Maximum number of entity links shown per query.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="HTTP timeout in seconds.",
    )
    return parser.parse_args()


def fetch_search_html(name: str, timeout: float) -> tuple[str, str]:
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


def extract_entities(page: str, max_links: int) -> list[tuple[str, str]]:
    pattern = re.compile(r'<a[^>]+href="(/entities/[^"]+)"[^>]*>(.*?)</a>', re.DOTALL)
    entities: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for rel_url, raw_title in pattern.findall(page):
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


def search_once(name: str, max_links: int, timeout: float) -> int:
    try:
        url, page = fetch_search_html(name, timeout)
    except Exception as exc:
        print(f"\nName: {name}")
        print(f"Status: error")
        print(f"Fehler: {exc}")
        return 1

    print(f"\nName: {name}")
    print(f"Suche: {url}")

    if NO_MATCH_MARKER in page:
        print("Status: no_match")
        print("Treffer: 0")
        return 0

    entities = extract_entities(page, max_links)
    if not entities:
        print("Status: unknown")
        print("Hinweis: Seite ohne auslesbare Entity-Links.")
        return 0

    print("Status: match")
    print(f"Treffer (max {max_links}): {len(entities)}")
    for idx, (title, link) in enumerate(entities, start=1):
        label = title if title else "(ohne Titel)"
        print(f"{idx}. {label}")
        print(f"   {link}")
    return 0


def interactive_loop(max_links: int, timeout: float) -> int:
    print("OpenSanctions Terminalsuche")
    print("Gib einen Namen ein und drücke Enter.")
    print("Befehle: :quit oder :q beendet das Programm.")

    while True:
        try:
            name = input("\nName> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBeendet.")
            return 0

        if not name:
            continue
        if name.lower() in {":quit", ":q", "quit", "exit"}:
            print("Beendet.")
            return 0

        _ = search_once(name, max_links, timeout)
        print(f"Zeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def main() -> int:
    args = parse_args()
    if args.name:
        return search_once(args.name.strip(), args.max_links, args.timeout)
    return interactive_loop(args.max_links, args.timeout)


if __name__ == "__main__":
    sys.exit(main())
