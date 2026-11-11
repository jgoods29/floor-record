# Floor Record

A website that shows how members of the U.S. House vote, in plain English, straight from the official record.

It collects every House roll call from the Clerk of the House, works out simple statistics (how often each member
votes with or against their party, attendance), and builds a page for every vote, member and bill, plus a sortable
leaderboard. It updates itself every four hours.

## Putting it online (one time)

1. Put these files in a GitHub repository.
2. In the repository, open **Settings → Pages** and set **Source** to **GitHub Actions**.
3. Open the **Actions** tab, choose **Update data and publish site**, and press **Run workflow**.
   The first run downloads every House vote since January 2025 and takes about ten minutes.
4. When it finishes, the site's address is shown on the run's summary page and under **Settings → Pages**.

After that it runs on its own.

## Optional extras

Add these under **Settings → Secrets and variables → Actions → New repository secret**.

| Secret | What it adds | Where to get it |
| --- | --- | --- |
| `CONGRESS_API_KEY` | Proper bill titles, sponsors, topics (which turns on the topic picker on each profile), official summaries, and the bills each member introduced or signed onto | Free sign-up at https://api.congress.gov/sign-up/ |
| `ANTHROPIC_API_KEY` | AI-written plain names and one-line explanations for votes, and short bill summaries, always labelled as AI-written | A paid key from https://platform.claude.com |

AI bill summaries are only written for bills that have an official Congressional Research Service summary to work
from, so they need `CONGRESS_API_KEY` too.

## Featured votes and approved wording

`editorial.json` is the one file a person edits by hand:

- `pins` lists votes to feature at the top of the home page. A pin lasts 90 days; after that the automatic rule
  (recent, close, or many members crossing party lines) takes over.
- `votes` sets an approved name, outcome word and one-line explanation for a vote. Approved wording always wins over
  AI or automatic wording, and it is the only wording besides the automatic kind that the home page's big votes use.

## Settings

`config.json` holds the site name, the years covered, a contact email for corrections, and the minimum number of
votes a member needs before appearing on the leaderboard.

## How it is organised

| Path | What it does |
| --- | --- |
| `floorrecord/ingest.py` | Downloads roll calls, the member list and (optionally) bill details into `data/` |
| `floorrecord/stats.py` | Calculates every statistic; the definitions are at the top of the file and on the About page |
| `floorrecord/explain.py` | The rules that say what a Yea or Nay meant, and the optional AI summaries |
| `floorrecord/build.py` | Turns the data into the website in `site/` |
| `templates/`, `static/` | Page layouts, styles and the small script for search, sorting and tabs |
| `tests/` | Checks the counting against House Roll Call 317 (Nov 10, 2026) |

## Running it on your own computer

```
pip install -r requirements.txt
python -m unittest discover tests
python -m floorrecord.ingest
python -m floorrecord.build
python -m http.server --directory site
```

## Not in this version yet

- The Senate, and years before 2025
- News coverage links on bill pages
- District facts and "find my representative by zip code"
- Member photos

## A note on the test file

`tests/fixtures/roll317_reconstructed.xml` was rebuilt from the Clerk's published totals and news reports because
the place this code was written could not reach clerk.house.gov. It is used only by the tests. The live site
always downloads the real records.
