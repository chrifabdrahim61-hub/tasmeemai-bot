"""Configuration loading for the Logo Prompt Engineer bot.

Reads the Telegram bot token from a .env file located next to this file,
so the token never lives inside the source code.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Load .env from the project folder (if present).
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()

# Version marker, updated at every development step.
PROJECT_VERSION = "0.8.1 (Step 8 hotfix: owner can grant credits in any syntax, /addcredits, one-tap ＋N me buttons)"

# ---------------------------------------------------------------------------
# Support & community (Step 7)
# ---------------------------------------------------------------------------

# The human behind the bot - shown by /help and /support.
SUPPORT_HANDLE: str = os.getenv("SUPPORT_HANDLE", "@vxgix").strip()
SUPPORT_URL: str = "https://t.me/" + SUPPORT_HANDLE.lstrip("@").lstrip("t.me/").strip("/")

# Owner accounts (Step 8): Telegram NUMERIC IDs of the bot admins.
# They unlock the hidden /admin dashboard (stats + credit grants).
ADMIN_IDS: tuple = tuple(
    int(x)
    for x in os.getenv("ADMIN_IDS", "8974969463").split(",")
    if x.strip().isdigit()
)

# Channel every user must join before using the bot (force-subscribe).
REQUIRED_CHANNEL: str = os.getenv("REQUIRED_CHANNEL", "@gifthubai").strip()
CHANNEL_URL: str = "https://t.me/" + REQUIRED_CHANNEL.lstrip("@").strip("/")
# Set FORCE_SUBSCRIBE=0 in .env to disable the gate entirely.
FORCE_SUBSCRIBE: bool = os.getenv("FORCE_SUBSCRIBE", "1").strip().lower() not in (
    "0", "false", "no",
)

# ---------------------------------------------------------------------------
# Credits economy (Step 7)
# ---------------------------------------------------------------------------

START_CREDITS = int(os.getenv("START_CREDITS", "5"))       # granted once, at first /start
DAILY_REFILL = int(os.getenv("DAILY_REFILL", "3"))         # added back every UTC day
REFERRAL_BONUS = int(os.getenv("REFERRAL_BONUS", "2"))     # per friend who starts via your link
GENERATION_COST = int(os.getenv("GENERATION_COST", "1"))   # per generated prompt

# Donation buttons shown after the output (Telegram Stars).
DONATE_AMOUNTS = tuple(
    int(x) for x in os.getenv("DONATE_AMOUNTS", "25,50,75,100").split(",") if x.strip()
)


def token_is_set() -> bool:
    """Return True when a non-empty bot token is configured."""
    return bool(BOT_TOKEN)
