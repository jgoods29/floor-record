"""The list of bills a person should look at, and the check that a social post matches the record."""
import html
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from floorrecord import review
from floorrecord.common import DATA, ROOT, read_json, write_json

SENATE_VOTE = {"year": 2026, "roll": 9, "amendment": {"number": "S.Amdt. 1", "purpose": "In the nature of a substitute."},
               "documents": [], "question_text": "On the Cloture Motion S.Amdt. 1 to H.R. 77 (No short title on file)",
               "title": "Motion to Invoke Cloture: Smith Amdt. No. 1", "question": "On the Cloture Motion", "document_text": ""}


class ReviewList(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data = Path(self.tmp.name)
        write_json(self.data / "senate" / "2026" / "00009.json", SENATE_VOTE)
        write_json(self.data / "bills.json", {"hr-77": {"title": "Small Tax Act"}, "s-5": {"title": "Old Name Act"}})
        write_json(self.data / "texts" / "s-5.json", {"versions": [], "compare": {"earlier": "es", "later": "eah", "from_earlier": 0.02, "kept": 0.1, "verdict": "replaced"}})

    def tearDown(self):
        self.tmp.cleanup()

    def test_substitute_and_replaced_text_are_listed(self):
        rows = review.to_review(self.data, {})
        self.assertEqual([r["slug"] for r in rows], ["hr-77", "s-5"])
        self.assertIn("s2026-9", rows[0]["why"][0])
        self.assertEqual(rows[1]["label"], "S. 5")

    def test_a_person_clears_a_bill(self):
        editorial = {"carried": {"hr-77": {"note": "x"}}, "reviewed": {"s-5": {"on": "2026-01-01"}}}
        self.assertEqual(review.to_review(self.data, editorial), [])

    def test_a_substitute_clears_when_the_text_stayed_the_same(self):
        write_json(self.data / "texts" / "hr-77.json", {"versions": [], "compare": {"earlier": "eh", "later": "enr", "from_earlier": 0.9, "kept": 0.9, "verdict": "similar"}})
        self.assertEqual([r["slug"] for r in review.to_review(self.data, {})], ["s-5"])
        # ...but not on the strength of the House's own versions, which came before the Senate's substitute
        write_json(self.data / "texts" / "hr-77.json", {"versions": [], "compare": {"earlier": "ih", "later": "eh", "from_earlier": 0.9, "kept": 0.9, "verdict": "similar"}})
        self.assertEqual([r["slug"] for r in review.to_review(self.data, {})], ["hr-77", "s-5"])

    def test_headings_keep_abbreviations(self):
        self.assertEqual(review.nice_heading("ANTI-CBDC SURVEILLANCE STATE ACT", ["Anti-CBDC Surveillance State Act"]), "Anti-CBDC Surveillance State Act")
        self.assertEqual(review.nice_heading("CIVIL LIBERTIES REVIEW OF FBI QUERIES"), "Civil Liberties Review Of FBI Queries")


class SocialPostMatchesTheRecord(unittest.TestCase):
    """Every row of the Schumer and Van Hollen carousel must match the comparison page and the Senate record."""

    def test_carousel_rows(self):
        matchup = next((m for m in read_json(DATA / "matchups.json", []) if m["slug"] == "schumer-van-hollen"), None)
        script = ROOT / "social" / "race_carousel_example.py"
        if not matchup or not script.exists():
            self.skipTest("the comparison page or the carousel is no longer in the repository")
        spec = importlib.util.spec_from_file_location("carousel", script)
        carousel = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(carousel)
        lis = {s["lis"]: b for b, s in read_json(DATA / "senators.json", {}).items()}
        unchecked = {slug for slug, row in review.flagged().items() if not row["checked"]}
        self.assertEqual(len(carousel.SPLITS), len(matchup["groups"]))
        for (name, a, b, count, about), group in zip(carousel.SPLITS, matchup["groups"]):
            plain = lambda s: html.unescape(s).replace("\u2019", "'")   # the carousel uses curly apostrophes
            self.assertEqual((name, plain(about), count), (group["name"], plain(group["about"]), len(group["votes"])))
            self.assertNotIn(group.get("bill"), unchecked, f"{name}: this bill's text changed and has not been checked yet")
            for vote in group["votes"]:
                year, roll = vote[1:].split("-")
                raw = read_json(DATA / "senate" / year / f"{int(roll):05d}.json")
                cast = {lis.get(p[0]): {"yea": "Yes", "nay": "No"}.get(p[3]) for p in raw["positions"]}
                self.assertEqual((cast[matchup["a"]], cast[matchup["b"]]), (a, b), f"{name}: {vote}")


if __name__ == "__main__":
    unittest.main()
