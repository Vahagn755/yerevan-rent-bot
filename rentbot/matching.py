"""Decide whether a listing matches a user's filter."""
from collections.abc import Mapping


def parse_set(value: str | None) -> set[str]:
    return {x for x in (value or "").split(",") if x}


def join_set(values: set[str]) -> str:
    return ",".join(sorted(values))


def matches(flt: Mapping, listing: Mapping) -> bool:
    price = listing["price_usd"]
    lo, hi = flt["price_min"], flt["price_max"]
    if lo is not None or hi is not None:
        if price is None:
            return False
        if lo is not None and price < lo:
            return False
        if hi is not None and price > hi:
            return False

    rooms = parse_set(flt["rooms"])
    if rooms:
        r = listing["rooms"]
        if r is None or str(min(int(r), 5)) not in rooms:
            return False

    districts = parse_set(flt["districts"])
    if districts and listing["district"] not in districts:
        return False

    if flt["pets"] and listing["pets"] != 1:
        return False
    return True
