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

    def test_non_bills(self):
        self.assertIsNone(parse_legis("QUORUM"))
        self.assertIsNone(parse_legis(""))
        self.assertEqual(parse_legis("H J RES 213"), ("hjres", 213))
        self.assertEqual(parse_legis("S 723"), ("s", 723))


if __name__ == "__main__":
    unittest.main()
