"""Tests for the deterministic parser. Run: python3 -m unittest test_receipt_parse.py (from scripts/)."""

import unittest
from decimal import Decimal as D

from receipt_parse import find_date, gstin_valid, mask_pan, normalise, parse_amount, parse_receipt


class Amounts(unittest.TestCase):
    def test_separators(self):
        self.assertEqual(parse_amount("1,234.56"), D("1234.56"))
        self.assertEqual(parse_amount("1.234,56"), D("1234.56"))
        self.assertEqual(parse_amount("1 234,56"), D("1234.56"))
        self.assertEqual(parse_amount("1'234.50"), D("1234.50"))
        self.assertEqual(parse_amount("1,23,456.78"), D("123456.78"))
        self.assertEqual(parse_amount("12,50"), D("12.50"))

    def test_currency_decimals(self):
        self.assertEqual(parse_amount("1,500", decimals=0), D("1500"))
        self.assertEqual(parse_amount("12.345", decimals=3), D("12.345"))
        self.assertEqual(parse_amount("1.234", decimals=2), D("1234"))

    def test_unicode_digits(self):
        self.assertEqual(normalise("٤٥٫٥٠"), "45.50")
        self.assertEqual(normalise("۱۲۳"), "123")
        self.assertEqual(normalise("१२०.००"), "120.00")
        self.assertEqual(normalise("１２３．４５"), "123.45")
        self.assertEqual(normalise("๑๒๓"), "123")


class Dates(unittest.TestCase):
    def test_formats(self):
        self.assertEqual(find_date(["2026-03-14 10:22"])[0], "2026-03-14")
        self.assertEqual(find_date(["14.03.2026"])[0], "2026-03-14")
        self.assertEqual(find_date(["03/14/2026"])[0], "2026-03-14")
        self.assertEqual(find_date(["2026年3月14日"])[0], "2026-03-14")
        self.assertEqual(find_date(["2026년 3월 14일"])[0], "2026-03-14")
        self.assertEqual(find_date(["令和8年3月14日"])[0], "2026-03-14")
        self.assertEqual(find_date(["14/03/2569"])[0], "2026-03-14")
        self.assertEqual(find_date(["14 Mar 2026"])[0], "2026-03-14")

    def test_ambiguous_uses_order(self):
        iso, _, notes = find_date(["04/05/2026"], order="MDY")
        self.assertEqual(iso, "2026-04-05")
        self.assertFalse(any("ambiguous" in n for n in notes))
        iso, _, notes = find_date(["04/05/2026"])
        self.assertEqual(iso, "2026-05-04")
        self.assertTrue(any("ambiguous" in n for n in notes))


class Ids(unittest.TestCase):
    def test_gstin(self):
        self.assertTrue(gstin_valid("27AAPFU0939F1ZV"))
        self.assertFalse(gstin_valid("27AAPFU0939F1ZX"))

    def test_mask(self):
        self.assertEqual(mask_pan("Card 4111 1111 1111 1111"), "Card **** **** **** 1111")


class Receipts(unittest.TestCase):
    def test_english_exclusive_tax(self):
        r = parse_receipt(["Corner Cafe", "12/03/2026 09:15", "Latte 2 x 3.50 7.00", "Muffin 3.25",
                           "Subtotal 10.25", "Tax 8% 0.82", "Total 11.07", "Cash 20.00", "Change 8.93"], currency_hint="USD")
        self.assertEqual(r.total.value, D("11.07"))
        self.assertEqual(r.subtotal.value, D("10.25"))
        self.assertTrue(r.reconciliation["totals_reconcile"])
        self.assertTrue(r.reconciliation["items_match_subtotal"])
        self.assertTrue(r.line_items[0]["qty_x_price_ok"])

    def test_german_vat_inclusive(self):
        r = parse_receipt(["Bäckerei Müller", "14.03.2026", "Brot 3,20", "Kaffee 2,80", "Zwischensumme 6,00",
                           "MwSt 7% 0,39", "Summe EUR 6,00", "Gegeben 10,00", "Rückgeld 4,00"])
        self.assertEqual(r.currency.value, "EUR")
        self.assertEqual(r.total.value, D("6.00"))
        self.assertEqual(r.reconciliation["tax_mode"], "inclusive")

    def test_india_gst(self):
        r = parse_receipt(["Sharma Stores", "GSTIN 27AAPFU0939F1ZV", "Date 14/03/2026", "Rice 5kg 450.00",
                           "Oil 1L 180.00", "Sub Total ₹630.00", "CGST 2.5% 15.75", "SGST 2.5% 15.75", "Grand Total ₹661.50"])
        self.assertEqual(r.currency.value, "INR")
        self.assertEqual(r.tax.value, D("31.50"))
        self.assertTrue(r.reconciliation["totals_reconcile"])
        self.assertTrue(r.tax_ids[0]["checksum_ok"])

    def test_japanese_zero_decimal(self):
        r = parse_receipt(["コンビニ", "2026年3月14日", "おにぎり ¥150", "お茶 ¥130", "小計 ¥280", "消費税 ¥22",
                           "合計 ¥302", "お預り ¥1,000", "お釣り ¥698"], currency_hint="JPY")
        self.assertEqual(r.total.value, D("302"))
        self.assertTrue(r.reconciliation["totals_reconcile"])

    def test_arabic_digits(self):
        r = parse_receipt(["متجر", "المجموع الفرعي ١٠٠٫٠٠", "ضريبة القيمة المضافة ١٥٫٠٠", "الإجمالي ١١٥٫٠٠ SAR"])
        self.assertEqual(r.total.value, D("115.00"))
        self.assertTrue(r.reconciliation["totals_reconcile"])


if __name__ == "__main__":
    unittest.main()


class Runner(unittest.TestCase):
    """Line grouping and multi-run voting in receipt_ocr.py, with simulated engine output (no OCR engine needed)."""

    def words(self, rows):
        out = []
        for y, row in enumerate(rows):
            x = 0
            for w in row.split():
                out.append((w, 0.97, x, y * 30, x + 10 * len(w), y * 30 + 20))
                x += 10 * len(w) + 8
        return out

    def test_group_and_vote(self):
        import receipt_ocr as ro
        rows = ["Corner Cafe", "12/03/2026", "Latte 7.00", "Muffin 3.25", "Subtotal 10.25", "Tax 0.82", "Total 11.07"]
        lines, confs = ro.to_lines(self.words(rows), rtl=False)
        self.assertEqual(lines, rows)
        good = parse_receipt(lines, confs, "USD", "DMY").to_dict()
        misread = parse_receipt([l.replace("11.07", "11.01") for l in lines], confs, "USD", "DMY").to_dict()
        unsure = ro.vote({"a/original": parse_receipt(lines, confs, "USD").to_dict()}, 0.85)
        self.assertEqual(unsure["fields"]["date"]["status"], "review")
        agreed = ro.vote({"a/original": good, "b/original": good}, 0.85)
        self.assertEqual(agreed["fields"]["total"]["status"], "accepted")
        self.assertEqual(agreed["status"], "accepted")
        split = ro.vote({"a/original": good, "b/binary": misread}, 0.85)
        self.assertEqual(split["fields"]["total"]["status"], "review")
        self.assertEqual(split["status"], "review")
