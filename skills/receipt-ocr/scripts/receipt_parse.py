"""Deterministic receipt parser: OCR lines in, structured fields out. Standard library only, no LLM.

Handles any Unicode decimal digits (Arabic-Indic, Persian, Devanagari, Thai, full-width, ...), the common
decimal/grouping conventions (1,234.56 / 1.234,56 / 1 234,56 / 1'234.56 / 1,23,456.78), zero- and
three-decimal currencies, multilingual total/tax/subtotal keywords, and several calendar formats.
Every field carries the evidence line and a list of checks, so callers can auto-accept only verified values.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field, asdict
from datetime import date
from decimal import Decimal, InvalidOperation

# ---------------------------------------------------------------- normalisation

_EXTRA_MAP = {
    "٫": ".",  # Arabic decimal separator
    "٬": ",",  # Arabic thousands separator
    "．": ".", "，": ",", "：": ":", "／": "/", "－": "-",
    "−": "-", "–": "-", "—": "-",
    " ": " ", " ": " ", " ": " ", " ": " ",
    "’": "'", "ʼ": "'",
}


def normalise(text: str) -> str:
    """NFKC, then map every Unicode decimal digit to ASCII and unify separators and dashes."""
    text = unicodedata.normalize("NFKC", text)
    out = []
    for ch in text:
        if ch in _EXTRA_MAP:
            out.append(_EXTRA_MAP[ch])
            continue
        d = unicodedata.decimal(ch, None)
        out.append(str(d) if d is not None and not ch.isascii() else ch)
    return "".join(out)


# ---------------------------------------------------------------- currencies

ZERO_DECIMAL = {"JPY", "KRW", "VND", "CLP", "ISK", "UGX", "PYG", "XAF", "XOF", "RWF", "KMF", "GNF", "VUV", "DJF", "BIF"}
THREE_DECIMAL = {"BHD", "KWD", "OMR", "JOD", "TND", "LYD", "IQD"}

# Dollar and peso signs with a country prefix (US$, CA$, NZ$, R$ ...). Matched as whole tokens by _DOLLAR_RE, so that
# "AR$" is never read as Brazil's "R$". Ambiguous prefixes: "C$" is also the Nicaraguan córdoba, "B$" is Bahamas or
# Brunei; they resolve to the listed default only when no country evidence says otherwise.
DOLLAR_PREFIX = {
    "US": "USD", "U": "USD", "CA": "CAD", "C": "CAD", "AU": "AUD", "A": "AUD", "NZ": "NZD", "S": "SGD", "SG": "SGD",
    "HK": "HKD", "NT": "TWD", "MX": "MXN", "MEX": "MXN", "R": "BRL", "AR": "ARS", "CL": "CLP", "CLP": "CLP",
    "COL": "COP", "CO": "COP", "RD": "DOP", "J": "JMD", "JA": "JMD", "TT": "TTD", "EC": "XCD", "BZ": "BZD",
    "BDS": "BBD", "FJ": "FJD", "N": "NAD", "L": "LRD", "SI": "SBD", "CI": "KYD", "GY": "GYD", "SR": "SRD",
    "BN": "BND", "BSD": "BSD", "Z": "ZWL",
}
DOLLAR_PREFIX_AMBIGUOUS = {"C": ["CAD", "NIO"], "B": ["BSD", "BND"]}
_DOLLAR_RE = re.compile(r"(?<![A-Za-z])([A-Z][A-Za-z]{0,2})\$|\$(U)(?![A-Za-z])")

SYMBOLS = [  # longest first; dollar-prefixed forms are handled by DOLLAR_PREFIX
    ("VNĐ", "VND"), ("zł", "PLN"), ("Kč", "CZK"), ("Ft", "HUF"), ("lei", "RON"), ("₹", "INR"), ("€", "EUR"), ("£", "GBP"),
    ("₩", "KRW"), ("₫", "VND"), ("฿", "THB"), ("₱", "PHP"), ("₺", "TRY"), ("₽", "RUB"), ("₪", "ILS"),
    ("₦", "NGN"), ("₴", "UAH"), ("₸", "KZT"), ("₲", "PYG"), ("₡", "CRC"), ("₵", "GHS"), ("৳", "BDT"),
    ("₨", "PKR"), ("﷼", "SAR"), ("د.إ", "AED"), ("ر.س", "SAR"), ("د.ك", "KWD"), ("Rp", "IDR"), ("RM", "MYR"),
]
DOLLAR_CURRENCIES = ["USD", "CAD", "AUD", "NZD", "SGD", "HKD", "TWD", "MXN", "ARS", "CLP", "COP", "UYU", "DOP", "BRL",
                     "JMD", "TTD", "XCD", "BSD", "BBD", "BZD", "BND", "FJD", "NAD", "LRD", "SBD", "KYD", "GYD", "SRD",
                     "CUP", "NIO", "TOP", "WST", "KID"]
AMBIGUOUS_SYMBOLS = {"$": DOLLAR_CURRENCIES, "¥": ["JPY", "CNY"], "kr": ["SEK", "NOK", "DKK", "ISK"],
                     "Rs": ["INR", "PKR", "LKR", "NPR"]}
ISO_CODES = {
    "USD", "EUR", "GBP", "INR", "JPY", "CNY", "RMB", "KRW", "AUD", "CAD", "CHF", "SEK", "NOK", "DKK", "PLN", "CZK", "HUF",
    "RON", "BGN", "TRY", "RUB", "UAH", "ILS", "AED", "SAR", "QAR", "KWD", "BHD", "OMR", "JOD", "EGP", "MAD", "TND", "ZAR",
    "NGN", "KES", "GHS", "BRL", "MXN", "ARS", "CLP", "COP", "PEN", "SGD", "MYR", "IDR", "THB", "VND", "PHP", "HKD", "TWD",
    "NZD", "PKR", "BDT", "LKR", "NPR", "ISK", "KZT", "LYD", "IQD",
}


# Usual printed symbol per ISO code (for output; detection uses SYMBOLS above).
CODE_SYMBOL = {"INR": "₹", "SGD": "S$", "THB": "฿", "MYR": "RM", "IDR": "Rp", "CAD": "$", "VND": "₫", "USD": "$",
               "EUR": "€", "GBP": "£", "JPY": "¥", "CNY": "¥", "KRW": "₩", "AUD": "$", "NZD": "$", "HKD": "$",
               "PHP": "₱", "TRY": "₺", "RUB": "₽", "ILS": "₪", "NGN": "₦", "UAH": "₴", "PLN": "zł", "CZK": "Kč",
               "HUF": "Ft", "CHF": "CHF", "SEK": "kr", "NOK": "kr", "DKK": "kr", "BRL": "R$", "MXN": "$", "ZAR": "R",
               "AED": "د.إ", "SAR": "﷼", "PKR": "Rs", "LKR": "Rs", "NPR": "Rs", "BDT": "৳", "KZT": "₸"}


def currency_symbol(lines: list[str], code: str | None) -> str | None:
    """The symbol actually printed for `code` if one appears, else its usual symbol."""
    joined = "\n".join(lines)
    for sym, c in SYMBOLS:
        if c == code and sym in joined:
            return sym
    for sym, options in AMBIGUOUS_SYMBOLS.items():
        if code in options and re.search(rf"(?<![A-Za-z]){re.escape(sym)}(?![A-Za-z])", joined):
            return sym
    return CODE_SYMBOL.get(code) if code else None


def detect_currency(lines: list[str], hint: str | None = None, country_currency: str | None = None) -> tuple[str | None, str]:
    """Return (ISO code or None, evidence). Order: ISO code next to an amount, prefixed dollar sign (US$, CA$ ...),
    unambiguous symbol, then an ambiguous symbol ($, ¥, kr, Rs) resolved by country evidence or the hint.
    An ambiguous symbol with nothing to resolve it returns None, so the receipt goes to review."""
    joined = "\n".join(lines)
    # an ISO code counts only next to an amount: "SDN BHD" is a Malaysian company suffix, not Bahraini dinars
    codes = [a or b for a, b in re.findall(r"(?<![A-Za-z])([A-Z]{3})\s?-?\d|\d[\d.,]*\s?([A-Z]{3})(?![A-Za-z])", joined)]
    for c in codes:
        if c in ISO_CODES:
            c = "CNY" if c == "RMB" else c
            if hint and hint.upper() != c:
                return c, f"code {c} conflicts with hint {hint.upper()}"
            return c, f"code {c}"
    for m in _DOLLAR_RE.finditer(joined):
        prefix = m.group(1) or m.group(2)
        key = prefix.upper()
        if m.group(2):
            return "UYU", "symbol $U"
        if key in DOLLAR_PREFIX_AMBIGUOUS:
            opts = DOLLAR_PREFIX_AMBIGUOUS[key]
            pick = next((c for c in (country_currency, hint and hint.upper()) if c in opts), None)
            if pick:
                return pick, f"symbol {prefix}$ + {'country' if pick == country_currency else 'hint'}"
            return None, f"ambiguous symbol {prefix}$ ({' or '.join(opts)}): pass --currency"
        if key in DOLLAR_PREFIX:
            return DOLLAR_PREFIX[key], f"symbol {prefix}$"
    for sym, code in SYMBOLS:
        if sym in joined:
            return code, f"symbol {sym}"
    if re.search(r"\d\s?(?:đ|VNĐ)(?![a-zà-ỹ])", joined):  # Vietnamese đồng written after the amount
        return "VND", "symbol đ"
    for sym, options in AMBIGUOUS_SYMBOLS.items():
        if re.search(rf"(?<![A-Za-z]){re.escape(sym)}(?![A-Za-z])", joined):
            if country_currency in options:
                return country_currency, f"symbol {sym} + country on receipt"
            if hint and hint.upper() in options:
                return hint.upper(), f"symbol {sym} + hint"
            if sym == "Rs" and re.search(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b", joined.upper()):
                return "INR", "symbol Rs + Indian GSTIN on receipt"
            return None, f"ambiguous symbol {sym}: pass --currency"
    if hint:
        return hint.upper(), "hint only"
    return None, "no currency found"


# Officially two decimals, but receipts often print whole units ("Rp 58.000"), so amounts need not show decimals.
LOOSE_DECIMALS = {"IDR", "HUF", "COP", "ARS", "PYG", "LKR", "PKR", "NGN", "KES", "UZS"}


def decimals_for(currency: str | None) -> int | None:
    if currency in ZERO_DECIMAL:
        return 0
    if currency in THREE_DECIMAL:
        return 3
    return 2 if currency else None


# ---------------------------------------------------------------- amounts

_AMOUNT_RE = re.compile(
    r"(?<![\w.,])(-?)\s?(\d{1,3}(?:[ .,']\d{2,3})+(?:[.,]\d{1,3})?|\d+(?:[.,]\d{1,3})?)(?![\w%]|[.,]\d)"
)


def parse_amount(token: str, decimals: int | None = None, decimal_sep: str | None = None) -> Decimal | None:
    """Parse one numeric token. `decimals` is the currency's minor-unit count; `decimal_sep` a locale hint."""
    t = token.strip().replace(" ", "").replace("'", "")
    neg = t.startswith("-")
    t = t.lstrip("-")
    if not t or not re.fullmatch(r"[\d.,]+", t):
        return None
    seps = [c for c in t if c in ".,"]
    if not seps:
        value = t
    elif len(set(seps)) == 2:  # both used: the last one is the decimal separator
        dec = t[max(t.rfind("."), t.rfind(","))]
        grp = "," if dec == "." else "."
        value = t.replace(grp, "").replace(dec, ".")
    else:
        sep = seps[0]
        tail = t.rsplit(sep, 1)[1]
        if decimals == 0:
            value = t.replace(sep, "")
        elif len(seps) > 1:  # repeated single separator is grouping (1.234.567 or 1,23,456)
            value = t.replace(sep, "")
        elif len(tail) == 3 and decimals == 3:
            value = t.replace(sep, ".")
        elif len(tail) == 3:  # 1,234 or 1.234: grouping unless the locale says otherwise
            value = t.replace(sep, ".") if decimal_sep == sep and decimals not in (None, 2) else t.replace(sep, "")
        else:
            value = t.replace(sep, ".")
    try:
        d = Decimal(value)
    except InvalidOperation:
        return None
    return -d if neg else d


_PREFIXES = sorted(ISO_CODES | {"RM", "Rp", "Rs", "VNĐ"} | {p + "$" for p in DOLLAR_PREFIX} | {"B$", "$"}, key=len, reverse=True)
_GLUED = re.compile(r"(?<![A-Za-z])(" + "|".join(re.escape(p) for p in _PREFIXES) + r")\.?(?=-?\d)")
_ID_LINE = re.compile(r"(gstin|gst\s?reg|reg(istration)?\s?no|tax\s?id|tin\b|vat\s?(no|reg|id)|mst\b|npwp|abn\b|sst\s?no|"
                      r"gst/hst|#\s?\d{6,}|เลขประจำตัว|uen\b)", re.I)


def amounts_in(line: str, decimals: int | None, decimal_sep: str | None = None, money_only: bool = False) -> list[Decimal]:
    """Amounts on a line. Registration-number lines, masked card numbers and long bare digit runs are not amounts."""
    if _ID_LINE.search(line) or re.search(r"[x*•]{2,}[\s-]?\d", line, re.I):
        return []
    line = _GLUED.sub(r"\1 ", line)
    out = []
    for m in _AMOUNT_RE.finditer(line):
        tok = m.group(2)
        if re.fullmatch(r"\d{8,}", tok):
            continue
        if money_only and not re.search(r"[.,]\d{2}$", tok):
            continue  # a 2-decimal currency: invoice numbers, phone numbers and quantities are not amounts
        if " " in tok and not re.fullmatch(r"\d{1,3}( \d{3})+([.,]\d{1,2})?", tok):
            for piece in tok.split(" "):  # "1 41,000" is a quantity and a price, not 141,000
                v = parse_amount(piece, decimals, decimal_sep)
                if v is not None:
                    out.append(v)
            continue
        v = parse_amount(m.group(1) + m.group(2), decimals, decimal_sep)
        if v is not None:
            out.append(v)
    return out


# ---------------------------------------------------------------- keywords (lower-cased, normalised)

KW = {
    "subtotal": ["subtotal", "sub total", "sub-total", "subttl", "sub ttl", "zwischensumme", "sous-total", "sous total", "subtotale",
                 "subtotaal", "suma częściowa", "mezisoučet", "részösszeg", "промежуточный итог", "ara toplam",
                 "小计", "小計", "소계", "المجموع الفرعي", "סכום ביניים", "ยอดรวมย่อย", "tạm tính", "thành tiền", "total exclude", "total excluding", "total excl", "excluding gst", "excluded gst",
                 "exclude gst", "excl gst", "excl. gst", "before tax", "before gst", "sebelum cukai", "cộng tiền hàng", "subjumlah", "รวมเงิน", "รวมย่อย"],
    "total": ["grand total", "grandtotal", "net amount", "due", "total inclusive", "total incl", "inc. gst", "inc gst", "net total", "nett total", "total due", "amount due", "balance due", "total amount", "amount payable", "to pay",
              "total", "gesamtbetrag", "gesamt", "summe", "zu zahlen", "endbetrag", "total ttc", "net à payer",
              "montant", "à payer", "totale", "importe", "total a pagar", "a pagar", "totaal", "te betalen",
              "razem", "do zapłaty", "suma", "celkem", "k úhradě", "összesen", "fizetendő", "итого", "всего",
              "к оплате", "toplam", "genel toplam", "totalt", "att betala", "i alt", "yhteensä", "σύνολο",
              "合计", "合計", "总计", "總計", "应付", "應付", "お会計", "ご請求額", "합계", "총액", "결제금액", "받을금액",
              "कुल", "योग", "कुल राशि", "মোট", "மொத்தம்", "మొత్తం", "المجموع", "الإجمالي", "الاجمالي", "المبلغ",
              "סה\"כ", "סה״כ", "לתשלום", "รวม", "ยอดรวม", "ยอดสุทธิ", "tổng cộng", "tổng tiền", "thanh toán",
              "jumlah", "jumlah bayar", "kabuuan", "jumla"],
    "tax": ["tax", "vat", "gst", "cgst", "sgst", "igst", "utgst", "cess", "hst", "pst", "qst", "sales tax", "mwst",
            "ust", "umsatzsteuer", "tva", "iva", "btw", "moms", "mva", "alv", "dph", "áfa", "ptu", "ндс", "kdv",
            "税", "税额", "消費税", "內含稅", "부가세", "세액", "ضريبة", "القيمة المضافة", "מע\"מ", "מע״מ", "ppn",
            "pajak", "pb1", "sst", "service tax", "tps", "tvq", "tvh", "ภาษี", "thuế", "gtgt", "jct"],
    "rounding": ["rounding adj", "rounding adjustment", "rounding", "round amt", "round amount", "round off", "round-off", "pembundaran",
                 "pelarasan", "làm tròn", "arrondi", "redondeo", "rundung"],
    "tip": ["tip", "gratuity", "service charge", "service", "trinkgeld", "bedienung", "pourboire", "propina",
            "mancia", "servizio", "服务费", "服務費", "サービス料", "봉사료", "बख्शीश", "إكرامية"],
    "discount": ["discount", "rabatt", "remise", "descuento", "sconto", "korting", "rabat", "sleva", "скидка",
                 "indirim", "折扣", "优惠", "割引", "値引", "할인", "छूट", "خصم", "הנחה", "ส่วนลด", "giảm giá", "diskon"],
    "not_total": ["change", "changed", "kembali", "cash", "tendered", "paid", "received", "rückgeld", "wechselgeld", "gegeben", "bar",
                  "rendu", "monnaie", "espèces", "cambio", "vuelto", "efectivo", "resto", "contanti", "wisselgeld",
                  "reszta", "zdáno", "сдача", "наличные", "para üstü", "nakit", "växel", "找零", "找赎", "现金",
                  "現金", "お釣り", "お預り", "거스름돈", "받은금액", "현금", "बाकी", "نقدا", "الباقي", "עודף", "เงินทอน",
                  "เงินสด", "tiền thừa", "kembalian", "tunai", "points", "savings", "you saved"],
    "item_count": ["items", "item", "item count", "qty", "quantity", "pcs", "jumlah item", "jml item", "anzahl", "artikel",
                   "articles", "件", "点", "개"],
}


# Lines that name the amount actually payable win over other "total" lines (gross totals before rounding,
# "total supplies" on adjustment notes, totals before a discount).
PAYABLE = ["total payable", "amount payable", "net payable", "payable", "amount due", "total due", "balance due",
           "grand total", "grandtotal", "net amount", "to pay", "jumlah bayaran",
           "jumlah perlu dibayar", "à payer", "net à payer", "zu zahlen", "a pagar", "te betalen", "do zapłaty",
           "k úhradě", "к оплате", "应付", "應付", "ご請求額", "결제금액", "ยอดสุทธิ", "tổng thanh toán"]


def _is_payable(line_lc: str) -> bool:
    return any((re.search(rf"(?<![a-z]){re.escape(k)}(?![a-z])", line_lc) if k.isascii() else k in line_lc) for k in PAYABLE)


def choose_total(totals: list, lines_n: list, roundings: list | None = None) -> tuple | None:
    """Pick the amount actually paid: the first total after a rounding line, else the last payable-labelled line
    ("Total Payable", "Grand Total", "Amount Due"), else the largest total."""
    if not totals:
        return None
    if roundings:
        after = [c for c in totals if c[0] > roundings[-1][0]]
        if after:
            return after[0]
    payable = [c for c in totals if _is_payable(lines_n[c[0]].lower())]
    if payable:
        return payable[-1]
    return max(totals, key=lambda c: (c[1], c[0]))


def has_kw(line_lc: str, kind: str) -> str | None:
    line_lc = re.sub(r"sub[\s_,.\-]*total", "subtotal", line_lc.replace("_", " "))
    for k in KW[kind]:
        if re.search(r"[A-Za-z]", k):
            if re.search(rf"(?<![a-z]){re.escape(k)}(?![a-z])", line_lc):
                return k
        elif k in line_lc:
            return k
    return None


# ---------------------------------------------------------------- dates and times

_MONTHS = {m: i + 1 for i, names in enumerate([
    "jan january januar janvier enero gennaio januari styczeń", "feb february februar février febrero febbraio februari luty",
    "mar march märz mars marzo maart marzec", "apr april avril abril aprile kwiecień",
    "may mai mayo maggio mei maj", "jun june juni juin junio giugno czerwiec",
    "jul july juli juillet julio luglio lipiec", "aug august août agosto augustus sierpień",
    "sep sept september septembre septiembre settembre wrzesień", "oct october oktober octobre octubre ottobre październik",
    "nov november novembre noviembre listopad", "dec december dezember décembre diciembre dicembre grudzień",
]) for m in names.split()}


def _valid(y: int, m: int, d: int) -> date | None:
    if not 1990 <= y <= 2100:  # receipts outside this range are almost always misreads
        return None
    try:
        return date(y, m, d)
    except ValueError:
        return None


def _year(y: int) -> tuple[int, str | None]:
    if y < 100:
        return 2000 + y, None
    if 2400 <= y <= 2700:  # Thai Buddhist era
        return y - 543, "buddhist era converted"
    if 1300 <= y <= 1500:  # likely Solar Hijri or Hijri: do not guess a conversion
        return y, "possible non-Gregorian year; check calendar"
    return y, None


def _suspect(line: str, m: re.Match) -> list[str]:
    """Signs that OCR may have damaged a numeric date: a look-alike letter touching it, or mixed zero-padding."""
    notes = []
    before = line[max(0, m.start() - 1):m.start()]
    after = line[m.end():m.end() + 1]
    if re.fullmatch(r"[lIOoSBZbg|]", before or "x") or re.fullmatch(r"[lIOoSBZbg|]", after or "x"):
        notes.append("suspect: look-alike letter touching the date")
    parts = [g for g in m.groups() if g and len(g) <= 2]
    if len(parts) >= 2 and len({len(g) for g in parts}) > 1 and any(g.startswith("0") for g in parts):
        notes.append("suspect: inconsistent zero-padding")
    return notes


def find_date(lines: list[str], order: str | None = None) -> tuple[str | None, str | None, list[str]]:
    """Return (ISO date, evidence line, notes). `order` (DMY or MDY) resolves ambiguous numeric dates; without it
    DMY is assumed and the date is marked ambiguous."""
    notes: list[str] = []
    for line in lines:
        lc = line.lower()
        m = re.search(r"令和\s?(\d{1,2})\s?年\s?(\d{1,2})\s?月\s?(\d{1,2})\s?日", line)
        if m and (dt := _valid(2018 + int(m.group(1)), int(m.group(2)), int(m.group(3)))):
            return dt.isoformat(), line, ["reiwa era converted"]
        m = re.search(r"(\d{2,4})\s?[年년]\s?(\d{1,2})\s?[月월]\s?(\d{1,2})\s?[日일]?", line)
        if m:
            y, n = _year(int(m.group(1)))
            if dt := _valid(y, int(m.group(2)), int(m.group(3))):
                return dt.isoformat(), line, [n] if n else []
        m = re.search(r"(?<!\d)(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})(?!\d)", line)
        if m:
            y, n = _year(int(m.group(1)))
            if dt := _valid(y, int(m.group(2)), int(m.group(3))):
                return dt.isoformat(), line, ([n] if n else []) + _suspect(line, m)
        m = re.search(r"(?<!\d)(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})(?!\d)", line)
        if m:
            a, b, yy = int(m.group(1)), int(m.group(2)), int(m.group(3))
            y, n = _year(yy)
            cands = []
            if (dt := _valid(y, b, a)):
                cands.append(("DMY", dt))
            if (dt := _valid(y, a, b)):
                cands.append(("MDY", dt))
            sus = _suspect(line, m)
            if len(cands) == 1 or (len(cands) == 2 and cands[0][1] == cands[1][1]):
                return cands[0][1].isoformat(), line, ([n] if n else []) + sus
            if len(cands) == 2:
                pick = next((dt for o, dt in cands if o == (order or "DMY")), cands[0][1])
                note = f"day/month order set by --date-order {order}" if order else "ambiguous day/month, assumed DMY"
                return pick.isoformat(), line, [note] + ([n] if n else []) + sus
        m = re.search(r"(\d{1,2})\.?\s+([a-zà-ž]{3,10})\.?,?\s+(\d{2,4})", lc) or None
        if m and m.group(2) in _MONTHS:
            y, n = _year(int(m.group(3)))
            if dt := _valid(y, _MONTHS[m.group(2)], int(m.group(1))):
                return dt.isoformat(), line, [n] if n else []
        m = re.search(r"([a-z]{3,10})\.?\s+(\d{1,2}),?\s+(\d{2,4})", lc)
        if m and m.group(1) in _MONTHS:
            y, n = _year(int(m.group(3)))
            if dt := _valid(y, _MONTHS[m.group(1)], int(m.group(2))):
                return dt.isoformat(), line, [n] if n else []
    return None, None, notes


def all_dates(lines: list[str], order: str | None) -> set[str]:
    found = set()
    for l in lines:
        d, _, _ = find_date([l], order)
        if d:
            found.add(d)
    return found


def find_time(lines: list[str]) -> str | None:
    for line in lines:
        m = re.search(r"(?<!\d)([01]?\d|2[0-3])[:h]([0-5]\d)(?::([0-5]\d))?\s?(am|pm|AM|PM)?(?!\d)", line)
        if m:
            h = int(m.group(1))
            if m.group(4):
                h = h % 12 + (12 if m.group(4).lower() == "pm" else 0)
            return f"{h:02d}:{m.group(2)}" + (f":{m.group(3)}" if m.group(3) else "")
    return None


# ---------------------------------------------------------------- identifiers and payment

def gstin_valid(g: str) -> bool:
    """India GSTIN checksum (mod 36)."""
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if not re.fullmatch(r"\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]", g):
        return False
    total = 0
    for i, c in enumerate(g[:14]):
        p = chars.index(c) * (2 if i % 2 else 1)
        total += p // 36 + p % 36
    return chars[(36 - total % 36) % 36] == g[14]


_TAX_ID_LABELS = r"(gstin|gst\s?no|vat\s?(?:no|reg|id|number)?|tin|abn|ust-?id(?:nr)?|steuer-?nr|siret|siren|rfc|cnpj|nif|cif|p\.?iva|partita iva|btw|kvk|nip|ico|dič|inn|инн|trn|vkn|npwp|统一社会信用代码|사업자등록번호|الرقم الضريبي)"


def find_tax_ids(lines: list[str]) -> list[dict]:
    found = []
    for line in lines:
        for g in re.findall(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][1-9A-Z]Z[0-9A-Z]\b", line.upper()):
            found.append({"type": "GSTIN", "value": g, "checksum_ok": gstin_valid(g)})
        m = re.search(_TAX_ID_LABELS + r"\s*[:#.]?\s*([A-Z0-9][A-Z0-9 ./-]{5,24})", line, re.I)
        if m and not any(f["value"] in line.upper() for f in found):
            found.append({"type": m.group(1).upper(), "value": m.group(2).strip(), "checksum_ok": None})
    return found


def find_payment(lines: list[str]) -> dict:
    joined = " ".join(lines).lower()
    method = None
    for name, keys in [("card", ["visa", "mastercard", "amex", "american express", "rupay", "maestro", "debit", "credit", "card",
                                 "karte", "carte", "tarjeta", "carta", "kaart", "karta", "卡", "카드", "บัตร", "بطاقة"]),
                       ("upi", ["upi"]), ("wallet", ["apple pay", "google pay", "paytm", "phonepe", "alipay", "wechat pay",
                                                     "支付宝", "微信"]),
                       ("cash", ["cash", "bar", "espèces", "efectivo", "contanti", "现金", "現金", "현금", "नकद", "نقدا"])]:
        if any(re.search(rf"(?<![a-z]){re.escape(k)}(?![a-z])", joined) if k.isascii() else k in joined for k in keys):
            method = name
            break
    last4 = None
    m = re.search(r"(?:[x*•#]{2,}[\s-]?)+(\d{4})\b", " ".join(lines), re.I)
    if m:
        last4 = m.group(1)
    return {"method": method, "card_last4": last4}


def mask_pan(text: str) -> str:
    """Mask anything that looks like a full card number, keeping the last four digits."""
    def _mask(m: re.Match) -> str:
        digits = re.sub(r"\D", "", m.group(0))
        return "**** **** **** " + digits[-4:] if 12 <= len(digits) <= 19 else m.group(0)
    return re.sub(r"(?<!\d)(?:\d[ -]?){12,19}(?!\d)", _mask, text)


# ---------------------------------------------------------------- receipt

@dataclass
class Field:
    value: object = None
    evidence: str | None = None
    confidence: float = 0.0
    checks: list[str] = field(default_factory=list)


@dataclass
class Receipt:
    merchant: Field = field(default_factory=Field)
    date: Field = field(default_factory=Field)
    time: Field = field(default_factory=Field)
    currency: Field = field(default_factory=Field)
    currency_symbol: str | None = None
    address: dict = field(default_factory=dict)
    subtotal: Field = field(default_factory=Field)
    tax: Field = field(default_factory=Field)
    tip: Field = field(default_factory=Field)
    discount: Field = field(default_factory=Field)
    total: Field = field(default_factory=Field)
    line_items: list[dict] = field(default_factory=list)
    tax_ids: list[dict] = field(default_factory=list)
    payment: dict = field(default_factory=dict)
    reconciliation: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        def conv(o):
            if isinstance(o, Decimal):
                return str(o)
            if isinstance(o, dict):
                return {k: conv(v) for k, v in o.items()}
            if isinstance(o, list):
                return [conv(v) for v in o]
            return o
        return conv(asdict(self))


def _line_conf(confs: list[float] | None, i: int) -> float:
    return confs[i] if confs and i < len(confs) else 0.9


def parse_receipt(lines: list[str], confs: list[float] | None = None, currency_hint: str | None = None,
                  date_order: str | None = None, decimal_sep: str | None = None, country_hint: str | None = None) -> Receipt:
    """Parse OCR lines (top to bottom) into a Receipt. `confs` are per-line OCR confidences (0-1)."""
    raw = [mask_pan(normalise(l)).strip() for l in lines]
    keep = [i for i, l in enumerate(raw) if l]
    lines_n = [raw[i] for i in keep]
    confs_n = [_line_conf(confs, i) for i in keep]
    r = Receipt()

    try:
        from receipt_address import find_address, currency_for_country
        r.address = find_address(lines_n, country_hint)
    except ImportError:  # running without the address module
        r.address, currency_for_country = {}, (lambda cc: None)
    country = r.address.get("country") or (country_hint.upper() if country_hint else None)
    cur, ev = detect_currency(lines_n, currency_hint, currency_for_country(country) if country else None)
    r.currency = Field(cur, ev, 0.5 if "conflicts" in ev else (0.99 if cur and ev != "hint only" else (0.9 if cur else 0.0)),
                       ["from the --currency hint, not printed on the receipt"] if ev == "hint only" else [])
    m_sym = re.match(r"symbol (\S+)", ev)
    r.currency_symbol = m_sym.group(1) if m_sym else currency_symbol(lines_n, cur)
    if cur is None:
        r.warnings.append(ev)
    dec = decimals_for(cur)
    money = dec == 2 and cur not in LOOSE_DECIMALS

    d, dline, dnotes = find_date(lines_n, date_order)
    if d:
        age = (date.today() - date.fromisoformat(d)).days
        if age > 3650 or age < -2:  # older than ten years or in the future: almost always a misread or a wrong date
            dnotes = dnotes + [f"suspect: date is {'in the future' if age < 0 else f'{age // 365} years old'}"]
    if d and len(dates := all_dates(lines_n, date_order)) > 1:
        dnotes = dnotes + [f"suspect: several different dates on the receipt {sorted(dates)}"]
    shaky = any("ambiguous" in n or "non-Gregorian" in n or n.startswith("suspect") for n in dnotes)
    r.date = Field(d, dline, (0.7 if shaky else 0.95) if d else 0.0, dnotes)
    r.time = Field(find_time(lines_n), None, 0.9)

    addr_lines = set(r.address.get("lines") or [])
    for i, l in enumerate(lines_n[:5]):
        if l in addr_lines:
            continue
        letters = sum(c.isalpha() for c in l)
        if letters >= 3 and letters / max(len(l), 1) > 0.5 and not amounts_in(l, dec) and not re.search(r"\d{3,}", l):
            r.merchant = Field(l, l, round(0.6 * confs_n[i], 3), ["top-of-receipt heuristic"])
            break

    totals, subtotals, taxes, tips, discounts, roundings = [], [], [], [], [], []
    first_summary = None
    for i, l in enumerate(lines_n):
        lc = l.lower()
        amts = amounts_in(l, dec, decimal_sep, money)
        if not amts and re.fullmatch(r"[^\d]*", l) and any(has_kw(lc, k) for k in ("total", "subtotal", "tax", "discount")):
            for j in (i + 1, i - 1):  # label and value printed on separate lines
                if 0 <= j < len(lines_n) and (a := amounts_in(lines_n[j], dec, decimal_sep, money)) and \
                        not any(has_kw(lines_n[j].lower(), k) for k in ("total", "subtotal", "tax", "not_total", "discount", "tip")):
                    amts = a
                    break
        if amts and has_kw(lc, "item_count") and has_kw(lc, "total") and not _is_payable(lc) and \
                not re.search(r"\d[.,]\d{3}|\d[.,]\d{2}\b", l.split(has_kw(lc, "item_count"))[-1] if has_kw(lc, "item_count") in l else l):
            continue  # "TOTAL QTY 2", "Total Item: 2"
        if not amts:
            if has_kw(lc, "total") and not has_kw(lc, "subtotal") and re.search(r"\d", l) and not _ID_LINE.search(l):
                r.warnings.append(f"total line unreadable: {l}")
            continue
        val = amts[-1]
        if has_kw(lc, "not_total"):
            continue
        is_tax, is_total = bool(has_kw(lc, "tax")), bool(has_kw(lc, "total"))
        if is_tax and is_total:  # "Total GST" is tax, "Total incl. GST" is the total, "Total excl. GST" the subtotal
            if re.search(r"incl|inc\.|inclusive|including|termasuk|ttc", lc):
                is_tax = False
            elif re.search(r"excl|exclud|before|sebelum|\bht\b", lc):
                subtotals.append((i, val)); first_summary = first_summary if first_summary is not None else i
                continue
            else:
                is_total = False
        if is_total and len(amts) >= 2 and amts[-1] < amts[0] and re.search(r"%|\bsr\b|\bzr\b|gst|vat|tax", lc):
            continue  # a tax summary table row: taxable amount then tax
        if has_kw(lc, "rounding"):
            roundings.append((i, val)); first_summary = first_summary if first_summary is not None else i
        elif has_kw(lc, "subtotal"):
            subtotals.append((i, val)); first_summary = first_summary if first_summary is not None else i
        elif has_kw(lc, "discount"):
            discounts.append((i, abs(val))); first_summary = first_summary if first_summary is not None else i
        elif is_tax:
            if "%" in l and len(amts) == 1 and val < 100 and not re.search(r"\d[.,]\d{2}\b", l.split("%")[-1]):
                continue  # a bare rate line such as "VAT 20%"
            taxes.append((i, val)); first_summary = first_summary if first_summary is not None else i
        elif has_kw(lc, "tip") and not has_kw(lc, "tax"):
            tips.append((i, val)); first_summary = first_summary if first_summary is not None else i
        elif is_total:
            totals.append((i, val)); first_summary = first_summary if first_summary is not None else i

    def pick(cands, name):
        if not cands:
            return Field()
        i, v = cands[-1] if name == "subtotal" else choose_total(cands, lines_n, roundings)
        return Field(v, lines_n[i], round(confs_n[i], 3), ["keyword match"])

    r.subtotal = pick(subtotals, "subtotal")
    if taxes:
        tsum = sum(v for _, v in taxes)
        r.tax = Field(tsum, " | ".join(lines_n[i] for i, _ in taxes), round(min(confs_n[i] for i, _ in taxes), 3),
                      [f"{len(taxes)} tax line(s) summed"])
    if tips:
        r.tip = Field(sum(v for _, v in tips), lines_n[tips[0][0]], round(confs_n[tips[0][0]], 3))
    if discounts:
        r.discount = Field(sum(v for _, v in discounts), lines_n[discounts[0][0]], round(confs_n[discounts[0][0]], 3))
    if roundings:
        r.reconciliation["rounding"] = sum(v for _, v in roundings)
    r.total = pick(totals, "total")
    if r.total.value is not None:
        t_idx = choose_total(totals, lines_n, roundings)[0]
        above = [i for i, _ in taxes + subtotals if i > t_idx and len(amounts_in(lines_n[i], dec, decimal_sep, money)) == 1]
        if above:
            r.total.checks.append("total line is above tax or subtotal lines")
    if r.total.value is None:
        bottom = [(i, a[-1]) for i, l in enumerate(lines_n) if i >= len(lines_n) // 2
                  and (a := amounts_in(l, dec, decimal_sep, money)) and not has_kw(l.lower(), "not_total")]
        if bottom:
            i, v = max(bottom, key=lambda c: c[1])
            r.total = Field(v, lines_n[i], round(0.4 * confs_n[i], 3), ["no total keyword: largest amount in lower half"])
            r.warnings.append("total found without a keyword")

    # line items: amount-ending lines above the first summary line
    stop = first_summary if first_summary is not None else len(lines_n)
    for i, l in enumerate(lines_n[:stop]):
        amts = amounts_in(l, dec, decimal_sep, money)
        if not amts or l == r.merchant.value or l == r.date.evidence:
            continue
        desc = _AMOUNT_RE.sub("", l).strip(" .:-*x×@")
        if sum(c.isalpha() for c in desc) < 2:
            continue
        qty, unit = None, None
        m = re.search(r"(?<![\d.,])(\d{1,4})\s?[x×@*]\s?(\d[\d.,]*)", l, re.I)
        if m:
            qty, unit = int(m.group(1)), parse_amount(m.group(2), dec, decimal_sep)
        r.line_items.append({"description": desc, "quantity": qty, "unit_price": unit, "amount": amts[-1],
                             "confidence": round(confs_n[i], 3)})

    r.tax_ids = find_tax_ids(lines_n)
    r.payment = find_payment(lines_n)
    _reconcile(r, dec)
    return r


def _reconcile(r: Receipt, dec: int | None) -> None:
    tol = Decimal(1).scaleb(-(dec if dec is not None else 2))
    rec = {"rounding": r.reconciliation.get("rounding", Decimal(0))} if r.reconciliation.get("rounding") else {}
    rnd = rec.get("rounding", Decimal(0))
    items_sum = sum((it["amount"] for it in r.line_items), Decimal(0))
    if r.line_items:
        rec["items_sum"] = items_sum
        for it in r.line_items:
            if it["quantity"] and it["unit_price"] is not None:
                it["qty_x_price_ok"] = abs(it["quantity"] * it["unit_price"] - it["amount"]) <= tol
    sub = r.subtotal.value
    tax = r.tax.value or Decimal(0)
    tip = r.tip.value or Decimal(0)
    disc = r.discount.value or Decimal(0)
    tot = r.total.value
    if r.line_items and sub is not None:
        rec["items_match_subtotal"] = abs(items_sum - sub) <= tol * max(1, len(r.line_items))
        if rec["items_match_subtotal"]:
            r.subtotal.checks.append("equals sum of line items")
    misplaced = "total line is above tax or subtotal lines" in r.total.checks
    if misplaced:
        rec["total_position_ok"] = False
    if sub is not None and tot is not None and not misplaced:
        exclusive = abs(sub + tax + tip - disc + rnd - tot) <= tol * 2
        inclusive = abs(sub + tip - disc + rnd - tot) <= tol * 2  # tax already inside the subtotal (VAT-inclusive)
        rec["totals_reconcile"] = exclusive or inclusive
        rec["tax_mode"] = "exclusive" if exclusive and tax else ("inclusive" if inclusive else None)
        if rec["totals_reconcile"]:
            r.total.checks.append("reconciles with subtotal, tax, tip and discount")
    elif r.line_items and tot is not None and not misplaced:
        rec["items_match_total"] = abs(items_sum + tip - disc + rnd - tot) <= tol * max(1, len(r.line_items)) or \
            abs(items_sum + tax + tip - disc + rnd - tot) <= tol * max(1, len(r.line_items))
        if rec["items_match_total"]:
            r.total.checks.append("reconciles with line items")
    if tot is not None and tot < 0:
        r.warnings.append("negative total (refund?)")
        r.total.checks.append("negative total: credit note or refund")
    r.reconciliation = rec
