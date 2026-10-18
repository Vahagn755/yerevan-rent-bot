"""Extract rental details (price, rooms, district, phone, pets) from free text.

Works with Armenian, Russian and English posts typical for Yerevan rental channels.
"""
import hashlib
import re
from dataclasses import dataclass

from .districts import DISTRICTS

USD_RANGE = (50, 20_000)
AMD_RANGE = (20_000, 10_000_000)

# 450 | 1450 | 200 000 | 200,000 | 200.000  (separators only between groups of 3 digits)
NUM = r"(\d{1,3}(?:[  .,]\d{3})+|\d+)"
MULT = r"(?:\s?(k|к|тыс\.?|հազ(?:ար)?\.?))?"
USD_WORDS = r"(?:\$|usd|долл\w*|դոլար\w*|dollars?|у\.?\s?е\.?)"
AMD_WORDS = r"(?:֏|amd|драм\w*|դրամ\w*|dram)"

_USD_BEFORE = re.compile(r"\$\s?" + NUM + MULT)
_USD_AFTER = re.compile(NUM + MULT + r"\s?" + USD_WORDS)
_AMD = re.compile(NUM + MULT + r"\s?" + AMD_WORDS)
_NUM = re.compile(r"(?<!\d)" + NUM)
_AMD_HINT = re.compile(AMD_WORDS)
_MULT_HINT = re.compile(r"\d\s?(?:k|к|тыс|հազ)")

_PHONE = re.compile(
    r"(?:\+?\s?374|(?<!\d)0)[\s\-()]*(\d{2})[\s\-()]*(\d{2})[\s\-]*(\d{2})[\s\-]*(\d{2})(?!\d)"
)

_ROOMS = re.compile(
    r"(?<!\d)([1-9])\s?-?\s?(?:х\s?|x\s?)?"
    r"(?:սենյակ|սեն\.|комн|к\.?\s?кв|bedroom|room|br\b|bed\b)"
)
_ROOM_WORDS = {
    "однокомн": 1, "однушк": 1, "студи": 1, "studio": 1, "մեկսենյակ": 1,
    "двухкомн": 2, "двушк": 2, "երկսենյակ": 2,
    "трехкомн": 3, "трёхкомн": 3, "трешк": 3, "трёшк": 3, "եռասենյակ": 3, "երեքսենյակ": 3,
    "четырехкомн": 4, "четырёхкомн": 4, "քառասենյակ": 4, "չորսսենյակ": 4,
}

_PETS_NO = ["без живот", "животных нельзя", "животные нельзя", "no pets", "առանց կենդանի",
            "կենդանիներ չի", "կենդանիներ արգել", "կենդանի չի"]
_PETS_YES = ["можно с живот", "с животными можно", "животные разрешен", "животные можно",
             "pets allowed", "pet friendly", "pet-friendly", "կենդանիներ թույլ", "կենդանի կարելի",
             "կենդանիներով"]

# posts that are not rental offers: people looking for a flat, or sales
_NOT_OFFER = ["сниму", "ищу квартир", "ищу жиль", "փնտրում եմ", "կվարձակալեմ", "looking for",
              "продается", "продаётся", "продам", "վաճառվում", "վաճառք", "for sale"]

_DISTRICT_RE = {
    key: re.compile(r"(?<!\w)(?:" + "|".join(d["aliases"]) + ")")
    for key, d in DISTRICTS.items()
}


@dataclass
class Price:
    amount: float
    currency: str  # "USD" | "AMD"
    usd: float


@dataclass
class ParsedListing:
    price: Price | None
    rooms: int | None
    district: str | None
    phone: str | None
    pets: int | None  # 1 allowed, 0 not allowed, None unknown


def to_number(raw: str) -> float:
    s = raw.strip().replace(" ", " ")
    if re.fullmatch(r"\d{1,3}(?:[ .,]\d{3})+", s):
        s = re.sub(r"[ .,]", "", s)
    return float(s.replace(" ", "").replace(",", "."))


def _apply_mult(n: float, mult: str | None) -> float:
    return n * 1000 if mult else n


def _valid(amount: float, currency: str) -> bool:
    lo, hi = USD_RANGE if currency == "USD" else AMD_RANGE
    return lo <= amount <= hi


def _make_price(amount: float, currency: str, amd_per_usd: float) -> Price | None:
    if not _valid(amount, currency):
        return None
    usd = amount if currency == "USD" else round(amount / amd_per_usd, 2)
    return Price(amount, currency, usd)


def parse_price(text: str, amd_per_usd: float) -> Price | None:
    """Price with an explicit currency marker ($, դրամ, драм ...)."""
    low = text.lower()
    candidates: list[tuple[int, float, str]] = []
    for rx, cur in ((_USD_BEFORE, "USD"), (_USD_AFTER, "USD"), (_AMD, "AMD")):
        for m in rx.finditer(low):
            candidates.append((m.start(), _apply_mult(to_number(m.group(1)), m.group(2)), cur))
    for _, amount, cur in sorted(candidates):
        price = _make_price(amount, cur, amd_per_usd)
        if price:
            return price
    return None


def parse_price_input(text: str, amd_per_usd: float) -> Price | None:
    """Price typed by a landlord; a bare number is USD if small, AMD if large."""
    price = parse_price(text, amd_per_usd)
    if price:
        return price
    m = _NUM.search(text.lower())
    if not m:
        return None
    n = _apply_mult(to_number(m.group(1)), _MULT_HINT.search(text.lower()))
    return _make_price(n, "USD" if n <= USD_RANGE[1] else "AMD", amd_per_usd)


ANY_WORDS = {"0", "-", "any", "любая", "любые", "ցանկացած", "ցանկացած գին"}


def parse_price_range(text: str, amd_per_usd: float) -> tuple[float | None, float | None] | None:
    """Filter range in USD. Returns (None, None) for "any", None if unreadable."""
    low = text.lower().strip()
    if low in ANY_WORDS:
        return (None, None)
    nums = [to_number(n) for n in _NUM.findall(low)]
    if not nums:
        return None
    if _MULT_HINT.search(low):
        nums = [n * 1000 for n in nums]
    is_amd = bool(_AMD_HINT.search(low)) or max(nums) > USD_RANGE[1]

    def conv(n: float) -> float:
        return round(n / amd_per_usd) if is_amd else n

    if len(nums) >= 2:
        lo, hi = sorted(nums[:2])
        return (conv(lo), conv(hi))
    upto = re.search(r"до|մինչև|up ?to|max|<", low)
    from_ = re.search(r"от|սկսած|from|min|>|-ից", low)
    if from_ and not upto:
        return (conv(nums[0]), None)
    return (None, conv(nums[0]))


def normalize_phone(text: str) -> str | None:
    m = _PHONE.search(text)
    return "374" + "".join(m.groups()) if m else None


def format_phone(phone: str | None) -> str:
    if not phone or len(phone) != 11:
        return phone or "—"
    return f"+374 {phone[3:5]} {phone[5:8]} {phone[8:]}"


def parse_rooms(text: str) -> int | None:
    low = text.lower()
    m = _ROOMS.search(low)
    if m:
        return int(m.group(1))
    for word, n in _ROOM_WORDS.items():
        if word in low:
            return n
    return None


def parse_district(text: str) -> str | None:
    low = text.lower()
    best: tuple[int, str] | None = None
    for key, rx in _DISTRICT_RE.items():
        m = rx.search(low)
        if m and (best is None or m.start() < best[0]):
            best = (m.start(), key)
    return best[1] if best else None


def parse_pets(text: str) -> int | None:
    low = text.lower()
    if any(w in low for w in _PETS_NO):
        return 0
    if any(w in low for w in _PETS_YES):
        return 1
    return None


def is_offer(text: str) -> bool:
    low = text.lower()
    return not any(w in low for w in _NOT_OFFER)


def parse_listing(text: str, amd_per_usd: float) -> ParsedListing | None:
    """Parse a channel post. Returns None if it does not look like a rental offer."""
    if not text or not is_offer(text):
        return None
    price = parse_price(text, amd_per_usd)
    rooms = parse_rooms(text)
    district = parse_district(text)
    if not price or (rooms is None and district is None):
        return None
    return ParsedListing(price, rooms, district, normalize_phone(text), parse_pets(text))


def text_hash(text: str) -> str:
    return hashlib.sha1(re.sub(r"\s+", " ", text.lower()).strip().encode()).hexdigest()
