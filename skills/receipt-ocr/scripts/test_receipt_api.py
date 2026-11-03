#!/usr/bin/env python3
"""Tests for receipt_api.py: a real server on a free port, plus one end-to-end OCR run on a generated receipt.

Run from this folder:  python3 -m unittest test_receipt_api -v
The end-to-end test needs an OCR engine and OpenCV, and is skipped without them.
"""

from __future__ import annotations

import base64
import http.client
import json
import os
import sys
import threading
import unittest
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import receipt_api  # noqa: E402
import receipt_ocr  # noqa: E402

KEY = "test-key-123"
PNG_1PX = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")


def receipt_png() -> bytes:
    """A clean synthetic receipt, about 800 px wide, black text on white."""
    import cv2
    import numpy as np
    lines = ["CORNER CAFE", "23/03/2026", "Latte 7.00", "Muffin 3.25", "Subtotal 10.25", "Tax 0.82", "Total 11.07"]
    img = np.full((90 * len(lines) + 80, 800, 3), 255, np.uint8)
    for i, t in enumerate(lines):
        cv2.putText(img, t, (40, 90 + 90 * i), cv2.FONT_HERSHEY_SIMPLEX, 1.6, (0, 0, 0), 3, cv2.LINE_AA)
    ok, buf = cv2.imencode(".png", img)
    assert ok
    return buf.tobytes()


class Server:
    def __init__(self, **kw):
        self.srv = receipt_api.make_server("127.0.0.1", 0, **kw)
        self.port = self.srv.server_address[1]
        self.t = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.t.start()

    def request(self, method, path, body=b"", headers=None, timeout=600):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=timeout)
        try:
            c.request(method, path, body=body, headers=headers or {})
            r = c.getresponse()
            return r.status, json.loads(r.read() or b"{}")
        finally:
            c.close()

    def stop(self):
        self.srv.shutdown()
        self.srv.server_close()


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        receipt_api.sys.stderr = open(os.devnull, "w")  # keep access logs out of test output
        cls.s = Server(api_key=KEY, max_bytes=2000)

    @classmethod
    def tearDownClass(cls):
        cls.s.stop()
        receipt_api.sys.stderr.close()
        receipt_api.sys.stderr = sys.__stderr__

    def auth(self, **h):
        return {"Authorization": f"Bearer {KEY}", **h}

    def test_healthz(self):
        st, body = self.s.request("GET", "/healthz")
        self.assertEqual(st, 200 if receipt_ocr.available_engines() else 503)
        self.assertEqual(body["engines"], receipt_ocr.available_engines())

    def test_404(self):
        self.assertEqual(self.s.request("GET", "/nope")[0], 404)
        self.assertEqual(self.s.request("POST", "/v1/other", PNG_1PX, self.auth(**{"Content-Type": "image/png"}))[0], 404)

    def test_401_without_or_with_wrong_key(self):
        self.assertEqual(self.s.request("POST", "/v1/receipts", PNG_1PX, {"Content-Type": "image/png"})[0], 401)
        st, _ = self.s.request("POST", "/v1/receipts", PNG_1PX,
                               {"Content-Type": "image/png", "Authorization": "Bearer wrong"})
        self.assertEqual(st, 401)

    def test_415_unknown_type_and_mismatched_bytes(self):
        st, body = self.s.request("POST", "/v1/receipts", b"hello", self.auth(**{"Content-Type": "text/plain"}))
        self.assertEqual(st, 415)
        self.assertIn("error", body)
        st, _ = self.s.request("POST", "/v1/receipts", b"not a png", self.auth(**{"Content-Type": "image/png"}))
        self.assertEqual(st, 415)

    def test_413_too_large(self):
        st, body = self.s.request("POST", "/v1/receipts", b"\x89PNG" + b"0" * 5000, self.auth(**{"Content-Type": "image/png"}))
        self.assertEqual(st, 413)
        self.assertIn("limit", body["error"])

    def test_400_bad_options(self):
        for q in ["date_order=YMD", "min_conf=2", "min_conf=abc", "decimal_sep=x", "currency=EURO",
                  "engine=magic", "no_variants=maybe", "lang=English", "colour=red"]:
            st, body = self.s.request("POST", f"/v1/receipts?{q}", PNG_1PX, self.auth(**{"Content-Type": "image/png"}))
            self.assertEqual(st, 400, q)
            self.assertIn("error", body, q)

    def test_400_bad_json(self):
        st, _ = self.s.request("POST", "/v1/receipts", b"{not json", self.auth(**{"Content-Type": "application/json"}))
        self.assertEqual(st, 400)
        st, _ = self.s.request("POST", "/v1/receipts", json.dumps({"image_base64": "@@@"}).encode(),
                               self.auth(**{"Content-Type": "application/json"}))
        self.assertEqual(st, 400)


def multipart(fields: dict, filename: str, data: bytes, ctype: str) -> tuple[bytes, str]:
    b = uuid.uuid4().hex
    out = b""
    for k, v in fields.items():
        out += f'--{b}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode()
    out += (f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f"Content-Type: {ctype}\r\n\r\n").encode() + data + f"\r\n--{b}--\r\n".encode()
    return out, f"multipart/form-data; boundary={b}"


def _has_cv2() -> bool:
    try:
        import cv2  # noqa: F401
        return True
    except ImportError:
        return False


@unittest.skipUnless(receipt_ocr.available_engines() and _has_cv2(), "needs an OCR engine and OpenCV")
class EndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        receipt_api.sys.stderr = open(os.devnull, "w")
        cls.s = Server(defaults={"currency": "USD", "date_order": "DMY"})  # no key: auth is off
        cls.png = receipt_png()

    @classmethod
    def tearDownClass(cls):
        cls.s.stop()
        receipt_api.sys.stderr.close()
        receipt_api.sys.stderr = sys.__stderr__

    def check(self, st, body, include_text=False):
        self.assertEqual(st, 200, body)
        self.assertIn(body["status"], {"accepted", "review"})
        self.assertTrue(body["request_id"] and body["engines"] and "processing_ms" in body)
        self.assertIn("review", body["notice"])
        page = body["pages"][0]
        self.assertEqual(page["fields"]["total"]["value"], "11.07")
        self.assertFalse(page["file"].startswith(("/", "receipt-")), "temp path must not leak")
        self.assertEqual("runs_detail" in page, include_text)

    def test_raw(self):
        self.check(*self.s.request("POST", "/v1/receipts?no_variants=true", self.png, {"Content-Type": "image/png"}))

    def test_multipart(self):
        body, ctype = multipart({"no_variants": "true", "currency": "USD"}, "r.png", self.png, "application/octet-stream")
        self.check(*self.s.request("POST", "/v1/receipts", body, {"Content-Type": ctype}))

    def test_base64_json_with_text(self):
        payload = {"image_base64": base64.b64encode(self.png).decode(), "filename": "x.png", "no_variants": True,
                   "include_text": True}
        self.check(*self.s.request("POST", "/v1/receipts", json.dumps(payload).encode(),
                                   {"Content-Type": "application/json"}), include_text=True)

    def test_concurrent_requests_queue(self):
        res = []
        def go():
            res.append(self.s.request("POST", "/v1/receipts?no_variants=true", self.png, {"Content-Type": "image/png"}))
        ts = [threading.Thread(target=go) for _ in range(3)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        self.assertEqual(len(res), 3)
        for st, body in res:
            self.check(st, body)


if __name__ == "__main__":
    unittest.main()
