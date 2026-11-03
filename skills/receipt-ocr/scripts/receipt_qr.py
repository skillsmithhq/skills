"""Deterministic receipt QR-code decoder (no LLM, no network).

Decodes QR codes found on receipt images with OpenCV and parses the payload into a
common shape: format, amount, currency, country, date, tax, seller, seller_tax_id,
checks, warnings, raw_kind, plus format-specific details under "extra".

Nothing here fetches URLs. A URL in a QR code is returned as text only.

IMPORTANT: a static payment QR (the sticker on a shop counter) normally carries only
the merchant's account, with NO amount. Only dynamic QRs (generated per bill) carry
an amount. "amount" is therefore often None, and that is correct, not a failure.

Formats and the sources they were checked against
--------------------------------------------------
emvco  EMV Merchant-Presented QR (PayNow SG, DuitNow MY, PromptPay TH, QRIS ID,
       VietQR VN, FPS HK, ...). VERIFIED against the Hong Kong Monetary Authority's
       "Common QR Code Specification for Retail Payments in Hong Kong", which is
       built on EMVCo's EMV QRCPS Merchant-Presented Mode:
       https://www.hkma.gov.hk/media/chi/doc/key-functions/financial-infrastructure/infrastructure/retail-payment-initiatives/Common_QR_Code_Specification.pdf
       - data object = 2-digit ID + 2-digit length + value (1..99 chars)
       - 00 payload format indicator "01"; 01 point of initiation "11" static / "12" dynamic
       - 53 currency (ISO 4217 numeric), 54 amount (digits + optional single ".",
         non-zero, absent when the payer types the amount), 58 country (ISO 3166-1
         alpha-2), 59 merchant name, 60 merchant city
       - 63 CRC: ISO/IEC 13239, polynomial 0x1021, init 0xFFFF, computed over every
         data object including "6304", written as 4 hex chars (= CRC-16/CCITT-FALSE).
       IDs 26-51 (merchant account templates) are split into sub-objects and their
       "00" GUID is reported as-is; mapping GUIDs to scheme names is NOT done
       (not verified). The EMVCo document itself (emvco.com) sits behind a licence
       click-through and was not read directly.
upi    India UPI deep link upi://pay?pa=..&pn=..&am=..&cu=INR. VERIFIED against
       NPCI "UPI Linking Specifications" v1.6 (Nov 2017, draft), via a mirror:
       https://www.labnol.org/files/linking.pdf  (pa payee VPA, pn payee name,
       mc merchant code, tr txn ref, tn note, am amount - absent means payer types
       it, mam min amount, cu currency - "Currently ONLY INR").
zatca  Saudi ZATCA (FATOORA) QR: base64 of TLV, 1-byte tag, 1-byte length, UTF-8
       value; 1 seller name, 2 VAT number, 3 timestamp, 4 total with VAT, 5 VAT
       total, 6-9 hash/signature/public key (phase 2). VERIFIED against ZATCA
       "Guide to Developed FATOORA Compliant QR Code" (Nov 2021):
       https://zatca.gov.sa/ar/E-Invoicing/SystemsDevelopers/Documents/QRCodeCreation.pdf
       The QR does not encode currency; SAR is assumed and a warning says so.
pt-atcud  Portugal AT QR (Portaria 195/2020). VERIFIED against AT "Technical
       Specifications - Two-dimensional Bar Code - QR Code" v1.1 (Oct 2020):
       https://info.portaldasfinancas.gov.pt/pt/docs/Conteudos_1pagina/Documents/QR_Code_Technical_Specifications.pdf
       (read via web.archive.org). Fields "CODE:value" joined by "*": A issuer NIF,
       B customer NIF (999999990 = final consumer), C customer country, D doc type,
       E status, F date YYYYMMDD, G document id, H ATCUD, I1-I8/J1-J8/K1-K8 VAT by
       tax region, L non-taxable, M stamp duty, N total taxes, O gross total,
       P withholding, Q 4 hash chars, R certificate no., S other. Money is always
       in euros with 2 decimals.
in-einvoice  India GST e-invoice signed QR (a JWT signed by the IRP). BEST EFFORT:
       no official NIC schema was reachable. Claim names (SellerGstin, BuyerGstin,
       DocNo, DocTyp, DocDt dd/mm/yyyy, TotInvVal, ItemCnt, MainHsnCode, Irn,
       IrnDt) are taken from a GSP's decoded-QR sample:
       https://docs.logitax.in/Docs/Get_Decrypted_Signed_QR_Code
       The payload is decoded WITHOUT verifying the signature, so every value is
       reported with the warning "unverified signature".
my-myinvois  Malaysia MyInvois validation link. Format "{portal}/{uuid}/share/{longId}"
       from the MyInvois SDK: https://sdk.myinvois.hasil.gov.my/einvoicingapi/08-get-document-details/
       Portal hosts myinvois.hasil.gov.my (prod) and preprod.myinvois.hasil.gov.my
       (sandbox) from https://sdk.myinvois.hasil.gov.my/faq . The link carries no
       amount/seller; it is never fetched. BEST EFFORT on the path parsing.
url / text  anything else, returned as-is.

ISO 4217 numeric -> alpha mapping below is the standard ISO 4217 list (subset).
"""

from __future__ import annotations

import base64
import binascii
import json
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from urllib.parse import parse_qs, unquote, urlsplit

try:  # image decoding is optional; payload parsing works without OpenCV
    import cv2
    import numpy as np
except ImportError:  # pragma: no cover
    cv2 = None
    np = None

ISO4217_NUMERIC = {
    "702": "SGD", "458": "MYR", "764": "THB", "360": "IDR", "704": "VND",
    "356": "INR", "682": "SAR", "978": "EUR", "840": "USD", "124": "CAD",
    "036": "AUD", "344": "HKD", "554": "NZD", "608": "PHP", "410": "KRW",
    "392": "JPY", "156": "CNY", "826": "GBP",
}

MYINVOIS_HOSTS = {"myinvois.hasil.gov.my": "production", "preprod.myinvois.hasil.gov.my": "sandbox"}

_AMOUNT_RE = re.compile(r"^\d+(\.\d*)?$|^\.\d+$")


def _result(fmt: str, raw_kind: str) -> dict:
    return {
        "format": fmt, "amount": None, "currency": None, "country": None, "date": None,
        "tax": None, "seller": None, "seller_tax_id": None, "checks": [], "warnings": [],
        "raw_kind": raw_kind, "extra": {},
    }


def _decimal_str(value) -> str | None:
    """Return a plain decimal string, or None if value is not a non-negative number."""
    if value is None:
        return None
    s = str(value).strip()
    if not _AMOUNT_RE.match(s):
        return None
    try:
        d = Decimal(s)
    except InvalidOperation:
        return None
    return format(d, "f")


# --------------------------------------------------------------------------- EMVCo

def crc16_ccitt_false(data: bytes) -> int:
    """CRC-16/CCITT-FALSE: poly 0x1021, init 0xFFFF, no reflection, no xorout."""
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) if crc & 0x8000 else (crc << 1)
            crc &= 0xFFFF
    return crc


def emv_crc(payload_without_crc_value: str) -> str:
    """CRC over everything up to and including '6304'. Returns 4 uppercase hex chars."""
    return f"{crc16_ccitt_false(payload_without_crc_value.encode('utf-8')):04X}"


def parse_emv_tlv(s: str) -> list[tuple[str, str]]:
    """Split an EMV string into (id, value) pairs. Raises ValueError if malformed."""
    out, i = [], 0
    while i < len(s):
        head = s[i:i + 4]
        if len(head) < 4 or not head.isdigit():
            raise ValueError(f"bad TLV header at {i}")
        tag, length = head[:2], int(head[2:])
        value = s[i + 4:i + 4 + length]
        if length == 0 or len(value) != length:
            raise ValueError(f"truncated TLV at tag {tag}")
        out.append((tag, value))
        i += 4 + length
    return out


def _parse_emvco(s: str) -> dict:
    r = _result("emvco", "emv-mpm")
    try:
        objs = parse_emv_tlv(s)
    except ValueError as e:
        r["warnings"].append(f"truncated tlv: {e}")
        return r
    fields = dict(objs)
    # CRC must be the last object, "63" length 04.
    if not objs or objs[-1][0] != "63" or len(objs[-1][1]) != 4 or not s.endswith(objs[-1][1]):
        r["warnings"].append("crc missing")
        crc_ok = False
    else:
        expected = emv_crc(s[:-4])
        crc_ok = expected == objs[-1][1].upper()
        if crc_ok:
            r["checks"].append("crc ok")
        else:
            r["warnings"].append(f"crc failed (expected {expected}, got {objs[-1][1]})")
    if fields.get("00") != "01":
        r["warnings"].append("payload format indicator is not 01")

    poi = fields.get("01")
    r["extra"]["initiation"] = {"11": "static", "12": "dynamic"}.get(poi, poi)
    cur = fields.get("53")
    if cur:
        r["currency"] = ISO4217_NUMERIC.get(cur)
        r["extra"]["currency_numeric"] = cur
        if r["currency"] is None:
            r["warnings"].append(f"unknown currency code {cur}")
    r["country"] = fields.get("58")
    r["seller"] = fields.get("59")
    r["extra"]["city"] = fields.get("60")

    amount = _decimal_str(fields.get("54"))
    if "54" in fields and (amount is None or Decimal(amount) == 0):
        r["warnings"].append("invalid amount field 54")
        amount = None
    if crc_ok:
        r["amount"] = amount
    elif amount is not None:
        r["extra"]["amount_untrusted"] = amount
        r["warnings"].append("amount ignored because crc failed")
    if r["amount"] is None and "54" not in fields:
        r["checks"].append("no amount in QR (payer enters it; typical of static QR)")

    schemes = []
    for tag, value in objs:
        if "26" <= tag <= "51":
            try:
                sub = dict(parse_emv_tlv(value))
                schemes.append({"id": tag, "guid": sub.get("00"), "fields": sub})
            except ValueError:
                schemes.append({"id": tag, "raw": value})
        elif "02" <= tag <= "25":
            schemes.append({"id": tag, "raw": value})
    r["extra"]["merchant_accounts"] = schemes
    if "62" in fields:
        try:
            r["extra"]["additional_data"] = dict(parse_emv_tlv(fields["62"]))
        except ValueError:
            r["extra"]["additional_data"] = {"raw": fields["62"]}
    return r


# --------------------------------------------------------------------------- UPI

def _parse_upi(s: str) -> dict:
    r = _result("upi", "upi-deeplink")
    parts = urlsplit(s)
    if parts.netloc.lower() != "pay":
        r["warnings"].append(f"upi link is '{parts.netloc}', not 'pay'")
    q = {k: v[0] for k, v in parse_qs(parts.query, keep_blank_values=True).items()}
    r["country"] = "IN"
    r["seller"] = q.get("pn") or None
    cu = q.get("cu")
    if cu:
        r["currency"] = cu.upper()
        if r["currency"] != "INR":
            r["warnings"].append(f"cu={cu}; NPCI spec supports only INR")
    else:
        r["currency"] = "INR"
        r["checks"].append("currency implied: UPI supports only INR")
    if "am" in q:
        r["amount"] = _decimal_str(q["am"])
        if r["amount"] is None:
            r["warnings"].append(f"invalid amount am={q['am']!r}")
    else:
        r["checks"].append("no amount in QR (payer enters it; typical of static QR)")
    if not q.get("pa"):
        r["warnings"].append("payee address pa missing")
    r["extra"] = {k: q[k] for k in ("pa", "pn", "mc", "tid", "tr", "tn", "mam", "url") if k in q}
    return r


# --------------------------------------------------------------------------- ZATCA

def _b64decode_strict(s: str) -> bytes | None:
    t = s.strip()
    if len(t) < 8 or not re.fullmatch(r"[A-Za-z0-9+/]+={0,2}", t):
        return None
    try:
        return base64.b64decode(t + "=" * (-len(t) % 4), validate=True)
    except (binascii.Error, ValueError):
        return None


def parse_zatca_tlv(data: bytes) -> list[tuple[int, bytes]]:
    out, i = [], 0
    while i < len(data):
        if i + 2 > len(data):
            raise ValueError("truncated TLV header")
        tag, length = data[i], data[i + 1]
        value = data[i + 2:i + 2 + length]
        if len(value) != length:
            raise ValueError(f"truncated TLV value for tag {tag}")
        out.append((tag, value))
        i += 2 + length
    return out


def _looks_like_zatca(s: str) -> list[tuple[int, bytes]] | None:
    raw = _b64decode_strict(s)
    if raw is None:
        return None
    try:
        objs = parse_zatca_tlv(raw)
    except ValueError:
        return None
    tags = [t for t, _ in objs]
    if not {1, 2, 4}.issubset(tags) or any(t < 1 or t > 9 for t in tags):
        return None
    try:
        for t, v in objs:
            if t <= 5:
                v.decode("utf-8")
    except UnicodeDecodeError:
        return None
    return objs


def _iso_datetime(s: str) -> str | None:
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).isoformat()
    except ValueError:
        return None


def _parse_zatca(objs: list[tuple[int, bytes]]) -> dict:
    r = _result("zatca", "zatca-tlv-base64")
    f = {t: v for t, v in objs}
    txt = {t: v.decode("utf-8") for t, v in f.items() if t <= 5}
    r["country"] = "SA"
    r["seller"] = txt.get(1)
    r["seller_tax_id"] = txt.get(2)
    if 3 in txt:
        r["date"] = _iso_datetime(txt[3])
        if r["date"] is None:
            r["warnings"].append(f"unparseable timestamp {txt[3]!r}")
    r["amount"] = _decimal_str(txt.get(4))
    r["tax"] = _decimal_str(txt.get(5))
    if 4 in txt and r["amount"] is None:
        r["warnings"].append(f"invalid total {txt[4]!r}")
    r["currency"] = "SAR"
    r["warnings"].append("currency not encoded in ZATCA QR; assumed SAR")
    if r["seller_tax_id"] and not re.fullmatch(r"3\d{13}3", r["seller_tax_id"]):
        r["warnings"].append("VAT number is not 15 digits starting and ending with 3")
    if any(t >= 6 for t in f):
        r["warnings"].append("phase-2 signature present but not verified")
    r["extra"] = {"tags_present": sorted(f), "phase2_fields": {t: v.hex() for t, v in f.items() if t >= 6}}
    return r


# --------------------------------------------------------------------------- Portugal

_PT_REQUIRED = ["A", "B", "C", "D", "E", "F", "G", "H", "N", "O", "Q", "R"]


def _parse_pt(s: str) -> dict:
    r = _result("pt-atcud", "pt-at-qr")
    fields: dict[str, str] = {}
    for part in s.split("*"):
        code, sep, value = part.partition(":")
        if not sep:
            r["warnings"].append(f"field without ':' {part!r}")
            continue
        fields[code.strip()] = value
    missing = [c for c in _PT_REQUIRED if c not in fields]
    if missing:
        r["warnings"].append("missing required fields: " + ",".join(missing))
    else:
        r["checks"].append("required fields present")
    r["country"] = "PT"
    r["currency"] = "EUR"
    r["seller_tax_id"] = fields.get("A")
    f = fields.get("F", "")
    if re.fullmatch(r"\d{8}", f):
        try:
            r["date"] = date(int(f[:4]), int(f[4:6]), int(f[6:])).isoformat()
        except ValueError:
            r["warnings"].append(f"invalid date F:{f}")
    elif f:
        r["warnings"].append(f"invalid date F:{f}")
    for key, code in (("amount", "O"), ("tax", "N")):
        if code in fields:
            r[key] = _decimal_str(fields[code])
            if r[key] is None:
                r["warnings"].append(f"invalid amount {code}:{fields[code]}")
    r["extra"] = {
        "customer_tax_id": fields.get("B"), "customer_country": fields.get("C"),
        "doc_type": fields.get("D"), "doc_status": fields.get("E"), "doc_id": fields.get("G"),
        "atcud": fields.get("H"), "hash4": fields.get("Q"), "certificate": fields.get("R"),
        "fields": fields,
    }
    return r


# --------------------------------------------------------------------------- India e-invoice JWT

def _b64url(seg: str) -> bytes:
    return base64.urlsafe_b64decode(seg + "=" * (-len(seg) % 4))


def _jwt_payload(s: str) -> dict | None:
    parts = s.strip().split(".")
    if len(parts) != 3 or not all(re.fullmatch(r"[A-Za-z0-9_-]+", p) for p in parts[:2]):
        return None
    try:
        header = json.loads(_b64url(parts[0]))
        payload = json.loads(_b64url(parts[1]))
    except (ValueError, binascii.Error):
        return None
    if not isinstance(header, dict) or not isinstance(payload, dict):
        return None
    return payload


def _einvoice_data(payload: dict) -> dict | None:
    data = payload.get("data", payload)
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except ValueError:
            return None
    if isinstance(data, dict) and ("SellerGstin" in data or "Irn" in data):
        return data
    return None


def _parse_in_einvoice(payload: dict, data: dict) -> dict:
    r = _result("in-einvoice", "jwt")
    r["warnings"].append("unverified signature: JWT decoded without checking the IRP signature")
    r["country"] = "IN"
    r["currency"] = "INR"
    r["seller_tax_id"] = data.get("SellerGstin")
    tot = data.get("TotInvVal")
    if tot is not None:
        r["amount"] = _decimal_str(tot)
        if r["amount"] is None:
            r["warnings"].append(f"invalid TotInvVal {tot!r}")
    dt = str(data.get("DocDt") or "")
    m = re.fullmatch(r"(\d{2})/(\d{2})/(\d{4})", dt)
    if m:
        try:
            r["date"] = date(int(m[3]), int(m[2]), int(m[1])).isoformat()
        except ValueError:
            r["warnings"].append(f"invalid DocDt {dt}")
    elif dt:
        r["warnings"].append(f"unrecognised DocDt {dt}")
    r["extra"] = {k: data.get(k) for k in
                  ("BuyerGstin", "DocNo", "DocTyp", "ItemCnt", "MainHsnCode", "Irn", "IrnDt") if k in data}
    if "iss" in payload:
        r["extra"]["iss"] = payload["iss"]
    return r


# --------------------------------------------------------------------------- MyInvois / URL

def _parse_url(s: str) -> dict:
    parts = urlsplit(s.strip())
    host = (parts.hostname or "").lower()
    if host in MYINVOIS_HOSTS:
        r = _result("my-myinvois", "url")
        r["country"] = "MY"
        segs = [unquote(x) for x in parts.path.split("/") if x]
        r["extra"] = {"url": s.strip(), "environment": MYINVOIS_HOSTS[host]}
        if len(segs) >= 3 and segs[-2].lower() == "share":
            r["extra"]["uuid"] = segs[-3]
            r["extra"]["long_id"] = segs[-1]
            r["checks"].append("validation link shape uuid/share/longId")
        else:
            r["warnings"].append("MyInvois URL not in {uuid}/share/{longId} form")
        r["warnings"].append("validation link only: amount/seller are not in the QR; URL not fetched")
        return r
    r = _result("url", "url")
    r["extra"] = {"url": s.strip(), "host": host}
    r["checks"].append("url not fetched")
    return r


# --------------------------------------------------------------------------- dispatcher

def parse_payload(s: str) -> dict:
    """Classify a QR payload string and extract receipt-relevant fields."""
    if s is None:
        s = ""
    t = s.strip()
    if t.lower().startswith("upi://"):
        return _parse_upi(t)
    if t.startswith("000201"):
        return _parse_emvco(t)
    if re.match(r"^A:[^*]*\*B:", t):
        return _parse_pt(t)
    payload = _jwt_payload(t)
    if payload is not None:
        data = _einvoice_data(payload)
        if data is not None:
            return _parse_in_einvoice(payload, data)
        r = _result("text", "jwt")
        r["warnings"].append("JWT of unknown issuer; not decoded further")
        r["extra"] = {"text": t}
        return r
    if re.match(r"^https?://", t, re.I):
        return _parse_url(t)
    objs = _looks_like_zatca(t)
    if objs is not None:
        return _parse_zatca(objs)
    r = _result("text", "text")
    r["extra"] = {"text": s}
    return r


# --------------------------------------------------------------------------- image decoding

def _variants(img):
    yield img
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    yield gray
    up = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    yield up
    _, bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    yield bw
    _, bwu = cv2.threshold(up, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    yield bwu
    # The classic detector sometimes misses a clean QR at one particular scale
    # (observed on synthetic receipts); a downscaled copy usually recovers it.
    yield cv2.resize(gray, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)


def _detectors():
    yield cv2.QRCodeDetector()
    if hasattr(cv2, "QRCodeDetectorAruco"):  # OpenCV >= 4.8
        yield cv2.QRCodeDetectorAruco()


def _decode_one(det, img) -> list[str]:
    try:
        ok, decoded, _pts, _ = det.detectAndDecodeMulti(img)
        if ok and any(decoded):
            return [d for d in decoded if d]
    except cv2.error:
        pass
    try:
        d, _pts, _ = det.detectAndDecode(img)
        return [d] if d else []
    except cv2.error:
        return []


def decode_qr_image(img) -> list[str]:
    """Return the distinct QR payload strings found in an image (path or ndarray).

    Tries cv2.QRCodeDetector (multi, then single) and, when available,
    cv2.QRCodeDetectorAruco, on the original, grayscale, 2x upscaled, Otsu-binarised
    and half-scale variants. Results are deduplicated in first-seen order.
    """
    if cv2 is None:
        raise RuntimeError("opencv (cv2) is not installed")
    if isinstance(img, (str, bytes)) or hasattr(img, "__fspath__"):
        path = img
        img = cv2.imread(str(path))
        if img is None:
            raise ValueError(f"cannot read image {path}")
    found: list[str] = []
    variants = list(_variants(img))
    for det in _detectors():
        for v in variants:
            for t in _decode_one(det, v):
                if t not in found:
                    found.append(t)
    return found


def qr_fields(img) -> list[dict]:
    """Decode every QR in the image and parse each payload."""
    return [dict(parse_payload(t), payload=t) for t in decode_qr_image(img)]


if __name__ == "__main__":  # pragma: no cover
    import sys
    for arg in sys.argv[1:]:
        print(json.dumps(qr_fields(arg), indent=2, ensure_ascii=False))
