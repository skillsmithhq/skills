---
name: receipt-ocr
description: "Extract merchant, address and postal code, country, date, currency code and symbol, subtotal, tax, tip, discount, total, line items, tax IDs and payment method from receipt images or PDFs in any language, plus payment and e-invoice QR codes, using only free, local open-source OCR engines and deterministic rules: no LLM, no paid API, no data leaves the machine. Several engines and image variants vote on each field, and a field is auto-accepted only when every run agrees and the arithmetic checks out; everything else goes to review. Use when asked to read, digitise or extract data from receipts or bills."
---

# receipt-ocr

Free, local receipt extraction. OCR engines read the text, a deterministic parser (`scripts/receipt_parse.py`, Python standard library only) turns the text into fields, and a gate decides what is safe to accept without a human.

## How accuracy is achieved (and what to promise)

- **Several readings.** Every installed engine reads three versions of the image (original, contrast-enhanced, binarised after deskew). Each reading is parsed separately.
- **Agreement.** A date or currency is accepted only if the readings that found it all agree and at least half of all readings (minimum two) found it.
- **Arithmetic.** A total is accepted when at least two readings each reconcile it independently and agree on it, and no reconciling reading gives a different total. Reconciling means line items add up to the subtotal, and subtotal plus tax, tip and rounding, minus discount, equals the total. VAT-inclusive receipts are handled.
- **QR codes.** Many receipts print a payment QR (EMVCo: PayNow, DuitNow, PromptPay, QRIS, VietQR; India UPI) or a tax QR (Saudi ZATCA, Portugal AT). `scripts/receipt_qr.py` decodes these with OpenCV and validates their structure and checksum. A QR amount equal to an OCR reading confirms the total; a different amount sends it to review. A QR currency or country code also confirms or resolves the currency. India GST e-invoice and Malaysia MyInvois QRs are decoded for information only (signatures are not verified), and URLs in QR codes are never fetched.
- **Sanity rules.** Look-alike letters touching a date (l, O, S, B), mixed zero-padding, ambiguous day/month order, unreadable total lines, and totals printed above the tax lines all send a field to review.
- **Never claim a fixed accuracy for every receipt.** No OCR system, cloud or local, can promise 99.99% on faded, crumpled or handwritten receipts. What this skill can deliver is very high precision on the fields it auto-accepts, with the rest sent to review. Measure it on the user's own labelled receipts with `scripts/receipt_eval.py` before relying on it. To show 99.99% at 95% confidence with zero errors needs about 30,000 checked fields.

## Instructions

1. **Check the setup.** The scripts need Python 3.9 or later. Find which engines are installed (`python3 scripts/receipt_ocr.py --help` reports when none is). If none is, explain the options and ask before installing anything:
   - RapidOCR (`pip install rapidocr_onnxruntime`): PaddleOCR's recognition models running on ONNX Runtime, about 300 MB with its dependencies. This is the best choice when disk space is limited.
   - PaddleOCR (`pip install paddlepaddle paddleocr`): the full framework, with more language models. It needs a few GB of disk space.
   - Tesseract (system package plus language packs, then `pip install pytesseract`): small, covers 100+ languages, best on clean scans.
   - EasyOCR (`pip install easyocr`): covers 80+ languages, and needs PyTorch.
   - Optional: `opencv-python-headless` for the image variants (strongly recommended), and `pymupdf` for PDFs.
   Two engines give a better cross-check than one. With a single engine, the image variants provide the cross-check. All of these tools are free and open source, and run offline after their models download.
2. **Ask for, or infer from the receipts:** the languages (main script first, for example `ar,en`); the country (`--country IN`) or currency (`--currency CAD`) when receipts don't show it; and the date order (`DMY` or `MDY`) for numeric dates. Without the date order, ambiguous dates go to review.
3. **Run** `python3 scripts/receipt_ocr.py <files or folders> --lang <codes> [--country XX] [--currency XXX] [--date-order DMY] --out results/`. It writes one JSON per file. Each field has a `status` (`accepted` or `review`), its value, the agreement count, the checks passed, the reasons for review, and the line it came from. The receipt-level `status` is `accepted` only when date, currency and total are all accepted.
4. **Report:** how many receipts were fully accepted, the fields sent to review and why (grouped by reason), and any errors per engine. Never present review-status values as confirmed.
5. **Measure accuracy before automating.** Have the user hand-check a sample and write `labels/<file stem>.json` (for example `{"date": "2026-03-14", "currency": "INR", "total": "1180.00"}`). Then run `python3 scripts/receipt_eval.py --pred results/ --truth labels/`. Report coverage, accepted precision and the 95% lower bound for each field. Raise `--min-conf` or add an engine if precision is too low.
6. **For regressions,** run `python3 scripts/receipt_bench.py` (synthetic receipts in eight regional formats, with simulated OCR errors) and `python3 -m unittest test_receipt_parse.py` from `scripts/` after any change to the parser.

## HTTP API

`scripts/receipt_api.py` serves the same pipeline over local HTTP, using only the standard library:

```
python3 scripts/receipt_api.py --port 8080 --api-key KEY --currency EUR      # or set RECEIPT_API_KEY
curl -H "Authorization: Bearer KEY" -H "Content-Type: image/jpeg" --data-binary @r.jpg "http://127.0.0.1:8080/v1/receipts?date_order=DMY"
curl -H "Authorization: Bearer KEY" -F file=@r.png http://127.0.0.1:8080/v1/receipts
```

- `POST /v1/receipts` takes a raw image or PDF, a multipart `file` field, or JSON `{"image_base64": ...}`. Options: lang, currency, country, date_order, decimal_sep, engine, min_conf, no_variants, include_text.
- It returns `status` (accepted, review or error), `pages`, `engines` and `processing_ms`. Treat values marked `review` as unconfirmed.
- `GET /healthz` lists the installed engines and returns 503 if there are none.
- The defaults keep it safe: it binds to 127.0.0.1, has a 15 MB limit (`--max-mb`), runs one OCR job at a time, and stores each upload in a temporary file readable only by its owner (mode 0600), deleted after processing. Logs never contain receipt data.
- Before exposing it beyond localhost, set an API key and put it behind HTTPS (a reverse proxy). Ask the user before doing that.
- Tests: `python3 -m unittest test_receipt_api` (from `scripts/`).

## What it handles

- **Currency, as an ISO 4217 code plus the symbol actually printed.** The order of evidence is: an ISO code next to an amount; a prefixed dollar or peso sign (US$, CA$, A$, NZ$, S$, HK$, NT$, MX$, R$, AR$, CLP$, COL$, RD$, J$, TT$, EC$, $U and others); an unambiguous symbol; and then, for symbols shared by several countries (`$` in more than 30 currencies, `¥`, `kr`, `Rs`, `C$`, `B$`), the country found on the receipt, a QR code, or the `--currency` hint. A bare `$` is never assumed to be USD: with nothing to resolve it, the receipt goes to review.
- **Address, postal code and country** (`scripts/receipt_address.py`): the address block, the postal code and the region (state or province), for India, Singapore, Malaysia, Thailand, Indonesia, Vietnam, Canada, the US, the UK and major EU formats. A country is assigned only with evidence: a country, state or city name, a postal-code label, a phone prefix, or a tax-ID type. Digits alone are never enough. The country also resolves an ambiguous currency symbol, for example `$` with a Canadian postcode is CAD.
- Digits in any Unicode script (Arabic-Indic, Persian, Devanagari, Bengali, Thai, full-width and others). Grouping and decimal styles: 1,234.56, 1.234,56, 1 234,56, 1'234.56, and Indian 1,23,456.78. Zero-decimal currencies (JPY, KRW, VND and others) and three-decimal currencies (KWD, BHD, OMR and others).
- Total, subtotal, tax, tip, discount, rounding and change keywords in about 40 languages. Indian CGST/SGST/IGST with GSTIN checksum, Canadian GST/HST/PST and TPS/TVQ, EU VAT lines, Malaysian SST and rounding to 5 sen, Indonesian PPN and PB1, Thai and Vietnamese VAT.
- Dates in ISO, D/M/Y, M/D/Y and dotted formats, with month names; CJK year-month-day; the Thai Buddhist era and the Japanese Reiwa era (converted); Solar Hijri or Hijri years (flagged, not converted).
- Right-to-left scripts (word order is reversed when the main language is Arabic, Persian, Hebrew or Urdu).
- Card numbers are masked to the last four digits before parsing. Raw OCR text is left out of the output unless `--keep-text` is passed.

## Measured results (2026-11-03)

**Real photos, free local OCR.** RapidOCR and Tesseract each read three image variants, with no LLM and no API. Results on public receipt datasets:

| Dataset | Field | Read correctly | Auto-accepted | Accepted and correct |
|---|---|---|---|---|
| SROIE 2019 test (353 Malaysian receipts) | total | 88.7% | 94 | 94/94 |
| SROIE 2019 test | date | 89.0% | 197 | 197/197 |
| CORD v2 validation and test (196 Indonesian receipts) | total | 89.9% | 84 | 84/84 |

Every value the gate accepted was correct. The cost is coverage: only 12% of SROIE receipts had all critical fields auto-accepted. Those scans are old and low resolution, and the rest went to review. CORD receipts print no date, so none of them can be fully accepted. With zero errors in about 375 accepted values, the 95% upper bound on the error rate is roughly 0.8%. That supports high precision, not 99.99%.

**Parser only**, using the OCR text supplied with CORD (193 receipts): the total was read correctly for 97.9%, and all 118 accepted totals were correct.

**Synthetic** (`receipt_bench.py`, 1,000 receipts per region for India, Singapore, Thailand, Malaysia, Bali, Canada, Europe and Vietnam): clean text parsed 100% correctly. With simulated OCR errors of 1–5% per character, accepted fields stayed 99.98–100% correct.

Measure on the user's own receipts with `receipt_eval.py` before relying on any of this.

## Constraints

- Receipts contain personal data (names, card digits, addresses, loyalty IDs). Process them locally, keep outputs out of version control, and delete raw OCR text when it's no longer needed.
- Merchant names come from a top-of-receipt heuristic and always go to review.
- Handwritten receipts, very faded thermal paper and heavy creases need human review whatever the engine.
- Only process receipts the user has the right to process.
- Public receipt datasets have their own licences (for example CORD is CC BY 4.0; SROIE is for research use). Check the licence before downloading one, and don't redistribute the data.

## Examples

### Example 1

Input: "extract totals from these 300 Bangkok restaurant receipts into a spreadsheet"

Output: Run with `--lang th,en --currency THB --date-order DMY` using PaddleOCR and Tesseract. 241 receipts were fully accepted. 59 went to review: 31 because the runs disagreed on the total, 18 because a date was unreadable, and 10 because the total didn't reconcile, mostly torn receipts. Buddhist-era years were converted. The CSV has a status column, and the 59 review rows are highlighted for a person to check.
