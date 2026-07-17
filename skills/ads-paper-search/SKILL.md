---
name: ads-paper-search
description: Use when searching for scientific papers in astronomy, astrophysics, space physics, heliophysics, or planetary science — finding literature by topic/author/year, looking up citations or references of a paper, exporting BibTeX, resolving a bibcode/DOI/arXiv ID, or computing citation metrics. Connects to the NASA ADS (Astrophysics Data System, ui.adsabs.harvard.edu) API.
---

# NASA ADS Paper Search

## Overview

Search the NASA Astrophysics Data System (ADS / SciX) — the standard literature
database for astronomy, astrophysics, space physics, and planetary science
(~15M records). This skill wraps the ADS API (`https://api.adsabs.harvard.edu/v1`)
via a bundled stdlib-only Python script.

## Setup (one-time, per user)

A personal ADS API token is required (free). The script looks for it in:

1. `ADS_API_TOKEN` environment variable (use this on claude.ai or in CI)
2. `~/.ads/token` — written by the `setup` subcommand below

If a command exits with "No ADS API token found", relay its setup steps to the
user and ask for their token:

1. Create a free account at https://ui.adsabs.harvard.edu/
2. Copy the token from https://ui.adsabs.harvard.edu/user/settings/token
3. Run `python3 scripts/ads.py setup THEIR_TOKEN` — this verifies the token
   against the API and saves it to `~/.ads/token` (mode 600), so setup never
   needs to happen again.

Never hardcode a token into this skill or share one token between users — ADS
tokens are personal and rate limits (5000 requests/day) are per-account.

## Quick reference

Run all commands with `python3 scripts/ads.py` (paths relative to this skill's
directory). Add `--json` for raw JSON, `-h` for full options.

| Task | Command |
|------|---------|
| Search papers | `search 'QUERY' --rows 10 --sort "citation_count desc"` |
| Search with abstracts | `search 'QUERY' --abstract` |
| Look up bibcode(s) | `get 2016SSRv..199....5B [more...]` |
| BibTeX export | `export bibtex 2016SSRv..199....5B [more...]` |
| Papers citing X | `citations BIBCODE --rows 25` |
| Papers cited by X | `references BIBCODE --rows 25` |
| Just a citation count | `citations BIBCODE --rows 1` — total is in the `# N citations` header |
| Citation metrics / h-index | `metrics BIBCODE [more...]` |

Sort options: `score desc` (relevance, default), `citation_count desc`,
`date desc` (newest first), `read_count desc`.

## Query syntax essentials

Unfielded terms search title+abstract+keywords. Combine with `AND` (implicit),
`OR`, `NOT`, parentheses. Quote phrases.

| Field | Example |
|-------|---------|
| Author | `author:"Smith, J"` — first author: `author:"^Smith, J"` |
| Year / range | `year:2024`, `year:2019-2024` |
| Title / abstract | `title:"magnetic reconnection"`, `abs:"radiation belt"` |
| Full text | `full:"chorus waves"` |
| Journal | `bibstem:ApJ`, `bibstem:JGRA`, `bibstem:GeoRL` |
| Object (SIMBAD) | `object:"Sgr A*"` |
| Identifiers | `bibcode:2022ApJ...930L..12E`, `doi:10.1126/science.aaf2939`, `arXiv:2101.01234` (as unfielded term or `identifier:`) |
| Refereed only | add `property:refereed` |
| Open access | `property:openaccess` |
| Collection | `collection:astronomy` / `physics` / `heliophysics` / `planetary_science` |
| Citation graph | `citations(bibcode:X)`, `references(bibcode:X)`, `reviews(topic)`, `useful(...)`, `similar(...)`, `trending(...)` |

Example — highly-cited recent first-author papers on radiation belts:

```bash
python3 scripts/ads.py search 'author:"^Li, W" abs:"radiation belt" year:2020-2026 property:refereed' \
  --sort "citation_count desc" --rows 10
```

Full field list and operators: see [references/search-syntax.md](references/search-syntax.md).

## Workflow guidance

- **Literature search**: start broad, check the reported total count, then
  narrow with fields (`year:`, `bibstem:`, `property:refereed`) or paginate with
  `--start`. Fetch abstracts (`--abstract`) only for the shortlist.
- **"Find THE paper"**: prefer `--sort "citation_count desc"` for foundational
  work, `date desc` for latest results.
- **Review articles**: `reviews(TOPIC)` or add `doctype:review` / `property:refereed`.
- **Follow the citation graph**: use `citations`/`references` subcommands on a
  key paper to expand a literature review in both directions.
- **Paper URL**: any result links as
  `https://ui.adsabs.harvard.edu/abs/<BIBCODE>/abstract`.

## Common mistakes

- **Author names need quotes and "Last, First" order**: `author:"Chu, X"`, not
  `author:Chu X`. Use `^` inside the quotes for first-author.
- **Bibcodes are case-sensitive** and exactly 19 characters; don't reconstruct
  them by hand — get them from search results.
- **Escape `&` in shell**: bibcodes like `1979A&A....75..228L` must be quoted
  in bash.
- **`collection:` filters silently drop relevant records** (e.g.
  `collection:physics` excludes mission/instrument papers indexed only under
  astronomy). Search without a collection filter first; add one only if the
  unfiltered results are noisy.
- **Rate limits**: 5000 requests/day for search. The script warns when <100
  remain. Batch bibcodes into one `get`/`export`/`metrics` call instead of
  looping.
- **Large downloads**: `--rows` max is 2000 per request; paginate with `--start`.

## Direct API (no script)

If the script is unavailable, call the API directly:

```bash
curl -H "Authorization: Bearer $ADS_API_TOKEN" \
  "https://api.adsabs.harvard.edu/v1/search/query?q=exoplanet+atmospheres&fl=bibcode,title,year&rows=5"
```

Full API docs: https://ui.adsabs.harvard.edu/help/api/api-docs.html
