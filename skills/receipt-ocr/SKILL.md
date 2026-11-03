---
name: receipt-ocr
description: "Extract merchant, date, currency, subtotal, tax, tip, discount, total, line items, tax IDs and payment method from receipt images or PDFs in any language, using only free, local open-source OCR engines and deterministic rules: no LLM, no paid API, no data leaves the machine. Several engines and image variants vote on each field, and a field is auto-accepted only when every run agrees and the arithmetic checks out; everything else goes to review. Use when asked to read, digitise or extract data from receipts or bills."
---

# receipt-ocr

Free, local receipt extraction. OCR engines read the text, a deterministic parser (`scripts/receipt_parse.py`, Python standard library only) turns the text into fields, and a gate decides what is safe to accept without a human.

## How accuracy is achieved (and what to promise)

- **Several readings.** Every installed engine reads three versions of the image (original, contrast-enhanced, binarised after deskew). Each reading is parsed separately.
- **Agreement.** A field is accepted only if every reading produced the same value. One disagreeing or missing reading sends it to review.
- **Arithmetic.** The total is accepted only if it reconciles in every reading: line items to subtotal, and subtotal plus tax, tip, rounding, minus discount, to total. VAT-inclusive receipts are handled.
- **Sanity rules.** Look-alike letters touching a date (l, O, S, B), mixed zero-padding, ambiguous day/month order, unreadable total lines, and totals printed above the tax lines all send a field to review.
- **Never claim a fixed accuracy for every receipt.** No OCR system, cloud or local, can promise 99.99% on faded, crumpled or handwritten receipts. What this skill can deliver is very high precision on the fields it auto-accepts, with the rest sent to review. Measure it on the user's own labelled receipts with `scripts/receipt_eval.py` before relying on it. To show 99.99% at 95% confidence with zero errors needs about 30,000 checked fields.

## Instructions

1. **Check the setup.** The scripts need Python 3.9 or later. Find which engines are installed (`python3 scripts/receipt_ocr.py --help` reports when none is). If none is, explain the options and ask before installing anything:
   - PaddleOCR (`pip install paddlepaddle paddleocr`): the strongest default, especially for Chinese, Japanese and Korean, and for photographed receipts. It needs a few GB of disk space.
   - Tesseract (system package plus language packs, then `pip install pytesseract`): small, covers 100+ languages, best on clean scans.
   - EasyOCR (`pip install easyocr`): covers 80+ languages, and needs PyTorch.
   - Optional: `opencv-python-headless` for the image variants (strongly recommended), and `pymupdf` for PDFs.
   Two engines give a better cross-check than one. With a single engine, the image variants provide the cross-check. All of these tools are free and open source, and run offline after their models download.
2. **Ask for, or infer from the receipts:** the languages (main script first, for example `ar,en`); the currency if the symbol is ambiguous (`$`, `¥`, `kr`, `Rs`); and the date order (`DMY` or `MDY`) for numeric dates. If the date order is not given, ambiguous dates go to review.
3. **Run** `python3 scripts/receipt_ocr.py <files or folders> --lang <codes> [--currency XXX] [--date-order DMY] --out results/`. It writes one JSON per file. Each field has a `status` (`accepted` or `review`), its value, the agreement count, the checks passed, the reasons for review, and the line it came from. The receipt-level `status` is `accepted` only when date, currency and total are all accepted.
4. **Report:** how many receipts were fully accepted, the fields sent to review and why (grouped by reason), and any errors per engine. Never present review-status values as confirmed.
5. **Measure accuracy before automating.** Have the user hand-check a sample and write `labels/<file stem>.json` (for example `{"date": "2026-03-14", "currency": "INR", "total": "1180.00"}`). Then run `python3 scripts/receipt_eval.py --pred results/ --truth labels/`. Report coverage, accepted precision and the 95% lower bound for each field. Raise `--min-conf` or add an engine if precision is too low.
6. **For regressions,** run `python3 scripts/receipt_bench.py` (synthetic receipts in eight regional formats, with simulated OCR errors) and `python3 -m unittest test_receipt_parse.py` from `scripts/` after any change to the parser.

## What it handles

- Digits in any Unicode script (Arabic-Indic, Persian, Devanagari, Bengali, Thai, full-width and others). Grouping and decimal styles: 1,234.56, 1.234,56, 1 234,56, 1'234.56, and Indian 1,23,456.78. Zero-decimal currencies (JPY, KRW, VND and others) and three-decimal currencies (KWD, BHD, OMR and others).
- Total, subtotal, tax, tip, discount, rounding and change keywords in about 40 languages. Indian CGST/SGST/IGST with GSTIN checksum, Canadian GST/HST/PST and TPS/TVQ, EU VAT lines, Malaysian SST and rounding to 5 sen, Indonesian PPN and PB1, Thai and Vietnamese VAT.
- Dates in ISO, D/M/Y, M/D/Y and dotted formats, with month names; CJK year-month-day; the Thai Buddhist era and the Japanese Reiwa era (converted); Solar Hijri or Hijri years (flagged, not converted).
- Right-to-left scripts (word order is reversed when the main language is Arabic, Persian, Hebrew or Urdu).
- Card numbers are masked to the last four digits before parsing. Raw OCR text is left out of the output unless `--keep-text` is passed.

## Measured results (2026-11-03)

These test the parser and the gate, not the OCR engines, because they use OCR text that ships with public datasets:

- **CORD v2** (real Indonesian receipts, CC BY 4.0), validation and test splits, 193 receipts with a labelled total: the total was correct for 97.9% of them. 60.6% were auto-accepted, and all 117 accepted totals were correct.
- **Synthetic** (`receipt_bench.py`, 1,000 receipts per region for India, Singapore, Thailand, Malaysia, Bali, Canada, Europe and Vietnam): clean text parsed 100% correctly. With simulated OCR errors of 1–5% per character, accepted critical fields were 99.98–100% correct, and coverage fell as noise rose.

Real OCR errors are not random, and these figures do not replace a measurement on the user's own receipts with `receipt_eval.py`.

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
