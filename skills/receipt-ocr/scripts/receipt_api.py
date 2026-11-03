#!/usr/bin/env python3
"""Small local HTTP API around receipt_ocr.process(). Python standard library only; no LLM, no cloud.

Usage:
  python3 receipt_api.py --port 8080 [--host 127.0.0.1] [--api-key KEY] [--max-mb 15] [--lang en] [--currency EUR]
  (or set RECEIPT_API_KEY instead of --api-key; server flags are defaults that each request may override)

Endpoints:
  GET  /healthz      {"ok": true, "engines": [...]}; 503 when no OCR engine is installed
  POST /v1/receipts  one receipt image or PDF, sent as any of:
    raw body     Content-Type image/jpeg, image/png, image/webp, image/tiff or application/pdf
    multipart    form field "file" (plus option fields)
    JSON         {"image_base64": "...", "filename": "x.jpg", ...options}
  Options (query string, form fields or JSON keys): lang, currency, country, date_order (DMY|MDY), decimal_sep (. or ,),
  engine (auto or comma list), min_conf (0..1), no_variants (true|false), include_text (true|false).

Examples:
  curl -s -H "Authorization: Bearer KEY" -H "Content-Type: image/jpeg" --data-binary @r.jpg \\
       "http://127.0.0.1:8080/v1/receipts?currency=EUR&date_order=DMY"
  curl -s -H "Authorization: Bearer KEY" -F file=@r.png -F lang=en http://127.0.0.1:8080/v1/receipts
  curl -s http://127.0.0.1:8080/healthz

Privacy: the upload goes to a private temp file (mode 0600) that is deleted after processing. Logs hold only
method, path, status, size and time, never receipt contents. Raw OCR text is returned only with include_text=true.
OCR engines are not thread-safe, so requests are processed one at a time; concurrent requests wait their turn.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import hmac
import json
import os
import re
import sys
import tempfile
import threading
import time
import uuid
from argparse import Namespace
from email.parser import BytesParser
from email.policy import HTTP
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import receipt_ocr  # noqa: E402

NOTICE = ("Values with status 'review' are not confirmed: check them against the receipt before use. "
          "Even 'accepted' values come from OCR and can be wrong.")
RAW_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/tiff": ".tiff",
             "application/pdf": ".pdf"}
EXT_TYPES = {".jpg": ".jpg", ".jpeg": ".jpg", ".png": ".png", ".webp": ".webp", ".tif": ".tiff", ".tiff": ".tiff",
             ".pdf": ".pdf"}
OPTION_KEYS = {"lang", "currency", "country", "date_order", "decimal_sep", "engine", "min_conf", "no_variants", "include_text"}
TEXT_KEYS = {"lines", "line_confs", "runs_detail"}  # raw OCR output, stripped unless include_text=true
OCR_LOCK = threading.Lock()  # engines are not thread-safe: one process() call at a time


class ApiError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status, self.message = status, message


# ---------------------------------------------------------------- option validation

def parse_bool(key: str, v) -> bool:
    if isinstance(v, bool):
        return v
    s = str(v).strip().lower()
    if s in {"1", "true", "yes", "on"}:
        return True
    if s in {"0", "false", "no", "off", ""}:
        return False
    raise ApiError(400, f"{key} must be true or false")


def build_options(defaults: dict, raw: dict) -> tuple[Namespace, bool]:
    """Merge request options over server defaults and validate. Returns (args for process(), include_text)."""
    unknown = sorted(set(raw) - OPTION_KEYS)
    if unknown:
        raise ApiError(400, f"unknown option(s): {', '.join(unknown)}")
    o = {**defaults, **{k: v for k, v in raw.items() if v is not None}}
    lang = str(o["lang"]).strip().lower()
    if not re.fullmatch(r"[a-z]{2,3}(-[a-z]{2,4})?(,[a-z]{2,3}(-[a-z]{2,4})?)*", lang):
        raise ApiError(400, "lang must be comma-separated ISO 639-1 codes, e.g. en or ar,en")
    currency = o.get("currency")
    if currency in ("", None):
        currency = None
    else:
        currency = str(currency).strip().upper()
        if not re.fullmatch(r"[A-Z]{3}", currency):
            raise ApiError(400, "currency must be a 3-letter ISO 4217 code, e.g. EUR")
    date_order = o.get("date_order") or None
    if date_order is not None:
        date_order = str(date_order).strip().upper()
        if date_order not in {"DMY", "MDY"}:
            raise ApiError(400, "date_order must be DMY or MDY")
    decimal_sep = o.get("decimal_sep") or None
    if decimal_sep is not None and decimal_sep not in {".", ","}:
        raise ApiError(400, "decimal_sep must be . or ,")
    engine = str(o["engine"]).strip().lower()
    if engine != "auto":
        names = [e.strip() for e in engine.split(",") if e.strip()]
        bad = [e for e in names if e not in receipt_ocr.ENGINES]
        if not names or bad:
            raise ApiError(400, f"engine must be auto or a comma list of {', '.join(receipt_ocr.ENGINES)}")
        missing = [e for e in names if e not in receipt_ocr.available_engines()]
        if missing:
            raise ApiError(400, f"engine not installed on this server: {', '.join(missing)}")
        engine = ",".join(names)
    try:
        min_conf = float(o["min_conf"])
    except (TypeError, ValueError):
        raise ApiError(400, "min_conf must be a number between 0 and 1") from None
    if not 0.0 <= min_conf <= 1.0:
        raise ApiError(400, "min_conf must be a number between 0 and 1")
    include_text = parse_bool("include_text", o.get("include_text", False))
    country = o.get("country")
    if country in ("", None):
        country = None
    else:
        country = str(country).strip().upper()
        if not re.fullmatch(r"[A-Z]{2}", country):
            raise ApiError(400, "country must be a 2-letter ISO 3166-1 code, e.g. IN")
    args = Namespace(lang=lang, engine=engine, currency=currency, country=country, date_order=date_order, decimal_sep=decimal_sep,
                     min_conf=min_conf, no_variants=parse_bool("no_variants", o["no_variants"]), keep_text=include_text)
    return args, include_text


# ---------------------------------------------------------------- body decoding

def sniff_ext(data: bytes) -> str | None:
    """File type from magic bytes, so the declared Content-Type cannot smuggle other content to the decoder."""
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    if data[:4] in (b"II*\x00", b"MM\x00*"):
        return ".tiff"
    if data.startswith(b"%PDF-"):
        return ".pdf"
    return None


def parse_multipart(content_type: str, body: bytes) -> tuple[bytes | None, str | None, dict]:
    """Minimal multipart/form-data parser on email.parser (cgi was removed in Python 3.13)."""
    if "boundary=" not in content_type:
        raise ApiError(400, "multipart body without boundary")
    msg = BytesParser(policy=HTTP).parsebytes(b"Content-Type: " + content_type.encode("latin-1") + b"\r\n\r\n" + body)
    if not msg.is_multipart():
        raise ApiError(400, "malformed multipart body")
    data, filename, fields = None, None, {}
    for part in msg.iter_parts():
        name = part.get_param("name", header="content-disposition")
        if not name:
            continue
        payload = part.get_payload(decode=True) or b""
        if name == "file":
            data, filename = payload, part.get_filename()
        else:
            fields[name] = payload.decode("utf-8", "replace")
    return data, filename, fields


def decode_body(content_type: str, body: bytes) -> tuple[bytes, str, str | None, dict]:
    """Return (file bytes, file extension, original filename, body option fields)."""
    ctype = content_type.split(";")[0].strip().lower()
    if ctype in RAW_TYPES:
        data, filename, fields, declared = body, None, {}, RAW_TYPES[ctype]
    elif ctype == "multipart/form-data":
        data, filename, fields = parse_multipart(content_type, body)
        if data is None:
            raise ApiError(400, "multipart body needs a 'file' field")
        declared = None
    elif ctype == "application/json":
        try:
            obj = json.loads(body)
        except (ValueError, UnicodeDecodeError):
            raise ApiError(400, "invalid JSON body") from None
        if not isinstance(obj, dict) or not isinstance(obj.get("image_base64"), str):
            raise ApiError(400, "JSON body needs a string field 'image_base64'")
        b64 = obj.pop("image_base64")
        if b64.startswith("data:") and "," in b64:  # tolerate data: URLs
            b64 = b64.split(",", 1)[1]
        try:
            data = base64.b64decode(b64, validate=True)
        except (binascii.Error, ValueError):
            raise ApiError(400, "image_base64 is not valid base64") from None
        filename = obj.pop("filename", None)
        filename = filename if isinstance(filename, str) else None
        fields, declared = obj, None
    else:
        raise ApiError(415, "unsupported Content-Type; send image/jpeg, image/png, image/webp, image/tiff, "
                            "application/pdf, multipart/form-data or application/json")
    if not data:
        raise ApiError(400, "empty file")
    ext = sniff_ext(data)
    if ext is None:
        raise ApiError(415, "file is not a JPEG, PNG, WebP, TIFF or PDF")
    if declared and declared != ext:
        raise ApiError(415, "Content-Type does not match the file contents")
    if filename and Path(filename).suffix.lower() in EXT_TYPES and EXT_TYPES[Path(filename).suffix.lower()] != ext:
        raise ApiError(415, "filename extension does not match the file contents")
    return data, ext, filename, fields


def clean_result(res: dict, filename: str, include_text: bool) -> list[dict]:
    """Drop the temp path, and raw OCR text unless asked for."""
    pages = []
    for p in res.get("pages", []):
        p = {k: v for k, v in p.items() if include_text or k not in TEXT_KEYS}
        p["file"] = filename
        pages.append(p)
    return pages


def overall_status(pages: list[dict]) -> str:
    st = [p.get("status") for p in pages]
    if not st or all(s == "error" for s in st):
        return "error"
    return "accepted" if all(s == "accepted" for s in st) else "review"


# ---------------------------------------------------------------- HTTP handler

class Handler(BaseHTTPRequestHandler):
    server_version = "receipt-api/1"
    sys_version = ""
    timeout = 60  # seconds per socket read: slow or stalled clients are dropped

    def log_message(self, fmt, *a):  # silence default logging (it can include request lines/errors)
        pass

    def _log(self, status: int, size: int, t0: float) -> None:
        path = urlsplit(self.path).path  # no query string
        sys.stderr.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {self.command} {path} {status} "
                         f"{size}B {(time.monotonic() - t0) * 1000:.0f}ms\n")

    def _send(self, status: int, obj: dict, t0: float, size: int = 0, request_id: str | None = None) -> None:
        out = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(out)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if request_id:
            self.send_header("X-Request-ID", request_id)
        if status == 401:
            self.send_header("WWW-Authenticate", 'Bearer realm="receipt-api"')
        if status >= 400:
            self.close_connection = True
            self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(out)
        self._log(status, size, t0)

    def _authorized(self) -> bool:
        key = self.server.config["api_key"]
        if not key:
            return True
        got = self.headers.get("Authorization", "")
        token = got[7:] if got[:7].lower() == "bearer " else ""
        return hmac.compare_digest(token.encode("utf-8"), key.encode("utf-8"))

    def do_GET(self):
        t0 = time.monotonic()
        if urlsplit(self.path).path != "/healthz":
            return self._send(404, {"error": "not found"}, t0)
        engines = receipt_ocr.available_engines()
        self._send(200 if engines else 503, {"ok": bool(engines), "engines": engines}, t0)

    def do_POST(self):
        t0 = time.monotonic()
        request_id = uuid.uuid4().hex
        url = urlsplit(self.path)
        size = 0
        try:
            if url.path != "/v1/receipts":
                raise ApiError(404, "not found")
            if not self._authorized():
                raise ApiError(401, "missing or invalid API key (send Authorization: Bearer <key>)")
            if self.headers.get("Transfer-Encoding", "").lower() == "chunked":
                raise ApiError(411, "chunked uploads are not supported; send Content-Length")
            try:
                size = int(self.headers.get("Content-Length", ""))
            except ValueError:
                raise ApiError(411, "Content-Length required") from None
            if size < 0:
                raise ApiError(400, "bad Content-Length")
            limit = self.server.config["max_bytes"]
            if size > limit:
                raise ApiError(413, f"body larger than the {limit}-byte limit")
            ctype = self.headers.get("Content-Type", "")
            if ctype.split(";")[0].strip().lower() not in {*RAW_TYPES, "multipart/form-data", "application/json"}:
                raise ApiError(415, "unsupported Content-Type; send image/jpeg, image/png, image/webp, image/tiff, "
                                    "application/pdf, multipart/form-data or application/json")
            body = self.rfile.read(size)
            if len(body) != size:
                raise ApiError(400, "body shorter than Content-Length")
            data, ext, filename, fields = decode_body(ctype, body)
            raw = {k: v[-1] for k, v in parse_qs(url.query, keep_blank_values=True).items()}
            raw.update(fields)  # body fields win over the query string
            args, include_text = build_options(self.server.config["defaults"], raw)
            if args.engine == "auto" and not receipt_ocr.available_engines():
                raise ApiError(503, "no OCR engine installed on this server")
            name = Path(filename).name[:200] if filename else f"upload{ext}"
            fd, tmp = tempfile.mkstemp(prefix="receipt-", suffix=ext)  # mkstemp creates the file with mode 0600
            try:
                with os.fdopen(fd, "wb") as f:
                    f.write(data)
                del data, body
                with OCR_LOCK:
                    try:
                        res = receipt_ocr.process(Path(tmp), args)
                    except SystemExit:  # process()/load_images() exit on unreadable input or missing PDF support
                        raise ApiError(422, "could not read the file (corrupt image, or PDF support "
                                            "(pymupdf) not installed)") from None
            finally:
                try:
                    os.unlink(tmp)
                except FileNotFoundError:
                    pass
            pages = clean_result(res, name, include_text)
            engines = sorted({e for p in pages for e in p.get("engines", [])})
            self._send(200, {"request_id": request_id, "status": overall_status(pages), "pages": pages,
                             "engines": engines, "processing_ms": round((time.monotonic() - t0) * 1000),
                             "notice": NOTICE}, t0, size, request_id)
        except ApiError as e:
            self._send(e.status, {"error": e.message, "request_id": request_id}, t0, size, request_id)
        except Exception as e:  # never echo receipt data; type name only
            self._send(500, {"error": f"internal error ({type(e).__name__})", "request_id": request_id},
                       t0, size, request_id)


# ---------------------------------------------------------------- server setup

def make_server(host: str = "127.0.0.1", port: int = 8080, api_key: str | None = None, max_bytes: int = 15 << 20,
                defaults: dict | None = None) -> ThreadingHTTPServer:
    """Build (not start) the server. port=0 picks a free port (see server.server_address)."""
    base = {"lang": "en", "engine": "auto", "currency": None, "country": None, "date_order": None, "decimal_sep": None,
            "min_conf": 0.85, "no_variants": False, "include_text": False}
    base.update({k: v for k, v in (defaults or {}).items() if v is not None})
    build_options(base, {})  # fail fast on bad server-wide defaults
    srv = ThreadingHTTPServer((host, port), Handler)
    srv.daemon_threads = True
    srv.config = {"api_key": api_key or None, "max_bytes": max_bytes, "defaults": base}
    return srv


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", default="127.0.0.1", help="bind address (default 127.0.0.1, local only)")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--api-key", default=os.environ.get("RECEIPT_API_KEY"),
                    help="require Authorization: Bearer <key> (default: RECEIPT_API_KEY env var)")
    ap.add_argument("--max-mb", type=float, default=15, help="max request body in MB (default 15)")
    ap.add_argument("--lang", default="en")
    ap.add_argument("--engine", default="auto")
    ap.add_argument("--currency")
    ap.add_argument("--country", help="ISO 3166-1 alpha-2, for receipts that do not show their country")
    ap.add_argument("--date-order", choices=["DMY", "MDY"])
    ap.add_argument("--decimal-sep", choices=[".", ","])
    ap.add_argument("--min-conf", type=float, default=0.85)
    ap.add_argument("--no-variants", action="store_true")
    a = ap.parse_args()
    defaults = {"lang": a.lang, "engine": a.engine, "currency": a.currency, "country": a.country, "date_order": a.date_order,
                "decimal_sep": a.decimal_sep, "min_conf": a.min_conf, "no_variants": a.no_variants}
    try:
        srv = make_server(a.host, a.port, a.api_key, int(a.max_mb * 1024 * 1024), defaults)
    except ApiError as e:
        sys.exit(f"bad default option: {e.message}")
    if a.host in ("0.0.0.0", "::", "") and not a.api_key:
        print("WARNING: listening on all interfaces without an API key; anyone on the network can submit receipts. "
              "Set --api-key or RECEIPT_API_KEY.", file=sys.stderr)
    engines = receipt_ocr.available_engines()
    print(f"receipt API on http://{a.host}:{srv.server_address[1]} engines={engines or 'NONE'} "
          f"auth={'on' if a.api_key else 'off'} max={a.max_mb}MB", file=sys.stderr)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()


if __name__ == "__main__":
    main()
