"""TASMEEM AI - Logo Prompt Bot (Telegram).

QCM mode, multilingual, full generator (Step 6): the bot asks a
professional questionnaire in the user's language (English / Francais /
العربية) - buttons for choices, text for brand name, tagline and free
descriptions - then builds a professional, ready-to-use logo-generation
prompt from the answers, following the "Logo Prompt Engineer" master
skill:

- the industry uses a two-level tree: FIELD (Food & Drink, Tech &
  Digital, ...) then SPECIALTY (Restaurant, Cafe, ...). Every button is
  exactly ONE theme - combined categories are gone
- every "Other" button opens a typed input: the user describes what he
  wants in his own words, in English, French, Arabic, Darija or Arabizi
  (engine/knowledge.py understands them all)
- more questions, wider descriptions: motif, audience, brand
  personality, typography feel and an optional tagline complete the
  classic brief (brand, industry, type, colors, style, 2D/3D,
  background, usage, exclusions)
- the prompt follows the 12-part master structure and is validated on
  a 100-point scale (engine/builder.py)
- the deliverable is a copyable prompt block preceded by the design
  type and direction; the RESTRICTIONS guidelines block is no longer
  displayed - the mandatory negative constraints live inside the prompt
  itself ("Strictly avoid: ...")

Hotfix 0.6.1 - the two reported bugs, both rooted in the same place:

- buttons stored a ROW-LOCAL index in callback_data, so any button not
  on the first keyboard row resolved to the wrong option ("3D" stored
  "2D", "coffee" stored "restaurant", "Other" stored the first option
  and the typed input was skipped). The callback_data now carries the
  option VALUE itself: what you tap is exactly what gets stored.
- typing is now accepted on EVERY button question: recognized text
  (English, French, Arabic, Darija, Arabizi) selects the matching
  button; a specialty typed on the field question fills the whole
  subtree at once; anything unrecognized on a question that has an
  Other escape is kept as the free description.

Step 7 - growth & monetization (store.py, SQLite persistence):

- credits: every new user starts with 5 credits, +3 are restored
  automatically every UTC day, and each generated prompt costs 1
  credit (checked before the questionnaire and again on Generate)
- referrals: /start ref<user_id> deep links pay the inviter +2 credits
  per friend, exactly once; self-invites and re-clicks pay nothing
- force-subscribe: membership of the required channel is checked
  before /start, before the questionnaire and before generating, with
  a 5-minute cache; if the check itself fails (bot not added to the
  channel) it fails OPEN so users are never locked out
- commands: /credits, /help, /support, /donate and a hidden owner
  /admin; /lang now also answers with quick buttons; the BotFather
  command menu is published automatically at startup
- support: @vxgix is one tap away from /help, /support and the menu
- donations: a white-heart button under the generated prompt (and in
  the menu) opens 25/50/75/100 Stars choices and charges them with a
  Telegram Stars invoice (currency XTR, no provider token needed)

Step 8 - second creation mode + visibility (engine/modes.py):

- TWO modes in the menu: "Logo prompt" (the original flow) and
  "Social media post (ads)" - a full professional questionnaire with
  trees of choices like the logo one: the SAME industry tree, a goal
  tree (Sell & promote -> Sale / New arrival / Flash sale...), a
  visual-scene tree (Product showcase -> Studio shot / Lifestyle /
  Close-up / Flat-lay...), platform -> format, CTA, language of the
  on-image text, offer, exact headline
- the ads questionnaire asks for the brand name AND the @username of
  the brand or page, and whether the user has a logo; the final
  message carries a HOW TO USE IT block telling him to PASTE HIS
  LOGO IMAGE together with the prompt into the AI model (and that the
  brand name / username are already embedded in the prompt)
- @vxgix now appears right after EVERY output (support line + button)
  so people know the maker faster
- /admin unlocks by NUMERIC ID (ADMIN_IDS, default the owner's id)
  in addition to the support-handle username

Hotfix 0.8.1 - the owner could not add credits to himself:

- /admin only accepted the exact form "/admin add <user_id> <amount>";
  the owner typing "/admin <8974969463><45>" got a silent no-op. The
  grant parser now tolerates every natural syntax - brackets, commas
  and the keyword "add" are optional, a single number grants to the
  sender himself, the amount/id order is auto-corrected and a
  negative amount removes credits
- new /addcredits command: the same grammar without the dashboard
- the dashboard carries one-tap buttons: ＋10 ⚡ me / ＋50 ⚡ me /
  ＋100 ⚡ me, plus a live usage reminder when arguments are unreadable
- every grant now answers with a confirmation (target + new balance)

Rule-based only: no AI services are involved.
"""

from __future__ import annotations

import html
import logging
import time
from typing import Optional

from telegram import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)

import config
import store
from engine import i18n, knowledge, modes
from engine.builder import GeneratedPrompt, generate_prompt
from engine.questions import (
    INDUSTRY_GROUPS,
    QUESTIONS_BY_ID,
    option_label,
    option_rows,
    toggle_exclusions,
    validate_text_answer,
)
from engine.questions_ads import AD_GOAL_GROUPS, AD_VISUAL_GROUPS
from user_settings import VALID_LANG_CODES, get_lang, normalize_code, set_lang

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger("tasmeem-ai")

# The choice trees whose subtree can be filled by TYPING a leaf
# ("coffee shop" on the field question -> food/cafe at once).
TREE_GROUPS = {
    "industry": INDUSTRY_GROUPS,
    "ad_goal": AD_GOAL_GROUPS,
    "ad_visual": AD_VISUAL_GROUPS,
}


def first_question_id(answers: dict):
    """First question of the LOGO mode (compatibility helper/tests)."""
    return modes.first_question_id(modes.MODE_LOGO, answers)

# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def _lang_of(source) -> str:
    """Interface language for the user behind an Update or CallbackQuery."""
    user = getattr(source, "effective_user", None) or getattr(source, "from_user", None)
    return get_lang(user.id) if user else i18n.DEFAULT_LANG


def _user_id_of(source) -> int | None:
    """The Telegram user id behind an Update, a CallbackQuery or a Message."""
    user = getattr(source, "effective_user", None) or getattr(source, "from_user", None)
    return user.id if user else None


def _source_message(source):
    """The message to reply on, from an Update or a CallbackQuery."""
    message = getattr(source, "effective_message", None)
    if message is None:
        message = getattr(source, "message", None)
    return message


def _support_button(lang: str) -> InlineKeyboardButton:
    """URL button that opens the support chat (@vxgix)."""
    return InlineKeyboardButton(i18n.t(lang, "btn_support"), url=config.SUPPORT_URL)

def _menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Language row + the two creation modes + donate/support row."""
    lang_row = []
    for code in VALID_LANG_CODES:
        marker = "[x] " if code == lang else ""
        lang_row.append(
            InlineKeyboardButton(
                marker + i18n.LANGUAGE_NATIVE[code], callback_data=f"lang:{code}"
            )
        )
    mode_row = [
        InlineKeyboardButton(
            i18n.t(lang, "btn_mode_logo"), callback_data="q:start:logo"
        ),
        InlineKeyboardButton(
            i18n.t(lang, "btn_mode_ads"), callback_data="q:start:ads"
        ),
    ]
    return InlineKeyboardMarkup(
        [
            lang_row,
            mode_row,
            [
                InlineKeyboardButton(
                    i18n.t(lang, "btn_donate"), callback_data="donate:open"
                ),
                _support_button(lang),
            ],
        ]
    )


def _confirm_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    i18n.t(lang, "btn_generate"), callback_data="q:generate"
                ),
                InlineKeyboardButton(
                    i18n.t(lang, "btn_restart"), callback_data="q:restart"
                ),
            ]
        ]
    )


def _new_prompt_keyboard(
    lang: str, mode: str = modes.DEFAULT_MODE
) -> InlineKeyboardMarkup:
    """Keyboard shown under a generated prompt.

    The donation button carries the white heart right after the output,
    next to the support contact; "Create another one" re-enters the
    SAME mode that produced this prompt.
    """
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    i18n.t(lang, "btn_new"), callback_data=f"q:start:{mode}"
                )
            ],
            [
                InlineKeyboardButton(
                    i18n.t(lang, "btn_donate"), callback_data="donate:open"
                ),
                _support_button(lang),
            ],
        ]
    )


def render_prompt_html(
    result: GeneratedPrompt,
    lang: str,
    credits_left: int | None = None,
    mode: str = modes.DEFAULT_MODE,
) -> str:
    """Format a GeneratedPrompt as the final Telegram message.

    The IMAGE GENERATION PROMPT block is a <pre> block: Telegram shows
    a copy button when the user taps it. In ads mode a HOW TO USE IT
    block follows the prompt: paste your LOGO IMAGE together with the
    prompt, the brand name / @username are already inside. Every output
    closes with the support tag (@vxgix) so people know the maker.
    When credits_left is given, a live balance line closes the message.
    """
    is_ads = mode == modes.MODE_ADS
    intro_key = "prompt_intro_ads" if is_ads else "prompt_intro"
    text = (
        f"{i18n.t(lang, intro_key)}\n\n"
        "<b>DESIGN TYPE:</b>\n"
        f"{html.escape(result.design_type)}\n\n"
        "<b>DESIGN DIRECTION:</b>\n"
        f"{html.escape(result.design_direction)}\n\n"
        "<b>IMAGE GENERATION PROMPT:</b>\n"
        f"<pre>{html.escape(result.image_prompt)}</pre>\n\n"
        "<i>"
        f"{html.escape(i18n.t(lang, 'prompt_score', score=result.score))}"
        "</i>"
    )
    if result.score < 90:
        text += "\n\n" + html.escape(i18n.t(lang, "prompt_warning"))
    if is_ads:
        text += "\n\n" + i18n.t(lang, "ads_howto")
        if getattr(result, "logo", "") == "no":
            text += "\n\n" + html.escape(i18n.t(lang, "ads_howto_nologo"))
    if credits_left is not None:
        text += "\n\n" + i18n.t(
            lang, "out_credits", credits=credits_left, refill=config.DAILY_REFILL
        )
    support = f'<a href="{config.SUPPORT_URL}">{html.escape(config.SUPPORT_HANDLE)}</a>'
    text += "\n\n🤍 " + i18n.t(lang, "out_support", support=support)
    return text


def _buttons_keyboard(lang: str, question_id: str) -> InlineKeyboardMarkup:
    """Inline keyboard for a buttons-kind question.

    The callback_data carries the option VALUE itself (never a positional
    index): what the user taps is exactly what gets stored, whatever the
    keyboard layout is. (The old index-based scheme restarted at 0 on
    every row, so tapping "3D" could store "2D".)
    """
    question = QUESTIONS_BY_ID[question_id]
    rows = []
    for row in option_rows(question.options, per_row=2):
        buttons = []
        for option in row:
            label = option_label(question_id, option.value, lang)
            buttons.append(
                InlineKeyboardButton(
                    label, callback_data=f"ans:{question_id}:{option.value}"
                )
            )
        rows.append(buttons)
    return InlineKeyboardMarkup(rows)


def _skip_keyboard(lang: str, question_id: str) -> InlineKeyboardMarkup:
    """Keyboard with the skip option of a text_with_skip question."""
    question = QUESTIONS_BY_ID[question_id]
    buttons = [
        InlineKeyboardButton(
            option_label(question_id, option.value, lang),
            callback_data=f"ans:{question_id}:{option.value}",
        )
        for option in question.options
    ]
    return InlineKeyboardMarkup([buttons])


def _toggle_keyboard(lang: str, selected: set) -> InlineKeyboardMarkup:
    """Keyboard for the toggle question (checkbox style, ASCII marks)."""
    question = QUESTIONS_BY_ID["exclusions"]
    rows = []
    for option in question.options:
        mark = "[x] " if option.value in selected else "[ ] "
        label = option_label("exclusions", option.value, lang)
        rows.append(
            [InlineKeyboardButton(mark + label, callback_data=f"tog:{option.value}")]
        )
    rows.append([InlineKeyboardButton(i18n.t(lang, "btn_done"), callback_data="tog:done")])
    return InlineKeyboardMarkup(rows)


async def _ask_question(source, context: ContextTypes.DEFAULT_TYPE, question_id: str) -> str:
    """Send one question in the user's language; return the state id."""
    lang = _lang_of(source)
    question = QUESTIONS_BY_ID[question_id]
    context.user_data["current_question"] = question_id

    if question.kind == "buttons":
        message = await source.message.reply_text(
            i18n.t(lang, f"q_{question_id}"),
            reply_markup=_buttons_keyboard(lang, question_id),
        )
    elif question.kind == "toggle":
        selected = context.user_data.setdefault("exclusions", set())
        message = await source.message.reply_text(
            i18n.t(lang, f"q_{question_id}"),
            reply_markup=_toggle_keyboard(lang, selected),
        )
    elif question.kind == "text_with_skip":
        message = await source.message.reply_text(
            i18n.t(lang, f"q_{question_id}"),
            reply_markup=_skip_keyboard(lang, question_id),
        )
    else:  # plain text question
        message = await source.message.reply_text(i18n.t(lang, f"q_{question_id}"))

    context.user_data["question_message_id"] = message.message_id
    context.user_data["chat_id"] = message.chat_id
    return question_id


async def _advance(source, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Move to the next non-skipped question, or to the confirm screen."""
    answers = context.user_data.setdefault("answers", {})
    current = context.user_data.get("current_question")
    mode = context.user_data.get("mode", modes.DEFAULT_MODE)
    nxt = modes.next_question_id(mode, current, answers)
    if nxt is None:
        return await _show_confirm(source, context)
    return await _ask_question(source, context, nxt)


async def _show_confirm(source, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Show the collected answers and ask for confirmation."""
    lang = _lang_of(source)
    mode = context.user_data.get("mode", modes.DEFAULT_MODE)
    answers = context.user_data.setdefault("answers", {})
    exclusions = context.user_data.get("exclusions", set())
    summary = html.escape(
        modes.build_answers_summary(mode, answers, exclusions, lang)
    )
    await source.message.reply_text(
        i18n.t(lang, "summary_note", summary=summary),
        reply_markup=_confirm_keyboard(lang),
        parse_mode=ParseMode.HTML,
    )
    return "confirm"


async def _freeze_keyboard(query) -> None:
    """Remove the buttons of an answered question message."""
    try:
        await query.edit_message_reply_markup(reply_markup=None)
    except Exception:  # message may be too old or already edited
        pass


def _freeze_by_message_id(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove the buttons of the current question message (typed answers).

    When the user answers by TYPING instead of tapping, the inline
    keyboard of the question stays on screen; deactivate it so a late
    tap can never register a second answer.
    """
    message_id = context.user_data.get("question_message_id")
    chat_id = context.user_data.get("chat_id")
    if message_id is None or chat_id is None:
        return
    try:
        context.bot.edit_message_reply_markup(
            chat_id=chat_id, message_id=message_id, reply_markup=None
        )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Force-subscribe gate & credits helpers (Step 7)
# ---------------------------------------------------------------------------

_MEMBER_CACHE_TTL = 300  # seconds a membership verdict is trusted
_member_cache: dict = {}


async def _is_member(
    context: ContextTypes.DEFAULT_TYPE, user_id: int, force: bool = False
) -> bool:
    """Channel-membership check with a short cache.

    FAILS OPEN: if Telegram refuses the check (the bot was not added to
    the channel, network hiccup, ...) the user is allowed through
    instead of being locked out by a misconfiguration - logged loudly.
    """
    if not config.FORCE_SUBSCRIBE:
        return True
    now = time.monotonic()
    if not force:
        cached = _member_cache.get(user_id)
        if cached and now - cached[0] < _MEMBER_CACHE_TTL:
            return cached[1]
    try:
        member = await context.bot.get_chat_member(
            chat_id=config.REQUIRED_CHANNEL, user_id=user_id
        )
        ok = member.status in ("member", "administrator", "creator")
    except Exception as exc:
        logger.warning(
            "Membership check for %s failed (fail-open): %s", user_id, exc
        )
        return True
    _member_cache[user_id] = (now, ok)
    return ok


async def _ensure_subscribed(source, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Gate used by /start, the menu button and Generate. False = blocked."""
    user_id = _user_id_of(source)
    if user_id is None or await _is_member(context, user_id):
        return True
    lang = get_lang(user_id)
    message = _source_message(source)
    if message is not None:
        try:
            await message.reply_text(
                i18n.t(lang, "fs_required", channel_link=config.CHANNEL_URL),
                reply_markup=_force_sub_keyboard(lang),
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            pass
    return False


def _force_sub_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Join button + the check-again button."""
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(i18n.t(lang, "btn_join"), url=config.CHANNEL_URL)],
            [InlineKeyboardButton(i18n.t(lang, "btn_check"), callback_data="fs:check")],
        ]
    )


def _donate_keyboard() -> InlineKeyboardMarkup:
    """The Stars amounts: 25 / 50 / 75 / 100, two per row."""
    amounts = config.DONATE_AMOUNTS or (25, 50, 75, 100)
    rows = []
    for i in range(0, len(amounts), 2):
        rows.append(
            [
                InlineKeyboardButton(f"⭐ {amount}", callback_data=f"donate:{amount}")
                for amount in amounts[i : i + 2]
            ]
        )
    return InlineKeyboardMarkup(rows)


def _earn_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Keyboard under the not-enough-credits message."""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    i18n.t(lang, "btn_donate"), callback_data="donate:open"
                )
            ]
        ]
    )


def _not_enough_text(user_id: int) -> str:
    user = store.snapshot(user_id)
    return i18n.t(
        get_lang(user_id),
        "not_enough",
        cost=config.GENERATION_COST,
        credits=user["credits"],
        refill=config.DAILY_REFILL,
        bonus=config.REFERRAL_BONUS,
    )


async def _referral_link(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> str:
    """https://t.me/<bot>?start=ref<user_id> - the +2-credits invite link."""
    bot_data = getattr(context, "bot_data", None)
    username = bot_data.get("bot_username") if isinstance(bot_data, dict) else None
    if not username:
        me = await context.bot.get_me()
        username = me.username
        if isinstance(bot_data, dict):
            bot_data["bot_username"] = username
    return f"https://t.me/{username}?start=ref{user_id}"


async def _send_menu(message, user_id: int, lang: str) -> None:
    """The /start menu with a live credits line."""
    user = store.snapshot(user_id)
    text = (
        i18n.t(lang, "menu_text")
        + "\n\n"
        + i18n.t(
            lang, "menu_credits", credits=user["credits"], refill=config.DAILY_REFILL
        )
    )
    await message.reply_text(
        text, reply_markup=_menu_keyboard(lang), parse_mode=ParseMode.HTML
    )


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Entry point: referral deep link, subscribe gate, then the menu."""
    user_id = update.effective_user.id
    lang = _lang_of(update)

    # Referral deep link: /start ref12345 - pays the inviter once.
    args = list(context.args or [])
    if args:
        payload = args[0].strip().lower()
        if payload.startswith("ref") and payload[3:].isdigit():
            referrer_id = int(payload[3:])
            if store.register_referral(user_id, referrer_id):
                logger.info("Referral: %s was invited by %s", user_id, referrer_id)
                try:
                    await context.bot.send_message(
                        referrer_id,
                        i18n.t(
                            get_lang(referrer_id),
                            "ref_bonus_notify",
                            bonus=config.REFERRAL_BONUS,
                        ),
                        parse_mode=ParseMode.HTML,
                    )
                except Exception:
                    pass  # the referrer may never have started the bot

    context.user_data.pop("answers", None)
    context.user_data.pop("exclusions", None)
    context.user_data.pop("current_question", None)

    if not await _ensure_subscribed(update, context):
        return "menu"

    await _send_menu(update.effective_message, user_id, lang)
    return "menu"


async def cmd_credits(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/credits: balance, daily refill and the personal referral link."""
    user_id = update.effective_user.id
    lang = _lang_of(update)
    user = store.snapshot(user_id)
    link = await _referral_link(context, user_id)
    await update.effective_message.reply_text(
        i18n.t(
            lang,
            "credits_text",
            credits=user["credits"],
            refill=config.DAILY_REFILL,
            bonus=config.REFERRAL_BONUS,
            link=link,
        ),
        reply_markup=_earn_keyboard(lang),
        parse_mode=ParseMode.HTML,
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/help: how the bot works + the support contact."""
    lang = _lang_of(update)
    support = f'<a href="{config.SUPPORT_URL}">{html.escape(config.SUPPORT_HANDLE)}</a>'
    await update.effective_message.reply_text(
        i18n.t(
            lang,
            "help_text",
            refill=config.DAILY_REFILL,
            bonus=config.REFERRAL_BONUS,
            support=support,
        ),
        parse_mode=ParseMode.HTML,
    )


async def cmd_support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/support: the human behind the bot (@vxgix)."""
    lang = _lang_of(update)
    support = f'<a href="{config.SUPPORT_URL}">{html.escape(config.SUPPORT_HANDLE)}</a>'
    await update.effective_message.reply_text(
        i18n.t(lang, "support_text", support=support),
        reply_markup=InlineKeyboardMarkup([[_support_button(lang)]]),
        parse_mode=ParseMode.HTML,
    )


async def cmd_donate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/donate: the Stars donation choices."""
    lang = _lang_of(update)
    await update.effective_message.reply_text(
        i18n.t(lang, "donate_intro"),
        reply_markup=_donate_keyboard(),
        parse_mode=ParseMode.HTML,
    )


def _is_owner(user) -> bool:
    """The owner: any ADMIN_IDS numeric account or the support handle.

    Since Step 8 the numeric Telegram ID (config.ADMIN_IDS, default
    8974969463) unlocks /admin even when the username cannot be read.
    """
    if not user:
        return False
    if getattr(user, "id", None) and user.id in config.ADMIN_IDS:
        return True
    owner = config.SUPPORT_HANDLE.lstrip("@").lower()
    return (user.username or "").lower() == owner


ADMIN_USAGE = (
    "➕ Add credits - ANY of these works:\n"
    "• /admin add 8974969463 45   (user id, then amount)\n"
    "• /admin 8974969463 45\n"
    "• /admin 45   (credits for yourself)\n"
    "• /addcredits 8974969463 45   /   /addcredits 45\n"
    "Brackets, commas and the word 'add' are all optional -\n"
    "/admin <8974969463><45> works too. Negative amounts remove\n"
    "credits (e.g. /admin 8974969463 -10).\n"
    "Or tap a button below to top yourself up instantly."
)


def _parse_grant_args(args) -> Optional[tuple]:
    """Turn loose admin arguments into (user_id_or_None, amount).

    Built for the way the owner actually types it - every one of these
    grants 45 credits to user 8974969463:
      /admin add 8974969463 45     /admin 8974969463 45
      /admin <8974969463><45>      /admin 8974969463, 45
      /admin 45 8974969463         (order fixed automatically)
    and each of these grants 45 credits to the sender himself:
      /admin add 45   /admin 45   /addcredits 45
    Angle brackets, commas, plus signs and the keyword "add" are all
    tolerated and stripped. A negative amount removes credits.
    Returns (None, amount) when no user id was given, or None when no
    usable number is found at all.
    """
    joined = " ".join(str(a) for a in args)
    for ch in "<>[](),;":
        joined = joined.replace(ch, " ")
    tokens = [t for t in joined.split() if t]
    if tokens and tokens[0].lower() in ("add", "give", "grant", "plus"):
        tokens = tokens[1:]

    def to_int(tok: str) -> Optional[int]:
        cleaned = tok.strip().lstrip("+")
        if not cleaned:
            return None
        if cleaned.isdigit() or (cleaned[0] == "-" and cleaned[1:].isdigit()):
            return int(cleaned)
        return None

    numbers = [n for n in (to_int(t) for t in tokens) if n is not None]
    if not numbers:
        return None
    if len(numbers) == 1:
        return (None, numbers[0])
    first, second = numbers[0], numbers[1]
    # Telegram ids are large: if the first number is small it must be
    # the amount and the id came first in the sentence.
    if -100_000 < first <= 100_000 and second > 100_000:
        first, second = second, first
    return (first, second)


def _admin_dashboard_text() -> str:
    """The live stats block shown by /admin (and refreshed by its buttons)."""
    s = store.stats()
    return (
        f"TASMEEM AI - owner dashboard\n"
        f"Version: {config.PROJECT_VERSION}\n"
        f"Users: {s['users']}\n"
        f"Referred users: {s['referred_users']}\n"
        f"Credits outstanding: {s['credits_outstanding']}\n"
        f"Donations: {s['donated_stars']} Stars"
    )


def _admin_keyboard() -> InlineKeyboardMarkup:
    """One-tap self top-ups for the owner: +10 / +50 / +100 credits."""
    row = [
        InlineKeyboardButton(f"＋{amount} ⚡ me", callback_data=f"admcred:{amount}")
        for amount in (10, 50, 100)
    ]
    return InlineKeyboardMarkup([row])


def _grant_confirmation(target_id: int, amount: int, user: dict) -> str:
    """The human confirmation line after a manual credit change."""
    if amount >= 0:
        return (
            f"OK: granted {amount} credits to {target_id}.\n"
            f"Balance now: {user['credits']} credits."
        )
    return (
        f"OK: removed {-amount} credits from {target_id}.\n"
        f"Balance now: {user['credits']} credits."
    )


async def cmd_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/admin: owner-only dashboard; grants credits in any natural syntax.

    /admin add <user_id> <amount> - the classic form
    /admin <user_id> <amount>     - brackets/commas optional
    /admin <amount>               - grant to yourself
    A negative amount removes credits. When the arguments cannot be
    read, the dashboard explains every accepted form instead.
    """
    if not _is_owner(update.effective_user):
        return  # silent for everyone else
    text = _admin_dashboard_text()
    grant = _parse_grant_args(context.args or [])
    if grant is not None:
        target_id, amount = grant
        if target_id is None:
            target_id = update.effective_user.id
        user = store.add_credits(target_id, amount)
        text += "\n\n" + _grant_confirmation(target_id, amount, user)
    else:
        text += "\n\n" + ADMIN_USAGE
    await update.effective_message.reply_text(text, reply_markup=_admin_keyboard())


async def cmd_addcredits(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/addcredits: the explicit grant command (owner only).

    /addcredits 45                  - top yourself up
    /addcredits 8974969463 45       - grant to any user
    Same tolerant parsing as /admin, without the dashboard.
    """
    if not _is_owner(update.effective_user):
        return  # silent for everyone else
    grant = _parse_grant_args(context.args or [])
    if grant is None:
        await update.effective_message.reply_text(ADMIN_USAGE)
        return
    target_id, amount = grant
    if target_id is None:
        target_id = update.effective_user.id
    user = store.add_credits(target_id, amount)
    await update.effective_message.reply_text(_grant_confirmation(target_id, amount, user))


async def admin_credit_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """The ＋N ⚡ me buttons: one tap, instant self top-up."""
    query = update.callback_query
    if not _is_owner(query.from_user):
        await query.answer()
        return
    _, _, amount_raw = query.data.partition(":")
    if not amount_raw.lstrip("+").isdigit():
        await query.answer()
        return
    amount = int(amount_raw)
    user = store.add_credits(update.effective_user.id, amount)
    await query.answer(f"+{amount} credits -> balance {user['credits']} ⚡")
    try:
        await query.edit_message_text(
            _admin_dashboard_text() + "\n\n" + ADMIN_USAGE,
            reply_markup=_admin_keyboard(),
        )
    except Exception:  # message too old / unchanged - the toast is enough
        pass


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the questionnaire."""
    lang = _lang_of(update)
    context.user_data.pop("answers", None)
    context.user_data.pop("exclusions", None)
    context.user_data.pop("current_question", None)
    await update.effective_message.reply_text(i18n.t(lang, "cancel_text"))
    return ConversationHandler.END


async def cmd_lang(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /lang: view or set the interface language."""
    lang = _lang_of(update)
    raw = " ".join(context.args or []).strip()

    if not raw:
        await update.effective_message.reply_text(
            i18n.t(lang, "lang_usage", current=i18n.LANGUAGE_NATIVE[lang]),
            reply_markup=_lang_buttons_markup(),
            parse_mode=ParseMode.HTML,
        )
        return

    code = normalize_code(raw)
    if not code:
        await update.effective_message.reply_text(
            i18n.t(lang, "lang_unknown") + "\n\n"
            + i18n.t(lang, "lang_usage", current=i18n.LANGUAGE_NATIVE[lang]),
            reply_markup=_lang_buttons_markup(),
            parse_mode=ParseMode.HTML,
        )
        return

    set_lang(update.effective_user.id, code)
    logger.info("User %s set interface language to %s", update.effective_user.id, code)
    await update.effective_message.reply_text(
        i18n.t(code, "lang_set", label=i18n.LANGUAGE_NATIVE[code]),
        parse_mode=ParseMode.HTML,
    )


def _lang_buttons_markup() -> InlineKeyboardMarkup:
    """The three interface languages as quick buttons (used by /lang)."""
    row = [
        InlineKeyboardButton(
            i18n.LANGUAGE_NATIVE[code], callback_data=f"lang:{code}"
        )
        for code in VALID_LANG_CODES
    ]
    return InlineKeyboardMarkup([row])


# ---------------------------------------------------------------------------
# Conversation handlers
# ---------------------------------------------------------------------------


async def menu_start_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """A mode button was pressed: gates first, then reset and ask.

    callback_data carries the mode: "q:start:logo" / "q:start:ads"
    (legacy "q:start" opens the logo mode).
    """
    query = update.callback_query
    await query.answer()

    data = query.data or ""
    parts = data.split(":")
    mode = modes.normalize_mode(parts[2]) if len(parts) >= 3 else modes.DEFAULT_MODE

    # Gate 1: the required channel.
    if not await _ensure_subscribed(query, context):
        return "menu"

    # Gate 2: at least one credit must be available for the generation
    # at the end of the questionnaire (better to know before question 1).
    user_id = query.from_user.id
    user = store.snapshot(user_id)
    if user["credits"] < max(config.GENERATION_COST, 1):
        await query.message.reply_text(
            _not_enough_text(user_id),
            reply_markup=_earn_keyboard(get_lang(user_id)),
            parse_mode=ParseMode.HTML,
        )
        return "menu"

    context.user_data["mode"] = mode
    context.user_data["answers"] = {}
    context.user_data["exclusions"] = set()

    first = modes.first_question_id(mode, {})
    return await _ask_question(query, context, first)


def _option_by_value(question, value: str):
    """The Option of ``question`` whose value is ``value`` (None if absent)."""
    for option in question.options:
        if option.value == value:
            return option
    return None


async def handle_answer_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """One option of a buttons-kind question was tapped.

    The callback_data carries the option VALUE ("ans:<question>:<value>")
    so the tapped button and the stored answer can never diverge.
    """
    query = update.callback_query
    await query.answer()

    data = query.data or ""
    parts = data.split(":", 2)
    if len(parts) != 3 or parts[0] != "ans":
        return context.user_data.get("current_question", "menu")
    _, question_id, value = parts

    current = context.user_data.get("current_question")
    if current != question_id:
        # stale button from an old message - re-ask the current question
        if current is None:
            return "menu"
        lang = _lang_of(query)
        await query.message.reply_text(i18n.t(lang, "stale_question"))
        return await _ask_question(query, context, current)

    question = QUESTIONS_BY_ID[question_id]
    option = _option_by_value(question, value)
    if option is None:
        # unknown value - never store a guess, re-ask the question
        return await _ask_question(query, context, question_id)

    context.user_data.setdefault("answers", {})[question_id] = option.value
    logger.info("User answered %s = %s", question_id, option.value)

    await _freeze_keyboard(query)
    return await _advance(query, context)


async def handle_skip_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """The skip button of a text_with_skip question was tapped."""
    query = update.callback_query
    await query.answer()

    data = query.data or ""
    parts = data.split(":", 2)
    if len(parts) != 3 or parts[0] != "ans":
        return context.user_data.get("current_question", "menu")
    _, question_id, value = parts

    if context.user_data.get("current_question") != question_id:
        current = context.user_data.get("current_question")
        if current is None:
            return "menu"
        return await _ask_question(query, context, current)

    question = QUESTIONS_BY_ID[question_id]
    option = _option_by_value(question, value)
    if option is None:
        return await _ask_question(query, context, question_id)

    context.user_data.setdefault("answers", {})[question_id] = option.value
    logger.info("User skipped %s (%s)", question_id, option.value)
    await _freeze_keyboard(query)
    return await _advance(query, context)


async def handle_answer_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """A typed answer arrived for the current text question."""
    lang = _lang_of(update)
    question_id = context.user_data.get("current_question")
    if question_id not in QUESTIONS_BY_ID:
        return "menu"
    question = QUESTIONS_BY_ID[question_id]

    cleaned = validate_text_answer(question, update.effective_message.text or "")
    if cleaned is None:
        await update.effective_message.reply_text(
            i18n.t(lang, "invalid_text", max_len=question.max_len)
        )
        return question_id

    context.user_data.setdefault("answers", {})[question_id] = cleaned
    logger.info("User typed answer for %s (%d chars)", question_id, len(cleaned))
    return await _advance(update, context)


async def handle_buttons_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Typed answer while a buttons question is active.

    Typing is always accepted - the user must never be stuck because the
    choice he wants is not in the list:

    1. recognized text (any language) behaves exactly like tapping the
       matching button;
    2. typing a specialty ("coffee shop", "مقهى", "café") on the FIELD
       question fills the whole industry subtree at once;
    3. otherwise, when the question has an Other escape, the text is kept
       as the free description (same as Other + typing) and the extra
       typed-input question is skipped;
    4. otherwise (closed technical questions) the question is re-asked
       with a short hint.
    """
    lang = _lang_of(update)
    question_id = context.user_data.get("current_question")
    question = QUESTIONS_BY_ID.get(question_id) if question_id else None
    if question is None or question.kind != "buttons":
        return await need_input_reply(update, context)

    cleaned = validate_text_answer(question, update.effective_message.text or "")
    if cleaned is None:
        await update.effective_message.reply_text(
            i18n.t(lang, "invalid_text", max_len=question.max_len)
        )
        return question_id

    answers = context.user_data.setdefault("answers", {})

    # A tree question: typing the exact name of a group (any language)
    # behaves like tapping it - the subtree is asked next.
    groups = TREE_GROUPS.get(question_id)
    if groups:
        group_exact = knowledge.label_exact_match(question_id, cleaned)
        if group_exact is not None and group_exact in groups:
            answers[question_id] = group_exact
            _freeze_by_message_id(context)
            logger.info("User typed %r -> %s (group)", cleaned, group_exact)
            return await _advance(update, context)

    # A recognized option value selects the matching button.
    matched = knowledge.match_option(question_id, cleaned)

    # A tree question: a recognized LEAF fills the whole subtree at once
    if groups:
        leaf_values = {leaf for leaves in groups.values() for leaf in leaves}
        if matched is not None and matched in leaf_values:
            group = next(
                (
                    group
                    for group, leaves in groups.items()
                    if matched in leaves
                ),
                None,
            )
            if group is not None:
                answers[question_id] = group
                answers[f"{question_id}_{group}"] = matched
                answers.pop(f"{question_id}_text", None)
                _freeze_by_message_id(context)
                logger.info(
                    "User typed %r -> %s/%s (subtree filled)",
                    cleaned,
                    question_id,
                    matched,
                )
                return await _advance(update, context)
        # The typed text may name a LEAF of one subtree ("giveaway",
        # "flat-lay", "plat dressé"...): ask each subtree question.
        if matched is None:
            for group, leaves in groups.items():
                leaf_hit = knowledge.match_option(
                    f"{question_id}_{group}", cleaned
                )
                if leaf_hit in leaves:
                    answers[question_id] = group
                    answers[f"{question_id}_{group}"] = leaf_hit
                    answers.pop(f"{question_id}_text", None)
                    _freeze_by_message_id(context)
                    logger.info(
                        "User typed %r -> %s/%s (leaf of the subtree)",
                        cleaned,
                        question_id,
                        leaf_hit,
                    )
                    return await _advance(update, context)

    if matched in {option.value for option in question.options}:
        answers[question_id] = matched
        _freeze_by_message_id(context)
        logger.info("User typed %r -> %s = %s", cleaned, question_id, matched)
        return await _advance(update, context)

    if "other" in {option.value for option in question.options}:
        # keep the description under the key the builder reads
        text_key = (
            "industry_text"
            if question_id.startswith("industry_")
            else f"{question_id}_text"
        )
        answers[question_id] = "other"
        answers[text_key] = cleaned
        _freeze_by_message_id(context)
        logger.info(
            "User typed a custom answer for %s (%d chars)", question_id, len(cleaned)
        )
        await update.effective_message.reply_text(
            i18n.t(lang, "custom_noted", text=cleaned)
        )
        return await _advance(update, context)

    await update.effective_message.reply_text(i18n.t(lang, "type_instead_hint"))
    return question_id


async def handle_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Toggle buttons / Done of the exclusions question."""
    query = update.callback_query
    await query.answer()

    data = query.data or ""
    current = context.user_data.get("current_question")
    if current != "exclusions":
        return await _ask_question(query, context, current or "exclusions")

    if data == "tog:done":
        selected = context.user_data.get("exclusions", set())
        context.user_data.setdefault("answers", {})["exclusions"] = "done"
        logger.info("User exclusions: %s", sorted(selected))
        await _freeze_keyboard(query)
        return await _advance(query, context)

    if not data.startswith("tog:"):
        return "exclusions"
    value = data.split(":", 1)[1]

    selected = toggle_exclusions(context.user_data.get("exclusions", set()), value)
    context.user_data["exclusions"] = selected
    try:
        await query.edit_message_reply_markup(
            reply_markup=_toggle_keyboard(_lang_of(query), selected)
        )
    except Exception:
        pass
    return "exclusions"


async def confirm_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Generate / Restart on the confirmation screen."""
    query = update.callback_query
    await query.answer()
    lang = _lang_of(query)
    mode = context.user_data.get("mode", modes.DEFAULT_MODE)

    action = (query.data or "").split(":")[-1]

    if action == "restart":
        context.user_data["answers"] = {}
        context.user_data["exclusions"] = set()
        first = modes.first_question_id(mode, {})
        return await _ask_question(query, context, first)

    if action == "generate":
        user_id = query.from_user.id

        # Gate 1: still a member of the required channel.
        if not await _ensure_subscribed(query, context):
            return "confirm"

        # Gate 2: pay one credit for the generation.
        if not store.spend(user_id):
            await query.message.reply_text(
                _not_enough_text(user_id),
                reply_markup=_earn_keyboard(get_lang(user_id)),
                parse_mode=ParseMode.HTML,
            )
            return "confirm"

        answers = context.user_data.setdefault("answers", {})
        exclusions = context.user_data.get("exclusions", set())
        result = modes.mode_of(mode).builder(answers, exclusions)
        credits_left = store.snapshot(user_id)["credits"]
        logger.info(
            "Generated prompt for user %s: mode=%s type=%s score=%s credits_left=%s",
            user_id,
            mode,
            result.design_type,
            result.score,
            credits_left,
        )
        await query.message.reply_text(
            render_prompt_html(result, lang, credits_left=credits_left, mode=mode),
            parse_mode=ParseMode.HTML,
            reply_markup=_new_prompt_keyboard(lang, mode),
        )
        context.user_data.pop("current_question", None)
        return ConversationHandler.END

    return "confirm"


async def language_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Language button pressed (works in menu, mid-quiz and outside).

    Returns the next conversation state when used inside the
    conversation, None otherwise.
    """
    query = update.callback_query
    await query.answer()

    code = (query.data or "").split(":")[-1]
    if code not in VALID_LANG_CODES:
        return None
    set_lang(query.from_user.id, code)
    logger.info("User %s set interface language to %s (button)", query.from_user.id, code)

    current = context.user_data.get("current_question")
    if current in QUESTIONS_BY_ID:
        # mid-quiz: re-ask the current question in the new language
        return await _ask_question(query, context, current)
    if current == "confirm":
        return await _show_confirm(query, context)

    # in menu or outside: re-show the menu in the new language
    await query.message.reply_html(
        i18n.t(code, "menu_text"), reply_markup=_menu_keyboard(code)
    )
    return None


async def language_cb_conv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """Language button inside the conversation - returns a state."""
    state = await language_cb(update, context)
    if state is not None:
        return state
    return context.user_data.get("current_question", "menu")


async def language_cb_outside(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Language button outside the conversation."""
    await language_cb(update, context)


async def need_input_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    """User sent something the current question cannot accept."""
    await update.effective_message.reply_text(
        i18n.t(_lang_of(update), "need_input_text")
    )
    return context.user_data.get("current_question", "menu")


# ---------------------------------------------------------------------------
# Force-subscribe check & Stars donations (Step 7)
# ---------------------------------------------------------------------------


async def fs_check_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """The "I joined - check" button of the force-subscribe gate."""
    query = update.callback_query
    user_id = query.from_user.id
    lang = get_lang(user_id)

    if await _is_member(context, user_id, force=True):
        await query.answer()
        context.user_data.pop("answers", None)
        context.user_data.pop("exclusions", None)
        context.user_data.pop("current_question", None)
        await _send_menu(query.message, user_id, lang)
        return

    await query.answer(i18n.t(lang, "fs_still"), show_alert=True)


async def donate_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """The white-heart button: open the amounts, then send a Stars invoice."""
    query = update.callback_query
    lang = _lang_of(query)
    data = (query.data or "").split(":", 1)[-1]

    if data == "open":
        await query.answer()
        await query.message.reply_text(
            i18n.t(lang, "donate_intro"),
            reply_markup=_donate_keyboard(),
            parse_mode=ParseMode.HTML,
        )
        return

    try:
        amount = int(data)
    except ValueError:
        await query.answer()
        return
    if amount not in config.DONATE_AMOUNTS:
        await query.answer()
        return

    await query.answer()
    logger.info("User %s chose to donate %s Stars", query.from_user.id, amount)
    # XTR = Telegram Stars; the provider token MUST stay empty for Stars.
    await context.bot.send_invoice(
        chat_id=query.message.chat_id,
        title="TASMEEM AI",
        description=i18n.t(lang, "donate_desc"),
        payload=f"donate:{amount}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=f"⭐ {amount}", amount=amount)],
    )


async def on_precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Approve every TASMEEM AI Stars checkout."""
    query = update.pre_checkout_query
    if (query.invoice_payload or "").startswith("donate:"):
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message="Unknown payment.")


async def on_successful_payment(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """A Stars donation landed: record it and thank the donor."""
    payment = update.message.successful_payment
    user_id = update.effective_user.id
    stars = payment.total_amount  # for XTR this is the amount in Stars
    store.record_donation(user_id, stars)
    logger.info("User %s donated %s Stars", user_id, stars)
    await update.message.reply_text(
        i18n.t(_lang_of(update), "donate_thanks", stars=stars),
        parse_mode=ParseMode.HTML,
    )


async def outside_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Free text outside the questionnaire."""
    await update.effective_message.reply_text(i18n.t(_lang_of(update), "outside_text"))


# ---------------------------------------------------------------------------
# Application assembly
# ---------------------------------------------------------------------------


def build_conversation_handler() -> ConversationHandler:
    """Assemble the questionnaire state machine from ALL modes' questions."""
    states = {
        "menu": [CallbackQueryHandler(menu_start_cb, pattern=r"^q:start")],
        "confirm": [CallbackQueryHandler(confirm_cb, pattern=r"^q:")],
    }

    for question in modes.all_questions():
        question_id = question.id
        if question.kind == "buttons":
            states[question_id] = [
                CallbackQueryHandler(handle_answer_button, pattern=r"^ans:"),
                # typing is always accepted, even on button questions
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons_text),
            ]
        elif question.kind == "toggle":
            states[question_id] = [CallbackQueryHandler(handle_toggle, pattern=r"^tog:")]
        elif question.kind == "text_with_skip":
            states[question_id] = [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer_text),
                CallbackQueryHandler(handle_skip_button, pattern=r"^ans:"),
            ]
        else:  # plain text
            states[question_id] = [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer_text)
            ]

    return ConversationHandler(
        entry_points=[
            CommandHandler("start", cmd_start),
            # the "Create another one" button under a generated prompt
            # re-enters the conversation even after it ended, in the
            # same mode ("q:start:logo" / "q:start:ads")
            CallbackQueryHandler(menu_start_cb, pattern=r"^q:start"),
        ],
        states=states,
        fallbacks=[
            CommandHandler("cancel", cmd_cancel),
            CommandHandler("lang", cmd_lang),
            CommandHandler("credits", cmd_credits),
            CommandHandler("help", cmd_help),
            CommandHandler("support", cmd_support),
            CommandHandler("donate", cmd_donate),
            CallbackQueryHandler(menu_start_cb, pattern=r"^q:start"),
            CallbackQueryHandler(language_cb_conv, pattern=r"^lang:"),
            MessageHandler(~filters.COMMAND, need_input_reply),
        ],
        allow_reentry=True,
        per_message=False,
    )


async def _post_init(application: Application) -> None:
    """Cache the bot username and publish the BotFather command menu."""
    try:
        me = await application.bot.get_me()
        application.bot_data["bot_username"] = me.username
    except Exception as exc:
        logger.warning("Could not cache the bot username: %s", exc)
    try:
        await application.bot.set_my_commands(
            [
                BotCommand("start", "Create a logo or an ad prompt"),
                BotCommand("credits", "Your credits and referral link"),
                BotCommand("lang", "Change the interface language"),
                BotCommand("help", "How to use the bot"),
                BotCommand("donate", "Support the bot with Stars"),
                BotCommand("support", "Contact support"),
                BotCommand("cancel", "Stop the questionnaire"),
            ]
        )
    except Exception as exc:
        logger.warning("Could not set the command menu: %s", exc)


def main() -> None:
    """Build the Telegram application and start polling."""
    if not config.token_is_set():
        raise SystemExit(
            "No bot token found.\n"
            "1. Copy .env.example and rename the copy to .env\n"
            "2. Put your token inside it: BOT_TOKEN=123456:ABC...\n"
            "(Get a token from @BotFather on Telegram.)"
        )

    store.configure()

    application = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .post_init(_post_init)
        .build()
    )

    application.add_handler(build_conversation_handler())

    # Commands - registered as fallbacks too, so they work mid-quiz
    for name, handler in (
        ("credits", cmd_credits),
        ("help", cmd_help),
        ("support", cmd_support),
        ("donate", cmd_donate),
        ("admin", cmd_admin),
        ("addcredits", cmd_addcredits),
    ):
        application.add_handler(CommandHandler(name, handler))
    application.add_handler(CommandHandler("lang", cmd_lang))

    # Callbacks outside the questionnaire
    application.add_handler(
        CallbackQueryHandler(fs_check_cb, pattern=r"^fs:check$")
    )
    application.add_handler(CallbackQueryHandler(donate_cb, pattern=r"^donate:"))
    application.add_handler(
        CallbackQueryHandler(admin_credit_cb, pattern=r"^admcred:")
    )
    application.add_handler(
        CallbackQueryHandler(language_cb_outside, pattern=r"^lang:")
    )

    # Payments: approve checkouts, then record + thank for the donation.
    # Registered BEFORE the catch-all non-text handler (first match wins).
    application.add_handler(PreCheckoutQueryHandler(on_precheckout))
    application.add_handler(
        MessageHandler(filters.SUCCESSFUL_PAYMENT, on_successful_payment)
    )
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, outside_text)
    )
    application.add_handler(
        MessageHandler(~filters.COMMAND & ~filters.TEXT, need_input_reply)
    )

    logger.info("TASMEEM AI %s is starting...", config.PROJECT_VERSION)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
