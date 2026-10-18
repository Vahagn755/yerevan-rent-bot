import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
except ImportError:  # python-dotenv is optional
    def load_dotenv() -> bool:
        return False


@dataclass(frozen=True)
class Config:
    token: str
    admin_ids: frozenset[int]
    db_path: str
    amd_per_usd: float
    report_limit: int
    daily_post_limit: int
    allowed_channels: frozenset[int]


def _ids(value: str) -> frozenset[int]:
    return frozenset(int(x) for x in value.replace(" ", "").split(",") if x)


def load_config() -> Config:
    load_dotenv()
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("BOT_TOKEN is not set. Copy .env.example to .env and fill it in.")
    return Config(
        token=token,
        admin_ids=_ids(os.getenv("ADMIN_IDS", "")),
        db_path=os.getenv("DB_PATH", "data/bot.db"),
        amd_per_usd=float(os.getenv("AMD_PER_USD", "390")),
        report_limit=int(os.getenv("REPORT_LIMIT", "3")),
        daily_post_limit=int(os.getenv("DAILY_POST_LIMIT", "5")),
        allowed_channels=_ids(os.getenv("ALLOWED_CHANNELS", "")),
    )
