#!/usr/bin/env python3
"""NASA ADS (Astrophysics Data System) API client — stdlib only.

Token resolution order:
  1. ADS_API_TOKEN environment variable
  2. ~/.ads/token file (written by the `setup` subcommand)

Subcommands:
  setup       One-time: verify a token and save it to ~/.ads/token
  search      Search for papers (full ADS/Solr query syntax)
  get         Fetch full metadata for one or more bibcodes
  export      Export citations (bibtex, aastex, ris, endnote, ...)
  citations   List papers that cite a given bibcode
  references  List papers referenced by a given bibcode
  metrics     Citation metrics for a set of bibcodes

Run `ads.py <subcommand> -h` for options.
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request

API_BASE = "https://api.adsabs.harvard.edu/v1"
DEFAULT_FIELDS = "bibcode,title,author,year,pub,citation_count,doi,abstract"


TOKEN_FILE = os.path.expanduser("~/.ads/token")

SETUP_INSTRUCTIONS = """\
No ADS API token found. To set up (takes ~1 minute, free):
  1. Create a free account at https://ui.adsabs.harvard.edu/
  2. Copy your personal token from https://ui.adsabs.harvard.edu/user/settings/token
  3. Run: python3 {script} setup YOUR_TOKEN
     (verifies the token, then saves it to ~/.ads/token for future use)
Alternatively, set the ADS_API_TOKEN environment variable."""


def find_token():
    tok = os.environ.get("ADS_API_TOKEN") or os.environ.get("ADS_DEV_KEY")
    if tok:
        return tok.strip()
    if os.path.isfile(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            tok = f.read().strip()
        if tok:
            return tok
    sys.exit(SETUP_INSTRUCTIONS.format(script=sys.argv[0]))


def request(method, path, token, params=None, body=None):
    url = API_BASE + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": "Bearer " + token,
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            remaining = resp.headers.get("X-RateLimit-Remaining")
            if remaining is not None and int(remaining) < 100:
                print(f"warning: only {remaining} API requests remaining today",
                      file=sys.stderr)
            return json.load(resp)
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:500]
        if "not in allowlist" in detail or e.headers.get("x-deny-reason"):
            sys.exit(f"error: HTTP {e.code} — blocked by this environment's "
                     f"network egress proxy, NOT by ADS: {detail}\n"
                     "Fix: allow the domain api.adsabs.harvard.edu in the "
                     "sandbox network settings (on claude.ai: Settings > "
                     "Capabilities > Allow network egress > Additional "
                     "allowed domains).")
        sys.exit(f"error: HTTP {e.code} from the ADS API: {detail}")


def print_docs(docs, as_json):
    if as_json:
        json.dump(docs, sys.stdout, indent=2)
        print()
        return
    for d in docs:
        title = (d.get("title") or ["<no title>"])[0]
        authors = d.get("author") or []
        author_str = "; ".join(authors[:3]) + (" et al." if len(authors) > 3 else "")
        line2_parts = [str(d.get("year", "")), d.get("pub", ""),
                       f"citations: {d.get('citation_count', '?')}"]
        doi = d.get("doi")
        if doi:
            line2_parts.append("doi:" + doi[0])
        print(f"[{d.get('bibcode', '?')}] {title}")
        if author_str:
            print(f"    {author_str}")
        print(f"    {' | '.join(p for p in line2_parts if p)}")
        if d.get("abstract"):
            print(f"    {d['abstract']}")
        print()


def do_setup(args):
    token = args.token.strip()
    data = request("GET", "/search/query", token,
                   params={"q": "star", "rows": 1, "fl": "bibcode"})
    if "response" not in data:
        sys.exit("error: token verification returned an unexpected response")
    os.makedirs(os.path.dirname(TOKEN_FILE), exist_ok=True)
    with open(TOKEN_FILE, "w") as f:
        f.write(token + "\n")
    os.chmod(TOKEN_FILE, 0o600)
    print(f"Token verified and saved to {TOKEN_FILE}. You're all set.")


def do_search(args, token):
    fl = args.fields
    if args.abstract and "abstract" not in fl:
        fl += ",abstract"
    params = {"q": args.query, "fl": fl, "rows": args.rows,
              "start": args.start, "sort": args.sort}
    if args.filter:
        params["fq"] = args.filter
    data = request("GET", "/search/query", token, params=params)
    resp = data["response"]
    print(f"# {resp['numFound']} results (showing {args.start + 1}-"
          f"{args.start + len(resp['docs'])}), sorted by {args.sort}\n",
          file=sys.stderr)
    docs = resp["docs"]
    if not args.abstract and not args.json:
        for d in docs:
            d.pop("abstract", None)
    print_docs(docs, args.json)


def do_get(args, token):
    q = " OR ".join(f"bibcode:{b}" for b in args.bibcodes)
    params = {"q": q, "fl": args.fields, "rows": len(args.bibcodes)}
    data = request("GET", "/search/query", token, params=params)
    print_docs(data["response"]["docs"], args.json)


def do_export(args, token):
    data = request("POST", f"/export/{args.format}", token,
                   body={"bibcode": args.bibcodes})
    print(data["export"])


def do_linked(args, token, operator):
    params = {"q": f"{operator}(bibcode:{args.bibcode})",
              "fl": args.fields, "rows": args.rows,
              "sort": "citation_count desc"}
    data = request("GET", "/search/query", token, params=params)
    resp = data["response"]
    print(f"# {resp['numFound']} {operator} for {args.bibcode} "
          f"(showing {min(args.rows, resp['numFound'])})\n", file=sys.stderr)
    if not args.json:
        for d in resp["docs"]:
            d.pop("abstract", None)
    print_docs(resp["docs"], args.json)


def do_metrics(args, token):
    data = request("POST", "/metrics", token, body={"bibcodes": args.bibcodes})
    basic = data.get("basic stats", {})
    cit = data.get("citation stats", {})
    ind = data.get("indicators", {})
    summary = {
        "papers": basic.get("number of papers"),
        "total citations": cit.get("total number of citations"),
        "h-index": ind.get("h"),
        "reads": basic.get("total number of reads"),
    }
    if args.json:
        json.dump(data, sys.stdout, indent=2)
        print()
    else:
        for k, v in summary.items():
            print(f"{k}: {v}")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("setup", help="verify a token and save it to ~/.ads/token")
    sp.add_argument("token", help="API token from "
                    "https://ui.adsabs.harvard.edu/user/settings/token")

    def add_common(sp):
        sp.add_argument("--fields", default=DEFAULT_FIELDS,
                        help="comma-separated fields to return")
        sp.add_argument("--json", action="store_true",
                        help="output raw JSON instead of formatted text")

    sp = sub.add_parser("search", help="search for papers")
    sp.add_argument("query", help="ADS query, e.g. 'author:\"^Chu, X\" year:2020-2024'")
    sp.add_argument("--rows", type=int, default=10)
    sp.add_argument("--start", type=int, default=0)
    sp.add_argument("--sort", default="score desc",
                    help="e.g. 'citation_count desc', 'date desc'")
    sp.add_argument("--filter", help="fq filter, e.g. 'database:astronomy'")
    sp.add_argument("--abstract", action="store_true", help="include abstracts")
    add_common(sp)

    sp = sub.add_parser("get", help="fetch metadata for bibcodes")
    sp.add_argument("bibcodes", nargs="+")
    add_common(sp)

    sp = sub.add_parser("export", help="export citations")
    sp.add_argument("format", choices=["bibtex", "bibtexabs", "aastex", "ris",
                                       "endnote", "medlars", "csl", "icarus",
                                       "mnras", "soph"])
    sp.add_argument("bibcodes", nargs="+")

    for name in ("citations", "references"):
        sp = sub.add_parser(name, help=f"list {name} of a paper")
        sp.add_argument("bibcode")
        sp.add_argument("--rows", type=int, default=25)
        add_common(sp)

    sp = sub.add_parser("metrics", help="citation metrics for bibcodes")
    sp.add_argument("bibcodes", nargs="+")
    sp.add_argument("--json", action="store_true")

    args = p.parse_args()
    if args.cmd == "setup":
        do_setup(args)
        return
    token = find_token()
    if args.cmd == "search":
        do_search(args, token)
    elif args.cmd == "get":
        do_get(args, token)
    elif args.cmd == "export":
        do_export(args, token)
    elif args.cmd == "citations":
        do_linked(args, token, "citations")
    elif args.cmd == "references":
        do_linked(args, token, "references")
    elif args.cmd == "metrics":
        do_metrics(args, token)


if __name__ == "__main__":
    main()
