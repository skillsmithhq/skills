"""Deterministic receipt address and postal-code extractor. Standard library only, no LLM.

find_address(lines, country_hint=None) finds the address block near the top of a receipt, the postal code,
and the country, and says which evidence decided the country. Digits alone never decide a country: a
5-digit number fits Malaysia, Thailand, Indonesia, the US, Germany, France and more. The country comes from
a country or region name, a postal label, a phone prefix, a tax-ID style, a letter-bearing postal format
(Canada, UK, Netherlands, Ireland, Japan, "S(123456)"), or the caller's hint. Evidence that disagrees gives
country None and a note, never a guess.

currency_for_country(cc) maps an ISO 3166-1 alpha-2 code to its ISO 4217 currency.
"""

from __future__ import annotations

import json
import os
import re
import sys
import unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from receipt_parse import normalise  # noqa: E402

__all__ = ["find_address", "currency_for_country"]

# ---------------------------------------------------------------- currencies

_EURO = "AT BE HR CY EE FI FR DE GR IE IT LV LT LU MT NL PT SK SI ES BG MC SM VA AD ME XK".split()
_CURRENCY = {
    "IN": "INR", "SG": "SGD", "TH": "THB", "MY": "MYR", "ID": "IDR", "CA": "CAD", "VN": "VND", "US": "USD",
    "GB": "GBP", "AU": "AUD", "JP": "JPY", "KR": "KRW", "CN": "CNY", "AE": "AED", "SA": "SAR", "PL": "PLN",
    "CZ": "CZK", "HU": "HUF", "SE": "SEK", "DK": "DKK", "NO": "NOK", "CH": "CHF", "LI": "CHF", "NZ": "NZD",
    "HK": "HKD", "TW": "TWD", "PH": "PHP", "PK": "PKR", "BD": "BDT", "LK": "LKR", "NP": "NPR", "TR": "TRY",
    "RU": "RUB", "UA": "UAH", "IL": "ILS", "EG": "EGP", "ZA": "ZAR", "NG": "NGN", "KE": "KES", "BR": "BRL",
    "MX": "MXN", "AR": "ARS", "CL": "CLP", "CO": "COP", "PE": "PEN", "QA": "QAR", "KW": "KWD", "BH": "BHD",
    "OM": "OMR", "JO": "JOD", "RO": "RON", "IS": "ISK", "MA": "MAD", "TN": "TND", "KH": "KHR", "LA": "LAK",
    "MM": "MMK", "MO": "MOP", "BN": "BND", "GH": "GHS", "KZ": "KZT",
}
_CURRENCY.update({cc: "EUR" for cc in _EURO})


def currency_for_country(cc: str) -> str | None:
    """ISO 3166-1 alpha-2 -> ISO 4217, or None when unknown."""
    if not cc:
        return None
    return _CURRENCY.get(cc.strip().upper())


# ---------------------------------------------------------------- text helpers

_FOLD = str.maketrans({"đ": "d", "ł": "l", "ø": "o", "ß": "ss", "æ": "ae", "œ": "oe", "ı": "i"})


def fold(text: str) -> str:
    """Lower-case, strip accents and other non-spacing marks; used only for name matching."""
    text = unicodedata.normalize("NFKD", text.lower().translate(_FOLD))
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


_L = r"[^\W\d_]"  # one letter, any script


def _lab(alternatives: str) -> str:
    """A label that is not glued to other letters (digits may follow directly)."""
    return rf"(?<!{_L})(?:{alternatives})(?!{_L})"


def _mask(chars: list, start: int, end: int, protected: list) -> None:
    for i in range(start, end):
        if not any(a <= i < b for a, b in protected):
            chars[i] = " "


# ---------------------------------------------------------------- names: countries, states, cities
# "Canonical|variant|variant". S = state/province/region (strong evidence), C = city (weak evidence:
# London, Dublin and Paris also exist elsewhere, so a city never overrules other evidence).

_COUNTRY_NAMES = {
    "IN": "India|Bharat|भारत", "SG": "Singapore|Singapura", "MY": "Malaysia", "TH": "Thailand|ประเทศไทย",
    "ID": "Indonesia", "VN": "Vietnam|Viet Nam", "CA": "Canada", "US": "United States|United States of America",
    "GB": "United Kingdom|Great Britain|England|Scotland|Wales|Northern Ireland", "IE": "Ireland|Eire",
    "NL": "Netherlands|The Netherlands|Nederland|Holland", "DE": "Germany|Deutschland", "FR": "France",
    "ES": "Spain|España", "IT": "Italy|Italia", "PL": "Poland|Polska", "PT": "Portugal",
    "BE": "Belgium|Belgique|België", "AT": "Austria|Österreich", "CH": "Switzerland|Schweiz|Suisse|Svizzera",
    "DK": "Denmark|Danmark", "NO": "Norway|Norge", "AU": "Australia", "JP": "Japan|日本", "CN": "China|中国",
    "KR": "South Korea|Korea|대한민국", "PH": "Philippines", "HK": "Hong Kong", "MX": "Mexico|México",
    "SE": "Sweden|Sverige", "FI": "Finland|Suomi", "NZ": "New Zealand", "SA": "Saudi Arabia",
    "AE": "United Arab Emirates", "TW": "Taiwan", "LU": "Luxembourg",
}
_CASE_SENSITIVE_COUNTRY = [(r"U\.S\.A\.|USA", "US"), (r"U\.K\.|UK", "GB"), (r"UAE", "AE")]

_REGIONS = {
    "MY": {"S": ["Johor|Johore", "Selangor", "Kuala Lumpur|W.P. Kuala Lumpur|WP Kuala Lumpur",
                 "Wilayah Persekutuan|W.P.", "Penang|Pulau Pinang|P. Pinang|Pinang", "Perak", "Sabah", "Sarawak",
                 "Melaka|Malacca", "Kedah", "Kelantan", "Pahang", "Terengganu|Trengganu",
                 "Negeri Sembilan|N. Sembilan", "Perlis", "Putrajaya", "Labuan"],
           "C": ["Petaling Jaya", "Shah Alam", "Subang Jaya", "Johor Bahru", "Ipoh", "Kota Kinabalu", "Kuching",
                 "Seremban", "Klang", "Alor Setar", "Kota Bharu", "Kuantan", "Cyberjaya", "Puchong", "Cheras"]},
    "TH": {"S": ["Bangkok|กรุงเทพ|Krung Thep", "Chiang Mai|เชียงใหม่", "Phuket|ภูเก็ต", "Chon Buri|Chonburi|ชลบุรี",
                 "Nonthaburi|นนทบุรี", "Samut Prakan|Samut Prakarn|สมุทรปราการ", "Pathum Thani|ปทุมธานี",
                 "Khon Kaen|ขอนแก่น", "Krabi|กระบี่", "Surat Thani|สุราษฎร์ธานี", "Chiang Rai|เชียงราย",
                 "Nakhon Ratchasima|Korat|นครราชสีมา", "Songkhla|สงขลา", "Ayutthaya|อยุธยา", "Udon Thani|อุดรธานี",
                 "Prachuap Khiri Khan|ประจวบคีรีขันธ์"],
           "C": ["Pattaya|พัทยา", "Hua Hin|หัวหิน", "Ko Samui|Koh Samui|เกาะสมุย", "Hat Yai|หาดใหญ่"]},
    "ID": {"S": ["Bali", "Jakarta|DKI Jakarta|Jakarta Selatan|Jakarta Pusat|Jakarta Barat|Jakarta Timur|Jakarta Utara",
                 "Jawa Barat|West Java", "Jawa Tengah|Central Java", "Jawa Timur|East Java", "Jawa", "Banten",
                 "Yogyakarta|DI Yogyakarta|Jogjakarta|Jogja", "Sumatera Utara|North Sumatra", "Sumatera|Sumatra",
                 "Kalimantan", "Sulawesi", "Nusa Tenggara Barat|NTB", "Papua"],
           "C": ["Denpasar", "Badung", "Gianyar", "Tabanan", "Kuta", "Seminyak", "Ubud", "Canggu", "Sanur",
                 "Nusa Dua", "Jimbaran", "Bandung", "Surabaya", "Semarang", "Medan", "Makassar", "Tangerang",
                 "Bekasi", "Bogor", "Depok", "Malang", "Lombok"]},
    "VN": {"S": ["Hà Nội|Hanoi|Ha Noi", "Hồ Chí Minh|TP.HCM|TP HCM|TPHCM|HCMC|Sài Gòn|Saigon|Sai Gon",
                 "Đà Nẵng|Danang", "Hải Phòng", "Cần Thơ", "Huế", "Khánh Hòa", "Quảng Ninh", "Bình Dương",
                 "Đồng Nai", "Lâm Đồng", "Quảng Nam"],
           "C": ["Nha Trang", "Hội An", "Đà Lạt|Dalat", "Vũng Tàu"]},
    "IN": {"S": ["Maharashtra", "Karnataka", "Tamil Nadu", "Delhi|New Delhi|NCT of Delhi", "Telangana",
                 "Andhra Pradesh", "Kerala", "Gujarat", "Rajasthan", "Uttar Pradesh", "West Bengal", "Haryana", "Goa",
                 "Madhya Pradesh", "Bihar", "Odisha|Orissa", "Assam", "Jharkhand", "Uttarakhand", "Himachal Pradesh",
                 "Chandigarh", "Puducherry|Pondicherry"],
           "C": ["Mumbai|Bombay|Navi Mumbai", "Bengaluru|Bangalore", "Chennai", "Kolkata|Calcutta", "Pune",
                 "Ahmedabad", "Jaipur", "Gurugram|Gurgaon", "Noida", "Kochi|Cochin", "Lucknow", "Indore", "Bhopal",
                 "Nagpur", "Thane", "Coimbatore", "Mysuru|Mysore", "Visakhapatnam", "Secunderabad"]},
    "CA": {"S": ["Ontario", "Quebec", "British Columbia", "Alberta", "Manitoba", "Saskatchewan", "Nova Scotia",
                 "New Brunswick", "Newfoundland and Labrador|Newfoundland", "Prince Edward Island", "Yukon",
                 "Northwest Territories", "Nunavut"],
           "C": ["Toronto", "Montreal", "Vancouver", "Calgary", "Ottawa", "Edmonton", "Winnipeg", "Halifax",
                 "Mississauga", "Laval", "Gatineau", "Saskatoon", "Brampton"]},
    "US": {"S": ["California", "Texas", "New York", "Florida", "Illinois", "Massachusetts", "Pennsylvania", "Ohio",
                 "Michigan", "New Jersey", "Arizona", "Colorado", "Oregon", "Nevada", "North Carolina", "Tennessee",
                 "Minnesota", "Hawaii", "Alaska", "Utah", "Wisconsin", "Maryland", "Connecticut", "Louisiana"],
           "C": ["Los Angeles", "San Francisco", "Chicago", "Seattle", "Boston", "Houston", "Miami", "Denver",
                 "Philadelphia", "Atlanta", "Dallas", "San Diego", "Las Vegas", "Brooklyn", "Manhattan"]},
    "GB": {"C": ["London", "Manchester", "Edinburgh", "Glasgow", "Liverpool", "Leeds", "Cardiff", "Belfast",
                 "Oxford", "Sheffield", "Nottingham", "Brighton", "Leicester"]},
    "IE": {"C": ["Dublin|Baile Átha Cliath", "Cork", "Galway", "Limerick", "Kilkenny"]},
    "NL": {"S": ["Noord-Holland|Noord Holland", "Zuid-Holland|Zuid Holland", "Utrecht", "Gelderland",
                 "Noord-Brabant", "Friesland|Fryslân", "Overijssel"],
           "C": ["Amsterdam", "Rotterdam", "Den Haag|'s-Gravenhage|The Hague", "Eindhoven", "Haarlem", "Leiden",
                 "Delft", "Maastricht", "Nijmegen", "Tilburg", "Breda", "Arnhem", "Groningen"]},
    "DE": {"S": ["Bayern|Bavaria", "Berlin", "Hamburg", "Nordrhein-Westfalen|NRW", "Hessen", "Sachsen",
                 "Baden-Württemberg", "Niedersachsen", "Brandenburg", "Thüringen", "Rheinland-Pfalz",
                 "Schleswig-Holstein"],
           "C": ["München|Munich|Muenchen", "Köln|Koeln|Cologne", "Frankfurt am Main|Frankfurt", "Stuttgart",
                 "Düsseldorf|Duesseldorf", "Leipzig", "Dresden", "Hannover", "Nürnberg|Nuremberg", "Bonn",
                 "Dortmund", "Heidelberg", "Mannheim", "Bremen"]},
    "FR": {"S": ["Île-de-France", "Bretagne", "Normandie", "Occitanie", "Auvergne-Rhône-Alpes", "Nouvelle-Aquitaine",
                 "Hauts-de-France", "Grand Est", "Provence-Alpes-Côte d'Azur"],
           "C": ["Paris", "Lyon", "Marseille", "Toulouse", "Bordeaux", "Lille", "Nantes", "Strasbourg",
                 "Montpellier", "Rennes", "Grenoble", "Dijon", "Reims", "Le Havre", "Cannes", "Annecy"]},
    "ES": {"S": ["Madrid|Comunidad de Madrid", "Cataluña|Catalunya|Catalonia", "Andalucía|Andalusia",
                 "País Vasco|Euskadi", "Galicia", "Comunitat Valenciana|Comunidad Valenciana",
                 "Islas Baleares|Illes Balears", "Canarias"],
           "C": ["Barcelona", "Valencia", "Sevilla|Seville", "Málaga", "Bilbao", "Zaragoza", "Palma de Mallorca|Palma",
                 "Alicante", "Granada"]},
    "IT": {"S": ["Lombardia|Lombardy", "Lazio", "Toscana|Tuscany", "Veneto", "Campania", "Piemonte|Piedmont",
                 "Sicilia|Sicily", "Emilia-Romagna", "Liguria", "Puglia"],
           "C": ["Roma|Rome", "Milano|Milan", "Napoli|Naples", "Torino|Turin", "Firenze|Florence", "Venezia|Venice",
                 "Bologna", "Genova|Genoa", "Verona", "Palermo", "Pisa"]},
    "PL": {"S": ["Mazowieckie", "Małopolskie", "Pomorskie", "Dolnośląskie", "Wielkopolskie", "Śląskie", "Łódzkie"],
           "C": ["Warszawa|Warsaw", "Kraków|Cracow", "Gdańsk", "Wrocław", "Poznań", "Łódź", "Katowice", "Szczecin",
                 "Lublin", "Gdynia", "Sopot"]},
    "PT": {"C": ["Lisboa|Lisbon", "Porto|Oporto", "Faro", "Coimbra", "Braga", "Funchal"]},
    "BE": {"C": ["Bruxelles|Brussel|Brussels", "Antwerpen|Anvers|Antwerp", "Gent|Gand|Ghent", "Liège|Luik",
                 "Brugge|Bruges", "Leuven|Louvain", "Namur", "Charleroi", "Mechelen"]},
    "AT": {"C": ["Wien|Vienna", "Graz", "Salzburg", "Linz", "Innsbruck", "Klagenfurt"]},
    "CH": {"C": ["Zürich", "Genève|Geneva|Genf", "Basel|Bâle", "Bern|Berne", "Lausanne", "Luzern|Lucerne",
                 "Lugano", "Winterthur", "St. Gallen"]},
    "DK": {"C": ["København|Copenhagen", "Aarhus|Århus", "Odense", "Aalborg"]},
    "NO": {"C": ["Oslo", "Bergen", "Trondheim", "Stavanger", "Tromsø"]},
    "AU": {"S": ["New South Wales", "Queensland", "Tasmania", "Western Australia", "South Australia"],
           "C": ["Sydney", "Melbourne", "Brisbane", "Adelaide", "Canberra", "Perth", "Hobart"]},
    "JP": {"C": ["Tokyo|東京", "Osaka|大阪", "Kyoto|京都"]},
}

_NAME_TABLE = []  # (folded variant, cc, level, canonical)
for _cc, _names in _COUNTRY_NAMES.items():
    for _v in _names.split("|"):
        _NAME_TABLE.append((fold(_v), _cc, "country", _names.split("|")[0]))
for _cc, _levels in _REGIONS.items():
    for _lvl, _entries in _levels.items():
        for _entry in _entries:
            _variants = _entry.split("|")
            for _v in _variants:
                _NAME_TABLE.append((fold(_v), _cc, "state" if _lvl == "S" else "city", _variants[0]))
_NAME_TABLE.sort(key=lambda t: -len(t[0]))
_NAME_RES = [(re.compile(rf"(?<![a-z0-9]){re.escape(v)}(?![a-z0-9])"), cc, lvl, canon)
             for v, cc, lvl, canon in _NAME_TABLE]


def _find_names(text: str) -> list:
    """[(cc, level, canonical)] for every country/state/city name in the line, longest match first."""
    f = fold(text)
    found = []
    for rx, cc, lvl, canon in _NAME_RES:
        for m in rx.finditer(f):
            found.append((cc, lvl, canon))
            f = f[:m.start()] + " " * (m.end() - m.start()) + f[m.end():]
    for pat, cc in _CASE_SENSITIVE_COUNTRY:
        if re.search(rf"(?<![A-Za-z])(?:{pat})(?![A-Za-z])", text):
            found.append((cc, "country", cc))
    return found


# ---------------------------------------------------------------- codes: US states, Canadian provinces, AU states

_US_STATES = set("AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY "
                 "NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC PR".split())
_CA_PROV = {"ON": "Ontario", "QC": "Quebec", "BC": "British Columbia", "AB": "Alberta", "MB": "Manitoba",
            "SK": "Saskatchewan", "NS": "Nova Scotia", "NB": "New Brunswick", "NL": "Newfoundland and Labrador",
            "PE": "Prince Edward Island", "YT": "Yukon", "NT": "Northwest Territories", "NU": "Nunavut"}
# first letter of a Canadian postal code -> province
_CA_LETTER = {"A": "NL", "B": "NS", "C": "PE", "E": "NB", "G": "QC", "H": "QC", "J": "QC", "K": "ON", "L": "ON",
              "M": "ON", "N": "ON", "P": "ON", "R": "MB", "S": "SK", "T": "AB", "V": "BC", "Y": "YT"}
# Malaysian state -> first two digits of its postcodes
_MY_RANGES = {
    "Kuala Lumpur": [(50, 60)], "Selangor": [(40, 48), (63, 68)], "Johor": [(79, 86)], "Penang": [(10, 14)],
    "Perak": [(30, 36)], "Kedah": [(5, 9)], "Perlis": [(1, 2)], "Kelantan": [(15, 18)], "Terengganu": [(20, 24)],
    "Pahang": [(25, 28), (39, 39), (49, 49), (69, 69)], "Negeri Sembilan": [(70, 73)], "Melaka": [(75, 78)],
    "Sabah": [(88, 91)], "Sarawak": [(93, 98)], "Putrajaya": [(62, 62)], "Labuan": [(87, 87)],
}

# ---------------------------------------------------------------- phone prefixes

_PHONE_CC = {
    "1": {"US", "CA"}, "7": {"RU", "KZ"}, "20": {"EG"}, "27": {"ZA"}, "30": {"GR"}, "31": {"NL"}, "32": {"BE"},
    "33": {"FR"}, "34": {"ES"}, "36": {"HU"}, "39": {"IT"}, "40": {"RO"}, "41": {"CH"}, "43": {"AT"}, "44": {"GB"},
    "45": {"DK"}, "46": {"SE"}, "47": {"NO"}, "48": {"PL"}, "49": {"DE"}, "351": {"PT"}, "352": {"LU"},
    "353": {"IE"}, "358": {"FI"}, "420": {"CZ"}, "52": {"MX"}, "54": {"AR"}, "55": {"BR"}, "60": {"MY"},
    "61": {"AU"}, "62": {"ID"}, "63": {"PH"}, "64": {"NZ"}, "65": {"SG"}, "66": {"TH"}, "81": {"JP"}, "82": {"KR"},
    "84": {"VN"}, "86": {"CN"}, "852": {"HK"}, "886": {"TW"}, "90": {"TR"}, "91": {"IN"}, "92": {"PK"},
    "94": {"LK"}, "966": {"SA"}, "971": {"AE"}, "974": {"QA"},
}

# ---------------------------------------------------------------- label patterns

_PHONE_LABEL = re.compile(
    _lab(r"tel(?:ephone|p|f)?|phone|ph|fax|mobile|mob|hp|h/p|hotline|whatsapp|tél|téléphone|telefon|telefono|"
         r"teléfono|telefone|đt|sđt|điện thoại|dien thoai") + r"|โทร(?:ศัพท์|สาร)?", re.I)
_PHONE_AFTER_LABEL = re.compile(r"\s*\.?\s*[:.]?\s*(\+?[\d(][\d\s().\-/+]{4,}\d)")
_PHONE_PATTERNS = [
    re.compile(r"\+\s?\(?\d[\d\s().\-]{6,}\d"),
    re.compile(r"(?<![\d\-])\(\d{2,4}\)\s?\d[\d\s\-]{4,}\d"),
    re.compile(r"(?<![\d\-])0\d{1,3}[\s\-]\d{3,4}[\s\-]?\d{3,4}(?![\d\-])"),
    re.compile(r"(?<![\d\-])\d{3}[\-.]\d{3}[\-.]\d{4}(?![\d\-])"),
    re.compile(r"(?<![\d\-])[6-9]\d{4}\s?\d{5}(?![\d\-])"),  # Indian mobile without a label
]
_EMAIL_WEB = re.compile(
    r"\S+@\S+|www\.\S+|https?://\S+|\b[a-z0-9-]+\.(?:com|net|org|co|io|biz|info|my|sg|in|id|th|vn|ca|uk|de|fr|"
    r"nl|pl|es|it|pt|ie|be|at|ch|dk|no|au|jp|us)\b\S*", re.I)

# (pattern, countries or None, description). A tax label only counts when an ID follows it.
_TAX_LABELS = [
    (r"gstin", {"IN"}, "GSTIN"),
    (r"gst\s*reg(?:istration)?\.?(?:\s*(?:no\.?|number))?", {"SG"}, "GST Reg No"),
    (r"uen", {"SG"}, "UEN"),
    (r"sst(?:\s*(?:reg(?:istration)?\.?|id))?(?:\s*(?:no\.?|number))?", {"MY"}, "SST No"),
    (r"npwp", {"ID"}, "NPWP"),
    (r"mst|mã số thuế|ma so thue", {"VN"}, "MST"),
    (r"gst\s*/\s*hst|hst|qst|tvq|tps", {"CA"}, "GST/HST"),
    (r"abn", {"AU"}, "ABN"),
    (r"siret|siren", {"FR"}, "SIRET"),
    (r"ust-?id(?:nr)?\.?|ust\.?-?idnr\.?|steuer-?nr\.?|steuernummer|st\.-?nr\.?", {"DE"}, "USt-IdNr"),
    (r"uid(?:-nr\.?)?", {"AT"}, "UID"),
    (r"nif", {"ES", "PT"}, "NIF"),
    (r"cif", {"ES"}, "CIF"),
    (r"p\.\s?iva|partita\s+iva", {"IT"}, "P.IVA"),
    (r"nip", {"PL"}, "NIP"),
    (r"kvk", {"NL"}, "KvK"),
    (r"btw", {"NL", "BE"}, "BTW"),
    (r"cvr", {"DK"}, "CVR"),
    (r"org\.?\s*nr\.?|mva", {"NO", "SE"}, "Org.nr"),
    (r"เลขประจำตัวผู้เสียภาษี", {"TH"}, "Thai tax ID"),
    (r"gst(?:\s*(?:no\.?|number|#|id))?|vat(?:\s*reg(?:istration)?)?\.?(?:\s*(?:no\.?|number|id|#))?|"
     r"tva(?:\s*intra\w*)?|n°\s*tva|mwst|moms|iva|tin|tax\s*id|tax\s*no\.?|"
     r"(?:co\.?\s*)?reg(?:istration)?\.?\s*no\.?|roc|brn|company\s*no\.?|ein|cin", None, "tax ID"),
]
_TAX_RES = [(re.compile(_lab(p) + r"\s*[:.#\-]?\s*(?=[A-Za-z]{0,3}\s?\d)", re.I), cc, d) for p, cc, d in _TAX_LABELS]
_VAT_PREFIX = re.compile(r"(?<![A-Za-z])(GB|DE|FR|NL|BE|ES|IT|PL|PT|IE|AT|DK|SE|FI|CZ|HU|EL|LU|CHE)U?[\s\-]?\d")
_VAT_PREFIX_CC = {"EL": "GR", "CHE": "CH"}
_CA_BN = re.compile(r"\b\d{9}\s?RT\s?\d{4}\b")

_ID_LABEL = re.compile(
    r"(?:" + _lab(r"invoice|inv|receipt|rcpt|bill|order|trans(?:action)?|txn|ref|no|nr|n°|nº|number|số|hoá đơn|hóa đơn|"
         r"nota|faktur|struk|rechnung|facture|factura|ticket|table|tbl|cashier|kasir|terminal|tid|mid|batch|"
         r"trace|appr(?:oval)?|auth|seq|member|customer|cust|acct|account|voucher|kassa|beleg") +
    r"|#|เลขที่)" +
    r"\s*(?:no\.?|nr\.?|number|#)?\s*[:.#]?\s*(?:[A-Za-z]{0,4}[\-/]?)?\d[\w\-/]*", re.I)
_DATE_TIME = [
    re.compile(r"(?<!\d)\d{4}[./\-]\d{1,2}[./\-]\d{1,2}(?!\d)"),
    re.compile(r"(?<!\d)\d{1,2}[./\-]\d{1,2}[./\-]\d{2,4}(?!\d)"),
    re.compile(r"(?<!\d)\d{1,2}[\s\-]*(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?[\s\-,]*"
               r"\d{2,4}(?!\d)", re.I),
    re.compile(r"(?<![a-z])(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}"
               r"(?!\d)", re.I),
    re.compile(r"(?<!\d)\d{1,2}:\d{2}(?::\d{2})?(?!\d)"),
]
_AMOUNTS = [
    re.compile(r"\d[\d,.']*[.,]\d{2}(?!\d)"),
    re.compile(r"(?<![\d.,])\d{1,3}(?:[.,]\d{3})+(?![\d.,]*\d)"),
    re.compile(r"(?<!" + _L + r")(?:rp|rm|s\$|us\$|\$|€|£|₹|฿|₫|¥|zł|chf|eur|usd|sgd|myr|thb|idr|inr|vnd|gbp|"
               r"cad|aud|pln)\s?\d[\d.,]*", re.I),
    re.compile(r"\d[\d.,]*\s?(?:₫|đ|vnd|€|zł|baht|บาท|eur|dkk|nok|chf)(?!" + _L + r")", re.I),
]
_CARD = [re.compile(r"[*xX•#]{2,}[\s\-]?\d{4}"), re.compile(r"(?<!\d)(?:\d{4}[\s\-]){3}\d{4}(?!\d)")]
_HAS_AMOUNT = re.compile(r"\d[.,]\d{2}(?!\d)|(?<![\d.,])\d{1,3}(?:[.,]\d{3})+(?![\d.,]*\d)")

# (pattern, countries or None, description); a postal label counts when a code follows it directly
_POSTAL_LABELS = [
    (r"pin\s*code|pincode|pin", {"IN"}, "PIN"),
    (r"poskod", {"MY"}, "Poskod"),
    (r"kode\s*pos|kodepos", {"ID"}, "Kode Pos"),
    (r"plz|postleitzahl", {"DE", "AT", "CH"}, "PLZ"),
    (r"c\.\s?p\.|cp", {"ES", "FR", "MX"}, "CP"),
    (r"code\s+postal", {"FR", "BE", "CH", "LU", "CA"}, "code postal"),
    (r"c[oó]digo\s+postal", {"ES", "PT", "MX"}, "código postal"),
    (r"cap", {"IT"}, "CAP"),
    (r"mã\s*bưu\s*(?:chính|điện)|ma\s*buu\s*(?:chinh|dien)", {"VN"}, "Mã bưu chính"),
    (r"kod\s*pocztowy", {"PL"}, "kod pocztowy"),
    (r"eircode", {"IE"}, "Eircode"),
    (r"post\s*code|postcode|postal\s*code|zip(?:\s*code)?", None, "postcode"),
]
_POSTAL_LABEL_RES = [(re.compile(_lab(p) + r"\s*[:.\-#]?\s*", re.I), cc, d) for p, cc, d in _POSTAL_LABELS]
_THAI_POSTAL_LABEL = re.compile(r"รหัสไปรษณีย์\s*[:.]?\s*")

_HEADER_WORDS = re.compile(
    _lab(r"tax invoice|invoice|receipt|cash bill|cashier|kasir|table|order|struk|hoá đơn|hóa đơn|rechnung|"
         r"kassenbon|facture|factura|ticket|paragon|server|date|time|tarikh|tanggal|ngày|datum|subtotal|total|"
         r"qty|item") + r"|ใบเสร็จ|ใบกำกับภาษี", re.I)

_STREET = re.compile(
    _lab(r"jalan|jl|jln|lorong|lrg|taman|tmn|persiaran|lebuh|lebuhraya|road|rd|street|st|avenue|ave|av|"
         r"boulevard|blvd|lane|ln|drive|dr|way|place|pl|court|ct|crescent|cres|highway|hwy|parkway|pkwy|square|sq|"
         r"terrace|close|suite|ste|floor|fl|level|lvl|block|blk|unit|lot|shop|kiosk|plaza|mall|arcade|centre|"
         r"center|complex|tower|building|bldg|soi|thanon|đường|phố|phường|quận|huyện|tầng|ngõ|ngách|rue|bd|"
         r"chemin|allée|impasse|quai|straße|strasse|str|weg|platz|allee|gasse|calle|avda|avenida|paseo|carrer|"
         r"via|viale|piazza|corso|largo|ul|ulica|al|aleja|plac|osiedle|rua|travessa|praça|laan|straat|plein|"
         r"gracht|kade|singel|dijk|gade|vej|gata|gatan|gate|veien|nagar|marg|chowk|sector|colony|layout|gali|"
         r"bazaar|bazar|gang|komplek|ruko|kav|kavling|kel|kec|kelurahan|kecamatan|kabupaten|kab|kota|desa|"
         r"banjar|br|rt|rw|cedex") +
    r"|\w+(?:straße|strasse|str\.|straat|weg|plein|gracht|kade|laan|gade|vej|gata|gatan|veien|allee|platz|gasse)"
    r"(?!" + _L + r")|#\d{1,3}-\d{1,4}|ถนน|ถ\.|ซอย|ซ\.|แขวง|เขต|ตำบล|ต\.|อำเภอ|อ\.|จังหวัด|จ\.|หมู่|(?<!\w)c/\s?\w",
    re.I)

# ---------------------------------------------------------------- postal candidates

_DIGIT_BEFORE = r"(?<![\d.,/])(?<!\d-)"
_CANDIDATE_PATTERNS = [
    ("jp", re.compile(r"〒\s?(\d{3})-?(\d{4})(?!\d)")),
    ("pref", re.compile(r"(?<![A-Za-z])(CH|DK|NO|A|D|F|B|I|L)-\s?(\d{4,5})(?!\d)")),
    ("sg", re.compile(r"(?<![A-Za-z])S\s?\(?(\d{6})\)?(?!\d)")),
    ("ca", re.compile(r"(?<![A-Za-z0-9])([ABCEGHJ-NPRSTVXY]\d[ABCEGHJ-NPRSTV-Z])\s?(\d[ABCEGHJ-NPRSTV-Z]\d)"
                      r"(?![A-Za-z0-9])")),
    ("uk", re.compile(r"(?<![A-Za-z0-9])([A-PR-UWYZ][A-HK-Y]?\d[A-Z\d]?)\s?(\d[ABD-HJLNP-UW-Z]{2})(?![A-Za-z0-9])")),
    ("ie", re.compile(r"(?<![A-Za-z0-9])([AC-FHKNPRTV-Y]\d{2}|D6W)\s?([0-9AC-FHKNPRTV-Y]{4})(?![A-Za-z0-9])")),
    ("nl", re.compile(r"(?<![\w.,/-])([1-9]\d{3})\s?(?!SA|SD|SS)([A-Z]{2})(?![A-Za-z0-9])")),
    ("us", re.compile(r"(?<![A-Za-z])([A-Z]{2})\s+(\d{5})(?:-(\d{4}))?(?![\d\-])")),
    ("au", re.compile(r"(?<![A-Za-z])(NSW|VIC|QLD|WA|SA|TAS|ACT|NT)\s+(\d{4})(?!\d)")),
    ("zip4", re.compile(r"(?<![\d\-])(\d{5})-(\d{4})(?![\d\-])")),
    ("pt", re.compile(r"(?<![\d\-])(\d{4})-(\d{3})(?![\d\-])")),
    ("pl", re.compile(r"(?<![\d\-])(\d{2})-(\d{3})(?![\d\-])")),
    ("d6s", re.compile(_DIGIT_BEFORE + r"([1-9]\d{2})\s(\d{3})(?![\d]|[.,/:]\d|-\d)")),
    ("d6", re.compile(_DIGIT_BEFORE + r"(\d{6})(?![\d]|[.,/:]\d|-\d)")),
    ("d5", re.compile(_DIGIT_BEFORE + r"(\d{5})(?![\d]|[.,/:]\d|-\d)")),
    ("d4", re.compile(_DIGIT_BEFORE + r"(\d{4})(?![\d]|[.,/:]\d|-\d)")),
]
_PREF_CC = {"CH": ("CH", 4), "DK": ("DK", 4), "NO": ("NO", 4), "A": ("AT", 4), "D": ("DE", 5), "F": ("FR", 5),
            "B": ("BE", 4), "I": ("IT", 5), "L": ("LU", 4)}
_KINDS = {
    "IN": {"d6", "d6s"}, "SG": {"d6", "sg"}, "VN": {"d6", "d5"}, "CN": {"d6"}, "RU": {"d6"},
    "US": {"d5", "us", "zip4"}, "CA": {"ca"}, "GB": {"uk"}, "IE": {"ie"}, "NL": {"nl"}, "PL": {"pl"},
    "PT": {"pt"}, "JP": {"jp"}, "AU": {"d4", "au"},
}
for _cc in ("MY", "TH", "ID", "MX", "KR", "TR", "FI", "ES"):
    _KINDS[_cc] = {"d5"}
for _cc in ("DE", "FR", "IT"):
    _KINDS[_cc] = {"d5", "pref"}
for _cc in ("BE", "AT", "CH", "DK", "NO", "LU"):
    _KINDS[_cc] = {"d4", "pref"}
_NL_DIRECTIONS = {"NE", "NW", "SE", "SW"}


def _valid_for(cc: str, cand: dict) -> bool:
    kind, code = cand["kind"], cand["code"]
    if kind not in _KINDS.get(cc, set()):
        return False
    if kind == "pref":
        return cand["format_cc"] == {cc}
    if kind in ("us", "au") and cand["format_cc"] != {cc}:
        return False
    digits = re.sub(r"\D", "", code)
    if cc == "SG":
        return 1 <= int(digits[:2]) <= 82
    if cc in ("IN", "TH", "ID", "VN"):
        return digits[0] != "0"
    if cc in ("MY", "DE", "FR"):
        return int(digits) >= 1000
    if cc == "ES":
        return 1 <= int(digits[:2]) <= 52
    if cc == "US":
        return digits[:5] != "00000"
    return True


def _candidates(text: str, masked: str, line_idx: int) -> list:
    """Postal-code-shaped tokens in a masked line, longest/most specific patterns first."""
    taken = []
    out = []
    for kind, rx in _CANDIDATE_PATTERNS:
        for m in rx.finditer(masked):
            span = (m.start(), m.end())
            if any(a < span[1] and span[0] < b for a, b in taken):
                continue
            g = m.groups()
            fmt, region = None, None
            if kind == "jp":
                code, fmt = f"{g[0]}-{g[1]}", {"JP"}
            elif kind == "pref":
                cc, length = _PREF_CC[g[0]]
                if len(g[1]) != length:
                    continue
                code, fmt = g[1], {cc}
            elif kind == "sg":
                code, fmt = g[0], {"SG"}
            elif kind == "ca":
                code, fmt = f"{g[0]} {g[1]}", {"CA"}
            elif kind == "uk":
                code, fmt = f"{g[0]} {g[1]}", {"GB"}
            elif kind == "ie":
                code = f"{g[0]} {g[1]}"
                if re.search(r"[A-Z]", g[1]) and re.search(r"\d", g[1]):
                    fmt = {"IE"}
            elif kind == "nl":
                code = f"{g[0]} {g[1]}"
                rest = masked[m.end():].strip()
                if g[1] not in _NL_DIRECTIONS and (not rest or rest[0] == "," or re.match(r"[A-Z][a-z]|[A-Z]{3}", rest)):
                    fmt = {"NL"}
            elif kind == "us":
                if g[0] not in _US_STATES:
                    continue
                code, fmt, region = g[1] + (f"-{g[2]}" if g[2] else ""), {"US"}, g[0]
                span = (m.start(2), m.end())
            elif kind == "au":
                code, fmt, region = g[1], {"AU"}, g[0]
                span = (m.start(2), m.end())
            elif kind == "zip4":
                code = f"{g[0]}-{g[1]}"
            elif kind in ("pt", "pl"):
                code = f"{g[0]}-{g[1]}"
            else:
                code = "".join(g)
            taken.append((m.start(), m.end()))
            out.append({"code": code, "kind": kind, "line": line_idx, "start": span[0], "end": span[1],
                        "format_cc": fmt, "region": region, "label": None})
    out.sort(key=lambda c: c["start"])
    return out


# ---------------------------------------------------------------- per-line analysis

def _analyse(idx: int, raw: str) -> dict:
    text = re.sub(r"[ \t]+", " ", normalise(raw)).strip()
    chars = list(text)
    evidence = []  # (countries set, strength, description)
    protected = []
    cut = len(text)  # where the address part of the line ends (phone/email/tax tail removed)

    # postal labels first, so "Kode Pos 80361" is not masked as an ID number
    labels = []
    for rx, cc, desc in _POSTAL_LABEL_RES:
        for m in rx.finditer(text):
            labels.append((m.end(), cc, desc))
    for m in _THAI_POSTAL_LABEL.finditer(text):
        labels.append((m.end(), {"TH"}, "รหัสไปรษณีย์"))
    for end, _cc, _d in labels:
        m = re.match(r"[A-Z0-9][A-Z0-9 \-()]{2,8}", text[end:])
        if m:
            protected.append((end, end + len(m.group(0).rstrip())))
    for kind, rx in _CANDIDATE_PATTERNS[:2]:  # 〒 and CH-/DK-/D- prefixed codes
        for m in rx.finditer(text):
            protected.append((m.start(), m.end()))

    # tax IDs: evidence, then mask to end of line
    for rx, cc, desc in _TAX_RES:
        m = rx.search(text)
        if not m:
            continue
        if cc:
            evidence.append((set(cc), "strong", f"tax ID label '{desc}'"))
        pm = _VAT_PREFIX.match(text, m.end())
        if pm and cc is None:
            pcc = _VAT_PREFIX_CC.get(pm.group(1), pm.group(1))
            evidence.append(({pcc}, "strong", f"VAT number prefix '{pm.group(1)}'"))
        _mask(chars, m.start(), len(text), protected)
        cut = min(cut, m.start())
    if _CA_BN.search(text):
        m = _CA_BN.search(text)
        evidence.append(({"CA"}, "strong", "business number 'RT' style"))
        _mask(chars, m.start(), m.end(), protected)
        cut = min(cut, m.start())

    # phone numbers: labelled and unlabelled; "+cc" prefixes are evidence
    phone_spans = []
    for m in _PHONE_LABEL.finditer(text):
        cut = min(cut, m.start())
        pm = _PHONE_AFTER_LABEL.match(text, m.end())
        if pm:
            phone_spans.append((m.start(), pm.end()))
    for rx in _PHONE_PATTERNS:
        for m in rx.finditer(text):
            if len(re.sub(r"\D", "", m.group(0))) >= 8:
                phone_spans.append((m.start(), m.end()))
    for a, b in phone_spans:
        _mask(chars, a, b, protected)
    for m in re.finditer(r"(?<![\w+])\+\s?\(?(\d[\d\s\-()]{6,}\d)", text):
        digits = re.sub(r"\D", "", m.group(1))
        for n in (3, 2, 1):
            if digits[:n] in _PHONE_CC:
                evidence.append((set(_PHONE_CC[digits[:n]]), "strong", f"phone prefix +{digits[:n]}"))
                break
        cut = min(cut, m.start())

    em = _EMAIL_WEB.search(text)
    if em:
        cut = min(cut, em.start())
        _mask(chars, em.start(), em.end(), protected)

    for rx in _CARD + _DATE_TIME + _AMOUNTS:
        for m in rx.finditer("".join(chars)):
            _mask(chars, m.start(), m.end(), protected)
    for m in _ID_LABEL.finditer("".join(chars)):
        _mask(chars, m.start(), m.end(), protected)
    for m in re.finditer(r"\(\d+-[A-Z]\)", "".join(chars)):  # Malaysian company number "(123456-X)"
        _mask(chars, m.start(), m.end(), protected)
    masked = "".join(chars)

    has_amount = bool(_HAS_AMOUNT.search(text))
    has_date = any(rx.search(text) for rx in _DATE_TIME)
    names = [] if has_amount else _find_names(masked)
    cands = _candidates(text, masked, idx)

    for end, cc, desc in labels:
        for c in cands:
            if end <= c["start"] <= end + 2:
                if cc and not any(c["kind"] in _KINDS.get(k, ()) for k in cc):
                    break  # "PIN 1234" on a card slip is not an Indian PIN code
                c["label"] = desc
                if cc:
                    evidence.append((set(cc), "strong", f"postal label '{desc}'"))
                break
    for c in cands:
        if c["region"]:
            evidence.append((set(c["format_cc"]), "strong", f"state code '{c['region']}' before postcode"))
        elif c["format_cc"]:
            evidence.append((set(c["format_cc"]), "strong", f"postal format '{c['code']}'"))
    for cc, lvl, canon in names:
        strength = "weak" if lvl == "city" else "strong"
        evidence.append(({cc}, strength, f"{'country' if lvl == 'country' else lvl} name '{canon}'"))
    if re.search(r"(?<!" + _L + r")cedex(?!" + _L + r")", text, re.I):
        evidence.append(({"FR"}, "strong", "word 'Cedex'"))

    # Canadian province codes: next to a Canadian postal code, or after a comma ("Montréal, QC")
    prov = None
    for m in re.finditer(r"(?<![A-Za-z])(ON|QC|BC|AB|MB|SK|NS|NB|NL|PE|YT|NT|NU)(?![A-Za-z])", masked):
        before = masked[:m.start()].rstrip()
        near_ca = any(c["kind"] == "ca" and 0 <= c["start"] - m.end() <= 3 for c in cands)
        if near_ca or before.endswith(","):
            ccs = {"CA", "NL"} if m.group(1) == "NL" and not near_ca else {"CA"}
            evidence.append((ccs, "strong", f"province code '{m.group(1)}'"))
            prov = _CA_PROV[m.group(1)]
            break

    address_part = text[:cut]
    street = bool(_STREET.search(address_part))
    header = bool(_HEADER_WORDS.search(text))
    excluded = cut == 0 or has_amount or has_date or header or not address_part.strip()
    clean = re.sub(r"\s+", " ", address_part).strip(" ,;:|-")
    return {"idx": idx, "text": text, "clean": clean, "masked": masked, "evidence": evidence, "names": names,
            "cands": cands, "street": street, "excluded": excluded, "has_amount": has_amount, "province": prov}


# ---------------------------------------------------------------- country resolution

def _resolve(items: list, cands: list) -> tuple:
    """items: [(countries, strength, desc)]. Returns (cc or None, decisive descriptions, notes)."""
    notes = []
    strong = [it for it in items if it[1] == "strong"]
    weak = [it for it in items if it[1] == "weak"]
    pool = strong or weak
    if not pool:
        return None, [], ["no country evidence (digits alone are ambiguous)"]
    current = set(pool[0][0])
    for it in pool[1:]:
        current &= it[0]
    if not current:
        groups = {}
        for it in pool:
            groups.setdefault("/".join(sorted(it[0])), []).append(it[2])
        detail = "; ".join(f"{k}: {', '.join(v)}" for k, v in sorted(groups.items()))
        return None, [], [f"conflicting country evidence -> country left empty ({detail})"]
    if strong and weak:
        narrowed = set(current)
        for it in weak:
            if narrowed & it[0]:
                narrowed &= it[0]
            else:
                notes.append(f"ignored {it[2]} (disagrees with stronger evidence)")
        current = narrowed
    if len(current) > 1:
        fitting = {cc for cc in current if any(_valid_for(cc, c) for c in cands)}
        if len(fitting) == 1:
            cc = fitting.pop()
            notes.append(f"narrowed {'/'.join(sorted(current))} to {cc} by postal-code format")
            current = {cc}
        else:
            return None, [], notes + [f"country ambiguous between {', '.join(sorted(current))}"]
    cc = next(iter(current))
    decisive = []
    for it in items:
        if cc in it[0] and it[2] not in decisive:
            decisive.append(it[2])
    return cc, decisive, notes


# ---------------------------------------------------------------- public API

def find_address(lines: list[str], country_hint: str | None = None) -> dict:
    """Find the address block, postal code and country of a receipt. See module docstring."""
    rows = [_analyse(i, ln) for i, ln in enumerate(lines or [])]
    result = {"lines": [], "postal_code": None, "country": None, "country_evidence": "", "region": None,
              "confidence": 0.0, "notes": []}
    if not rows:
        result["notes"].append("no lines")
        return result

    # address-like lines: street words or a postcode (seed), or a place name (continuation)
    def is_seed(r):
        if r["excluded"]:
            return False
        if r["idx"] == 0 and len(rows) > 2 and not re.search(r"\d", r["clean"]):
            return False  # the first line is usually the merchant name
        good = [c for c in r["cands"] if c["kind"] != "d4" or r["names"]]
        return r["street"] or (bool(good) and (bool(r["names"]) or bool(re.search(r"[^\W\d_]", r["clean"]))))

    def is_cont(r):
        return not r["excluded"] and (is_seed(r) or bool(r["names"]))

    blocks = []
    used = set()
    for r in rows:
        if r["idx"] in used or not is_seed(r):
            continue
        start = end = r["idx"]
        while start - 1 >= 0 and start - 1 not in used and is_seed(rows[start - 1]) and end - start < 5:
            start -= 1
        while end + 1 < len(rows) and is_cont(rows[end + 1]) and end - start < 5:
            end += 1
        used.update(range(start, end + 1))
        blk = rows[start:end + 1]
        score = (3 * any(b["cands"] for b in blk) + 2 * any(b["names"] for b in blk) +
                 any(b["street"] for b in blk))
        blocks.append((score, -start, blk))
    block = max(blocks, key=lambda b: (b[0], b[1]))[2] if blocks else []
    block_idx = {b["idx"] for b in block}
    result["lines"] = [b["clean"] for b in block if b["clean"]]

    # country evidence from every line (names only from lines without amounts, handled in _analyse)
    items = []
    if country_hint:
        items.append(({country_hint.strip().upper()}, "strong", f"country_hint '{country_hint.strip().upper()}'"))
    for r in rows:
        for ev in r["evidence"]:
            # place names outside the address block are weak (could be a dish or a brand name)
            if r["idx"] not in block_idx and ev[2].split(" name ")[0] in ("country", "state", "city"):
                ev = (ev[0], "weak", ev[2])
            if r["idx"] not in block_idx and ev[2].startswith("postal format"):
                continue
            items.append(ev)
    all_cands = [c for r in rows if not r["excluded"] or r["idx"] in block_idx for c in r["cands"]]
    block_cands = [c for b in block for c in b["cands"]]
    cc, decisive, notes = _resolve(items, block_cands or all_cands)
    result["notes"].extend(notes)
    result["country"] = cc
    result["country_evidence"] = "; ".join(decisive)

    # postal code
    def rank(c):
        r = rows[c["line"]]
        return (c["line"] in block_idx, c["label"] is not None, bool(r["names"]), c["line"], c["start"])

    chosen = None
    if cc:
        pool = []
        for c in all_cands:
            r = rows[c["line"]]
            if not _valid_for(cc, c):
                continue
            if c["kind"] == "d4" and not any(n[0] == cc for n in r["names"]):
                continue
            if c["line"] in block_idx or c["label"] or any(n[0] == cc for n in r["names"]):
                pool.append(c)
        if pool:
            chosen = max(pool, key=rank)
        elif block_cands:
            result["notes"].append(f"no valid {cc} postal code found")
    else:
        pool = [c for c in block_cands if c["kind"] not in ("d4",)]
        if pool:
            chosen = max(pool, key=lambda c: (c["label"] is not None, c["format_cc"] is not None, rank(c)))
    if chosen:
        result["postal_code"] = chosen["code"]

    # region
    region_name = None
    if cc:
        if chosen and chosen["region"]:
            region_name = chosen["region"]
        for want in ("state", "city"):
            if region_name:
                break
            for r in sorted(rows, key=lambda r: (r["idx"] not in block_idx, r["idx"])):
                hits = [n[2] for n in r["names"] if n[0] == cc and n[1] == want]
                if hits:
                    region_name = hits[0]
                    break
        if cc == "CA" and not region_name:
            region_name = next((r["province"] for r in rows if r["province"]), None)
        if cc == "CA":
            region_name = next((r["province"] for r in block if r["province"]), region_name)
    result["region"] = region_name

    # confidence
    conf = 0.0
    if cc:
        conf = 0.3
        named = any(any(n[0] == cc for n in b["names"]) for b in block) or (chosen is not None and chosen["region"])
        if chosen:
            conf += 0.3
        if chosen and named:
            conf += 0.25
        elif named:
            conf += 0.1
        kinds = {d.split(" ")[0] for d in decisive}
        conf += min(0.1, 0.05 * max(0, len(kinds) - 1))
        consistent = _consistency(cc, chosen["code"] if chosen else None, region_name, result["notes"])
        if consistent is True:
            conf += 0.05
        elif consistent is False:
            conf -= 0.25
    else:
        conf = 0.15 if chosen else (0.05 if result["lines"] else 0.0)
        if chosen:
            result["notes"].append("postal code found but country undetermined")
    result["confidence"] = round(max(0.0, min(conf, 0.98)), 2)
    return result


def _consistency(cc: str, code: str | None, region: str | None, notes: list):
    """True / False when the postcode can be checked against the region, None when it cannot."""
    if not code or not region:
        return None
    if cc == "CA":
        prov = {v: k for k, v in _CA_PROV.items()}.get(region)
        expect = _CA_LETTER.get(code[0])
        if code[0] == "X":
            ok = prov in ("NT", "NU")
        elif prov and expect:
            ok = expect == prov
        else:
            return None
        if not ok:
            notes.append(f"postal code {code} does not match province {region}")
        return ok
    if cc == "MY" and region in _MY_RANGES:
        head = int(code[:2])
        ok = any(a <= head <= b for a, b in _MY_RANGES[region])
        if not ok:
            notes.append(f"postcode {code} is outside the usual range for {region}")
        return ok
    return None


def main(argv: list | None = None) -> int:
    """Read receipt lines from a file (or stdin) and print the result as JSON."""
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file", nargs="?", help="text file, one OCR line per line (default: stdin)")
    ap.add_argument("--country", help="ISO 3166-1 alpha-2 hint")
    args = ap.parse_args(argv)
    text = open(args.file, encoding="utf-8").read() if args.file else sys.stdin.read()
    res = find_address(text.splitlines(), args.country)
    res["currency"] = currency_for_country(res["country"]) if res["country"] else None
    print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
