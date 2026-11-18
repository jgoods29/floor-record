# Floor The Record: House Style

Rules the owner has set. Follow them for anything built for the site, the emails or the social posts.

## Spacing: everything sits on one grid

The owner wants every piece to feel evenly spaced, with no gap that is "a bit off in any direction".
Measure before publishing; do not judge spacing by eye alone.

**Website** (`static/style.css`, templates)

- Between major sections of a page: 56px on a computer, 40px on a phone. No page sets its own value.
- Inside sections and cards: only 8, 12, 16, 20 or 32px.
- A heading belongs to the block below it: wrap the two in one `section.stack`, never leave a heading as a
  direct child of the page wrapper.
- `gap` only works on flex or grid containers. A card that sets `gap` must also be `display: flex`.
- Do not render empty rows (an empty `.tags` div still takes a gap).
- Check with a script that walks `main` and lists the gap between consecutive blocks at 1280px and 390px wide.
  Every section gap should read 56 (or 40 on a phone).

**Social posts** (1080 x 1350 boards)

- 64px from every edge of the board: left, right, top and bottom.
- 32px between every block, down and across, including the gutter between side-by-side cards.
- 32px padding inside every card.
- Content fills the board: one block (or a set of equal boxes) has `flex: 1` so the last block ends exactly
  32px above the footer line. No dead space at the bottom.
- Rows that sit side by side in two cards line up: give each row `flex: 1` instead of padding with blank lines.
- Numbers are for steps only: things done in order ("1 Go to the site, 2 Type your ZIP"). For a list of
  facts or duties, use a short purple dash, never a number, because a number implies a sequence.
- **Readable on a phone.** A 1080 wide slide is shown at about a third of its size. On social slides, body text is at least 30px, small labels and footers at least 24px, row titles 42px. Fix a stray last word with a planned line break. `social/bigger.py` applies these sizes.
- **Use the Oxford comma.** In a list of three or more, put a comma before "and" or "or": "the House, the Senate, and the President". Owner's rule from November 18, 2026, for everything new. Existing pages get it as they are next edited.
- Break big headlines on purpose with `<br>` so no single word is left alone on a line.
- Before publishing, render a plain-HTML copy with Inter and Inter Tight loaded and measure: every gap 32,
  every block 64 from both sides, nothing overflowing.

**Emails**

- Same idea: one padding value for the left and right edge of every row, one gap between sections.
- No dark header bands: phone mail apps in dark mode recolor them and the email stops matching.

## Titles

- Every word capitalized.
- Never end with a period.
- Join two parts of a headline with a colon, not a comma ("Schumer And Van Hollen: Side By Side").

## Voice

- Plain English, non-partisan, the record and not opinion.
- Name both sides of a vote or neither ("How Each Senator Voted", not "Who Voted Yes").
- Do not promise what the site cannot show (it does not track campaign promises).
- Make it easy to act at every turn.
- Explain as much as possible, concisely: say what is in a bill and how it got there, in as few words as it takes.

## Accuracy: read every bill

Errors are very costly for this project. The owner's rule: read the bill itself before describing it.

- Before a bill or vote is named or described on the site, in an email or in a social post, read the text that was
  actually voted on, not only its official title or the Library of Congress summary.
- The Senate often takes a bill that has passed the House and replaces its text with something else (an amendment
  "in the nature of a substitute"). The official title stays the same. Describe what the Senate was voting on, and
  mark the bill under `carried` in `editorial.json`.
- If the text cannot be read, say so and do not publish the description until it has been.
- Before a social post goes out, check every row in it against the official record and one news source.

### A vote on a step is not a vote on the bill
Before saying how someone voted on a bill, list every vote they cast on it. Votes to start or end debate are steps.
If two people split on a step and then voted the same way on passage, the row must say so ("Taking Up The Housing
Bill", "Both later voted to pass it"). If there has been no final vote, say that. Numbers in a post are a snapshot:
recount them from the record on the day it goes out.

## Color

- Red is Republican, blue is Democrat, purple is neutral or unity.
- Light and airy, navy text, rounded cards, Inter and Inter Tight.
