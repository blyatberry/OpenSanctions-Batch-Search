# OpenSanctions Batch Search

This OSINT script searches multiple names on OpenSanctions and exports results to CSV.

File: `opensanctions_batch_search.py`

## Requirements

- Python 3.10+ (standard library only, no extra packages)
- Internet access

Optional, make it executable:

```bash
chmod +x opensanctions_batch_search.py
```

## Quick Start

```bash
./opensanctions_batch_search.py \
  --name "Svetlana Nekrasova" \
  --name "Veniamin Andreev" \
  --output opensanctions_results.csv
```

## Input Modes

The script can read names from multiple sources at the same time:

- `--name`: single names (can be used multiple times)
- `--input-txt`: text file, one name per line
- `--input-csv`: CSV file

### CSV Mode

1. Full name in one column:

```bash
./opensanctions_batch_search.py \
  --input-csv people.csv \
  --name-column "FullName" \
  --output results.csv
```

2. First name / last name from separate columns:

```bash
./opensanctions_batch_search.py \
  --input-csv diplomatische_vertretungen.csv \
  --first-name-column Vorname \
  --last-name-column Nachname \
  --output results.csv
```

Note: Without `--name-column`, the script defaults to `Vorname` and `Nachname`.

## Key Options

- `--output`: output file (default: `opensanctions_results.csv`)
- `--max-links`: max number of entity links per hit (default: `3`)
- `--sleep`: delay between requests in seconds (default: `0.5`)
- `--timeout`: HTTP timeout (default: `20`)
- `--limit`: process only first N names (`0` = all)
- `--no-dedupe`: disable name deduplication

## Output Format

The result CSV contains:

- `query_name`
- `status`
- `match_count`
- `search_url`
- `entity_results`
- `error`

### Status Values

- `match`: hit with parseable entity links
- `no_match`: OpenSanctions reports no match
- `unknown`: search page loaded, but no parseable entity links found
- `error`: request/parsing failed (details in `error`)

## Full Example

```bash
./opensanctions_batch_search.py \
  --input-csv diplomatische_vertretungen.csv \
  --output opensanctions_diplomaten.csv \
  --max-links 5 \
  --sleep 0.3
```

## Interpretation Notes

- Matches are name matches first, not confirmed identity matches.
- Results should be manually validated (transliteration, ambiguity, aliases).
