"""Run with:  python -m unittest discover tests"""
import unittest
from pathlib import Path

from floorrecord.explain import classify, explain, member_phrase
from floorrecord.ingest import bill_label, parse_legis, parse_roll_call
from floorrecord.stats import compute

FIXTURE = Path(__file__).parent / "fixtures" / "roll317_reconstructed.xml"
CFG = {"min_votes_for_ranking": 1}


class Roll317(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vote = parse_roll_call(FIXTURE.read_bytes(), 2026)
        cls.result = compute([cls.vote], {}, {}, CFG)

    def test_official_totals(self):
        self.assertEqual(self.vote["totals"], {"yea": 211, "nay": 204, "present": 0, "nv": 18})
        self.assertEqual(self.vote["by_party"]["R"], {"yea": 210, "nay": 1, "present": 0, "nv": 7})
        self.assertEqual(self.vote["by_party"]["D"], {"yea": 0, "nay": 203, "present": 0, "nv": 11})
        self.assertEqual(self.vote["by_party"]["I"]["yea"], 1)
        self.assertTrue(self.vote["tally_matches"])
        self.assertEqual(len(self.vote["positions"]), 433)

    def test_metadata(self):
        self.assertEqual((self.vote["id"], self.vote["date"], self.vote["time"]), ("2026-317", "2026-11-10", "6:02 PM"))
        self.assertEqual(parse_legis(self.vote["legis"]), ("hres", 1655))
        self.assertEqual(bill_label("hres", 1655), "H.Res. 1655")

    def test_party_split_and_breakers(self):
        v = self.result["votes"][0]
        self.assertEqual(v["party_pos"], {"R": "yea", "D": "nay"})
        self.assertTrue(v["split"])
        self.assertEqual(v["breakers"], ["M001184"])  # Thomas Massie
        self.assertEqual(len(v["absent"]), 18)
        self.assertEqual(v["margin"], 7)

    def test_member_stats(self):
        massie = self.result["people"]["M001184"]["all"]
        self.assertEqual((massie["split_counted"], massie["split_with"], massie["against"]), (1, 0, 1))
        self.assertEqual(massie["attendance_pct"], 100.0)
        pelosi = self.result["people"]["P000197"]["all"]  # did not vote
        self.assertEqual((pelosi["eligible"], pelosi["cast"], pelosi["counted"]), (1, 0, 0))
        independents = [p for p in self.result["people"].values() if p["party"] == "I"]
        self.assertEqual(len(independents), 1)
        self.assertEqual(independents[0]["all"]["counted"], 0)  # no party position to compare with

    def test_plain_wording_and_featured(self):
        from floorrecord.stats import pick_featured
        v = self.result["votes"][0]
        self.assertEqual(v["info"]["name"], "Impeachment of Peter Brian Hegseth, Secretary of Defense")
        self.assertEqual(v["info"]["outcome"], "Sent to committee")
        self.assertEqual(v["info"]["result_note"], "The motion passed. That sent the measure to a committee instead of a direct vote.")
        self.assertFalse(v["info"]["routine"])
        self.assertIn(("close", "Close vote"), v["tags"])
        self.assertIn(("broke", "1 Republican broke ranks"), v["tags"])
        self.assertEqual([f["id"] for f in pick_featured(self.result["votes"])], ["2026-317"])

    def test_explanation(self):
        info = explain(self.vote, {})
        self.assertEqual(info["kind"], "refer")
        self.assertEqual(info["headline"], "The House sent H.Res. 1655 to committee")
        self.assertTrue(info["procedural"])
        self.assertEqual(member_phrase(self.vote, "nay", {}),
                         "Voted to keep it on the floor, moving toward a direct vote (H.Res. 1655)")


class Questions(unittest.TestCase):
    def test_classify(self):
        cases = {
            "On Passage": "passage",
            "On Motion to Suspend the Rules and Pass, as Amended": "suspend_pass",
            "On Ordering the Previous Question": "previous_question",
            "On Motion to Table": "table",
            "On Motion to Recommit": "recommit",
            "On Agreeing to the Amendment": "amendment",
            "On Motion to Concur in the Senate Amendment": "concur",
            "Passage, Objections of the President To The Contrary Notwithstanding": "veto_override",
            "Something Unusual": "other",
        }
        for question, kind in cases.items():
            self.assertEqual(classify(question), kind, question)
        self.assertEqual(classify("On Agreeing to the Resolution", "Providing for consideration of H.R. 1013"), "rule")
        self.assertEqual(classify("On Agreeing to the Resolution", "Honoring someone"), "resolution")

    def test_plain_names(self):
        from floorrecord.explain import short_name
        self.assertEqual(short_name("Retire through Ownership Act", "S. 2403"), "Retire through Ownership Act")
        self.assertEqual(short_name("Impeaching Peter Brian Hegseth, Secretary of Defense, for high crimes and misdemeanors", "H.Res. 1655"),
                         "Impeachment of Peter Brian Hegseth, Secretary of Defense")
        self.assertEqual(short_name("Providing for consideration of the bill (H.R. 471) the Fix Our Forests Act; and providing for consideration of the bill (S. 5) the Laken Riley Act", "H.Res. 53"),
                         "Fix Our Forests Act and more")
        self.assertEqual(short_name("Nuclear REFUEL (Recycling Efficient Fuels Utilizing Expedited Licensing) Act", "H.R. 3978"), "Nuclear REFUEL Act")
        self.assertEqual(short_name("", "H.R. 12"), "H.R. 12")
        self.assertLessEqual(len(short_name("To amend " + "the very long name of a statute " * 8, "H.R. 1")), 80)

    def test_bill_status(self):
        from floorrecord.build import bill_status
        self.assertEqual(bill_status("Referred to the House Committee on Agriculture."), ("In committee", False))
        self.assertEqual(bill_status("Became Public Law No: 119-38."), ("Became law", True))
        self.assertEqual(bill_status("Received in the Senate and Read twice and referred to the Committee on the Judiciary."), ("Passed the House", True))
        self.assertEqual(bill_status("Motion to reconsider laid on the table Agreed to without objection.")[0], "Voted on in the House")

    def test_senate_vote(self):
        from floorrecord.ingest import parse_senate_vote
        v = parse_senate_vote((FIXTURE.parent / "senate_sample.xml").read_bytes())
        self.assertEqual((v["year"], v["session"], v["roll"], v["date"], v["time"]), (2026, 2, 7, "2026-05-18", "17:36"))
        self.assertEqual(v["totals"], {"yea": 2, "nay": 1, "present": 0, "nv": 1})
        self.assertTrue(v["tally_matches"])
        self.assertEqual(v["positions"][2][:4], ["S003", "I", "CC", "nay"])
        self.assertEqual(v["documents"][0]["name"], "S. 99")
        self.assertIsNone(v["amendment"]); self.assertIsNone(v["tie_breaker"])

    def test_floor_schedule(self):
        from floorrecord.ingest import parse_floor_schedule
        week = parse_floor_schedule((FIXTURE.parent / "floor_sample.xml").read_text())
        self.assertEqual(week["week"], "2026-11-09")
        self.assertEqual([(i["slug"], i["how"]) for i in week["items"]], [("hr-3074", "fast"), ("hconres-12", "rule")])
        self.assertTrue(week["items"][0]["doc"].startswith("https://"))

    def test_non_bills(self):
        self.assertIsNone(parse_legis("QUORUM"))
        self.assertIsNone(parse_legis(""))
        self.assertEqual(parse_legis("H J RES 213"), ("hjres", 213))
        self.assertEqual(parse_legis("S 723"), ("s", 723))


if __name__ == "__main__":
    unittest.main()


class NewsletterTest(unittest.TestCase):
    def test_friday_email_shows_how_your_own_members_voted(self):
        from floorrecord.newsletter import build_email
        data = {"term": "119th Congress", "upcoming": [], "week": [
            {"id": "2026-1", "pre": "", "chamber": "House", "date": "2026-11-10", "name": "Test Act", "plain": "It does a thing.",
             "outcome": "Passed", "yea": 220, "nay": 210, "close": True, "pos": {"A1": "nay"}}]}
        rep = {"id": "A1", "name": "Pat Example", "state": "KY", "where": "District 4", "party": "R", "phone": "202-555-0100", "pre": "", "role": "Your representative"}
        subject, body = build_email("friday", data, [rep], "https://example.org/", {"postal_address": "PO Box 1"})
        self.assertIn("How They Voted", subject)
        self.assertIn("Voted no", body)
        self.assertIn("https://example.org/votes/2026-1/", body)
        self.assertIn("{{unsub}}", body)
        self.assertIn("PO Box 1", body)
        _, monday = build_email("monday", data, [rep], "https://example.org/", {})
        self.assertIn("202-555-0100", monday)
