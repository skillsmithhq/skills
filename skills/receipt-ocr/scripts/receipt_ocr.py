#!/usr/bin/env python3
"""Free, local receipt OCR: open-source engines, several image variants, field voting, arithmetic gating. No LLM, no API.

Usage:
  python3 receipt_ocr.py receipt.jpg [more files or folders] --lang en,hi --currency INR --date-order DMY --out results/

Engines (any installed ones are used; install at least one):
  RapidOCR   pip install rapidocr_onnxruntime        (PaddleOCR models on ONNX Runtime: small, ~300 MB with deps)
  PaddleOCR  pip install paddlepaddle paddleocr      (full framework, several GB; more language models)
  Tesseract  apt/brew install tesseract + language packs; pip install pytesseract
  EasyOCR    pip install easyocr
Optional: pip install opencv-python-headless (preprocessing), pymupdf (PDF input).

Each field is "accepted" only when every engine/variant that produced it agrees and its checks pass;
otherwise it is returned with status "review" and the reasons. Accuracy must be measured with receipt_eval.py.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from receipt_parse import parse_receipt  # noqa: E402

# ISO 639-1 -> engine language codes (extend as needed; unknown codes are passed through)
TESS = {"en": "eng", "hi": "hin", "mr": "mar", "bn": "ben", "ta": "tam", "te": "tel", "kn": "kan", "ml": "mal", "gu": "guj",
        "pa": "pan", "ur": "urd", "ar": "ara", "fa": "fas", "he": "heb", "zh": "chi_sim", "zh-tw": "chi_tra", "ja": "jpn",
        "ko": "kor", "th": "tha", "vi": "vie", "id": "ind", "ms": "msa", "ru": "rus", "uk": "ukr", "de": "deu", "fr": "fra",
        "es": "spa", "it": "ita", "pt": "por", "nl": "nld", "pl": "pol", "tr": "tur", "el": "ell", "sv": "swe", "no": "nor",
        "da": "dan", "fi": "fin", "cs": "ces", "hu": "hun", "ro": "ron"}
PADDLE = {"zh": "ch", "zh-tw": "chinese_cht", "ja": "japan", "ko": "korean", "hi": "hi", "mr": "mr", "ar": "ar", "fa": "fa",
          "ru": "ru", "uk": "uk", "ta": "ta", "te": "te", "kn": "ka", "de": "german", "fr": "fr", "en": "en"}
EASY = {"zh": "ch_sim", "zh-tw": "ch_tra", "ja": "ja", "ko": "ko"}
RTL = {"ar", "fa", "he", "ur"}
FIELDS = ["merchant", "date", "time", "currency", "subtotal", "tax", "tip", "discount", "total"]
CRITICAL = {"date", "currency", "total"}


# ---------------------------------------------------------------- input and preprocessing

def load_images(path: Path) -> list:
    """Return a list of images (numpy arrays if OpenCV is available, else file paths)."""
    if path.suffix.lower() == ".pdf":
        try:
            import fitz  # PyMuPDF
            import numpy as np
        except ImportError:
            sys.exit("PDF input needs: pip install pymupdf numpy")
        out = []
        for page in fitz.open(path):
            pix = page.get_pixmap(dpi=300)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
            out.append(img[:, :, :3][:, :, ::-1].copy())  # RGB -> BGR
        return out
    try:
        import cv2
        img = cv2.imread(str(path))
        if img is None:
            sys.exit(f"cannot read image: {path}")
        return [img]
    except ImportError:
        return [str(path)]


def variants(img) -> dict:
    """Image variants that help different failure modes. Without OpenCV, only the original is used."""
    try:
        import cv2
        import numpy as np
    except ImportError:
        return {"original": img}
    if isinstance(img, str):
        img = cv2.imread(img)
    h, w = img.shape[:2]
    if w < 1200:  # small photos: upscale so thin thermal-print strokes survive
        img = cv2.resize(img, None, fx=1200 / w, fy=1200 / w, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # deskew from the dominant angle of dark pixels
    thr = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    coords = np.column_stack(np.where(thr > 0))
    if len(coords) > 100:
        angle = cv2.minAreaRect(coords)[-1]
        angle = -(90 + angle) if angle < -45 else -angle
        if angle > 45:
            angle -= 90
        if 0.3 < abs(angle) < 15:
            m = cv2.getRotationMatrix2D((gray.shape[1] / 2, gray.shape[0] / 2), angle, 1.0)
            img = cv2.warpAffine(img, m, (img.shape[1], img.shape[0]), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(gray)
    binar = cv2.adaptiveThreshold(cv2.fastNlMeansDenoising(clahe, h=10), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                  cv2.THRESH_BINARY, 31, 15)
    return {"original": img, "contrast": cv2.cvtColor(clahe, cv2.COLOR_GRAY2BGR), "binary": cv2.cvtColor(binar, cv2.COLOR_GRAY2BGR)}


# ---------------------------------------------------------------- engines -> words with boxes

def run_paddle(img, langs):
    from paddleocr import PaddleOCR
    lang = PADDLE.get(langs[0], langs[0])
    key = ("paddle", lang)
    if key not in _CACHE:
        _CACHE[key] = PaddleOCR(lang=lang, use_doc_orientation_classify=True, use_doc_unwarping=True,
                                use_textline_orientation=True)
    words = []
    for res in _CACHE[key].predict(img):
        d = res.json
        d = d.get("res", d)
        for text, score, box in zip(d.get("rec_texts", []), d.get("rec_scores", []), d.get("rec_boxes", [])):
            x0, y0, x1, y1 = [float(v) for v in box]
            words.append((text, float(score), x0, y0, x1, y1))
    return words


def run_rapidocr(img, langs):
    from rapidocr_onnxruntime import RapidOCR
    if "rapid" not in _CACHE:
        _CACHE["rapid"] = RapidOCR()  # default models: Chinese + English (Latin script); other scripts need their models
    result, _ = _CACHE["rapid"](img)
    words = []
    for box, text, score in result or []:
        xs, ys = [p[0] for p in box], [p[1] for p in box]
        words.append((text, float(score), min(xs), min(ys), max(xs), max(ys)))
    return words


def run_tesseract(img, langs):
    import pytesseract
    from pytesseract import Output
    lang = "+".join(TESS.get(l, l) for l in langs)
    d = pytesseract.image_to_data(img, lang=lang, config="--oem 1 --psm 4", output_type=Output.DICT)
    words = []
    for i, text in enumerate(d["text"]):
        if text.strip() and float(d["conf"][i]) >= 0:
            x, y, w, h = d["left"][i], d["top"][i], d["width"][i], d["height"][i]
            words.append((text, float(d["conf"][i]) / 100, x, y, x + w, y + h))
    return words


def run_easyocr(img, langs):
    import easyocr
    key = ("easy", tuple(langs))
    if key not in _CACHE:
        _CACHE[key] = easyocr.Reader([EASY.get(l, l) for l in langs], gpu=False, verbose=False)
    words = []
    for box, text, conf in _CACHE[key].readtext(img):
        xs, ys = [p[0] for p in box], [p[1] for p in box]
        words.append((text, float(conf), min(xs), min(ys), max(xs), max(ys)))
    return words


_CACHE: dict = {}
ENGINES = {"rapidocr": ("rapidocr_onnxruntime", run_rapidocr), "paddle": ("paddleocr", run_paddle), "tesseract": ("pytesseract", run_tesseract), "easyocr": ("easyocr", run_easyocr)}


def available_engines() -> list[str]:
    import importlib.util
    import shutil
    out = []
    for name, (mod, _) in ENGINES.items():
        if importlib.util.find_spec(mod) and (name != "tesseract" or shutil.which("tesseract")):
            out.append(name)
    return out


def to_lines(words, rtl: bool) -> tuple[list[str], list[float]]:
    """Group word boxes into visual lines by vertical overlap; order words by x (reversed for RTL scripts)."""
    words = sorted(words, key=lambda w: (w[3] + w[5]) / 2)
    rows: list[list] = []
    for w in words:
        cy, h = (w[3] + w[5]) / 2, max(w[5] - w[3], 1)
        if rows:
            last = rows[-1]
            ly = sum((x[3] + x[5]) / 2 for x in last) / len(last)
            lh = sum(max(x[5] - x[3], 1) for x in last) / len(last)
            if abs(cy - ly) < 0.5 * min(h, lh):
                last.append(w)
                continue
        rows.append([w])
    lines, confs = [], []
    for row in rows:
        row.sort(key=lambda w: w[2], reverse=rtl)
        lines.append(" ".join(w[0] for w in row))
        confs.append(min(w[1] for w in row))
    return lines, confs


# ---------------------------------------------------------------- voting and gating

def vote(parses: dict, min_conf: float) -> dict:
    """Combine parses from every engine x variant. A field is accepted when all runs that found it agree."""
    out = {"fields": {}, "runs": len(parses)}
    for f in FIELDS:
        vals = [(k, p[f]) for k, p in parses.items() if p[f]["value"] is not None]
        counts = Counter(str(v["value"]) for _, v in vals)
        if not counts:
            out["fields"][f] = {"value": None, "status": "missing" if f in CRITICAL else "absent"}
            continue
        best, n = counts.most_common(1)[0]
        agreeing = [v for _, v in vals if str(v["value"]) == best]
        conf = max(v["confidence"] for v in agreeing)
        checks = sorted(set.intersection(*[set(v["checks"]) for v in agreeing]))  # must hold in every agreeing run
        flags = {c for v in agreeing for c in v["checks"]}
        reasons = []
        if len(counts) > 1:
            reasons.append(f"runs disagree: {dict(counts)}")
        if n < len(parses):
            reasons.append(f"only {n} of {len(parses)} runs found this value")
        if f in CRITICAL and len(parses) < 2:
            reasons.append("single run: no cross-check (use two engines or image variants)")
        if conf < min_conf:
            reasons.append(f"confidence {conf:.2f} below {min_conf}")
        if f == "total" and not any("reconciles" in c for c in checks):
            reasons.append("total not confirmed by arithmetic in every run")
        if f == "total" and any(c.startswith("no total keyword") or c.startswith("total line is above") for c in flags):
            reasons.append("total position or keyword not confirmed")
        if f == "total" and any(w.startswith("total line unreadable") for p in parses.values() for w in p["warnings"]):
            reasons.append("a run could not read the total line")
        if f == "date" and any("ambiguous" in c or "non-Gregorian" in c or c.startswith("suspect") for c in flags):
            reasons.append("date format ambiguous")
        if f == "merchant":
            reasons.append("merchant name is heuristic")
        out["fields"][f] = {"value": best, "status": "review" if reasons else "accepted", "agreement": f"{n}/{len(parses)}",
                            "confidence": conf, "checks": checks, "reasons": reasons,
                            "evidence": agreeing[0]["evidence"]}
    best_run = max(parses, key=lambda k: (bool(parses[k]["reconciliation"].get("totals_reconcile")),
                                          len(parses[k]["line_items"])))
    out["line_items"] = parses[best_run]["line_items"]
    out["line_items_from"] = best_run
    out["reconciliation"] = parses[best_run]["reconciliation"]
    out["tax_ids"] = parses[best_run]["tax_ids"]
    out["payment"] = parses[best_run]["payment"]
    out["warnings"] = sorted({w for p in parses.values() for w in p["warnings"]})
    crit = [out["fields"][f]["status"] for f in CRITICAL]
    out["status"] = "accepted" if all(s == "accepted" for s in crit) else "review"
    return out


def process(path: Path, args) -> dict:
    langs = [l.strip().lower() for l in args.lang.split(",") if l.strip()]
    engines = [e for e in (args.engine.split(",") if args.engine != "auto" else available_engines())]
    if not engines:
        sys.exit("No OCR engine installed. Install one of: rapidocr_onnxruntime, paddleocr, pytesseract (+ tesseract), easyocr.")
    pages = load_images(path)
    results = []
    for pi, page in enumerate(pages):
        parses, errors = {}, {}
        vs = variants(page) if not args.no_variants else {"original": page}
        for eng in engines:
            for vname, img in vs.items():
                try:
                    words = ENGINES[eng][1](img, langs)
                except Exception as e:  # one engine failing must not hide the others
                    errors[f"{eng}/{vname}"] = f"{type(e).__name__}: {e}"
                    continue
                lines, confs = to_lines(words, rtl=langs[0] in RTL)
                rec = parse_receipt(lines, confs, args.currency, args.date_order, args.decimal_sep)
                parses[f"{eng}/{vname}"] = rec.to_dict()
                if args.keep_text:
                    parses[f"{eng}/{vname}"]["lines"] = lines
        if not parses:
            results.append({"file": str(path), "page": pi + 1, "status": "error", "errors": errors})
            continue
        res = vote(parses, args.min_conf)
        res.update({"file": str(path), "page": pi + 1, "engines": engines, "errors": errors})
        if args.keep_text:
            res["runs_detail"] = parses
        results.append(res)
    return {"file": str(path), "pages": results}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", help="image/PDF files or folders")
    ap.add_argument("--lang", default="en", help="comma-separated ISO 639-1 codes, main script first (e.g. ar,en)")
    ap.add_argument("--engine", default="auto", help="auto, or comma list of rapidocr,paddle,tesseract,easyocr")
    ap.add_argument("--currency", help="ISO code to resolve $, ¥ or kr")
    ap.add_argument("--date-order", choices=["DMY", "MDY"], help="day/month order for dates like 04/05/2026; "
                    "without it such dates are assumed DMY and sent to review")
    ap.add_argument("--decimal-sep", choices=[".", ","], help="locale decimal separator, for 1.234 style ambiguity")
    ap.add_argument("--min-conf", type=float, default=0.85)
    ap.add_argument("--no-variants", action="store_true", help="only the original image (faster, less accurate)")
    ap.add_argument("--keep-text", action="store_true", help="include raw OCR lines (may contain personal data)")
    ap.add_argument("--out", help="folder for one JSON per input; default prints to stdout")
    args = ap.parse_args()
    files = []
    for p in map(Path, args.inputs):
        files += sorted(f for f in p.rglob("*") if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp", ".pdf"}) if p.is_dir() else [p]
    for f in files:
        res = process(f, args)
        if args.out:
            Path(args.out).mkdir(parents=True, exist_ok=True)
            (Path(args.out) / f"{f.stem}.json").write_text(json.dumps(res, ensure_ascii=False, indent=2))
            print(f"{f}: " + ", ".join(p.get("status", "?") for p in res["pages"]))
        else:
            print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
