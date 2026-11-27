# Ideas To Revisit

Things that were explored and parked. Nothing here is live.

## "In The News" row in Trending
A row at the top of Trending for past votes that are being talked about again (first tried with the Senate's
January 2025 confirmation of Transportation Secretary Sean Duffy, 77 to 22, vote `s2025-21`).
- The code is still in place and switched off. To bring an entry back, add it to `data/in_the_news.json`:
  `{"vote": "s2025-21", "label": "Sean Duffy's Confirmation As Transportation Secretary", "until": "2026-11-27"}`
- Open question: picked by hand, or suggested automatically each day and approved by a person before it shows.
- Guardrail: resurface the vote only; never say why it is in the news.

## Promises versus votes
"What They Said / How They Voted": each member's own campaign-site positions, quoted with a link and date,
beside their votes on the same topic. No kept/broken verdict. Start with a pilot of about ten members.

## Cleaner look
A design canvas holds a stripped-down mockup and a middle-ground one. Neither was adopted.

## Accounts and emails: live (not parked)
Accounts, the Monday and Friday emails, the 30-second pop-up and the Subscribe button went live on November 16, 2026,
when floortherecord.com was connected. Emails send from hello@floortherecord.com. Still open: a postal address must be
added before any sponsored email, and the free email plan covers about 50 subscribers. See `accounts/README.md`.


## Redesign, November 2026 (owner approved the mockups on November 27)

Restore point: the branch `before-redesign-2026-11-27` is the site exactly as it was before any of this. To go back, restore the changed files from that branch (`git checkout before-redesign-2026-11-27 -- templates static floorrecord/build.py`) and push.

- Done: vote pages lead with the result, the score and one sentence, then a state tile map, then "The Details" (everything else, in sections that open). About half as many words show at first; nothing was removed.
- Next: the same answer-first pattern on member, bill and home pages.
- Next: a "Career" tab on member pages (offices held, work before politics, education). Every entry must come from the Biographical Directory of Congress or the legislators dataset and follow the two-source rule in STYLE.md. Do not publish entries written from memory.
- Idea: a "find your members" map on the home page using the same tile layout.

### Home page simplified (November 27, 2026)
- Home went from about 410 visible words to about 260. One sentence under the headline, three latest votes with the result on the right, a "Find Your Members" state map (press a state, see its senators and House members), five Trending pills at most, Your Page, the promise.
- Taken off the home page only: the "Speak Up" box (still on vote, bill, and topic pages) and the one-line description under each vote.
- The vote list is titled "Latest From Congress", not "This Week", because in a week with no votes it shows the last week that had them.

### Redesign paused (November 27, 2026)
- The owner found the new vote page map too confusing (first purple for Yea, then full and light party colors for Yea and Nay). The whole site, home page included, was put back to the version from before the redesign.
- The redesign is saved, not lost: branch `redesign-2026-11-27-paused`. To bring it back: `git checkout redesign-2026-11-27-paused -- templates static floorrecord/build.py` and push.
- Before trying again: show the owner a picture first and get a yes. The map's colors need a clearer idea. People expect red and blue, and one glance must tell them who voted Yea and who voted Nay.
