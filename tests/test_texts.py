"""Bill texts: reading a version, outlining it, and telling a replaced bill from an amended one."""
import os
import tempfile
import unittest

from floorrecord import texts
from floorrecord.common import NotFound

PAGE = "<html><body><pre>{}</pre></body></html>"
TAX = """AN ACT To amend the Internal Revenue Code of 1986.
SECTION 1. SHORT TITLE.
    This Act may be cited as the ``Small Tax Act''.
SEC. 2. EXCLUSION FROM GROSS INCOME.
    """ + " ".join(f"tax word{i} applies to income in year {i}." for i in range(200))
ENERGY = """Strike all after the enacting clause and insert the following:
SECTION 1. SHORT TITLE; TABLE OF CONTENTS.
    (a) Short Title.--This Act may be cited as the ``Big Energy Act''.
    (b) Table of Contents.--
Sec. 1. Short title; table of contents.
                   DIVISION A--PERMITS
                  TITLE I--POWER LINES
Sec. 101. Deadlines.
                   DIVISION A--PERMITS
                  TITLE I--POWER LINES
SEC. 101. DEADLINES.
    """ + " ".join(f"permit rule{i} sets a deadline of {i} days for agency review." for i in range(900))


class Texts(unittest.TestCase):
    def test_missing_version_is_not_a_bill(self):
        with self.assertRaises(NotFound):
            texts.plain_text(b"<html><body>Page not found</body></html>")

    def test_outline_counts_each_heading_once(self):
        o = texts.outline(texts.plain_text(PAGE.format(ENERGY)))
        self.assertEqual(o["short_titles"], ["Big Energy Act"])
        self.assertEqual(o["parts"], [["Division A", "PERMITS"], ["Title I", "POWER LINES"]])
        self.assertEqual(o["sections"], 2)   # Section 1 and Sec. 101, not the table of contents lines

    def test_verdicts(self):
        same = texts.compare(TAX, TAX + " One more sentence was added at the end of the bill here.")
        self.assertEqual(texts._verdict(same), "similar")
        gone = texts.compare(TAX, ENERGY)
        self.assertEqual(texts._verdict(gone), "replaced")
        inside = texts.compare(TAX, ENERGY + TAX)
        self.assertEqual(texts._verdict(inside), "expanded")
        self.assertGreater(inside["kept"], 0.9)

    def test_collect_flags_a_carried_bill(self):
        pages = {"ih": TAX, "eh": TAX, "eas": ENERGY + TAX}

        def get(url):
            code = url.rsplit("BILLS-119hr9", 1)[1].split(".")[0]
            if code not in pages:
                raise NotFound(url)
            return PAGE.format(pages[code]).encode()

        with tempfile.TemporaryDirectory() as tmp:
            old, texts.DATA = texts.DATA, __import__("pathlib").Path(tmp)
            try:
                rec = texts.collect("hr-9", 119, get=get)
                self.assertEqual([v["code"] for v in rec["versions"]], ["ih", "eh", "eas"])
                self.assertTrue(rec["versions"][2]["whole"])
                self.assertEqual(rec["compare"]["verdict"], "expanded")
                self.assertTrue(rec["review"])
                self.assertTrue(os.path.exists(os.path.join(tmp, "texts", "full", "hr-9.eas.txt.gz")))
                self.assertNotIn("_text", rec["versions"][0])
                # A second look fetches nothing new and reaches the same verdict from the saved text.
                again = texts.collect("hr-9", 119, old=rec, get=lambda url: (_ for _ in ()).throw(NotFound(url)))
                self.assertEqual(again["compare"]["verdict"], "expanded")
            finally:
                texts.DATA = old

    def test_a_list_of_small_changes_is_not_compared(self):
        rec = {"versions": [{"code": "eh", "_text": TAX}, {"code": "eas", "_text": "(1) On page 4, strike lines 15 through 22.", "whole": False}]}
        texts.review(rec)
        self.assertIsNone(rec["compare"])
        self.assertFalse(rec["review"])


if __name__ == "__main__":
    unittest.main()
