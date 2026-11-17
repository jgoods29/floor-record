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
