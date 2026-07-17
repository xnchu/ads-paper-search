# ADS Paper Search — Claude Skill

A connector [Agent Skill](https://agentskills.io) that lets Claude search the
[NASA Astrophysics Data System (ADS)](https://ui.adsabs.harvard.edu/) — the
standard literature database for astronomy, astrophysics, space physics, and
planetary science.

With this skill, Claude can:

- **Search papers** with full ADS query syntax (topic, author, year, journal, object, …)
- **Follow the citation graph** — papers citing or cited by any paper
- **Export BibTeX** (and AASTeX, RIS, EndNote, …)
- **Compute citation metrics** (totals, h-index, reads)
- **Resolve identifiers** — bibcodes, DOIs, arXiv IDs

## Setup

1. **Get a free ADS API token** (~1 minute):
   create an account at [ui.adsabs.harvard.edu](https://ui.adsabs.harvard.edu/),
   then copy your token from
   [Settings → API Token](https://ui.adsabs.harvard.edu/user/settings/token).

2. **Install the skill**:
   - **Claude Code**: copy (or symlink) `skills/ads-paper-search/` into
     `~/.claude/skills/`.
   - **claude.ai / Claude Science**: zip the `skills/ads-paper-search/` folder
     and upload it under Settings → Capabilities → Skills.

3. **First use**: ask Claude to find some papers. If no token is configured,
   the skill walks you through saving it (one time):

   ```bash
   python3 scripts/ads.py setup YOUR_TOKEN   # verifies, saves to ~/.ads/token
   ```

   Alternatively, set the `ADS_API_TOKEN` environment variable.

Your token is personal — it is stored only on your machine and is never
committed to this repo or bundled with the skill.

## Example prompts

- "Find the most-cited papers on chorus wave–driven electron precipitation since 2020"
- "Who has cited Angelopoulos 2008 (The THEMIS Mission)? Show the top 10"
- "Export BibTeX for these three bibcodes"
- "What's the h-index for this list of papers?"

## Repository layout

```
skills/ads-paper-search/
  SKILL.md                     # skill definition Claude reads
  scripts/ads.py               # stdlib-only CLI wrapping the ADS API
  references/search-syntax.md  # full query-syntax and endpoint reference
```

The CLI also works standalone: `python3 skills/ads-paper-search/scripts/ads.py -h`.

## Credits

Built on the [ADS API](https://ui.adsabs.harvard.edu/help/api/). This project
is not affiliated with NASA or the ADS team. If you use ADS-powered results in
a publication, please acknowledge ADS per their
[terms of use](https://ui.adsabs.harvard.edu/help/terms).
