"""Plain-English explanations of House votes.

Two layers:
1. Rules (always on): what the question was, and what a Yea and a Nay each did. These come from
   House procedure and never guess at a bill's contents.
2. AI summaries (optional, needs ANTHROPIC_API_KEY): a short neutral summary of what a bill does,
   written only from its official title and official summary, cached in data/summaries.json and
   always labelled as AI-written on the site.
"""
import json
import os
import re

from .common import DATA, fetch, read_json, write_json
from .ingest import bill_label, bill_slug, parse_legis

# (pattern on the vote question, kind)
RULES = [
    (r"suspend the rules and pass", "suspend_pass"),
    (r"suspend the rules and agree", "suspend_agree"),
    (r"suspend the rules and concur", "suspend_concur"),
    (r"objections of the president", "veto_override"),
    (r"^on passage", "passage"),
    (r"ordering the previous question", "previous_question"),
    (r"motion to refer", "refer"),
    (r"motion to table", "table"),
    (r"motion to recommit|motion to commit", "recommit"),
    (r"agreeing to the (.+ )?amendment", "amendment"),
    (r"concur in the senate amendment", "concur"),
    (r"conference report", "conference"),
    (r"agreeing to the resolution|agreeing to the concurrent resolution", "resolution"),
    (r"motion to adjourn", "adjourn"),
    (r"approving the journal", "journal"),
    (r"motion to discharge", "discharge"),
    (r"consideration of the (bill|resolution)", "consider"),
]

MEANING = {
    "passage": ("The House voted on whether to pass this bill.",
                "pass the bill", "reject the bill", False),
    "suspend_pass": ("The House voted on whether to pass this bill using a fast-track process. "
                     "Fast-track bills skip amendments and need two-thirds of those voting, not a simple majority.",
                     "pass the bill", "reject the bill", False),
    "suspend_agree": ("The House voted on whether to approve this resolution using a fast-track process "
                      "that needs two-thirds of those voting.",
                      "approve the resolution", "reject the resolution", False),
    "suspend_concur": ("The House voted on whether to accept the Senate's version using a fast-track process "
                       "that needs two-thirds of those voting.",
                       "accept the Senate's version", "reject the Senate's version", False),
    "veto_override": ("The House voted on whether to override the President's veto. "
                      "An override needs two-thirds of those voting.",
                      "override the veto", "let the veto stand", False),
    "previous_question": ("This was a procedural vote on whether to end debate and move to a final vote. "
                          "It was not a vote on the measure itself.",
                          "end debate and move to a vote", "keep debate open, which lets opponents offer changes", True),
    "refer": ("This was not a vote on the measure itself. Members voted on whether to send it to a committee "
              "instead of deciding it on the House floor. Sending a measure to committee usually sets it aside.",
              "send it to committee, setting it aside", "keep it on the floor, moving toward a direct vote", True),
    "table": ("This was not a vote on the measure itself. Members voted on whether to table it. "
              "Tabling a measure sets it aside and usually ends it.",
              "set the measure aside", "keep the measure alive", True),
    "recommit": ("Members voted on whether to send the bill back to committee, usually the last attempt "
                 "to change or stop a bill before the final vote.",
                 "send the bill back to committee", "move on to the final vote", True),
    "amendment": ("The House voted on whether to change the bill by adding this amendment.",
                  "add the amendment", "reject the amendment", False),
    "concur": ("The House voted on whether to accept the Senate's changes to this bill.",
               "accept the Senate's changes", "reject the Senate's changes", False),
    "conference": ("The House voted on the final compromise version worked out with the Senate.",
                   "approve the compromise", "reject the compromise", False),
    "resolution": ("The House voted on whether to approve this resolution.",
                   "approve the resolution", "reject the resolution", False),
    "rule": ("This vote set the rules for debating another measure: how long debate lasts and which amendments "
             "are allowed. It was a procedural step, not a vote on that measure itself.",
             "approve the debate rules and move ahead", "block the debate rules", True),
    "adjourn": ("A procedural vote on whether to end the House's session for the day.",
                "end the session", "keep working", True),
    "journal": ("A routine procedural vote approving the record of the previous day's proceedings.",
                "approve the record", "not approve the record", True),
    "discharge": ("Members voted on whether to pull a measure out of committee and bring it to the House floor.",
                  "bring the measure to the floor", "leave it in committee", True),
    "consider": ("A procedural vote on whether the House should take up this measure.",
                 "take up the measure", "not take it up", True),
    "other": ("", "vote in favor", "vote against", False),
}

HEADLINES = {
    # kind: (if it carried, if it failed)
    "passage": ("The House passed {x}", "The House rejected {x}"),
    "suspend_pass": ("The House passed {x}", "The House did not pass {x}"),
    "suspend_agree": ("The House approved {x}", "The House did not approve {x}"),
    "suspend_concur": ("The House accepted the Senate's version of {x}", "The House did not accept the Senate's version of {x}"),
    "veto_override": ("The House voted to override the veto of {x}", "The House failed to override the veto of {x}"),
    "previous_question": ("The House voted to end debate on {x}", "The House voted to keep debate open on {x}"),
    "refer": ("The House sent {x} to committee", "The House refused to send {x} to committee"),
    "table": ("The House set aside {x}", "The House refused to set aside {x}"),
    "recommit": ("The House sent {x} back to committee", "The House refused to send {x} back to committee"),
    "amendment": ("The House adopted an amendment to {x}", "The House rejected an amendment to {x}"),
    "concur": ("The House accepted the Senate's changes to {x}", "The House rejected the Senate's changes to {x}"),
    "conference": ("The House approved the final version of {x}", "The House rejected the final version of {x}"),
    "resolution": ("The House approved {x}", "The House rejected {x}"),
    "rule": ("The House approved the debate rules for another measure ({x})", "The House blocked the debate rules for another measure ({x})"),
    "adjourn": ("The House voted to adjourn", "The House voted not to adjourn"),
    "journal": ("The House approved the Journal", "The House did not approve the Journal"),
    "discharge": ("The House pulled {x} out of committee", "The House left {x} in committee"),
    "consider": ("The House agreed to take up {x}", "The House declined to take up {x}"),
}


def carried(result):
    r = (result or "").lower()
    return r.startswith("passed") or r.startswith("agreed")


def classify(question, desc=""):
    q = (question or "").lower()
    for pattern, kind in RULES:
        if re.search(pattern, q):
            if kind == "resolution" and re.match(r"providing for (the )?(further )?consideration", (desc or "").lower()):
                return "rule"
            return kind
    return "other"


def measure_name(vote, bills):
    """Shortest honest name for what was voted on."""
    parsed = parse_legis(vote["legis"])
    if not parsed:
        return vote["desc"] or vote["question"]
    label = bill_label(*parsed)
    return label


def explain(vote, bills):
    kind = classify(vote["question"], vote["desc"])
    what, yea, nay, procedural = MEANING[kind]
    parsed = parse_legis(vote["legis"])
    label = bill_label(*parsed) if parsed else ""
    title = ""
    if parsed:
        title = (bills.get(bill_slug(*parsed)) or {}).get("title", "")
    title = title or vote["desc"]
    if kind in HEADLINES and (label or kind in ("adjourn", "journal")):
        ok, no = HEADLINES[kind]
        headline = (ok if carried(vote["result"]) else no).format(x=label)
    else:
        headline = f"{vote['question']}: {label or title}".strip(": ")
    two_thirds = vote["type"].strip().startswith("2/3") or kind in ("suspend_pass", "suspend_agree", "suspend_concur", "veto_override")
    return {
        "kind": kind, "headline": headline, "what": what or f"Members voted on this question: {vote['question']}.",
        "yea": yea, "nay": nay, "procedural": procedural, "two_thirds": two_thirds,
        "label": label, "title": title,
    }


def member_phrase(vote, position, bills):
    """'Voted to send H.Res. 1655 to committee' for a member's row."""
    info = explain(vote, bills)
    if position == "yea":
        action = info["yea"]
    elif position == "nay":
        action = info["nay"]
    elif position == "present":
        return f"Voted present on {info['label'] or vote['question']}"
    else:
        return f"Did not vote on {info['label'] or vote['question']}"
    target = info["label"]
    text = f"Voted to {action}"
    if target and target not in text:
        text += f" ({target})"
    return text


# ---------------------------------------------------------------- optional AI summaries

PROMPT = """You write short, neutral summaries of U.S. congressional measures for a non-partisan public website.

Use ONLY the official material below. Do not add facts, numbers, motives, or predictions that are not in it.
Do not praise or criticise the measure or anyone involved. Write for a general reader with no legal background.
If the material is too thin to say what the measure does, say exactly that in one sentence.

Return JSON with two keys:
"one_sentence": one sentence, at most 30 words, saying what the measure would do.
"short": two to four sentences with the main provisions.

Official title: {title}
Official summary (Congressional Research Service), may be empty: {summary}
"""


def ai_summaries(votes, cfg, log=print):
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    cache = read_json(DATA / "summaries.json", {})
    if not key:
        log("AI summaries: ANTHROPIC_API_KEY not set, skipping")
        return cache
    bills = read_json(DATA / "bills.json", {})
    todo = []
    for v in reversed(votes):
        parsed = parse_legis(v["legis"])
        if not parsed:
            continue
        slug = bill_slug(*parsed)
        bill = bills.get(slug) or {}
        # Only summarise when there is official text to summarise from.
        if slug in cache or slug in todo or not bill.get("official_summary"):
            continue
        todo.append(slug)
    made = 0
    for slug in todo[: cfg.get("ai_max_new_summaries_per_run", 40)]:
        bill = bills[slug]
        body = json.dumps({
            "model": cfg.get("ai_model", "claude-haiku-5-5"),
            "max_tokens": 500,
            "messages": [{"role": "user", "content": PROMPT.format(
                title=bill.get("title", ""), summary=bill.get("official_summary", "")[:12000])}],
        }).encode()
        try:
            raw = fetch("https://api.anthropic.com/v1/messages", data=body, tries=2, headers={
                "x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"})
            text = json.loads(raw)["content"][0]["text"]
            found = re.search(r"\{.*\}", text, re.S)
            parsed_json = json.loads(found.group(0))
            cache[slug] = {
                "one_sentence": str(parsed_json["one_sentence"]).strip(),
                "short": str(parsed_json["short"]).strip(),
                "model": cfg.get("ai_model", ""),
            }
            made += 1
        except Exception as err:
            log(f"  ! AI summary for {slug} failed: {err}")
    write_json(DATA / "summaries.json", cache, compact=False)
    log(f"AI summaries: {made} new, {len(cache)} on file")
    return cache
