"""Tests for the address extractor. Run: python3 -m unittest test_receipt_address (from scripts/).

Every street, shop and company below is fictional.
"""

import unittest

from receipt_address import currency_for_country, find_address


class Base(unittest.TestCase):
    def check(self, lines, country, postal, region=None, hint=None, min_conf=0.8, first_line=None):
        r = find_address(lines, hint)
        self.assertEqual(r["country"], country, r)
        self.assertEqual(r["postal_code"], postal, r)
        if region is not None:
            self.assertEqual(r["region"], region, r)
        self.assertGreaterEqual(r["confidence"], min_conf, r)
        self.assertTrue(r["country_evidence"], r)
        if first_line is not None:
            self.assertEqual(r["lines"][0], first_line, r)
        for ln in r["lines"]:
            self.assertNotRegex(ln.lower(), r"\b(?:tel|fax|gstin|npwp|sst|uen|vat|mst|nip|siret|ust-id)\b|@|www\.")
        return r


class India(Base):
    def test_mumbai_spaced_pin(self):
        r = self.check(["Sharma Sweets", "Shop 4, Lotus Arcade", "Link Road, Andheri West", "Mumbai - 400 053",
                        "Maharashtra", "GSTIN: 27ABCDE1234F1Z5", "Tel: 022-2634 5678", "Date: 12/03/2024",
                        "Kaju Katli 450.00"], "IN", "400053", "Maharashtra", first_line="Shop 4, Lotus Arcade")
        self.assertEqual(r["lines"][-1], "Maharashtra")
        self.assertEqual(len(r["lines"]), 4)

    def test_bengaluru_pin_label(self):
        self.check(["Udupi Imaginary Cafe", "No. 17, 3rd Cross, Pretend Layout", "Bengaluru, Karnataka",
                    "PIN: 560001", "Ph: +91 80 4123 4567", "Bill No: 560002"], "IN", "560001", "Karnataka")

    def test_devanagari_digits(self):
        self.check(["Gupta Kirana Store", "12 Kalpanik Marg", "New Delhi - ११०००१", "India"], "IN", "110001")


class Singapore(Base):
    def test_singapore_word(self):
        r = self.check(["Kopi Bintang Pte Ltd", "123 Fictional Road #01-23", "Singapore 238801", "Tel 6123 4567",
                        "GST Reg No: 201912345K", "Kopi O 1.80"], "SG", "238801")
        self.assertEqual(r["lines"], ["123 Fictional Road #01-23", "Singapore 238801"])

    def test_s_bracket_format(self):
        self.check(["Makan Place Imaginary", "Blk 456 Pretend Ave 3 #05-67", "S(560456)", "UEN: 53123456X"],
                   "SG", "560456", min_conf=0.6)


class Malaysia(Base):
    def test_petaling_jaya(self):
        r = self.check(["Kedai Buku Pelangi Sdn Bhd (543210-K)", "No 5, Jalan Mawar 3,", "Taman Seri Indah,",
                        "47800 Petaling Jaya,", "Selangor", "Tel: 03-7801 2345", "Invoice No: 56001",
                        "Total RM 12.50"], "MY", "47800", "Selangor")
        self.assertEqual(r["lines"][0], "No 5, Jalan Mawar 3")

    def test_kuala_lumpur_wp(self):
        self.check(["Restoran Khayalan", "Lot 2-10, Jalan Bukit Khayalan", "50450 W.P. Kuala Lumpur",
                    "SST No: W10-1808-31000123"], "MY", "50450", "Kuala Lumpur")

    def test_poskod_label_and_arabic_indic_digits(self):
        self.check(["Kedai Runcit Bahagia", "Jalan Fiksyen 7", "Poskod ٨١١٠٠ Johor Bahru, Johor"],
                   "MY", "81100", "Johor")

    def test_state_range_mismatch_lowers_confidence(self):
        r = find_address(["Kedai Contoh", "Jalan Rekaan 1", "10050 Johor"])
        self.assertEqual(r["country"], "MY")
        self.assertLess(r["confidence"], 0.8)
        self.assertTrue(any("range" in n for n in r["notes"]), r)


class Thailand(Base):
    def test_thai_script_and_thai_digits(self):
        r = self.check(["ร้านกาแฟดาวเหนือ", "99/1 ถนนสุขสบาย แขวงลุมพินี", "เขตปทุมวัน กรุงเทพมหานคร ๑๐๓๓๐",
                        "โทร. 02-123-4567", "TAX ID 0105551234567"], "TH", "10330", "Bangkok")
        self.assertEqual(len(r["lines"]), 2)

    def test_english_bangkok(self):
        self.check(["Pretend Noodle House", "88 Soi Fictional 5, Thanon Sukhumvit", "Khlong Toei, Bangkok 10110",
                    "Thailand", "+66 2 123 4567"], "TH", "10110", "Bangkok")

    def test_chiang_mai(self):
        self.check(["Make-Believe Bakery", "21 Thanon Imaginary, Chiang Mai 50200"], "TH", "50200", "Chiang Mai")


class Indonesia(Base):
    def test_bali_kuta(self):
        self.check(["Warung Kopi Senja", "Jl. Pantai Imajiner No. 88", "Kuta, Badung, Bali 80361",
                    "Telp: +62 361 765432", "NPWP: 01.234.567.8-901.000"], "ID", "80361", "Bali")

    def test_ubud_kode_pos(self):
        self.check(["Toko Seni Khayalan", "Jl. Raya Rekaan No. 7, Ubud", "Gianyar, Bali", "Kode Pos 80571"],
                   "ID", "80571", "Bali")

    def test_jakarta(self):
        self.check(["Kedai Fiktif", "Jl. Fiktif Raya No. 10", "Jakarta Selatan 12190", "Indonesia"],
                   "ID", "12190", "Jakarta")


class Vietnam(Base):
    def test_hanoi(self):
        self.check(["Quán Cà Phê Gió Mát", "Số 12 Phố Hàng Giả, Phường Mây", "Quận Hoàn Kiếm, Hà Nội 100000",
                    "ĐT: 024 3825 1234", "MST: 0101234567"], "VN", "100000", "Hà Nội")

    def test_hcmc_label(self):
        self.check(["Tiệm Bánh Tưởng Tượng", "45 Đường Hư Cấu, Phường Bến Nghé", "Quận 1, TP.HCM",
                    "Mã bưu chính: 700000"], "VN", "700000", "Hồ Chí Minh")


class Canada(Base):
    def test_quebec(self):
        self.check(["Café Érable Imaginaire", "1234 rue des Pins Fictifs", "Montréal, QC H2X 1Y4",
                    "TPS: 123456789 RT0001", "TVQ: 1234567890 TQ0001"], "CA", "H2X 1Y4", "Quebec")

    def test_toronto(self):
        self.check(["Pretend Poutine Co", "500 Imaginary St W", "Toronto, ON M5V 2T6", "HST # 123456789 RT0001"],
                   "CA", "M5V 2T6", "Ontario")

    def test_province_mismatch(self):
        r = find_address(["Fake Shop", "1 Nowhere Rd", "Toronto, ON H2X 1Y4"])
        self.assertEqual(r["country"], "CA")
        self.assertLess(r["confidence"], 0.8)
        self.assertTrue(any("province" in n for n in r["notes"]), r)


class UnitedStates(Base):
    def test_springfield(self):
        self.check(["Maple Leaf Diner", "742 Evergreen Fictional Ave", "Springfield, IL 62704", "(217) 555-0199",
                    "Order #45012"], "US", "62704", "IL")

    def test_zip_plus_four(self):
        self.check(["Imaginary Deli", "1 Fictional Plaza, Suite 200", "New York, NY 10001-2345",
                    "Tel +1 212 555 0100"], "US", "10001-2345", "NY")


class UnitedKingdom(Base):
    def test_london(self):
        self.check(["The Crooked Kettle", "12 Imaginary Lane", "London SW1A 1AA", "VAT Reg No: GB 123 4567 89"],
                   "GB", "SW1A 1AA", "London")

    def test_manchester(self):
        self.check(["Pretend Pies Ltd", "Unit 3, Make Believe Street", "Manchester", "M1 1AE", "United Kingdom"],
                   "GB", "M1 1AE")


class Netherlands(Base):
    def test_amsterdam(self):
        self.check(["Bakkerij De Molen", "Fictiefstraat 12", "1012 AB Amsterdam", "KvK 12345678"],
                   "NL", "1012 AB", "Amsterdam")

    def test_utrecht(self):
        self.check(["Koffiehuis Verzonnen", "Verzonnenweg 8", "3511AB UTRECHT", "Tel +31 30 123 4567"],
                   "NL", "3511 AB", "Utrecht")


class Germany(Base):
    def test_berlin(self):
        self.check(["Bäckerei Sonnenschein", "Erfundene Straße 7", "10115 Berlin", "USt-IdNr: DE123456789"],
                   "DE", "10115", "Berlin")

    def test_munich(self):
        self.check(["Café Phantasie", "Musterallee 3", "80331 München", "Deutschland"], "DE", "80331")

    def test_plz_label_narrows_to_germany(self):
        r = find_address(["Laden Ausgedacht", "Traumweg 4", "PLZ 01067 Dresden"])
        self.assertEqual(r["country"], "DE", r)
        self.assertEqual(r["postal_code"], "01067")


class France(Base):
    def test_paris(self):
        self.check(["Boulangerie du Rêve", "15 rue Imaginaire", "75008 Paris", "SIRET 123 456 789 00012"],
                   "FR", "75008", "Paris")

    def test_lyon(self):
        self.check(["Bistrot Fictif", "8 avenue Inventée", "69002 Lyon", "France"], "FR", "69002", "Lyon")


class Spain(Base):
    def test_madrid(self):
        self.check(["Bar Inventado", "C/ Ficticia 22", "28013 Madrid", "España"], "ES", "28013")


class Italy(Base):
    def test_rome(self):
        self.check(["Trattoria Immaginaria", "Via della Finzione 9", "00184 Roma RM", "P.IVA 01234567890"],
                   "IT", "00184")


class Poland(Base):
    def test_warsaw(self):
        self.check(["Piekarnia Złoty Kłos", "ul. Wymyślona 5", "00-950 Warszawa", "NIP: 123-456-32-18"],
                   "PL", "00-950", "Warszawa")

    def test_krakow(self):
        self.check(["Kawiarnia Fikcja", "al. Fikcyjna 10", "30-001 Kraków", "Polska"], "PL", "30-001")


class OtherEurope(Base):
    def test_ireland_eircode(self):
        self.check(["The Made-Up Pub", "7 Pretend Quay", "Dublin 2", "D02 X285", "Ireland"], "IE", "D02 X285")

    def test_portugal(self):
        self.check(["Pastelaria Imaginária", "Rua da Fantasia 4", "1100-148 Lisboa", "Portugal"], "PT", "1100-148")

    def test_belgium_four_digits_with_city(self):
        self.check(["Friterie Fictive", "Rue Inventée 3", "1000 Bruxelles", "Belgique"], "BE", "1000")

    def test_switzerland_prefix(self):
        self.check(["Käserei Erfunden", "Traumgasse 2", "CH-8001 Zürich"], "CH", "8001", min_conf=0.6)

    def test_denmark(self):
        self.check(["Bageri Opdigtet", "Fantasigade 5", "2100 København Ø", "Danmark"], "DK", "2100")


class Negatives(unittest.TestCase):
    def test_phone_not_postal(self):
        r = find_address(["Kedai Kopi Harmoni", "Jalan Fiksyen 2", "Tel: 07-354 6789"], country_hint="MY")
        self.assertIsNone(r["postal_code"], r)
        self.assertEqual(r["lines"], ["Jalan Fiksyen 2"])

    def test_unlabelled_mobile_not_postal(self):
        r = find_address(["Imaginary Chai", "MG Fictional Road", "98765 43210"], country_hint="IN")
        self.assertIsNone(r["postal_code"], r)

    def test_invoice_number_not_postal(self):
        r = find_address(["Toko Maju Khayalan", "Jl. Fiktif 3", "Invoice 80361", "Receipt No: 80362"],
                         country_hint="ID")
        self.assertIsNone(r["postal_code"], r)
        r = find_address(["Kedai Contoh", "Jalan Rekaan 9", "Bill No 47801", "47800 Petaling Jaya"])
        self.assertEqual(r["postal_code"], "47800")

    def test_amounts_dates_times_not_postal(self):
        r = find_address(["Shop", "Jalan Contoh 1", "12345.00", "2024-03-12 14:05", "Total 45012.50"],
                         country_hint="MY")
        self.assertIsNone(r["postal_code"], r)

    def test_bare_five_digits_no_country(self):
        r = find_address(["Corner Shop", "Main Road 45012", "Total 5.00"])
        self.assertIsNone(r["country"], r)
        self.assertEqual(r["postal_code"], "45012")
        self.assertLess(r["confidence"], 0.3)
        r = find_address(["Corner Shop", "12345", "Total 5.00"])
        self.assertIsNone(r["country"])
        self.assertIsNone(r["postal_code"])

    def test_conflicting_evidence(self):
        r = find_address(["Kedai Runcit Maju", "Jalan Fiksyen 9", "50450 Kuala Lumpur", "Tel: +65 6123 4567"])
        self.assertIsNone(r["country"], r)
        self.assertTrue(any("conflict" in n for n in r["notes"]), r)
        self.assertEqual(r["country_evidence"], "")

    def test_hint_conflicts_with_document(self):
        r = find_address(["Kedai Contoh", "Jalan Rekaan 1", "47800 Petaling Jaya, Selangor"], country_hint="SG")
        self.assertIsNone(r["country"], r)
        self.assertTrue(any("conflict" in n for n in r["notes"]))

    def test_hint_decides_digits(self):
        r = find_address(["Kedai Contoh", "Jalan Rekaan 1", "45012 Bandar Khayalan"], country_hint="MY")
        self.assertEqual(r["country"], "MY")
        self.assertEqual(r["postal_code"], "45012")
        self.assertIn("country_hint", r["country_evidence"])
        self.assertLess(r["confidence"], 0.8)

    def test_phone_prefix_plus_one_ambiguous_until_format(self):
        r = find_address(["Fake Store", "9 Nowhere Blvd", "Tel +1 555 010 0199"])
        self.assertIsNone(r["country"], r)
        self.assertTrue(any("ambiguous" in n for n in r["notes"]))

    def test_dish_name_does_not_conflict(self):
        r = find_address(["Restoran Rekaan", "Jalan Fiksyen 3", "47800 Petaling Jaya, Selangor",
                          "Singapore Noodles 8.50", "Total 8.50"])
        self.assertEqual(r["country"], "MY", r)

    def test_empty(self):
        r = find_address([])
        self.assertIsNone(r["country"])
        self.assertEqual(r["lines"], [])
        self.assertEqual(r["confidence"], 0.0)


class Currency(unittest.TestCase):
    def test_map(self):
        expected = {"IN": "INR", "SG": "SGD", "TH": "THB", "MY": "MYR", "ID": "IDR", "CA": "CAD", "VN": "VND",
                    "US": "USD", "GB": "GBP", "AU": "AUD", "JP": "JPY", "KR": "KRW", "CN": "CNY", "AE": "AED",
                    "SA": "SAR", "DE": "EUR", "FR": "EUR", "NL": "EUR", "IE": "EUR", "HR": "EUR", "PL": "PLN",
                    "CZ": "CZK", "HU": "HUF", "SE": "SEK", "DK": "DKK", "NO": "NOK", "CH": "CHF"}
        for cc, cur in expected.items():
            self.assertEqual(currency_for_country(cc), cur, cc)
        self.assertEqual(currency_for_country("my"), "MYR")
        self.assertIsNone(currency_for_country("ZZ"))
        self.assertIsNone(currency_for_country(""))


if __name__ == "__main__":
    unittest.main()
