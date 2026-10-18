"""Validate Telegram Mini App initData (https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app)."""
import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

MAX_AGE = 24 * 3600


def validate_init_data(init_data: str, bot_token: str, max_age: int = MAX_AGE,
                       now: float | None = None) -> dict | None:
    """Returns the Telegram user dict if initData is authentic and fresh, otherwise None."""
    if not init_data:
        return None
    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=True))
    except ValueError:
        return None
    received = pairs.pop("hash", None)
    if not received:
        return None

    check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received):
        return None

    try:
        auth_date = int(pairs.get("auth_date", "0"))
        user = json.loads(pairs.get("user", "null"))
    except (ValueError, json.JSONDecodeError):
        return None
    if max_age and (now or time.time()) - auth_date > max_age:
        return None
    if not isinstance(user, dict) or "id" not in user:
        return None
    return user


def sign_init_data(fields: dict[str, str], bot_token: str) -> str:
    """Builds signed initData — used by the tests."""
    from urllib.parse import urlencode
    check_string = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    digest = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode({**fields, "hash": digest})
