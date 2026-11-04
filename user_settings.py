"""Per-user settings for the bot (Step 4: interface language).

The language selects the language of the whole questionnaire interface
(menu, questions, buttons, summary): en, fr or ar.
The final image-generation prompt is always built in English (master
skill, section 12).

Since Step 7 the language choice is also persisted in the SQLite store
(store.py), so it survives a bot restart; the in-memory dict stays the
fast path and the store is only consulted on a cache miss.
"""

from __future__ import annotations

from typing import Dict, Optional

LANG_EN = "en"
LANG_FR = "fr"
LANG_AR = "ar"

VALID_LANG_CODES = (LANG_EN, LANG_FR, LANG_AR)

LANG_LABELS: Dict[str, str] = {
    LANG_EN: "English",
    LANG_FR: "Français",
    LANG_AR: "العربية",
}

# Common ways users may type the language name.
_ALIASES: Dict[str, str] = {
    "en": LANG_EN, "eng": LANG_EN, "english": LANG_EN, "anglais": LANG_EN,
    "fr": LANG_FR, "french": LANG_FR, "francais": LANG_FR, "français": LANG_FR,
    "ar": LANG_AR, "arabi": LANG_AR, "arabic": LANG_AR, "arabe": LANG_AR,
    "darija": LANG_AR, "derja": LANG_AR, "العربية": LANG_AR,
    "عربي": LANG_AR, "عربية": LANG_AR,
}

_user_langs: Dict[int, str] = {}


def _from_store(user_id: int) -> Optional[str]:
    """Read the persisted language, never raising (store may be absent)."""
    try:
        import store

        code = store.get_lang(user_id)
    except Exception:
        return None
    return code if code in VALID_LANG_CODES else None


def get_lang(user_id: int) -> str:
    """Return the interface language for a user (default: English)."""
    if user_id in _user_langs:
        return _user_langs[user_id]
    saved = _from_store(user_id)
    if saved:
        _user_langs[user_id] = saved
        return saved
    return LANG_EN


def set_lang(user_id: int, code: str) -> bool:
    """Set a user's interface language. Returns False for unknown codes."""
    code = (code or "").strip().lower()
    if code not in VALID_LANG_CODES:
        return False
    _user_langs[user_id] = code
    try:
        import store

        store.set_lang(user_id, code)
    except Exception:
        pass  # memory-only mode (e.g. store unavailable)
    return True


def normalize_code(raw: str) -> str:
    """Turn raw user input like 'EN', ' Français ', 'darija' into a valid code.

    Returns an empty string when the input is not recognized.
    """
    raw = (raw or "").strip().lower()
    return _ALIASES.get(raw, "")
