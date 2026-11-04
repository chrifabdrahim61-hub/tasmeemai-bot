"""Question catalogue for the TASMEEM AI questionnaire (QCM mode, Step 6).

This module is pure Python (no telegram imports) so the whole
questionnaire logic stays unit-testable.

Design principles (v2, "professional edition"):
- ONE theme per button: combined categories like "Restaurant / Cafe / Food"
  are gone. Instead the industry uses a two-level tree: the user first
  picks a FIELD (group), then a SPECIALTY (leaf). Every leaf is exactly
  one business theme.
- Every "Other" button opens a typed input: the user is asked to describe
  in his own words what he wants (any language - the knowledge base
  understands English, French, Arabic, Darija and Arabizi).
- More questions, wider descriptions: motif, audience, brand personality,
  typography feel and an optional tagline were added so the final prompt
  is built from a genuinely professional brief.

A Question is one step of the wizard:
- id           : unique key, used as conversation state and answers key
- kind         : "text"           user must type an answer
                 "text_with_skip" user types OR presses a skip button
                 "buttons"        user taps one option
                 "toggle"         user toggles several options, then Done
- prompt       : text shown to the user (English fallback)
- options      : Option(label, value) tuples for button/toggle kinds
- skip_if      : optional predicate(answers) -> True to skip this question

Answers are stored as {question_id: value} where value is the Option
value (English, stable) - labels are for display only. This separation
is what lets the knowledge base map answers to professional design
language.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

MAX_TEXT_LEN = 120
MAX_BRAND_LEN = 40
MAX_TAGLINE_LEN = 60


@dataclass(frozen=True)
class Option:
    """One tappable choice. `label` is shown, `value` is stored."""

    label: str
    value: str


@dataclass(frozen=True)
class Question:
    """One step of the questionnaire."""

    id: str
    kind: str
    prompt: str
    options: Tuple[Option, ...] = ()
    skip_if: Optional[Callable[[Dict[str, str]], bool]] = None
    max_len: int = MAX_TEXT_LEN


# ---------------------------------------------------------------------------
# The industry tree: one theme per button
# ---------------------------------------------------------------------------
# Level 1 = FIELD (group). Level 2 = SPECIALTY (leaf). Every leaf value has
# its own entry in knowledge.INDUSTRY_DETAILS, so the final prompt speaks
# the exact design language of the user's business.

INDUSTRY_GROUPS: Dict[str, Tuple[str, ...]] = {
    "food": ("restaurant", "cafe", "fastfood", "bakery", "juice"),
    "fashion": ("clothing", "beauty", "barber", "perfume", "jewelry"),
    "tech": ("startup", "dev", "web", "cyber"),
    "media": ("photo", "video", "design", "marketing"),
    "education": ("school", "library", "training"),
    "sports": ("gym", "club", "coach"),
    "services": ("delivery", "realestate", "construction", "shop"),
    "gaming": ("team", "studio"),
}

GROUP_VALUES: Tuple[str, ...] = tuple(INDUSTRY_GROUPS.keys())
ALL_LEAF_VALUES: Tuple[str, ...] = tuple(
    leaf for leaves in INDUSTRY_GROUPS.values() for leaf in leaves
)

# The 8 specialty questions, one per group (only the matching one is shown).
INDUSTRY_LEAF_QUESTIONS: Tuple[str, ...] = tuple(
    f"industry_{group}" for group in GROUP_VALUES
)

# Display-name override for the summary screen: specialty answers use a
# dedicated label instead of repeating "Field".
SUMMARY_KEY_OVERRIDES: Dict[str, str] = {
    f"industry_{group}": "sum_industry_leaf" for group in GROUP_VALUES
}


# ---------------------------------------------------------------------------
# Skip predicates
# ---------------------------------------------------------------------------

def _make_leaf_skipper(group_value: str) -> Callable[[Dict[str, str]], bool]:
    """Show the specialty question only when its field was chosen.

    Skipped as well when the specialty leaf was already answered by
    TYPING it directly on the field question ("coffee shop" -> cafe):
    the subtree is then already filled.
    """

    def skipper(answers: Dict[str, str]) -> bool:
        if answers.get("industry") != group_value:
            return True
        return bool(answers.get(f"industry_{group_value}"))

    return skipper


def _skip_industry_text(answers: Dict[str, str]) -> bool:
    """The typed-activity question appears only after an "Other" choice:
    either the "Other" field itself, or "Other" inside a specialty list.

    It is skipped when the user already typed the description directly on
    the field/specialty question (typing is accepted everywhere).
    """
    if answers.get("industry_text", "").strip():
        return True  # already described in his own words
    group = answers.get("industry", "")
    if group == "other":
        return False
    if group in GROUP_VALUES:
        return answers.get(f"industry_{group}", "") != "other"
    return True


def _make_other_skipper(question_id: str) -> Callable[[Dict[str, str]], bool]:
    """Generic: show the typed-input question only when "other" was picked.

    Skipped as well when a description was already typed directly on the
    question (typing is accepted on every question - the description is
    then stored under "<question_id>_text" ahead of time).
    """

    def skipper(answers: Dict[str, str]) -> bool:
        if answers.get(question_id) != "other":
            return True
        return bool(answers.get(f"{question_id}_text", "").strip())

    return skipper


def _skip_typography(answers: Dict[str, str]) -> bool:
    # A pure symbol / abstract mark cannot contain text - the user already
    # answered this implicitly by choosing the logo type.
    return answers.get("category") in ("symbol", "abstract")


def _skip_font_style(answers: Dict[str, str]) -> bool:
    """The typography-feel question only matters when text will be rendered."""
    if answers.get("category") in ("symbol", "abstract"):
        return True
    return answers.get("typography") == "none"


def _skip_tagline(answers: Dict[str, str]) -> bool:
    """A tagline needs a name to sit under and text support in the logo."""
    if answers.get("category") in ("symbol", "abstract"):
        return True
    if answers.get("brand_name", "") in ("", "skip"):
        return True
    return answers.get("typography") == "none"


def _skip_motif(answers: Dict[str, str]) -> bool:
    # Pure text logos (wordmark / lettermark) have no symbol to describe.
    return answers.get("category") in ("wordmark", "lettermark")


# ---------------------------------------------------------------------------
# Reusable option tuples
# ---------------------------------------------------------------------------

OTHER_OPTION = Option("Other (I will describe it)", "other")

CATEGORY_OPTIONS: Tuple[Option, ...] = (
    Option("Symbol only (icon)", "symbol"),
    Option("Letters / initials (lettermark)", "lettermark"),
    Option("Brand name as text (wordmark)", "wordmark"),
    Option("Symbol + name (combination)", "combination"),
    Option("Abstract shape", "abstract"),
    Option("Badge / emblem", "emblem"),
    Option("You decide for me", "auto"),
    OTHER_OPTION,
)

STYLE_OPTIONS: Tuple[Option, ...] = (
    Option("Minimalist", "minimalist"),
    Option("Maximalist (rich, detailed)", "maximalist"),
    Option("Modern", "modern"),
    Option("Luxury / premium", "luxury"),
    Option("Futuristic", "futuristic"),
    Option("Vintage / retro", "vintage"),
    Option("Handcrafted / organic", "handcrafted"),
    Option("You decide", "auto"),
    OTHER_OPTION,
)

COLORS_OPTIONS: Tuple[Option, ...] = (
    Option("Blue & white", "blue_white"),
    Option("Green & white", "green_white"),
    Option("Black & gold", "black_gold"),
    Option("Red & white", "red_white"),
    Option("Dark & premium", "dark_premium"),
    Option("Soft pastels", "soft_pastel"),
    Option("Bold & vivid", "bold_vivid"),
    Option("Surprise me", "surprise"),
    OTHER_OPTION,
)

MOTIF_OPTIONS: Tuple[Option, ...] = (
    Option("An object from my activity", "object"),
    Option("My initial letter (as a shape)", "letter"),
    Option("Pure geometric shapes", "geometric"),
    Option("Nature (leaf, mountain, wave...)", "nature"),
    Option("Premium symbol (crown, star...)", "premium"),
    Option("You decide", "auto"),
    OTHER_OPTION,
)

PERSONALITY_OPTIONS: Tuple[Option, ...] = (
    Option("Bold & powerful", "bold"),
    Option("Calm & trustworthy", "calm"),
    Option("Playful & friendly", "playful"),
    Option("Elegant & refined", "elegant"),
    Option("Innovative & modern", "innovative"),
    Option("You decide", "auto"),
    OTHER_OPTION,
)


# ---------------------------------------------------------------------------
# The questionnaire
# ---------------------------------------------------------------------------

QUESTIONS: List[Question] = [
    # -- 1. brand name ------------------------------------------------------
    Question(
        id="brand_name",
        kind="text_with_skip",
        prompt=(
            "What is the exact brand name?\n\n"
            "Type it now - it will be kept exactly as you write it, "
            "including capitalization, spaces and punctuation, because the "
            "prompt reproduces it letter for letter. Or press the button "
            "below if the logo should carry no name at all."
        ),
        options=(Option("Skip - no name", "skip"),),
        max_len=MAX_BRAND_LEN,
    ),
    # -- 2. industry: field (level 1 of the tree) ---------------------------
    Question(
        id="industry",
        kind="buttons",
        prompt=(
            "What field is your brand in?\n\n"
            "Pick the closest field first - I will then ask for your exact "
            "specialty, because a cafe and a restaurant do not get the same "
            "design language. If nothing fits, choose Other and describe it."
        ),
        options=(
            Option("Food & Drink", "food"),
            Option("Fashion & Beauty", "fashion"),
            Option("Tech & Digital", "tech"),
            Option("Media & Creative", "media"),
            Option("Education & Books", "education"),
            Option("Sports & Fitness", "sports"),
            Option("Business & Services", "services"),
            Option("Gaming & Esports", "gaming"),
            OTHER_OPTION,
        ),
    ),
    # -- 3. industry: specialty (level 2, one theme per button) -------------
    Question(
        id="industry_food",
        kind="buttons",
        prompt="Food & Drink - what is your exact specialty?",
        options=(
            Option("Restaurant", "restaurant"),
            Option("Cafe (coffee)", "cafe"),
            Option("Fast food", "fastfood"),
            Option("Bakery & pastry", "bakery"),
            Option("Juice & cold drinks", "juice"),
            OTHER_OPTION,
        ),
        skip_if=_make_leaf_skipper("food"),
    ),
    Question(
        id="industry_fashion",
        kind="buttons",
        prompt="Fashion & Beauty - what is your exact specialty?",
        options=(
            Option("Clothing brand", "clothing"),
            Option("Beauty & cosmetics", "beauty"),
            Option("Barber & hair salon", "barber"),
            Option("Perfume & fragrance", "perfume"),
            Option("Jewelry & accessories", "jewelry"),
            OTHER_OPTION,
        ),
        skip_if=_make_leaf_skipper("fashion"),
    ),
    Question(
        id="industry_tech",
        kind="buttons",
        prompt="Tech & Digital - what is your exact specialty?",
        options=(
            Option("AI & tech startup", "startup"),
            Option("App & software development", "dev"),
            Option("Web agency & digital services", "web"),
            Option("IT & cybersecurity", "cyber"),
            OTHER_OPTION,
        ),
        skip_if=_make_leaf_skipper("tech"),
    ),
    Question(
        id="industry_media",
        kind="buttons",
        prompt="Media & Creative - what is your exact specialty?",
        options=(
            Option("Photography", "photo"),
            Option("Video & filming", "video"),
            Option("Graphic design", "design"),
            Option("Marketing & social media", "marketing"),
            OTHER_OPTION,
        ),
        skip_if=_make_leaf_skipper("media"),
    ),
    Question(
        id="industry_education",
        kind="buttons",
        prompt="Education & Books - what is your exact specialty?",
        options=(
            Option("School & tutoring", "school"),
            Option("Library & bookstore", "library"),
            Option("Courses & training", "training"),
            OTHER_OPTION,
        ),
        skip_if=_make_leaf_skipper("education"),
    ),
    Question(
        id="industry_sports",
        kind="buttons",
        prompt="Sports & Fitness - what is your exact specialty?",
        options=(
            Option("Gym & fitness", "gym"),
            Option("Sports club & team", "club"),
            Option("Personal coach", "coach"),
            OTHER_OPTION,
        ),
        skip_if=_make_leaf_skipper("sports"),
    ),
    Question(
        id="industry_services",
        kind="buttons",
        prompt="Business & Services - what is your exact specialty?",
        options=(
            Option("Delivery & transport", "delivery"),
            Option("Real estate", "realestate"),
            Option("Construction & BTP", "construction"),
            Option("Shop & e-commerce", "shop"),
            OTHER_OPTION,
        ),
        skip_if=_make_leaf_skipper("services"),
    ),
    Question(
        id="industry_gaming",
        kind="buttons",
        prompt="Gaming & Esports - what is your exact specialty?",
        options=(
            Option("Gaming brand & esports team", "team"),
            Option("Game studio & developer", "studio"),
            OTHER_OPTION,
        ),
        skip_if=_make_leaf_skipper("gaming"),
    ),
    # -- 4. free description after "Other" ----------------------------------
    Question(
        id="industry_text",
        kind="text",
        prompt=(
            "Describe your activity in a few words - add everything you "
            "want me to know.\n\n"
            "Any language works: English, French, Arabic, Darija or "
            "Arabizi (example: 'bot for downloading books', 'بوت لتحميل "
            "الكتب', 'livraison de poulet grillé')."
        ),
        skip_if=_skip_industry_text,
    ),
    # -- 5. logo category ----------------------------------------------------
    Question(
        id="category",
        kind="buttons",
        prompt=(
            "What type of logo do you want?\n\n"
            "Symbol = an icon alone. Lettermark = stylized initials. "
            "Wordmark = the name set as the logo. Combination = icon + "
            "name. Emblem = the name inside a badge. If you have something "
            "else in mind, choose Other and describe it."
        ),
        options=CATEGORY_OPTIONS,
    ),
    Question(
        id="category_text",
        kind="text",
        prompt=(
            "Describe the logo type you want in your own words - add "
            "everything you want.\n\n"
            "Example: 'a shield with my initials inside'."
        ),
        skip_if=_make_other_skipper("category"),
    ),
    # -- 6. motif (what the symbol should evoke) -----------------------------
    Question(
        id="motif",
        kind="buttons",
        prompt=(
            "What should the symbol evoke?\n\n"
            "This is the heart of the concept: the main idea the icon is "
            "built from. Pick a direction, or let me choose creatively "
            "from your field."
        ),
        options=MOTIF_OPTIONS,
        skip_if=_skip_motif,
    ),
    Question(
        id="motif_text",
        kind="text",
        prompt=(
            "Describe what the symbol should evoke - add everything you "
            "want.\n\n"
            "Example: 'a lion merged with a coffee cup, without drawing a "
            "real animal'."
        ),
        skip_if=_make_other_skipper("motif"),
    ),
    # -- 7. typography --------------------------------------------------------
    Question(
        id="typography",
        kind="buttons",
        prompt=(
            "Should the logo include any text?\n\n"
            "Name = the full brand name. Initials = a monogram. Name under "
            "the symbol = the classic combination lockup."
        ),
        options=(
            Option("No text at all", "none"),
            Option("The brand name", "name"),
            Option("Initials only", "initials"),
            Option("Name under the symbol", "name_under"),
            Option("You decide", "auto"),
        ),
        skip_if=_skip_typography,
    ),
    # -- 8. typography feel ----------------------------------------------------
    Question(
        id="font_style",
        kind="buttons",
        prompt=(
            "What feel should the lettering have?\n\n"
            "The lettering carries the brand character: sharp and modern, "
            "classic and serif, rounded and friendly, or handwritten."
        ),
        options=(
            Option("Modern & clean", "modern_sans"),
            Option("Classic serif", "classic_serif"),
            Option("Rounded & friendly", "rounded"),
            Option("Script / handwritten", "script"),
            Option("Geometric & minimal", "geometric"),
            Option("You decide", "auto"),
        ),
        skip_if=_skip_font_style,
    ),
    # -- 9. tagline -------------------------------------------------------------
    Question(
        id="tagline",
        kind="text_with_skip",
        prompt=(
            "Add a short slogan under the name?\n\n"
            "Type your exact tagline (up to 60 characters) and it will be "
            "rendered in small letters under the brand name - spelled "
            "exactly as you write it. Or press the button for a logo "
            "without any slogan."
        ),
        options=(Option("Skip - no slogan", "skip"),),
        max_len=MAX_TAGLINE_LEN,
        skip_if=_skip_tagline,
    ),
    # -- 10. colors ---------------------------------------------------------------
    Question(
        id="colors",
        kind="buttons",
        prompt=(
            "Which color palette do you prefer?\n\n"
            "Colors decide how the logo feels: blue reassures, gold "
            "signals luxury, red stimulates appetite. A professional logo "
            "stays between 1 and 3 colors."
        ),
        options=COLORS_OPTIONS,
    ),
    Question(
        id="colors_text",
        kind="text",
        prompt=(
            "Type the colors you want - add everything you want.\n\n"
            "Any language is fine, for example: 'green and white', "
            "'vert et or', 'أخضر وأبيض', 'akhdar w abyad'."
        ),
        skip_if=_make_other_skipper("colors"),
    ),
    # -- 11. style ------------------------------------------------------------------
    Question(
        id="style",
        kind="buttons",
        prompt=(
            "Which visual style fits your brand best?\n\n"
            "Think of it as the design era: minimalist is timeless, "
            "futuristic is high-tech, vintage feels heritage, handcrafted "
            "feels warm and artisanal."
        ),
        options=STYLE_OPTIONS,
    ),
    Question(
        id="style_text",
        kind="text",
        prompt=(
            "Describe the style you want - add everything you want.\n\n"
            "Example: 'like an old pharmacy sign, but cleaner'."
        ),
        skip_if=_make_other_skipper("style"),
    ),
    # -- 12. audience ------------------------------------------------------------------
    Question(
        id="audience",
        kind="buttons",
        prompt=(
            "Who is your main audience?\n\n"
            "The same brand does not speak the same way to teenagers, "
            "families or companies - the design adapts to them. If your "
            "audience is something else, choose Other and describe it."
        ),
        options=(
            Option("Young & trendy", "young"),
            Option("Families", "family"),
            Option("Companies & professionals", "business"),
            Option("High-end clients", "premium"),
            Option("Local community", "local"),
            Option("A bit of everything", "broad"),
            Option("You decide", "auto"),
            OTHER_OPTION,
        ),
    ),
    Question(
        id="audience_text",
        kind="text",
        prompt=(
            "Describe your audience in your own words - add everything "
            "you want.\n\n"
            "Example: 'university students', 'desetudiants', 'طلاب الجامعة'."
        ),
        skip_if=_make_other_skipper("audience"),
    ),
    # -- 13. personality -----------------------------------------------------------------
    Question(
        id="personality",
        kind="buttons",
        prompt=(
            "If your brand were a person, what character would it have?\n\n"
            "This sets the attitude of every curve and line in the logo."
        ),
        options=PERSONALITY_OPTIONS,
    ),
    Question(
        id="personality_text",
        kind="text",
        prompt=(
            "Describe your brand character in your own words - add "
            "everything you want.\n\n"
            "Example: 'serious at work, but with a small wink'."
        ),
        skip_if=_make_other_skipper("personality"),
    ),
    # -- 14. dimension ---------------------------------------------------------------------
    Question(
        id="dimension",
        kind="buttons",
        prompt=(
            "Flat or dimensional rendering?\n\n"
            "Flat vector is the timeless standard for logos; 3D renders "
            "look premium but age faster. When in doubt, stay flat or "
            "slightly 3D."
        ),
        options=(
            Option("Flat vector (2D)", "flat"),
            Option("Slightly 3D", "slight_3d"),
            Option("Full premium 3D", "full_3d"),
            Option("You decide", "auto"),
        ),
    ),
    # -- 15. background -----------------------------------------------------------------------
    Question(
        id="background",
        kind="buttons",
        prompt=(
            "Which background do you prefer?\n\n"
            "Pure white is the safest for generators; dark backgrounds "
            "make gold and neon pop; isolated means no visible background "
            "at all (transparent-ready)."
        ),
        options=(
            Option("Pure white", "white"),
            Option("Dark", "dark"),
            Option("Isolated (no visible background)", "isolated"),
            Option("You decide", "auto"),
            OTHER_OPTION,
        ),
    ),
    Question(
        id="background_text",
        kind="text",
        prompt=(
            "Describe the background you want - add everything you "
            "want.\n\n"
            "Example: 'deep green background' or 'fond bleu nuit'."
        ),
        skip_if=_make_other_skipper("background"),
    ),
    # -- 16. usage --------------------------------------------------------------------------------
    Question(
        id="usage",
        kind="buttons",
        prompt=(
            "Where will the logo be used most?\n\n"
            "This guides composition, proportions and safe margins: a "
            "Telegram avatar must stay readable at tiny sizes, while a "
            "website header can breathe horizontally."
        ),
        options=(
            Option("Telegram avatar (square)", "telegram_avatar"),
            Option("Website header", "website"),
            Option("Social media posts", "social"),
            Option("Print / packaging", "print"),
            Option("Everywhere", "everywhere"),
            OTHER_OPTION,
        ),
    ),
    Question(
        id="usage_text",
        kind="text",
        prompt=(
            "Where will the logo be used? Describe it - add everything "
            "you want.\n\n"
            "Example: 'on my delivery trucks and the storefront'."
        ),
        skip_if=_make_other_skipper("usage"),
    ),
    # -- 17. exclusions -----------------------------------------------------------------------------
    Question(
        id="exclusions",
        kind="toggle",
        prompt=(
            "Anything to avoid?\n\n"
            "Tap an item to toggle it, then press Done. Mandatory "
            "restrictions (no humans, no animals, no faces) are always "
            "applied automatically, whether you select things here or not."
        ),
        options=(
            Option("Neon effects", "neon"),
            Option("Gradients", "gradients"),
            Option("Shadows", "shadows"),
            Option("Extra decorations", "decorations"),
            Option("Complex details", "complex"),
        ),
    ),
]

QUESTION_IDS: List[str] = [q.id for q in QUESTIONS]
QUESTIONS_BY_ID: Dict[str, Question] = {q.id: q for q in QUESTIONS}

# Special conversation states (not questions)
STATE_MENU = "menu"
STATE_CONFIRM = "confirm"


# ---------------------------------------------------------------------------
# Flow helpers (pure functions)
# ---------------------------------------------------------------------------

def first_question_id(answers: Dict[str, str]) -> Optional[str]:
    """First question that is not skipped, from the beginning."""
    return next_question_id(None, answers)


def next_question_id(current: Optional[str], answers: Dict[str, str]) -> Optional[str]:
    """Next non-skipped question after `current` (None = start).

    Returns None when the questionnaire is finished.
    """
    started = current is None
    for question in QUESTIONS:
        if not started:
            if question.id == current:
                started = True
            continue
        if question.skip_if and question.skip_if(answers):
            continue
        return question.id
    return None


def summary_key(question_id: str) -> str:
    """i18n key for the display name of one answer in the summary."""
    return SUMMARY_KEY_OVERRIDES.get(question_id, f"sum_{question_id}")


def option_label(question_id: str, value: str, lang: str = "en") -> str:
    """Display label for a stored value, in the requested language.

    Lookup order: i18n key opt_<question_id>_<value>, then the English
    label defined on the Option, then the raw value (free-text answers
    are stored as typed).
    """
    if value == "":
        return ""
    from engine import i18n

    translated = i18n.get(lang, f"opt_{question_id}_{value}")
    if translated:
        return translated
    question = QUESTIONS_BY_ID.get(question_id)
    if question is None:
        return value
    for option in question.options:
        if option.value == value:
            return option.label
    return value  # free-text answers are stored as typed


def validate_text_answer(question: Question, raw: str) -> Optional[str]:
    """Clean and validate a typed answer. None = invalid, re-ask."""
    cleaned = " ".join((raw or "").split())
    if not cleaned:
        return None
    if len(cleaned) > question.max_len:
        return None
    return cleaned


def option_rows(options: Tuple[Option, ...], per_row: int = 2) -> List[List[Option]]:
    """Split options into rows for an inline keyboard."""
    return [list(options[i : i + per_row]) for i in range(0, len(options), per_row)]


def toggle_exclusions(selected: set, value: str) -> set:
    """Toggle one exclusion option by VALUE. Returns a new set.

    Value-based (not index-based) on purpose: the callback_data of a
    toggle button carries the value itself, so the tapped button and the
    toggled item can never diverge. Unknown values are ignored.
    """
    result = set(selected)
    valid = {option.value for option in QUESTIONS_BY_ID["exclusions"].options}
    if value not in valid:
        return result
    if value in result:
        result.discard(value)
    else:
        result.add(value)
    return result


def build_answers_summary(
    answers: Dict[str, str],
    exclusions: Optional[set] = None,
    lang: str = "en",
    questions: Optional[List[Question]] = None,
) -> str:
    """Human-readable summary of all collected answers (skipped omitted).

    Walks ``questions`` (the logo catalogue by default); engine.modes
    passes each mode's own list so both questionnaires summarize well.
    """
    from engine import i18n

    questions = questions if questions is not None else QUESTIONS
    lines: List[str] = []
    for question in questions:
        if question.kind == "toggle":
            continue  # handled after the regular answers
        value = answers.get(question.id)
        if value is None:
            continue  # skipped or not reached
        label = option_label(question.id, value, lang)
        if label == "":
            continue
        display = i18n.t(lang, summary_key(question.id))
        lines.append(f"- {display}: {label}")

    selected = sorted(exclusions or set())
    if selected:
        labels = ", ".join(option_label("exclusions", v, lang) for v in selected)
        lines.append(f"- {i18n.t(lang, 'summary_avoid')}: {labels}")

    if not lines:
        return i18n.t(lang, "summary_empty")
    return "\n".join(lines)
