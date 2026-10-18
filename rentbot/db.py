"""SQLite storage (stdlib sqlite3, run in a worker thread so the bot never blocks)."""
import asyncio
import os
import sqlite3
import time
from typing import Any

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY,
    lang TEXT NOT NULL DEFAULT 'hy',
    paused INTEGER NOT NULL DEFAULT 0,
    blocked INTEGER NOT NULL DEFAULT 0,
    created INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS filters(
    user_id INTEGER PRIMARY KEY REFERENCES users(id),
    price_min REAL,
    price_max REAL,
    rooms TEXT NOT NULL DEFAULT '',
    districts TEXT NOT NULL DEFAULT '',
    pets INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS listings(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,              -- 'bot' | 'channel'
    owner_id INTEGER,
    district TEXT,
    rooms INTEGER,
    price_amount REAL,
    currency TEXT,
    price_usd REAL,
    pets INTEGER,
    agent INTEGER NOT NULL DEFAULT 0,
    description TEXT NOT NULL DEFAULT '',
    phone TEXT,
    photo_id TEXT,
    photos TEXT NOT NULL DEFAULT '',
    link TEXT,
    text_hash TEXT,
    status TEXT NOT NULL DEFAULT 'active',  -- active | rented | blocked | deleted
    created INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_listings_phone ON listings(phone);
CREATE INDEX IF NOT EXISTS idx_listings_hash ON listings(text_hash, created);
CREATE INDEX IF NOT EXISTS idx_listings_owner ON listings(owner_id, created);
CREATE TABLE IF NOT EXISTS reports(
    listing_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    kind TEXT NOT NULL,                -- 'agent' | 'fake'
    created INTEGER NOT NULL,
    PRIMARY KEY(listing_id, user_id)
);
CREATE TABLE IF NOT EXISTS blacklist(
    phone TEXT PRIMARY KEY,
    reason TEXT,
    created INTEGER NOT NULL
);
"""

LISTING_FIELDS = ("source", "owner_id", "district", "rooms", "price_amount", "currency",
                  "price_usd", "pets", "agent", "description", "phone", "photo_id", "photos", "link", "text_hash")


def _lang_from_code(code: str | None) -> str:
    code = (code or "").lower()
    if code.startswith("ru"):
        return "ru"
    if code.startswith("en"):
        return "en"
    return "hy"


class Database:
    def __init__(self, path: str):
        self.path = path
        self._conn: sqlite3.Connection | None = None
        self._lock = asyncio.Lock()

    # ---------- plumbing ----------
    async def connect(self) -> None:
        if self.path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        cols = {r["name"] for r in self._conn.execute("PRAGMA table_info(listings)")}
        if "agent" not in cols:  # databases created before these columns existed
            self._conn.execute("ALTER TABLE listings ADD COLUMN agent INTEGER NOT NULL DEFAULT 0")
        if "photos" not in cols:
            self._conn.execute("ALTER TABLE listings ADD COLUMN photos TEXT NOT NULL DEFAULT ''")
        self._conn.commit()

    async def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def _run(self, sql: str, params: tuple, mode: str) -> Any:
        cur = self._conn.execute(sql, params)
        if mode == "one":
            return cur.fetchone()
        if mode == "all":
            return cur.fetchall()
        self._conn.commit()
        return cur

    async def _q(self, sql: str, params: tuple = (), mode: str = "exec") -> Any:
        async with self._lock:
            return await asyncio.to_thread(self._run, sql, params, mode)

    async def one(self, sql: str, params: tuple = ()) -> sqlite3.Row | None:
        return await self._q(sql, params, "one")

    async def all(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        return await self._q(sql, params, "all")

    async def exec(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return await self._q(sql, params, "exec")

    # ---------- users ----------
    async def ensure_user(self, user_id: int, language_code: str | None) -> tuple[str, bool]:
        """Returns (lang, is_new). Un-blocks a user who comes back."""
        row = await self.one("SELECT lang, blocked FROM users WHERE id=?", (user_id,))
        if row:
            if row["blocked"]:
                await self.exec("UPDATE users SET blocked=0 WHERE id=?", (user_id,))
            return row["lang"], False
        lang = _lang_from_code(language_code)
        await self.exec("INSERT OR IGNORE INTO users(id, lang, created) VALUES(?,?,?)",
                        (user_id, lang, int(time.time())))
        return lang, True

    async def set_lang(self, user_id: int, lang: str) -> None:
        await self.exec("UPDATE users SET lang=? WHERE id=?", (lang, user_id))

    async def set_paused(self, user_id: int, paused: bool) -> None:
        await self.exec("UPDATE users SET paused=? WHERE id=?", (int(paused), user_id))

    async def is_paused(self, user_id: int) -> bool:
        row = await self.one("SELECT paused FROM users WHERE id=?", (user_id,))
        return bool(row and row["paused"])

    async def mark_blocked(self, user_id: int) -> None:
        await self.exec("UPDATE users SET blocked=1 WHERE id=?", (user_id,))

    # ---------- filters ----------
    async def get_filter(self, user_id: int) -> sqlite3.Row:
        await self.exec("INSERT OR IGNORE INTO filters(user_id) VALUES(?)", (user_id,))
        return await self.one("SELECT * FROM filters WHERE user_id=?", (user_id,))

    async def update_filter(self, user_id: int, **fields: Any) -> sqlite3.Row:
        allowed = {"price_min", "price_max", "rooms", "districts", "pets"}
        await self.get_filter(user_id)
        for key, value in fields.items():
            if key not in allowed:
                raise ValueError(key)
            await self.exec(f"UPDATE filters SET {key}=? WHERE user_id=?", (value, user_id))
        return await self.get_filter(user_id)

    async def subscribers(self) -> list[sqlite3.Row]:
        return await self.all(
            "SELECT u.id AS user_id, u.lang, f.price_min, f.price_max, f.rooms, f.districts, f.pets "
            "FROM users u JOIN filters f ON f.user_id=u.id WHERE u.paused=0 AND u.blocked=0"
        )

    # ---------- listings ----------
    async def add_listing(self, **fields: Any) -> int:
        cols = [k for k in LISTING_FIELDS if k in fields]
        sql = (f"INSERT INTO listings({','.join(cols)}, created) "
               f"VALUES({','.join('?' * len(cols))}, ?)")
        cur = await self.exec(sql, tuple(fields[k] for k in cols) + (int(time.time()),))
        return cur.lastrowid

    async def get_listing(self, listing_id: int) -> sqlite3.Row | None:
        return await self.one("SELECT * FROM listings WHERE id=?", (listing_id,))

    async def set_listing_status(self, listing_id: int, status: str) -> None:
        await self.exec("UPDATE listings SET status=? WHERE id=?", (status, listing_id))

    async def active_listings(self, limit: int = 300, before_id: int | None = None) -> list[sqlite3.Row]:
        if before_id:
            return await self.all(
                "SELECT * FROM listings WHERE status='active' AND id<? ORDER BY id DESC LIMIT ?",
                (before_id, limit))
        return await self.all("SELECT * FROM listings WHERE status='active' ORDER BY id DESC LIMIT ?",
                              (limit,))

    async def listings_by_ids(self, ids: list[int]) -> list[sqlite3.Row]:
        ids = ids[:100]
        if not ids:
            return []
        marks = ",".join("?" * len(ids))
        return await self.all(
            f"SELECT * FROM listings WHERE status='active' AND id IN ({marks}) ORDER BY id DESC", tuple(ids))

    async def feed_stats(self) -> dict[str, int]:
        day_ago = int(time.time()) - 86400
        row = await self.one(
            "SELECT COUNT(*) AS active, SUM(CASE WHEN created>=? THEN 1 ELSE 0 END) AS today "
            "FROM listings WHERE status='active'", (day_ago,))
        return {"active": row["active"] or 0, "today": row["today"] or 0}

    async def user_listings(self, user_id: int, limit: int = 10) -> list[sqlite3.Row]:
        return await self.all(
            "SELECT * FROM listings WHERE owner_id=? AND status='active' ORDER BY id DESC LIMIT ?",
            (user_id, limit))

    async def count_user_listings_since(self, user_id: int, since: int) -> int:
        row = await self.one("SELECT COUNT(*) AS n FROM listings WHERE owner_id=? AND created>=?",
                             (user_id, since))
        return row["n"]

    async def is_duplicate(self, text_hash: str, since: int) -> bool:
        row = await self.one(
            "SELECT 1 FROM listings WHERE text_hash=? AND created>=? AND status!='deleted' LIMIT 1",
            (text_hash, since))
        return row is not None

    # ---------- reports & blacklist ----------
    async def add_report(self, listing_id: int, user_id: int, kind: str) -> bool:
        cur = await self.exec(
            "INSERT OR IGNORE INTO reports(listing_id, user_id, kind, created) VALUES(?,?,?,?)",
            (listing_id, user_id, kind, int(time.time())))
        return cur.rowcount == 1

    async def report_count(self, listing: sqlite3.Row) -> int:
        """Distinct reporters; for a phone number, counted across all its listings."""
        if listing["phone"]:
            row = await self.one(
                "SELECT COUNT(DISTINCT r.user_id) AS n FROM reports r "
                "JOIN listings l ON l.id=r.listing_id WHERE l.phone=?", (listing["phone"],))
        else:
            row = await self.one("SELECT COUNT(*) AS n FROM reports WHERE listing_id=?",
                                 (listing["id"],))
        return row["n"]

    async def blacklist_phone(self, phone: str, reason: str) -> None:
        await self.exec("INSERT OR REPLACE INTO blacklist(phone, reason, created) VALUES(?,?,?)",
                        (phone, reason, int(time.time())))
        await self.exec("UPDATE listings SET status='blocked' WHERE phone=? AND status='active'",
                        (phone,))

    async def unblacklist_phone(self, phone: str) -> None:
        await self.exec("DELETE FROM blacklist WHERE phone=?", (phone,))

    async def is_blacklisted(self, phone: str | None) -> bool:
        if not phone:
            return False
        return await self.one("SELECT 1 FROM blacklist WHERE phone=?", (phone,)) is not None

    # ---------- admin ----------
    async def stats(self) -> dict[str, int]:
        day_ago = int(time.time()) - 86400
        q = {
            "users": "SELECT COUNT(*) AS n FROM users",
            "subscribers": "SELECT COUNT(*) AS n FROM users u JOIN filters f ON f.user_id=u.id "
                           "WHERE u.paused=0 AND u.blocked=0",
            "active_listings": "SELECT COUNT(*) AS n FROM listings WHERE status='active'",
            "blacklist": "SELECT COUNT(*) AS n FROM blacklist",
        }
        out = {k: (await self.one(sql))["n"] for k, sql in q.items()}
        out["listings_24h"] = (await self.one(
            "SELECT COUNT(*) AS n FROM listings WHERE created>=?", (day_ago,)))["n"]
        return out
