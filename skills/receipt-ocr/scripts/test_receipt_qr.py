"""Tests for the receipt QR decoder. Run: python3 -m unittest test_receipt_qr.py (from scripts/)."""

import base64
import json
import unittest

from receipt_qr import crc16_ccitt_false, emv_crc, parse_emv_tlv, parse_payload

try:
    import cv2
    import numpy as np
    from receipt_qr import decode_qr_image, qr_fields
except ImportError:  # pragma: no cover
    cv2 = None


def tlv(tag: str, value: str) -> str:
    return f"{tag}{len(value):02d}{value}"


def emv(*objs: tuple[str, str]) -> str:
    body = "".join(tlv(t, v) for t, v in objs) + "6304"
    return body + emv_crc(body)


PAYNOW_DYNAMIC = emv(
    ("00", "01"), ("01", "12"),
    ("26", tlv("00", "SG.PAYNOW") + tlv("01", "2") + tlv("02", "201403121W") + tlv("03", "0")),
    ("52", "5812"), ("53", "702"), ("54", "23.50"), ("58", "SG"),
    ("59", "KOPI CORNER PTE LTD"), ("60", "Singapore"), ("62", tlv("01", "INV-8841")),
)

DUITNOW_STATIC = emv(
    ("00", "01"), ("01", "11"),
    ("26", tlv("00", "A0000006150001") + tlv("01", "890053") + tlv("02", "0012345678")),
    ("52", "5411"), ("53", "458"), ("58", "MY"), ("59", "KEDAI RUNCIT ALI"), ("60", "KUALA LUMPUR"),
)


def zatca_b64(fields: dict[int, str]) -> str:
    raw = b""
    for tag, value in fields.items():
        b = value.encode("utf-8")
        raw += bytes([tag, len(b)]) + b
    return base64.b64encode(raw).decode()


def fake_jwt(payload: dict) -> str:
    enc = lambda o: base64.urlsafe_b64encode(json.dumps(o).encode()).rstrip(b"=").decode()
    return f"{enc({'alg': 'RS256', 'kid': 'x', 'typ': 'JWT'})}.{enc(payload)}.ZmFrZXNpZw"


class Crc(unittest.TestCase):
    def test_standard_check_value(self):
        # CRC-16/CCITT-FALSE check value for "123456789" is 0x29B1.
        self.assertEqual(crc16_ccitt_false(b"123456789"), 0x29B1)

    def test_tlv_split(self):
        self.assertEqual(parse_emv_tlv("000201010211"), [("00", "01"), ("01", "11")])
        with self.assertRaises(ValueError):
            parse_emv_tlv("0002010105")


class Emvco(unittest.TestCase):
    def test_dynamic_paynow(self):
        r = parse_payload(PAYNOW_DYNAMIC)
        self.assertEqual(r["format"], "emvco")
        self.assertIn("crc ok", r["checks"])
        self.assertEqual((r["amount"], r["currency"], r["country"]), ("23.50", "SGD", "SG"))
        self.assertEqual(r["seller"], "KOPI CORNER PTE LTD")
        self.assertEqual(r["extra"]["initiation"], "dynamic")
        self.assertEqual(r["extra"]["merchant_accounts"][0]["guid"], "SG.PAYNOW")
        self.assertEqual(r["extra"]["additional_data"], {"01": "INV-8841"})
        self.assertEqual(r["warnings"], [])

    def test_static_has_no_amount(self):
        r = parse_payload(DUITNOW_STATIC)
        self.assertIn("crc ok", r["checks"])
        self.assertIsNone(r["amount"])
        self.assertEqual((r["currency"], r["country"]), ("MYR", "MY"))
        self.assertEqual(r["extra"]["initiation"], "static")

    def test_lowercase_crc_accepted(self):
        r = parse_payload(PAYNOW_DYNAMIC[:-4] + PAYNOW_DYNAMIC[-4:].lower())
        self.assertIn("crc ok", r["checks"])

    def test_bad_crc_drops_amount(self):
        tampered = PAYNOW_DYNAMIC.replace("540523.50", "540593.50")
        r = parse_payload(tampered)
        self.assertIsNone(r["amount"])
        self.assertTrue(any("crc failed" in w for w in r["warnings"]))
        self.assertEqual(r["extra"]["amount_untrusted"], "93.50")

    def test_truncated(self):
        r = parse_payload(PAYNOW_DYNAMIC[:40])
        self.assertEqual(r["format"], "emvco")
        self.assertIsNone(r["amount"])
        self.assertTrue(any("truncated" in w for w in r["warnings"]))

    def test_unknown_currency(self):
        r = parse_payload(emv(("00", "01"), ("53", "999"), ("54", "1"), ("58", "XX")))
        self.assertIsNone(r["currency"])
        self.assertTrue(any("unknown currency" in w for w in r["warnings"]))

    def test_zero_amount_rejected(self):
        r = parse_payload(emv(("00", "01"), ("53", "764"), ("54", "0.00"), ("58", "TH")))
        self.assertIsNone(r["amount"])
        self.assertEqual(r["currency"], "THB")


class Upi(unittest.TestCase):
    def test_dynamic(self):
        r = parse_payload("upi://pay?pa=chaiwala@okaxis&pn=Chai%20Wala&am=120.00&cu=INR&tr=ORD42&tn=2%20chai")
        self.assertEqual(r["format"], "upi")
        self.assertEqual((r["amount"], r["currency"], r["country"]), ("120.00", "INR", "IN"))
        self.assertEqual(r["seller"], "Chai Wala")
        self.assertEqual(r["extra"]["pa"], "chaiwala@okaxis")
        self.assertEqual(r["extra"]["tr"], "ORD42")

    def test_static_no_amount(self):
        r = parse_payload("upi://pay?pa=shop@ybl&pn=Shop")
        self.assertIsNone(r["amount"])
        self.assertEqual(r["currency"], "INR")

    def test_bad_amount(self):
        r = parse_payload("upi://pay?pa=a@b&pn=X&am=12,00")
        self.assertIsNone(r["amount"])
        self.assertTrue(r["warnings"])


class Zatca(unittest.TestCase):
    def test_official_example(self):
        # Example base64 string from ZATCA "Guide to Developed FATOORA Compliant QR Code".
        s = "AQxCb2JzIFJlY29yZHMCDzMxMDEyMjM5MzUwMDAwMwMUMjAyMi0wNC0yNVQxNTozMDowMFoEBzEwMDAuMDAFBjE1MC4wMA=="
        r = parse_payload(s)
        self.assertEqual(r["format"], "zatca")
        self.assertEqual(r["seller"], "Bobs Records")
        self.assertEqual(r["seller_tax_id"], "310122393500003")
        self.assertEqual((r["amount"], r["tax"], r["currency"], r["country"]), ("1000.00", "150.00", "SAR", "SA"))
        self.assertEqual(r["date"], "2022-04-25T15:30:00+00:00")

    def test_arabic_seller(self):
        s = zatca_b64({1: "مطعم الريان", 2: "300000000000003", 3: "2024-01-15T12:05:00Z", 4: "57.50", 5: "7.50"})
        r = parse_payload(s)
        self.assertEqual(r["seller"], "مطعم الريان")
        self.assertEqual(r["amount"], "57.50")

    def test_truncated_tlv_not_zatca(self):
        raw = base64.b64decode(zatca_b64({1: "Shop", 2: "300000000000003", 4: "10.00"}))
        r = parse_payload(base64.b64encode(raw[:-3]).decode())
        self.assertEqual(r["format"], "text")


class Portugal(unittest.TestCase):
    # Example 1 message from AT "QR Code Technical Specifications" v1.1 (Oct 2020).
    EXAMPLE = ("A:123456789*B:999999990*C:PT*D:FT*E:N*F:20191231*G:FT AB2019/0035*H:CSDF7T5H-0035*"
               "I1:PT*I2:12000.00*I3:15000.00*I4:900.00*I5:50000.00*I6:6500.00*I7:80000.00*I8:18400.00*"
               "J1:PT-AC*J2:10000.00*J3:25000.56*J4:1000.02*J5:75000.00*J6:6750.00*J7:100000.00*J8:18000.00*"
               "K1:PT-MA*K2:5000.00*K3:12500.00*K4:625.00*K5:25000.00*K6:3000.00*K7:40000.00*K8:8800.00*"
               "L:100.00*M:25.00*N:64000.02*O:513600.58*P:100.00*Q:kLp0*R:9999*S:TB;PT00000000000000000000000;513500.58")

    def test_official_example(self):
        r = parse_payload(self.EXAMPLE)
        self.assertEqual(r["format"], "pt-atcud")
        self.assertEqual((r["amount"], r["tax"], r["currency"]), ("513600.58", "64000.02", "EUR"))
        self.assertEqual((r["date"], r["seller_tax_id"], r["country"]), ("2019-12-31", "123456789", "PT"))
        self.assertEqual(r["extra"]["atcud"], "CSDF7T5H-0035")
        self.assertEqual(r["extra"]["doc_id"], "FT AB2019/0035")
        self.assertIn("required fields present", r["checks"])

    def test_missing_fields(self):
        r = parse_payload("A:123456789*B:999999990*F:20241399")
        self.assertTrue(any("missing required" in w for w in r["warnings"]))
        self.assertTrue(any("invalid date" in w for w in r["warnings"]))
        self.assertIsNone(r["date"])


class IndiaEinvoice(unittest.TestCase):
    DATA = {"SellerGstin": "27AAAPI3182M002", "BuyerGstin": "24AAAPI3182M002", "DocNo": "INV/24-25/0042",
            "DocTyp": "INV", "DocDt": "03/05/2024", "TotInvVal": 11800.5, "ItemCnt": 2,
            "MainHsnCode": "721119", "Irn": "d34b" * 16, "IrnDt": "2024-05-03 19:58:21"}

    def test_nested_data_string(self):
        r = parse_payload(fake_jwt({"data": json.dumps(self.DATA), "iss": "NIC"}))
        self.assertEqual(r["format"], "in-einvoice")
        self.assertEqual((r["amount"], r["currency"], r["date"]), ("11800.5", "INR", "2024-05-03"))
        self.assertEqual(r["seller_tax_id"], "27AAAPI3182M002")
        self.assertEqual(r["extra"]["DocNo"], "INV/24-25/0042")
        self.assertTrue(any("unverified signature" in w for w in r["warnings"]))

    def test_flat_payload(self):
        r = parse_payload(fake_jwt(self.DATA))
        self.assertEqual(r["format"], "in-einvoice")

    def test_other_jwt(self):
        r = parse_payload(fake_jwt({"sub": "123"}))
        self.assertEqual((r["format"], r["raw_kind"]), ("text", "jwt"))


class UrlsAndText(unittest.TestCase):
    def test_myinvois(self):
        r = parse_payload("https://myinvois.hasil.gov.my/F9D425P6DS7D8IU/share/LIJAF97HJJKH8298KHADH0990")
        self.assertEqual((r["format"], r["country"]), ("my-myinvois", "MY"))
        self.assertEqual(r["extra"]["uuid"], "F9D425P6DS7D8IU")
        self.assertEqual(r["extra"]["environment"], "production")
        self.assertIsNone(r["amount"])

    def test_generic_url(self):
        r = parse_payload("https://example.com/r/123")
        self.assertEqual(r["format"], "url")
        self.assertIn("url not fetched", r["checks"])

    def test_garbage(self):
        for s in ["", "hello world", "@@@@", "000201xx", "QUJDREVGR0g=", "a.b.c"]:
            r = parse_payload(s)
            self.assertIsNone(r["amount"], s)
            self.assertIn(r["format"], ("text", "emvco"), s)


@unittest.skipIf(cv2 is None, "opencv not installed")
class Image(unittest.TestCase):
    def _receipt_with_qr(self, payload: str):
        qr = cv2.QRCodeEncoder.create().encode(payload)
        qr = cv2.resize(qr, None, fx=6, fy=6, interpolation=cv2.INTER_NEAREST)
        canvas = np.full((1400, 700, 3), 255, np.uint8)
        for i, line in enumerate(["KOPI CORNER", "1x Kopi C   2.50", "1x Nasi Lemak 21.00", "TOTAL  23.50"]):
            cv2.putText(canvas, line, (40, 80 + 60 * i), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (30, 30, 30), 2)
        y, x = 450, (700 - qr.shape[1]) // 2
        canvas[y:y + qr.shape[0], x:x + qr.shape[1]] = cv2.cvtColor(qr, cv2.COLOR_GRAY2BGR)
        return canvas

    def test_decode_emv_on_receipt(self):
        img = self._receipt_with_qr(PAYNOW_DYNAMIC)
        self.assertEqual(decode_qr_image(img), [PAYNOW_DYNAMIC])
        (r,) = qr_fields(img)
        self.assertEqual((r["amount"], r["currency"], r["country"]), ("23.50", "SGD", "SG"))

    def test_blank_image(self):
        self.assertEqual(decode_qr_image(np.full((300, 300, 3), 255, np.uint8)), [])


if __name__ == "__main__":
    unittest.main()
