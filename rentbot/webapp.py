"""Mini App: serves the web page and a small JSON API authenticated with Telegram initData."""
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
from .render import format_price
from .texts import LANGS, t
from .webauth import validate_init_data

log = logging.getLogger(__name__)

WEB_DIR = Path(__file__).parent / "web"
PAGE_SIZE = 30
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
        "description": row["description"],
        "phone": format_phone(row["phone"]) if row["phone"] else None,
        "phone_raw": row["phone"],
        "link": row["link"],
        "photo": bool(row["photo_id"]),
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
    scope = request.query.get("scope", "feed")
    try:
        before = int(request.query.get("before", "0")) or None
    except ValueError:
        before = None
    flt = await db.get_filter(user["id"]) if scope == "feed" else None
    items: list[dict] = []
    cursor = before
    # walk back through active listings until a page of matches is collected
    for _ in range(10):
        rows = await db.active_listings(limit=200, before_id=cursor)
        if not rows:
            break
        for row in rows:
            if flt is None or matches(flt, row):
                items.append(serialize(row, lang, user["id"]))
                if len(items) >= PAGE_SIZE:
                    break
        cursor = rows[-1]["id"]
        if len(items) >= PAGE_SIZE:
            break
    next_before = items[-1]["id"] if len(items) >= PAGE_SIZE else None
    return web.json_response({"items": items, "next": next_before})


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
                      description=description, phone=phone)
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
    cache: OrderedDict = request.app[PHOTOS]
    if listing_id in cache:
        cache.move_to_end(listing_id)
        body = cache[listing_id]
    else:
        listing = await request.app[DB].get_listing(listing_id)
        if not listing or not listing["photo_id"] or listing["status"] == "blocked":
            raise web.HTTPNotFound()
        buf = await request.app[BOT].download(listing["photo_id"])
        body = buf.getvalue()
        cache[listing_id] = body
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
