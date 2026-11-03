#!/usr/bin/env python3
"""Synthetic benchmark for the parser and the accept/review gate (no OCR engine, no images, no network).

Generates labelled receipts in each region's real conventions, simulates two independent OCR engines that
make character-level mistakes, runs the parser and the vote, and reports per region:
  coverage            receipts whose critical fields (date, currency, total) were all auto-accepted
  accepted precision  accepted critical fields that are correct
This measures the deterministic layer only. Real-image accuracy must be measured on real receipts with
receipt_eval.py, because real OCR errors are not random.

  python3 receipt_bench.py --per-region 1000 --noise 0.02 --seed 7
"""

from __future__ import annotations

import argparse
import random
import sys
import os
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from receipt_parse import parse_receipt  # noqa: E402
import receipt_ocr as ro  # noqa: E402

Q2 = Decimal("0.01")
THAI = str.maketrans("0123456789", "๐๑๒๓๔๕๖๗๘๙")
ITEMS = {
    "en": ["Latte", "Sandwich", "Water 500ml", "Chicken Rice", "Notebook", "Shampoo", "Bread", "Milk 1L", "Eggs x12", "Coffee"],
    "hi": ["Rice 5kg", "Atta 10kg", "Toor Dal", "Masala Chai", "Paneer 200g", "Ghee 1L", "Biscuits", "Soap"],
    "th": ["ข้าวผัด", "ต้มยำกุ้ง", "ชาเย็น", "น้ำดื่ม", "ผัดไทย", "กาแฟ"],
    "ms": ["Nasi Lemak", "Teh Tarik", "Roti Canai", "Mee Goreng", "Milo Ais", "Kopi O"],
    "id": ["Nasi Goreng", "Mie Goreng", "Es Teh", "Bintang", "Sate Ayam", "Babi Guling", "Jus Alpukat"],
    "vi": ["Phở bò", "Bánh mì", "Cà phê sữa", "Trà đá", "Cơm tấm", "Bún chả"],
    "de": ["Brot", "Kaffee", "Milch", "Käse", "Apfelsaft"], "fr": ["Baguette", "Café", "Croissant", "Fromage"],
    "es": ["Pan", "Café con leche", "Agua", "Tortilla"], "it": ["Cornetto", "Caffè", "Acqua", "Panino"],
    "nl": ["Brood", "Koffie", "Kaas", "Melk"], "pl": ["Chleb", "Kawa", "Mleko", "Ser"],
}


def money(v: Decimal, style: str, dec: int = 2) -> str:
    q = Decimal(1).scaleb(-dec)
    v = v.quantize(q, ROUND_HALF_UP)
    whole, frac = f"{v:.{dec}f}".split(".") if dec else (f"{v:.0f}", "")
    if style == "lakh":  # 1,23,456.78
        head, tail = whole[:-3], whole[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        whole = ",".join(groups + [tail]) if groups else tail
        return whole + ("." + frac if dec else "")
    sep_g, sep_d = {"us": (",", "."), "eu": (".", ","), "space": (" ", ","), "dot0": (".", ",")}[style]
    g = ""
    for i, ch in enumerate(reversed(whole)):
        if i and i % 3 == 0:
            g = sep_g + g
        g = ch + g
    return g + (sep_d + frac if dec else "")


def lines_for(region: str, rng: random.Random):
    """Return (lines, truth, hints) for one synthetic receipt."""
    d = date.today() - timedelta(days=rng.randrange(1, 900))  # recent past dates, as on real receipts
    n = rng.randint(1, 7)
    hints = {"currency": None, "date_order": "DMY"}
    tax_lines, extra, inclusive = [], [], False
    if region == "india":
        lang, cur, dec, style, sym = "hi", "INR", 2, "lakh", rng.choice(["₹", "Rs.", "INR "])
        prices = [Decimal(rng.randint(20, 9000)) + Decimal(rng.choice([0, 50])) / 100 for _ in range(n)]
        sub = sum(prices)
        rate = Decimal(rng.choice([5, 12, 18]))
        if rng.random() < 0.8:
            half = (sub * rate / 200).quantize(Q2, ROUND_HALF_UP)
            tax_lines = [(f"CGST {rate / 2}%", half), (f"SGST {rate / 2}%", half)]
        else:
            tax_lines = [(f"IGST {rate}%", (sub * rate / 100).quantize(Q2, ROUND_HALF_UP))]
        head = [rng.choice(["Sharma General Store", "Annapurna Restaurant", "City Medicals"]), "GSTIN 27AAPFU0939F1ZV",
                f"Bill Date: {d:%d/%m/%Y}" if rng.random() < .6 else f"Date {d:%d-%m-%Y}"]
        labels = ("Sub Total", rng.choice(["Grand Total", "Net Amount", "Total", "कुल"]))
    elif region == "singapore":
        lang, cur, dec, style, sym = "en", "SGD", 2, "us", rng.choice(["S$", "SGD "])
        prices = [Decimal(rng.randint(150, 8000)) / 100 for _ in range(n)]
        sub = sum(prices)
        inclusive = rng.random() < 0.4
        g = (sub * 9 / 109 if inclusive else sub * Decimal("0.09")).quantize(Q2, ROUND_HALF_UP)
        tax_lines = [("GST 9% (incl.)" if inclusive else "GST 9%", g)]
        head = [rng.choice(["Toast Corner Pte Ltd", "Kopi Express", "FairPrice Xtra"]), "GST Reg No: 201234567K",
                f"{d:%d/%m/%Y} {rng.randint(8, 21):02d}:{rng.randint(0, 59):02d}"]
        labels = ("Subtotal", rng.choice(["Total", "Amount Due", "TOTAL"]))
    elif region == "thailand":
        lang, cur, dec, style, sym = "th", "THB", 2, "us", rng.choice(["฿", "THB "])
        prices = [Decimal(rng.randint(30, 1500)) for _ in range(n)]
        sub = sum(prices)
        inclusive = True
        tax_lines = [(rng.choice(["ภาษีมูลค่าเพิ่ม 7%", "VAT 7%"]), (sub * 7 / 107).quantize(Q2, ROUND_HALF_UP))]
        be = f"{d.day:02d}/{d.month:02d}/{d.year + 543}"
        head = [rng.choice(["ร้านอาหารบ้านสวน", "7-Eleven สาขา 1234", "Cafe Amazon"]), "TAX ID 0105536000123",
                be.translate(THAI) if rng.random() < 0.3 else be]
        labels = (rng.choice(["รวมเงิน", "Subtotal"]), rng.choice(["ยอดสุทธิ", "Total", "รวมทั้งสิ้น"]))
    elif region == "malaysia":
        lang, cur, dec, style, sym = "ms", "MYR", 2, "us", "RM"
        prices = [Decimal(rng.randint(150, 5000)) / 100 for _ in range(n)]
        sub = sum(prices)
        sst = (sub * Decimal(rng.choice([6, 8])) / 100).quantize(Q2, ROUND_HALF_UP)
        tax_lines = [(rng.choice(["SST 6%", "Service Tax 8%", "SST"]), sst)]
        raw = sub + sst
        rounded = (raw * 20).quantize(Decimal(1), ROUND_HALF_UP) / 20  # cash rounding to 5 sen
        if rounded != raw:
            extra = [("Rounding Adj", (rounded - raw).quantize(Q2))]
        head = [rng.choice(["Restoran Nasi Kandar", "Mamak Corner Sdn Bhd", "99 Speedmart"]), "SST No: W10-1808-32000123",
                f"Date: {d:%d/%m/%Y}"]
        labels = ("Sub Total", rng.choice(["Total", "Jumlah", "Total (RM)"]))
    elif region == "bali":
        lang, cur, dec, style, sym = "id", "IDR", 0, "dot0", rng.choice(["Rp ", "Rp. ", "IDR "])
        prices = [Decimal(rng.randint(3, 400) * 1000) for _ in range(n)]
        sub = sum(prices)
        svc = (sub * Decimal("0.05") * rng.choice([1, 2])).quantize(Decimal(1))
        extra = [(rng.choice(["Service 5%", "Service Charge"]), svc)] if rng.random() < 0.7 else []
        base = sub + (extra[0][1] if extra else 0)
        tax_lines = [(rng.choice(["PB1 10%", "Pajak 10%", "Tax 10%"]), (base * Decimal("0.1")).quantize(Decimal(1)))]
        head = [rng.choice(["Warung Made Seminyak", "Ubud Organic Cafe", "Kuta Beach Club"]), "Jl. Raya Seminyak No.12",
                f"{d:%d/%m/%Y}"]
        labels = ("Subtotal", rng.choice(["Total", "Grand Total", "Jumlah"]))
    elif region == "canada":
        lang, cur, dec, style, sym = "en", "CAD", 2, "us", "$"
        hints["currency"] = "CAD"
        prices = [Decimal(rng.randint(150, 9000)) / 100 for _ in range(n)]
        sub = sum(prices)
        prov = rng.choice(["ON", "QC", "BC", "AB"])
        if prov == "ON":
            tax_lines = [("HST 13%", (sub * Decimal("0.13")).quantize(Q2, ROUND_HALF_UP))]
        elif prov == "QC":
            tax_lines = [("TPS 5%", (sub * Decimal("0.05")).quantize(Q2, ROUND_HALF_UP)),
                         ("TVQ 9.975%", (sub * Decimal("0.09975")).quantize(Q2, ROUND_HALF_UP))]
        elif prov == "BC":
            tax_lines = [("GST 5%", (sub * Decimal("0.05")).quantize(Q2, ROUND_HALF_UP)),
                         ("PST 7%", (sub * Decimal("0.07")).quantize(Q2, ROUND_HALF_UP))]
        else:
            tax_lines = [("GST 5%", (sub * Decimal("0.05")).quantize(Q2, ROUND_HALF_UP))]
        head = [rng.choice(["Maple Diner", "Tim's Coffee", "Corner Pharmacy"]), "GST/HST # 123456789 RT0001",
                f"{d:%Y-%m-%d}" if rng.random() < .5 else f"{d:%m/%d/%Y}"]
        hints["date_order"] = "MDY"
        labels = ("Sous-total" if prov == "QC" else "Subtotal", "Total")
    elif region == "europe":
        lang = rng.choice(["de", "fr", "es", "it", "nl", "pl"])
        cur, dec = ("PLN", 2) if lang == "pl" else ("EUR", 2)
        style = rng.choice(["eu", "space"]) if lang in ("fr", "pl") else "eu"
        sym = {"pl": "zł", "de": "EUR ", "fr": "€", "es": "€", "it": "€", "nl": "€"}[lang]
        prices = [Decimal(rng.randint(50, 6000)) / 100 for _ in range(n)]
        sub = sum(prices)
        inclusive = True
        rate = {"de": 19, "fr": 20, "es": 21, "it": 22, "nl": 21, "pl": 23}[lang]
        vat = {"de": "MwSt", "fr": "TVA", "es": "IVA", "it": "IVA", "nl": "BTW", "pl": "PTU"}[lang]
        tax_lines = [(f"{vat} {rate}%", (sub * rate / (100 + rate)).quantize(Q2, ROUND_HALF_UP))]
        head = [{"de": "Bäckerei Schmidt", "fr": "Boulangerie Martin", "es": "Cafetería Sol", "it": "Bar Centrale",
                 "nl": "Bakkerij de Vries", "pl": "Piekarnia Nowak"}[lang], f"{d:%d.%m.%Y}" if lang in ("de", "pl") else f"{d:%d/%m/%Y}"]
        labels = ({"de": "Zwischensumme", "fr": "Sous-total", "es": "Subtotal", "it": "Subtotale", "nl": "Subtotaal", "pl": "Suma częściowa"}[lang],
                  {"de": "Summe", "fr": "Total TTC", "es": "Total", "it": "Totale", "nl": "Totaal", "pl": "Razem"}[lang])
    elif region == "vietnam":
        lang, cur, dec, style, sym = "vi", "VND", 0, "dot0", rng.choice(["đ", "VNĐ", "VND", "₫"])
        prices = [Decimal(rng.randint(10, 500) * 1000) for _ in range(n)]
        sub = sum(prices)
        rate = rng.choice([8, 10])
        tax_lines = [(rng.choice([f"Thuế GTGT {rate}%", f"VAT {rate}%"]), (sub * rate / 100).quantize(Decimal(1)))]
        head = [rng.choice(["Quán Phở Hà Nội", "Cà Phê Sài Gòn", "Bếp Nhà Mẹ"]), "MST: 0312345678", f"Ngày {d:%d/%m/%Y}"]
        labels = (rng.choice(["Tạm tính", "Thành tiền"]), rng.choice(["Tổng cộng", "Tổng tiền", "Thanh toán"]))
    else:
        raise ValueError(region)

    tax_total = sum((v for _, v in tax_lines), Decimal(0))
    extra_total = sum((v for _, v in extra), Decimal(0))
    total = sub + extra_total + (0 if inclusive else tax_total)
    fmt = lambda v: (f"{sym}{money(v, style, dec)}" if sym.strip() in ("₹", "Rs.", "S$", "฿", "RM", "Rp", "Rp.", "$", "€")
                     else f"{money(v, style, dec)} {sym.strip()}" if sym.strip() in ("đ", "₫", "zł") else f"{sym}{money(v, style, dec)}")
    names = ITEMS.get(lang, ITEMS["en"])
    body = []
    for p in prices:
        q = rng.choice([1, 1, 1, 2, 3])
        nm = rng.choice(names)
        if q > 1 and dec == 2 and (p / q).quantize(Q2) * q == p:
            body.append(f"{nm} {q} x {money(p / q, style, dec)} {fmt(p)}")
        else:
            body.append(f"{nm} {fmt(p)}")
    lines = head + body + [f"{labels[0]} {fmt(sub)}"] + [f"{lbl} {fmt(v)}" for lbl, v in extra if "Rounding" not in lbl] + \
        [f"{lbl} {fmt(v)}" for lbl, v in tax_lines] + [f"{lbl} {fmt(v)}" for lbl, v in extra if "Rounding" in lbl] + \
        [f"{labels[1]} {fmt(total)}"]
    if rng.random() < 0.4:
        paid = (total / 50000 + 1).quantize(Decimal(1)) * 50000 if dec == 0 else (total / 10 + 1).quantize(Decimal(1)) * 10
        lines += [f"Cash {fmt(paid)}", f"Change {fmt(paid - total)}"]
    else:
        lines += ["VISA XXXX XXXX XXXX 4821"]
    if region == "thailand" and rng.random() < 0.3:
        lines = [l.translate(THAI) if any(c.isdigit() for c in l) and "TAX" not in l else l for l in lines]
    truth = {"date": d.isoformat(), "currency": cur, "total": str(total.quantize(Decimal(1).scaleb(-dec)))}
    return lines, truth, hints


CONFUSE = {"0": "O", "O": "0", "1": "l", "l": "1", "5": "S", "S": "5", "8": "B", "B": "8", ".": ",", ",": ".", "6": "b", "2": "Z"}


def ocr_noise(lines, rng, p):
    """Simulate one OCR engine: character confusions and drops, with lower line confidence where it erred."""
    out, confs = [], []
    for l in lines:
        chars, err = [], 0
        for ch in l:
            r = rng.random()
            if r < p and ch in CONFUSE:
                chars.append(CONFUSE[ch]); err += 1
            elif r < p * 1.3:
                err += 1  # dropped character
            else:
                chars.append(ch)
        out.append("".join(chars))
        confs.append(max(0.3, 0.98 - 0.12 * err - rng.random() * 0.05 * (err > 0)))
    return out, confs


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--per-region", type=int, default=1000)
    ap.add_argument("--noise", type=float, default=0.02, help="per-character error rate of each simulated engine")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--show-errors", type=int, default=0, help="print up to N accepted-but-wrong cases")
    a = ap.parse_args()
    rng = random.Random(a.seed)
    regions = ["india", "singapore", "thailand", "malaysia", "bali", "canada", "europe", "vietnam"]
    print(f"{a.per_region} receipts per region, 2 simulated engines, noise {a.noise:.1%} per character\n")
    print(f"{'region':10} {'clean ok':>9} {'coverage':>9} {'acc.fields':>11} {'wrong':>6} {'precision':>10}")
    shown = 0
    g_acc = g_wrong = 0
    for region in regions:
        clean_ok = covered = acc = wrong = 0
        for _ in range(a.per_region):
            lines, truth, hints = lines_for(region, rng)
            clean = parse_receipt(lines, None, hints["currency"], hints["date_order"]).to_dict()
            clean_ok += all(str(clean[f]["value"]) == truth[f] for f in truth)
            runs = {}
            for eng in ("engA", "engB"):
                noisy, confs = ocr_noise(lines, rng, a.noise)
                runs[eng] = parse_receipt(noisy, confs, hints["currency"], hints["date_order"]).to_dict()
            v = ro.vote(runs, 0.85)
            covered += v["status"] == "accepted"
            for f in truth:
                fv = v["fields"][f]
                if fv.get("status") == "accepted":
                    acc += 1
                    if str(fv["value"]) != truth[f]:
                        wrong += 1
                        if shown < a.show_errors:
                            shown += 1
                            print(f"  WRONG {region} {f}: got {fv['value']} want {truth[f]} | {fv.get('evidence')}")
        g_acc += acc
        g_wrong += wrong
        prec = 1 - wrong / acc if acc else float("nan")
        print(f"{region:10} {clean_ok / a.per_region:9.2%} {covered / a.per_region:9.2%} {acc:11d} {wrong:6d} {prec:10.4%}")
    print(f"\nall regions: {g_acc} accepted critical fields, {g_wrong} wrong, precision {1 - g_wrong / max(g_acc, 1):.4%}")
    print("clean ok = parser correct on error-free text; coverage = receipts fully auto-accepted under noise.")


if __name__ == "__main__":
    main()
