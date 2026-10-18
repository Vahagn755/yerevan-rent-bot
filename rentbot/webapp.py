"""Mini App: serves the web page and a small JSON API authenticated with Telegram initData."""
import hashlib
import logging
import time
from collections import OrderedDict
from collections.abc import Mapping
from pathlib import Path

from aiogram import Bot
from aiogram.types import BufferedInputFile
from aiohttp import web

from .actions import DESC_MAX, NewListing, precheck_listing, publish_listing, report_listing
from .config import Config
from .db import Database
from .districts import DISTRICTS, district_name
from .matching import join_set, matches, parse_set
from .parser import format_phone, normalize_phone, parse_price_input
from .render import format_price, load_details
from .texts import LANGS, t
from .webauth import validate_init_data

log = logging.getLogger(__name__)

WEB_DIR = Path(__file__).parent / "web"
PAGE_SIZE = 30
MAX_SCAN = 3000  # newest active listings considered for filtering and sorting
PHOTO_MAX = 10 * 1024 * 1024
PHOTO_CACHE_SIZE = 200

DB = web.AppKey("db", Database)
CFG = web.AppKey("cfg", Config)
BOT = web.AppKey("bot", Bot)
PHOTOS = web.AppKey("photos", OrderedDict)


_ERRORS = {400: web.HTTPBadRequest, 401: web.HTTPUnauthorized, 404: web.HTTPNotFound,
           409: web.HTTPConflict}


def ApiError(status: int, code: str) -> web.HTTPException:  # noqa: N802 - used like an exception class
    return _ERRORS[status](text=f'{{"error":"{code}"}}', content_type="application/json")


# ---------- helpers ----------
def listing_photos(row: Mapping) -> list[str]:
    photos = [p for p in (row["photos"] or "").split(",") if p]
    return photos or ([row["photo_id"]] if row["photo_id"] else [])


def serialize(row: Mapping, lang: str, viewer_id: int) -> dict:
    return {
        "id": row["id"],
        "source": row["source"],
        "district": row["district"],
        "district_name": district_name(row["district"], lang) if row["district"] else None,
        "rooms": row["rooms"],
        "price": format_price(row),
        "price_usd": row["price_usd"],
        "pets": row["pets"],
        "agent": bool(row["agent"]),
        "details": load_details(row),
        "description": row["description"],
        "phone": format_phone(row["phone"]) if row["phone"] else None,
        "phone_raw": row["phone"],
        "link": row["link"],
        "photo": bool(row["photo_id"]),
        # one URL per photo; the version part changes with the photo, so a stale browser cache never shows another listing's picture
        "photos": [f"/api/photo/{row['id']}?n={i}&v={hashlib.sha1(fid.encode()).hexdigest()[:10]}"
                   for i, fid in enumerate(listing_photos(row))],
        "created": row["created"],
        "status": row["status"],
        "mine": row["owner_id"] == viewer_id,
    }


def filter_json(flt: Mapping) -> dict:
    return {
        "price_min": flt["price_min"], "price_max": flt["price_max"],
        "rooms": sorted(int(x) for x in parse_set(flt["rooms"])),
        "districts": sorted(parse_set(flt["districts"])),
        "pets": bool(flt["pets"]),
    }


@web.middleware
async def auth_middleware(request: web.Request, handler):
    if request.path.startswith("/api/") and not request.path.startswith("/api/photo/"):
        header = request.headers.get("Authorization", "")
        init_data = header[4:] if header.startswith("tma ") else ""
        user = validate_init_data(init_data, request.app[CFG].token)
        if not user:
            raise ApiError(401, "unauthorized")
        lang, _ = await request.app[DB].ensure_user(user["id"], user.get("language_code"))
        request["user"] = user
        request["lang"] = lang
    return await handler(request)


async def _json(request: web.Request) -> dict:
    try:
        data = await request.json()
    except Exception:
        raise ApiError(400, "bad_json")
    if not isinstance(data, dict):
        raise ApiError(400, "bad_json")
    return data


# ---------- pages ----------
async def index(request: web.Request) -> web.FileResponse:
    return web.FileResponse(WEB_DIR / "index.html", headers={"Cache-Control": "no-cache"})


async def health(request: web.Request) -> web.Response:
    return web.json_response({"ok": True})


# ---------- api ----------
async def api_me(request: web.Request) -> web.Response:
    db, cfg, user, lang = request.app[DB], request.app[CFG], request["user"], request["lang"]
    flt = await db.get_filter(user["id"])
    return web.json_response({
        "user": {"id": user["id"], "first_name": user.get("first_name", "")},
        "lang": lang,
        "paused": await db.is_paused(user["id"]),
        "filter": filter_json(flt),
        "districts": [{"key": k, "name": district_name(k, lang),
                       "names": {code: district_name(k, code) for code in LANGS}} for k in DISTRICTS],
        "stats": await db.feed_stats(),
        "amd_per_usd": cfg.amd_per_usd,
        "daily_post_limit": cfg.daily_post_limit,
    })


async def api_settings(request: web.Request) -> web.Response:
    db, user = request.app[DB], request["user"]
    data = await _json(request)
    if data.get("lang") in LANGS:
        await db.set_lang(user["id"], data["lang"])
    if "paused" in data:
        await db.set_paused(user["id"], bool(data["paused"]))
    return web.json_response({"ok": True})


def _num(value) -> float | None:
    if value in (None, ""):
        return None
    try:
        n = float(value)
    except (TypeError, ValueError):
        raise ApiError(400, "bad_price")
    if n < 0 or n > 1_000_000:
        raise ApiError(400, "bad_price")
    return n or None


async def api_save_filter(request: web.Request) -> web.Response:
    db, user = request.app[DB], request["user"]
    data = await _json(request)
    lo, hi = _num(data.get("price_min")), _num(data.get("price_max"))
    if lo and hi and lo > hi:
        lo, hi = hi, lo
    rooms = {str(r) for r in data.get("rooms") or [] if str(r) in {"1", "2", "3", "4", "5"}}
    districts = {d for d in data.get("districts") or [] if d in DISTRICTS}
    flt = await db.update_filter(user["id"], price_min=lo, price_max=hi, rooms=join_set(rooms),
                                 districts=join_set(districts), pets=int(bool(data.get("pets"))))
    return web.json_response({"filter": filter_json(flt)})


async def api_listings(request: web.Request) -> web.Response:
    db, user, lang = request.app[DB], request["user"], request["lang"]
    if ids := request.query.get("ids"):
        wanted = [int(x) for x in ids.split(",") if x.isdigit()]
        rows = await db.listings_by_ids(wanted)
        return web.json_response({"items": [serialize(r, lang, user["id"]) for r in rows], "next": None})

    scope = request.query.get("scope", "feed")
    district = request.query.get("district")
    district = district if district in DISTRICTS else None
    sort = request.query.get("sort", "new")
    try:
        offset = max(0, int(request.query.get("offset", "0")))
    except ValueError:
        offset = 0
    flt = await db.get_filter(user["id"]) if scope == "feed" else None

    rows = [r for r in await db.active_listings(limit=MAX_SCAN)
            if (not district or r["district"] == district) and (flt is None or matches(flt, r))]
    if sort in ("cheap", "expensive"):
        priced = [r for r in rows if r["price_usd"] is not None]
        priced.sort(key=lambda r: r["price_usd"], reverse=sort == "expensive")
        rows = priced + [r for r in rows if r["price_usd"] is None]
    page = rows[offset:offset + PAGE_SIZE]
    nxt = offset + PAGE_SIZE if offset + PAGE_SIZE < len(rows) else None
    return web.json_response({"items": [serialize(r, lang, user["id"]) for r in page],
                              "total": len(rows), "next": nxt})


async def api_my(request: web.Request) -> web.Response:
    db, user, lang = request.app[DB], request["user"], request["lang"]
    rows = await db.user_listings(user["id"], limit=50)
    return web.json_response({"items": [serialize(r, lang, user["id"]) for r in rows]})


async def api_create(request: web.Request) -> web.Response:
    db, cfg, bot, user, lang = (request.app[DB], request.app[CFG], request.app[BOT],
                                request["user"], request["lang"])
    form = await request.post()
    district = str(form.get("district", ""))
    if district not in DISTRICTS:
        raise ApiError(400, "bad_district")
    try:
        rooms = int(form.get("rooms", 0))
    except ValueError:
        rooms = 0
    if not 1 <= rooms <= 5:
        raise ApiError(400, "bad_rooms")
    price = parse_price_input(f"{form.get('price', '')} {form.get('currency', '')}", cfg.amd_per_usd)
    if not price:
        raise ApiError(400, "bad_price")
    description = str(form.get("description", "")).strip()
    if len(description) > DESC_MAX:
        raise ApiError(400, "desc_long")
    phone = normalize_phone(str(form.get("phone", "")))
    if not phone:
        raise ApiError(400, "bad_phone")

    item = NewListing(district=district, rooms=rooms, price_amount=price.amount,
                      currency=price.currency, price_usd=price.usd,
                      pets=int(form.get("pets") in ("1", "true", "on")),
                      description=description, phone=phone, details=_form_details(form))
    if err := await precheck_listing(db, cfg, user["id"], item):
        raise ApiError(409, err)

    photo = form.get("photo")
    if isinstance(photo, web.FileField):
        content = photo.file.read(PHOTO_MAX + 1)
        if len(content) > PHOTO_MAX:
            raise ApiError(400, "photo_big")
        # Telegram stores the photo for us: send it to the owner as a confirmation and keep its file_id
        msg = await bot.send_photo(user["id"], BufferedInputFile(content, "listing.jpg"),
                                   caption=t("published", lang))
        item.photo_id = msg.photo[-1].file_id

    async def on_sent(n: int) -> None:
        await bot.send_message(user["id"], t("sent_to", lang, n=n))

    listing_id = await publish_listing(bot, db, user["id"], item, on_sent)
    row = await db.get_listing(listing_id)
    return web.json_response({"item": serialize(row, lang, user["id"])}, status=201)


def _small_int(value, lo: int, hi: int) -> int | None:
    try:
        n = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    return n if lo <= n <= hi else None


def _form_details(form) -> dict:
    d: dict = {}
    if floor := _small_int(form.get("floor"), 1, 40):
        d["floor"] = floor
        if (floors := _small_int(form.get("floors"), 1, 40)) and floors >= floor:
            d["floors"] = floors
    if area := _small_int(form.get("area"), 10, 1000):
        d["area"] = area
    if address := str(form.get("address", "")).strip()[:45]:
        d["address"] = address
    if form.get("deposit") in ("0", "1"):
        d["deposit"] = form.get("deposit") == "1"
    if form.get("kids") in ("0", "1"):
        d["kids"] = form.get("kids") == "1"
    return d


async def api_rented(request: web.Request) -> web.Response:
    db, user = request.app[DB], request["user"]
    listing = await db.get_listing(int(request.match_info["id"]))
    if not listing or listing["owner_id"] != user["id"]:
        raise ApiError(404, "not_found")
    await db.set_listing_status(listing["id"], "rented")
    return web.json_response({"ok": True})


async def api_report(request: web.Request) -> web.Response:
    data = await _json(request)
    kind = data.get("kind")
    if kind not in ("agent", "fake"):
        raise ApiError(400, "bad_kind")
    result = await report_listing(request.app[BOT], request.app[DB], request.app[CFG],
                                  int(request.match_info["id"]), request["user"]["id"], kind)
    return web.json_response({"result": result})


async def api_photo(request: web.Request) -> web.Response:
    listing_id = int(request.match_info["id"])
    try:
        n = int(request.query.get("n", "0"))
    except ValueError:
        n = 0
    listing = await request.app[DB].get_listing(listing_id)
    photos = listing_photos(listing) if listing and listing["status"] != "blocked" else []
    if not 0 <= n < len(photos):
        raise web.HTTPNotFound()
    file_id = photos[n]
    cache: OrderedDict = request.app[PHOTOS]
    if file_id in cache:
        cache.move_to_end(file_id)
        body = cache[file_id]
    else:
        buf = await request.app[BOT].download(file_id)
        body = buf.getvalue()
        cache[file_id] = body
        if len(cache) > PHOTO_CACHE_SIZE:
            cache.popitem(last=False)
    return web.Response(body=body, content_type="image/jpeg",
                        headers={"Cache-Control": "public, max-age=604800"})


def create_app(db: Database, cfg: Config, bot: Bot) -> web.Application:
    app = web.Application(middlewares=[auth_middleware], client_max_size=PHOTO_MAX + 1024 * 1024)
    app[DB], app[CFG], app[BOT], app[PHOTOS] = db, cfg, bot, OrderedDict()
    app.router.add_get("/", index)
    app.router.add_get("/health", health)
    app.router.add_get("/api/me", api_me)
    app.router.add_post("/api/settings", api_settings)
    app.router.add_post("/api/filter", api_save_filter)
    app.router.add_get("/api/listings", api_listings)
    app.router.add_post("/api/listings", api_create)
    app.router.add_get("/api/my", api_my)
    app.router.add_post(r"/api/listings/{id:\d+}/rented", api_rented)
    app.router.add_post(r"/api/listings/{id:\d+}/report", api_report)
    app.router.add_get(r"/api/photo/{id:\d+}", api_photo)
    return app


async def start_web(db: Database, cfg: Config, bot: Bot) -> web.AppRunner:
    runner = web.AppRunner(create_app(db, cfg, bot), access_log=None)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", cfg.web_port).start()
    log.info("Mini App server on port %s (%s)", cfg.web_port, cfg.webapp_url or "no public URL yet")
    return runner
