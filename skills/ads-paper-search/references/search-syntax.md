# ADS search syntax — full reference

The ADS search API (`GET /v1/search/query`) uses Apache Solr query syntax with
ADS-specific fields and operators. This is the same syntax as the search box at
https://ui.adsabs.harvard.edu/.

## Query parameters

| Param | Meaning |
|-------|---------|
| `q` | The query (required) |
| `fl` | Comma-separated fields to return |
| `rows` | Results per page (default 10, max 2000) |
| `start` | Offset for pagination |
| `sort` | `field asc|desc`; fields: `score`, `date`, `citation_count`, `read_count`, `classic_factor`, `first_author`, `bibcode` |
| `fq` | Filter query (cached; good for repeated constraints like `database:astronomy`) |

## Search fields

| Field | Notes / example |
|-------|-----------------|
| `abs:` | abstract + title + keywords: `abs:"dark energy"` |
| `abstract:` | abstract only |
| `ack:` | acknowledgments section |
| `aff:` | affiliation string: `aff:"UCLA"` |
| `arXiv:` | arXiv ID: `arXiv:1711.05799` |
| `author:` | `author:"Last, F"`; `author:"^Last"` = first author; `author_count:[1 TO 5]` |
| `bibcode:` | 19-char ADS ID: `bibcode:2003AJ....125..525J` |
| `bibstem:` | journal abbreviation: `bibstem:ApJ`, `bibstem:MNRAS`, `bibstem:JGRA`, `bibstem:arXiv` |
| `body:` | article body text |
| `citation_count:` | `citation_count:[100 TO *]` |
| `collection:` | `astronomy`, `physics`, `general`, `earthscience`, `heliophysics`, `planetary_science` (alias: `database:`) |
| `doctype:` | `article`, `eprint`, `review`, `book`, `proceedings`, `inproceedings`, `phdthesis`, `software`, `dataset` |
| `doi:` | `doi:10.1086/345794` |
| `full:` | fulltext + acknowledgments |
| `identifier:` | matches bibcode, DOI, or arXiv ID |
| `inst:` | curated institution: `inst:MIT` |
| `keyword:` | publisher-supplied keywords |
| `object:` | SIMBAD/NED object: `object:"M 31"` |
| `orcid:` | `orcid:0000-0002-4110-3511` |
| `page:` | first page |
| `property:` | see below |
| `pub:` | full journal name: `pub:"The Astrophysical Journal"` |
| `pubdate:` | `pubdate:[2020-01 TO 2020-12]` |
| `title:` | `title:exoplanets` |
| `volume:` | `volume:105` |
| `year:` | `year:2000`, `year:2000-2005` |

## `property:` values

`refereed`, `notrefereed`, `article`, `eprint_opened`, `openaccess`,
`ads_openaccess`, `pub_openaccess`, `eprint_openaccess`, `data` (has data
links), `esource` (has electronic source), `inspection`, `ocrabstract`,
`associated`, `toc`.

## Boolean & positional operators

- `AND` (default between terms), `OR`, `NOT` / `-term`
- Grouping: `(transit OR "radial velocity") AND exoplanet`
- Proximity: `"weak lensing"~3` (words within 3 positions)
- Wildcards: `gala*` (not allowed as first character)
- Ranges: `[A TO B]` inclusive

## Functional (second-order) operators

Wrap any query Q:

| Operator | Returns |
|----------|---------|
| `citations(Q)` | papers citing the papers matched by Q |
| `references(Q)` | papers cited by the papers matched by Q |
| `reviews(Q)` | papers most cited alongside literature on Q (good for review-style overviews) |
| `useful(Q)` | papers frequently cited by reviews on Q (methods/tools) |
| `similar(Q)` | abstracts textually similar to Q's results |
| `trending(Q)` | papers being read now by readers of Q's results |
| `topn(N, Q, sort)` | top N of Q by sort |
| `pos(author:"Last", 2)` | match at position (2nd author) |

## Return fields (`fl`)

Common: `bibcode`, `title`, `author` (list), `first_author`, `year`, `pubdate`,
`pub`, `bibstem`, `volume`, `page`, `abstract`, `doi`, `arxiv_class`,
`citation_count`, `read_count`, `keyword`, `aff`, `orcid_pub`, `property`,
`doctype`, `identifier`, `esources`, `data`, `reference` (list of cited
bibcodes — large).

## Other API endpoints (base `https://api.adsabs.harvard.edu/v1`)

All need header `Authorization: Bearer TOKEN`.

| Endpoint | Method | Body / notes |
|----------|--------|--------------|
| `/search/query` | GET | main search |
| `/search/bigquery?q=*:*&rows=N` | POST | search restricted to a list of up to 2000 bibcodes (`Content-Type: big-query/csv`, body: `bibcode\nBIB1\n...`) |
| `/export/{format}` | POST | `{"bibcode": ["..."]}`; formats: `bibtex`, `bibtexabs`, `aastex`, `endnote`, `medlars`, `procite`, `refworks`, `ris`, `mnras`, `soph`, `icarus`, `csl`, `custom` |
| `/metrics` | POST | `{"bibcodes": ["..."]}` → h-index, citation stats, reads |
| `/resolver/{bibcode}` | GET | links to full text, data, arXiv for a record |
| `/reference/text` | POST | `{"reference": ["free-text citation string"]}` → resolve to bibcode |
| `/objects` | POST | `{"query": ["object:Andromeda"]}` → SIMBAD/NED object resolution |

## Rate limits

Response headers `X-RateLimit-Limit` / `-Remaining` / `-Reset`. Defaults:
search 5000/day, export 100/day (bulk), metrics 100/day. Quotas reset daily.
