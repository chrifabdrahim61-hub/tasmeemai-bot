"""Social Media posts (ads) questionnaire - Step 8.

A second full questionnaire, built with the same professional standard
as the logo one ("make the details good like the logo"):

- trees with ONE theme per button: the business field reuses the exact
  logo industry tree (Food & Drink -> Restaurant / Cafe / ...), the
  goal of the post is a two-level tree (Sell & promote -> Sale /
  discount, New arrival, Flash sale...), and the visual scene is a
  two-level tree too (Product showcase -> Clean studio shot / Lifestyle
  scene / Close-up / Flat-lay...)
- every "Other" button opens a typed input, understood in English,
  French, Arabic, Darija and Arabizi (engine/knowledge.py)
- typing is accepted everywhere (bot.py routes typed text through
  knowledge.match_option exactly like the logo questionnaire)
- the user is asked for his brand name AND the @username of his brand
  or page, and whether he has a logo - the final message then tells him
  to PASTE THE LOGO IMAGE together with the prompt into the AI model
  (and reminds him the brand name / username are already embedded)

The SHARED questions (industry tree, style, colors, audience,
exclusions) are the very same Question objects as the logo
questionnaire: one id, one translation, one answer key. The
ads-specific ids are prefixed "ad_" and registered into
questions.QUESTIONS_BY_ID so every existing lookup (labels,
typed-answer matching, conversation states) sees both questionnaires.

This module is pure Python (no telegram imports).
"""

from __future__ import annotations

from typing import Callable, Dict, List, Tuple

from engine.questions import (  # noqa: F401 - re-exported for modes.py
    COLORS_OPTIONS,
    MAX_BRAND_LEN,
    MAX_TEXT_LEN,
    OTHER_OPTION,
    QUESTIONS_BY_ID,
    STYLE_OPTIONS,
    SUMMARY_KEY_OVERRIDES,
    Question,
    Option,
    _make_leaf_skipper,
    _make_other_skipper,
    _skip_industry_text,
)

MAX_USERNAME_LEN = 60
MAX_HEADLINE_LEN = 80


# ---------------------------------------------------------------------------
# Tree skip predicates (same semantics as the logo industry tree)
# ---------------------------------------------------------------------------

def _make_tree_skipper(root_id: str, group_value: str) -> Callable[[Dict[str, str]], bool]:
    """Show the subtree question only when its group was chosen.

    Skipped as well when the leaf was already answered by TYPING it
    directly on the group question ("giveaway" -> giveaway).
    """

    def skipper(answers: Dict[str, str]) -> bool:
        if answers.get(root_id) != group_value:
            return True
        return bool(answers.get(f"{root_id}_{group_value}"))

    return skipper


def _make_tree_text_skipper(
    root_id: str, groups: Tuple[str, ...]
) -> Callable[[Dict[str, str]], bool]:
    """The typed-input question after an "Other" choice in a tree.

    Appears when the group itself is "other" or when the chosen leaf is
    "other"; skipped when the description was already typed directly on
    the group/leaf question (typing is accepted everywhere).
    """

    def skipper(answers: Dict[str, str]) -> bool:
        if answers.get(f"{root_id}_text", "").strip():
            return True
        root = answers.get(root_id, "")
        if root == "other":
            return False
        if root in groups:
            return answers.get(f"{root_id}_{root}", "") != "other"
        return True

    return skipper


def _skip_headline(answers: Dict[str, str]) -> bool:
    """No headline when the visual carries no text at all."""
    return answers.get("ad_lang_text", "") == "none"


# ---------------------------------------------------------------------------
# The two ads-specific trees
# ---------------------------------------------------------------------------

# Level 1 -> level 2 of the GOAL tree (what is this post for?).
AD_GOAL_GROUPS: Dict[str, Tuple[str, ...]] = {
    "sales": ("product", "discount", "new", "flash"),
    "growth": ("giveaway", "contest", "follow", "engage"),
    "announce": ("opening", "event", "rebrand", "info"),
    "traffic": ("booking", "order", "visit", "download"),
}
AD_GOAL_LEAVES: Tuple[str, ...] = tuple(
    leaf for leaves in AD_GOAL_GROUPS.values() for leaf in leaves
)

# Level 1 -> level 2 of the VISUAL tree (what should the visual show?).
AD_VISUAL_GROUPS: Dict[str, Tuple[str, ...]] = {
    "product": ("studio", "lifestyle", "detail", "flatlay"),
    "people": ("model", "hands", "team", "crowd"),
    "graphic": ("typographic", "illustration", "shapes", "pattern"),
    "food": ("dish", "drink", "ingredients"),
}
AD_VISUAL_LEAVES: Tuple[str, ...] = tuple(
    leaf for leaves in AD_VISUAL_GROUPS.values() for leaf in leaves
)

# Trees handled by the generic "type a leaf -> fill the subtree" logic.
ADS_TREES: Dict[str, Dict[str, Tuple[str, ...]]] = {
    "ad_goal": AD_GOAL_GROUPS,
    "ad_visual": AD_VISUAL_GROUPS,
}


# ---------------------------------------------------------------------------
# The ads questionnaire (in walking order)
# ---------------------------------------------------------------------------
# The shared questions (industry tree, style, colors, audience,
# exclusions) are pulled from the logo catalogue by id, so the very
# same objects serve both modes.

_SHARED_IDS_IN_ORDER: Tuple[str, ...] = (
    "industry",
    "industry_food", "industry_fashion", "industry_tech", "industry_media",
    "industry_education", "industry_sports", "industry_services",
    "industry_gaming",
    "industry_text",
    "style", "style_text",
    "colors", "colors_text",
    "audience", "audience_text",
    "exclusions",
)


def _shared(question_id: str) -> Question:
    question = QUESTIONS_BY_ID.get(question_id)
    if question is None:  # pragma: no cover - programming error guard
        raise KeyError(f"shared question missing: {question_id}")
    return question


ADS_ONLY_QUESTIONS: List[Question] = [
    # -- 1. brand / page name ------------------------------------------------
    Question(
        id="ad_brand_name",
        kind="text_with_skip",
        prompt=(
            "What is the exact brand or page name for this post?\n\n"
            "Type it now - it will be kept exactly as you write it "
            "(capitalization, spaces, punctuation) and written into the "
            "prompt letter for letter. Or press the button if the visual "
            "should carry no name."
        ),
        options=(Option("Skip - no name", "skip"),),
        max_len=MAX_BRAND_LEN,
    ),
    # -- 2. username of the brand / page --------------------------------------
    Question(
        id="ad_username",
        kind="text_with_skip",
        prompt=(
            "What is the @username of your brand or page?\n\n"
            "Example: @mybrand - it goes into the prompt so the AI model "
            "can place it on the visual (or you can paste it together "
            "with the prompt). No username? Press the button."
        ),
        options=(Option("Skip - no username", "skip"),),
        max_len=MAX_USERNAME_LEN,
    ),
    # -- goal tree ------------------------------------------------------------
    Question(
        id="ad_goal",
        kind="buttons",
        prompt=(
            "What is this post for?\n\n"
            "The goal decides the whole composition: a flash sale needs "
            "urgency and a big price zone, a giveaway needs excitement, "
            "an announcement needs clarity. Pick the closest goal - I "
            "will then ask for the exact type."
        ),
        options=(
            Option("Sell & promote", "sales"),
            Option("Grow my page", "growth"),
            Option("Announce something", "announce"),
            Option("Bring clients & orders", "traffic"),
            OTHER_OPTION,
        ),
    ),
    Question(
        id="ad_goal_sales",
        kind="buttons",
        prompt="Sell & promote - what exactly is the goal?",
        options=(
            Option("Promote a product", "product"),
            Option("Sale / discount / promo code", "discount"),
            Option("New arrival / launch", "new"),
            Option("Flash sale / limited offer", "flash"),
            OTHER_OPTION,
        ),
        skip_if=_make_tree_skipper("ad_goal", "sales"),
    ),
    Question(
        id="ad_goal_growth",
        kind="buttons",
        prompt="Grow my page - what exactly is the goal?",
        options=(
            Option("Giveaway", "giveaway"),
            Option("Contest / challenge", "contest"),
            Option("Get more followers", "follow"),
            Option("Engagement post (question / poll)", "engage"),
            OTHER_OPTION,
        ),
        skip_if=_make_tree_skipper("ad_goal", "growth"),
    ),
    Question(
        id="ad_goal_announce",
        kind="buttons",
        prompt="Announce something - what exactly is the goal?",
        options=(
            Option("Grand opening", "opening"),
            Option("Event / invitation", "event"),
            Option("Rebranding / new look", "rebrand"),
            Option("General announcement", "info"),
            OTHER_OPTION,
        ),
        skip_if=_make_tree_skipper("ad_goal", "announce"),
    ),
    Question(
        id="ad_goal_traffic",
        kind="buttons",
        prompt="Bring clients & orders - what exactly is the goal?",
        options=(
            Option("Bookings / appointments", "booking"),
            Option("Direct orders / menu", "order"),
            Option("Store / website visits", "visit"),
            Option("App / bot downloads", "download"),
            OTHER_OPTION,
        ),
        skip_if=_make_tree_skipper("ad_goal", "traffic"),
    ),
    Question(
        id="ad_goal_text",
        kind="text",
        prompt=(
            "Describe the goal of the post in your own words - add "
            "everything you want.\n\n"
            "Example: 'soldes d'été -30% sur tout le magasin', 'تخفيضات "
            "الصيف', 'RAMADAN OFFER'."
        ),
        skip_if=_make_tree_text_skipper("ad_goal", tuple(AD_GOAL_GROUPS)),
    ),
    # -- platform & format ------------------------------------------------------
    Question(
        id="ad_platform",
        kind="buttons",
        prompt=(
            "Where will this post be published?\n\n"
            "Each platform has its own codes: Instagram loves clean "
            "aesthetics, TikTok needs bold contrast, a Telegram post "
            "stays readable on small screens. Nothing fits? Choose Other."
        ),
        options=(
            Option("Instagram", "instagram"),
            Option("Facebook", "facebook"),
            Option("TikTok", "tiktok"),
            Option("Telegram", "telegram"),
            Option("WhatsApp status", "whatsapp"),
            OTHER_OPTION,
        ),
    ),
    Question(
        id="ad_platform_text",
        kind="text",
        prompt=(
            "Which platform or place is it? Describe it - add everything "
            "you want.\n\n"
            "Example: 'Snapchat', 'LinkedIn page', 'printed flyer'."
        ),
        skip_if=_make_other_skipper("ad_platform"),
    ),
    Question(
        id="ad_format",
        kind="buttons",
        prompt=(
            "Which format do you need?\n\n"
            "Square is the classic feed post, 9:16 fills stories and "
            "reels full-screen, 4:5 takes more room in the feed, 16:9 "
            "works as a wide banner or a page cover."
        ),
        options=(
            Option("Square post (1:1)", "square"),
            Option("Story / Reels (9:16)", "story"),
            Option("Portrait post (4:5)", "portrait"),
            Option("Wide banner (16:9)", "banner"),
            Option("Page cover", "cover"),
            Option("You decide", "auto"),
            OTHER_OPTION,
        ),
    ),
    Question(
        id="ad_format_text",
        kind="text",
        prompt=(
            "Describe the format you want - add everything you want.\n\n"
            "Example: 'two story frames', 'banner for my YouTube channel'."
        ),
        skip_if=_make_other_skipper("ad_format"),
    ),
    # -- the offer ---------------------------------------------------------------
    Question(
        id="ad_offer",
        kind="text_with_skip",
        prompt=(
            "What exactly are you promoting?\n\n"
            "Describe the product, service, price, discount, date or "
            "place - everything the visual must show truthfully "
            "(example: 'pizza medium 2000 DA, free delivery'). Or press "
            "the button if you prefer to keep it general."
        ),
        options=(Option("Skip - no details", "skip"),),
        max_len=MAX_TEXT_LEN,
    ),
    # -- call to action -----------------------------------------------------------
    Question(
        id="ad_cta",
        kind="buttons",
        prompt=(
            "Which call-to-action should appear on the visual?\n\n"
            "The CTA is the small button or banner that tells people "
            "what to do next: buy, book, write, follow..."
        ),
        options=(
            Option("Shop now", "shop_now"),
            Option("Order now", "order_now"),
            Option("Book now", "book_now"),
            Option("Learn more", "learn_more"),
            Option("Send us a message", "dm"),
            Option("Call now", "call"),
            Option("WhatsApp us", "whatsapp"),
            Option("Follow us", "follow"),
            Option("Visit us", "visit"),
            Option("You decide", "auto"),
            OTHER_OPTION,
        ),
    ),
    Question(
        id="ad_cta_text",
        kind="text",
        prompt=(
            "Type the exact call-to-action text - add everything you "
            "want.\n\n"
            "Example: 'احجز مقعدك', 'Commandez ici', 'Get yours today'."
        ),
        skip_if=_make_other_skipper("ad_cta"),
    ),
    # -- language of the text on the visual ------------------------------------------
    Question(
        id="ad_lang_text",
        kind="buttons",
        prompt=(
            "Which language for the text ON the visual?\n\n"
            "The AI model must render the exact words: choosing the "
            "language avoids mixed alphabets. 'No text' gives you a "
            "clean visual and you add the words yourself in Canva or "
            "similar."
        ),
        options=(
            Option("English", "en"),
            Option("French", "fr"),
            Option("Arabic", "ar"),
            Option("Arabic + English", "ar_en"),
            Option("French + English", "fr_en"),
            Option("No text on the visual", "none"),
            OTHER_OPTION,
        ),
    ),
    Question(
        id="ad_lang_text_text",
        kind="text",
        prompt=(
            "Which language(s) for the text on the visual? Describe it - "
            "add everything you want.\n\n"
            "Example: 'arabic dialect with a small english price tag'."
        ),
        skip_if=_make_other_skipper("ad_lang_text"),
    ),
    # -- headline --------------------------------------------------------------------
    Question(
        id="ad_headline",
        kind="text_with_skip",
        prompt=(
            "What is the exact headline text to write on the visual?\n\n"
            "Type it exactly as it must appear (up to 80 characters) - "
            "spelling, capitalization and punctuation are kept letter "
            "for letter. Or press the button and I choose a short punchy "
            "line for you."
        ),
        options=(Option("You decide for me", "skip"),),
        max_len=MAX_HEADLINE_LEN,
        skip_if=_skip_headline,
    ),
    # -- visual scene tree --------------------------------------------------------------
    Question(
        id="ad_visual",
        kind="buttons",
        prompt=(
            "What should the visual show?\n\n"
            "This is the heart of the ad: a product alone, people using "
            "it, a graphic poster or an appetizing food shot. Pick a "
            "family first - I will then ask for the exact scene."
        ),
        options=(
            Option("Product showcase", "product"),
            Option("People & lifestyle", "people"),
            Option("Graphic & typography", "graphic"),
            Option("Food & drink shots", "food"),
            Option("You decide", "auto"),
            OTHER_OPTION,
        ),
    ),
    Question(
        id="ad_visual_product",
        kind="buttons",
        prompt="Product showcase - which scene fits best?",
        options=(
            Option("Clean studio shot", "studio"),
            Option("Lifestyle scene (in real use)", "lifestyle"),
            Option("Close-up on the details", "detail"),
            Option("Flat-lay top view", "flatlay"),
            OTHER_OPTION,
        ),
        skip_if=_make_tree_skipper("ad_visual", "product"),
    ),
    Question(
        id="ad_visual_people",
        kind="buttons",
        prompt="People & lifestyle - which scene fits best?",
        options=(
            Option("A model presenting it", "model"),
            Option("Hands holding the product", "hands"),
            Option("The team / staff", "team"),
            Option("An event crowd", "crowd"),
            OTHER_OPTION,
        ),
        skip_if=_make_tree_skipper("ad_visual", "people"),
    ),
    Question(
        id="ad_visual_graphic",
        kind="buttons",
        prompt="Graphic & typography - which scene fits best?",
        options=(
            Option("Bold typography poster", "typographic"),
            Option("Custom illustration", "illustration"),
            Option("Abstract shapes & gradients", "shapes"),
            Option("Branded pattern", "pattern"),
            OTHER_OPTION,
        ),
        skip_if=_make_tree_skipper("ad_visual", "graphic"),
    ),
    Question(
        id="ad_visual_food",
        kind="buttons",
        prompt="Food & drink shots - which scene fits best?",
        options=(
            Option("Plated dish", "dish"),
            Option("Drink / beverage shot", "drink"),
            Option("Fresh ingredients", "ingredients"),
            OTHER_OPTION,
        ),
        skip_if=_make_tree_skipper("ad_visual", "food"),
    ),
    Question(
        id="ad_visual_text",
        kind="text",
        prompt=(
            "Describe what the visual should show - add everything you "
            "want.\n\n"
            "Example: 'my blue sneaker floating with paint splashes', "
            "'صحن كسكس مع الخضرة', 'une boîte de chocolats ouverte'."
        ),
        skip_if=_make_tree_text_skipper("ad_visual", tuple(AD_VISUAL_GROUPS)),
    ),
    # -- logo -------------------------------------------------------------------------
    Question(
        id="ad_logo",
        kind="buttons",
        prompt=(
            "Do you have a logo to place on the visual?\n\n"
            "If yes, at the end I will tell you to PASTE YOUR LOGO IMAGE "
            "together with the prompt into the AI model - that is how it "
            "gets integrated. If you have no logo yet, you can create it "
            "with the Logo mode of this bot first."
        ),
        options=(
            Option("Yes - I'll attach it", "yes"),
            Option("No logo yet", "no"),
            Option("Use the name as the mark", "name_only"),
            Option("You decide", "auto"),
        ),
    ),
]

# The full walking order: ads questions + the shared catalogue objects.
ADS_QUESTIONS: List[Question] = (
    ADS_ONLY_QUESTIONS[:2]                       # brand name, username
    + [_shared(i) for i in _SHARED_IDS_IN_ORDER[:10]]   # industry tree
    + ADS_ONLY_QUESTIONS[2:25]                   # goal -> visual -> logo
    + [_shared(i) for i in _SHARED_IDS_IN_ORDER[10:]]   # style..exclusions
)

# ---------------------------------------------------------------------------
# Registration: make every lookup see both questionnaires
# ---------------------------------------------------------------------------

# 1. The union registry - option_label(), knowledge.match_option() and the
#    conversation-state builder all read questions.QUESTIONS_BY_ID.
for _q in ADS_ONLY_QUESTIONS:
    QUESTIONS_BY_ID.setdefault(_q.id, _q)

# 2. The summary display name for the ads tree leaves ("Details").
SUMMARY_KEY_OVERRIDES.update(
    {f"ad_goal_{group}": "sum_ad_leaf" for group in AD_GOAL_GROUPS}
)
SUMMARY_KEY_OVERRIDES.update(
    {f"ad_visual_{group}": "sum_ad_leaf" for group in AD_VISUAL_GROUPS}
)

ADS_QUESTION_IDS: List[str] = [q.id for q in ADS_QUESTIONS]
