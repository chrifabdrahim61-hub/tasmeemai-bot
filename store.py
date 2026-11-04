"""Persistent user store for TASMEEM AI (Step 7): credits, referrals, language.

SQLite (Python stdlib, no new dependency). Everything the credits economy
needs survives a restart:

- credits: 5 granted at the very first /start, +3 restored every day,
  +2 for the referrer of every friend who joins through his link,
  1 spent per generated prompt
- referral: who invited whom (paid once, self-invite impossible)
- language: the interface language choice now survives restarts too
- donations: total Stars received per user

Storage location: data/tasmeem.db next to this file. Override with the
TASMEEM_DB environment variable - use ":memory:" for tests.

One shared connection guarded by a lock: handlers run on a single event
loop, the lock only protects the rare cross-thread call. The spend path
uses a conditional UPDATE (WHERE credits >= ?) so two overlapping
generations can never drive the balance below zero.
"""

from __future__ import annotations

import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id       INTEGER PRIMARY KEY,
    credits       INTEGER NOT NULL DEFAULT 0,
    lang          TEXT,
    referrer_id   INTEGER,
    last_refill   TEXT,
    donated_stars INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL
)
"""

_conn: Optional[sqlite3.Connection] = None
_lock = threading.RLock()


# ---------------------------------------------------------------------------
# Connection management
# ---------------------------------------------------------------------------

def _default_path() -> str:
    env = os.getenv("TASMEEM_DB", "").strip()
    if env:
        return env
    base = Path(__file__).resolve().parent / "data"
    return str(base / "tasmeem.db")


def configure(path: Optional[str] = None) -> None:
    """Open (or reopen) the shared connection and make sure the schema exists."""
    global _conn
    with _lock:
        if _conn is not None:
            try:
                _conn.close()
            except Exception:
                pass
            _conn = None
        target = path or _default_path()
        if target != ":memory:":
            Path(target).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(target, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute(_SCHEMA)
        conn.commit()
        _conn = conn


def _connection() -> sqlite3.Connection:
    if _conn is None:
        configure()
    return _conn


def close() -> None:
    """Close the connection (mainly for tests)."""
    global _conn
    with _lock:
        if _conn is not None:
            try:
                _conn.close()
            except Exception:
                pass
            _conn = None


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------

def _today() -> str:
    """UTC calendar day - the boundary for the daily +3 refill."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _fetch(user_id: int) -> Optional[sqlite3.Row]:
    return _connection().execute(
        "SELECT user_id, credits, lang, referrer_id, last_refill,"
        " donated_stars, created_at FROM users WHERE user_id = ?",
        (user_id,),
    ).fetchone()


def _to_dict(row: sqlite3.Row) -> dict:
    return {
        "user_id": row["user_id"],
        "credits": row["credits"],
        "lang": row["lang"],
        "referrer_id": row["referrer_id"],
        "last_refill": row["last_refill"],
        "donated_stars": row["donated_stars"],
        "created_at": row["created_at"],
    }


# ---------------------------------------------------------------------------
# Core credits API
# ---------------------------------------------------------------------------

def get_or_create(user_id: int) -> dict:
    """The user row; a brand-new user starts with START_CREDITS credits.

    last_refill is set to today so the daily refill begins TOMORROW:
    a new user gets exactly the starting credits on day one.
    """
    with _lock:
        conn = _connection()
        row = _fetch(user_id)
        if row is None:
            conn.execute(
                "INSERT INTO users (user_id, credits, last_refill, created_at)"
                " VALUES (?, ?, ?, ?)",
                (user_id, config.START_CREDITS, _today(), _now_iso()),
            )
            conn.commit()
            row = _fetch(user_id)
        return _to_dict(row)


def apply_daily_refill(user_id: int) -> dict:
    """Add the daily refill once per UTC day (lazy: on the first interaction).

    Returns the up-to-date user row.
    """
    user = get_or_create(user_id)
    today = _today()
    if user["last_refill"] == today:
        return user
    with _lock:
        conn = _connection()
        conn.execute(
            "UPDATE users SET credits = credits + ?, last_refill = ?"
            " WHERE user_id = ?",
            (config.DAILY_REFILL, today, user_id),
        )
        conn.commit()
    return get_or_create(user_id)


def snapshot(user_id: int) -> dict:
    """get_or_create + daily refill: call this at every user touchpoint."""
    return apply_daily_refill(user_id)


def spend(user_id: int, amount: Optional[int] = None) -> bool:
    """Remove credits for one generation. False when the balance is too low.

    The conditional UPDATE makes the check-and-spend atomic.
    """
    if amount is None:
        amount = config.GENERATION_COST
    apply_daily_refill(user_id)
    with _lock:
        conn = _connection()
        cur = conn.execute(
            "UPDATE users SET credits = credits - ?"
            " WHERE user_id = ? AND credits >= ?",
            (amount, user_id, amount),
        )
        conn.commit()
        return cur.rowcount == 1


def add_credits(user_id: int, amount: int) -> dict:
    """Grant credits (referral bonus, manual owner grant, ...)."""
    get_or_create(user_id)
    if amount:
        with _lock:
            conn = _connection()
            conn.execute(
                "UPDATE users SET credits = credits + ? WHERE user_id = ?",
                (amount, user_id),
            )
            conn.commit()
    return get_or_create(user_id)


def register_referral(new_user_id: int, referrer_id: int) -> bool:
    """Mark a brand-new user as referred and pay the referrer once.

    True only when THIS call created the user row (genuinely new) and
    the referrer is a different account - so re-clicking an invite link
    or inviting yourself can never farm credits.
    """
    if referrer_id == new_user_id:
        return False
    with _lock:
        conn = _connection()
        if _fetch(new_user_id) is not None:
            return False  # already known -> not a new referral
        get_or_create(referrer_id)  # the referrer earns even if never active
        conn.execute(
            "INSERT INTO users (user_id, credits, referrer_id, last_refill,"
            " created_at) VALUES (?, ?, ?, ?, ?)",
            (new_user_id, config.START_CREDITS, referrer_id, _today(), _now_iso()),
        )
        conn.execute(
            "UPDATE users SET credits = credits + ? WHERE user_id = ?",
            (config.REFERRAL_BONUS, referrer_id),
        )
        conn.commit()
    return True


def record_donation(user_id: int, stars: int) -> dict:
    """Accumulate the Stars a user donated (informational)."""
    get_or_create(user_id)
    if stars:
        with _lock:
            conn = _connection()
            conn.execute(
                "UPDATE users SET donated_stars = donated_stars + ?"
                " WHERE user_id = ?",
                (stars, user_id),
            )
            conn.commit()
    return get_or_create(user_id)


# ---------------------------------------------------------------------------
# Language persistence
# ---------------------------------------------------------------------------

def set_lang(user_id: int, code: str) -> None:
    with _lock:
        get_or_create(user_id)
        conn = _connection()
        conn.execute(
            "UPDATE users SET lang = ? WHERE user_id = ?", (code, user_id)
        )
        conn.commit()


def get_lang(user_id: int) -> Optional[str]:
    row = _fetch(user_id)
    if row is None:
        return None
    return row["lang"]


# ---------------------------------------------------------------------------
# Owner statistics (/admin)
# ---------------------------------------------------------------------------

def stats() -> dict:
    with _lock:
        conn = _connection()
        row = conn.execute(
            "SELECT COUNT(*) AS users,"
            " COALESCE(SUM(credits), 0) AS credits,"
            " COALESCE(SUM(donated_stars), 0) AS stars,"
            " SUM(CASE WHEN referrer_id IS NOT NULL THEN 1 ELSE 0 END) AS referred"
            " FROM users"
        ).fetchone()
        return {
            "users": row["users"],
            "credits_outstanding": row["credits"],
            "donated_stars": row["stars"],
            "referred_users": row["referred"] or 0,
        }
