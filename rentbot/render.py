"""Turn database rows into message text."""
import json
from collections.abc import Mapping
from html import escape

from .districts import district_name
from .matching import parse_set
from .parser import format_phone
from .texts import t

DESC_LIMIT = 600


def format_price(listing: Mapping) -> str:
    amount, cur, usd = listing["price_amount"], listing["currency"], listing["price_usd"]
    if amount is None:
        return "—"
    if cur == "AMD":
        return f"{amount:,.0f} ֏ (≈ ${usd:,.0f})".replace(",", " ")
    return f"${amount:,.0f}".replace(",", " ")


def load_details(listing: Mapping) -> dict:
    try:
        return json.loads(listing["details"] or "{}")
    except (KeyError, IndexError, ValueError, TypeError):
        return {}


def format_card(listing: Mapping, lang: str) -> str:
    """A tidy card built from the parsed facts, not a copy of the original post."""
    d = load_details(listing)
    head = []
    if listing["rooms"]:
        head.append(t("card_rooms", lang, n=listing["rooms"]))
    if listing["district"]:
        head.append(district_name(listing["district"], lang))
    lines = [f"🏠 <b>{', '.join(head) or '—'}</b>", f"💰 <b>{format_price(listing)}</b>"]
    if d.get("address"):
        lines.append(f"📍 {escape(d['address'])}")
    facts = []
    if d.get("floor"):
        facts.append(t("card_floor", lang, v=f"{d['floor']}/{d['floors']}" if d.get("floors") else d["floor"]))
    if d.get("area"):
        facts.append(t("card_area", lang, v=d["area"]))
    if facts:
        lines.append("   ".join(facts))
    if "deposit" in d:
        lines.append(t("card_deposit_yes" if d["deposit"] else "card_deposit_no", lang))
    if listing["pets"] == 1:
        lines.append(t("card_pets_yes", lang))
    elif listing["pets"] == 0:
        lines.append(t("card_pets_no", lang))
    if "kids" in d:
        lines.append(t("card_kids_yes" if d["kids"] else "card_kids_no", lang))

    if listing["source"] == "bot":  # the owner's own words; imported posts are summarised above instead
        desc = (listing["description"] or "").strip()
        if desc:
            if len(desc) > DESC_LIMIT:
                desc = desc[:DESC_LIMIT].rstrip() + "…"
            lines += ["", f"<i>{escape(desc)}</i>"]
    lines.append("")
    if listing["phone"]:
        lines.append(f"📞 {format_phone(listing['phone'])}")
    if listing["source"] == "bot":
        lines.append(t("card_owner", lang))
    elif listing["agent"]:
        lines.append(t("card_agent_pct", lang, p=d["commission"]) if d.get("commission") else t("card_agent", lang))
    return "\n".join(lines).rstrip()


def _price_range(flt: Mapping, lang: str) -> str:
    lo, hi = flt["price_min"], flt["price_max"]
    if lo is None and hi is None:
        return t("any", lang)
    if lo is None:
        return t("upto", lang, v=f"{hi:.0f}")
    if hi is None:
        return t("from", lang, v=f"{lo:.0f}")
    return f"${lo:.0f}–{hi:.0f}"


def format_filter(flt: Mapping, lang: str) -> str:
    rooms = sorted(parse_set(flt["rooms"]))
    districts = sorted(parse_set(flt["districts"]))
    return t(
        "filter_title", lang,
        price=_price_range(flt, lang),
        rooms=", ".join("5+" if r == "5" else r for r in rooms) or t("any", lang),
        districts=", ".join(district_name(d, lang) for d in districts) or t("any", lang),
        pets=t("pets_need", lang) if flt["pets"] else t("any", lang),
    )
