"""Ad-creative prompt builder and validator (Step 8).

Turns the "Social Media posts (ads)" questionnaire answers into a
professional, ready-to-use image-generation prompt for ADVERTISING
VISUALS - the sibling of engine/builder.py (logos), with the same
quality bar:

- Stage 2 (normalize) : typed answers understood by engine/knowledge.py
- Stage 3 (resolve)   : "auto" / "Other" answers resolved with
                        goal-, platform- and industry-aware decisions
- Stage 4 (build)     : a professional ad prompt covering objective,
                        format & safe zones, scene, exact texts
                        (headline, brand name, @username, CTA) with
                        their language, composition hierarchy, colors,
                        typography, logo integration, mood, quality
                        requirements and negative constraints
- Stage 5 (validate)  : 100-point quality scoring, same philosophy as
                        the logo builder (exact-text preservation is
                        scored case-SENSITIVE)
- Stage 6 (deliver)   : DESIGN TYPE / DESIGN DIRECTION / IMAGE
                        GENERATION PROMPT + a "how to use it" block
                        that tells the client to PASTE HIS LOGO IMAGE
                        together with the prompt into the AI model, and
                        reminds him the brand name / @username are
                        already embedded (never retype them wrong).

The final prompt is always professional English. Client texts (brand
name, username, headline, offer) are never translated and keep their
exact spelling. Rule-based only - no AI services.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from engine import builder as logo_builder
from engine import knowledge
from engine.questions_ads import AD_GOAL_LEAVES, AD_VISUAL_LEAVES

# ---------------------------------------------------------------------------
# Phrase tables
# ---------------------------------------------------------------------------

PLATFORM_PHRASES = {
    "instagram": "an Instagram feed advertising visual",
    "facebook": "a Facebook advertising visual",
    "tiktok": "a TikTok video-cover advertising visual",
    "telegram": "a Telegram channel-post advertising visual",
    "whatsapp": "a WhatsApp Status advertising visual",
}

PLATFORM_LABELS = {
    "instagram": "Instagram post",
    "facebook": "Facebook post",
    "tiktok": "TikTok cover",
    "telegram": "Telegram post",
    "whatsapp": "WhatsApp Status",
    "custom": "Custom-platform post",
}

FORMAT_PHRASES = {
    "square": (
        "square 1:1 format (1080x1080 px), main subject centered with "
        "balanced margins"
    ),
    "story": (
        "vertical 9:16 story format (1080x1920 px), all key elements kept "
        "inside the safe zone, away from the very top and the very bottom "
        "of the frame"
    ),
    "portrait": (
        "portrait 4:5 feed format (1080x1350 px), main subject in the "
        "upper two thirds"
    ),
    "banner": (
        "wide 16:9 banner format (1920x1080 px), horizontal composition "
        "with the message readable at a glance"
    ),
    "cover": (
        "wide page-cover format with a centered, symmetric composition "
        "that survives any profile-picture overlap"
    ),
    "custom": (
        "the exact custom format requested by the client, with the key "
        "elements kept inside a comfortable safe zone"
    ),
}

FORMAT_LABELS = {
    "square": "Square post",
    "story": "Story / Reels",
    "portrait": "Portrait post",
    "banner": "Wide banner",
    "cover": "Page cover",
    "custom": "Custom format",
}

# Goal leaves -> the advertising objective sentence.
GOAL_PHRASES = {
    "product": "promote a product and drive direct sales",
    "discount": "announce a special discount or promo code with a clear price-focus",
    "new": "launch a new arrival and make it feel fresh and desirable",
    "flash": "push a flash sale with a strong feeling of urgency and scarcity",
    "giveaway": "announce a giveaway and maximize participation",
    "contest": "announce a contest or challenge and boost engagement",
    "follow": "grow the account and invite people to follow the page",
    "engage": "spark engagement with a question or poll that invites replies",
    "opening": "announce a grand opening and make the local audience feel invited",
    "event": "invite people to an event with its date and place clearly visible",
    "rebrand": "reveal a rebranding or a new look with a premium announcement feel",
    "info": "share an important announcement with maximum clarity",
    "booking": "drive bookings and appointments with a reassuring, organized feel",
    "order": "drive direct orders (menu, delivery, online order) with appetite appeal",
    "visit": "drive visits to the store or the website with a welcoming invitation",
    "download": "drive app or bot downloads with a modern, tech-savvy feel",
    "custom": "serve the custom goal described by the client",
}

# Goal leaves -> the mood the composition should carry.
GOAL_MOODS = {
    "product": "confident and aspirational",
    "discount": "energetic and urgent, with the discount as the hero",
    "new": "fresh, bright and discovery-driven",
    "flash": "high-energy and urgent, built around a bold countdown feel",
    "giveaway": "playful, generous and exciting",
    "contest": "competitive, playful and participative",
    "follow": "friendly and community-driven",
    "engage": "conversational, light and curiosity-driven",
    "opening": "festive, welcoming and proud",
    "event": "exciting and invitation-like",
    "rebrand": "premium, confident and new-era",
    "info": "clear, calm and trustworthy",
    "booking": "organized, reassuring and service-minded",
    "order": "appetizing and immediate",
    "visit": "warm, welcoming and local",
    "download": "modern, smooth and tech-forward",
    "custom": "aligned with the client goal",
}

# Visual leaves -> the scene description.
VISUAL_PHRASES = {
    "studio": "the product alone, shot studio-style on a clean seamless background",
    "lifestyle": "the product in a real lifestyle scene, shown in natural use",
    "detail": "a macro close-up revealing the product texture and craftsmanship",
    "flatlay": "a top-view flat-lay arrangement of the product with tasteful props",
    "model": "a model presenting or using the product in a natural, flattering pose",
    "hands": "hands holding or using the product, framed close and personal",
    "team": "the team or staff of the business, welcoming and professional",
    "crowd": "a lively event crowd with an energetic, festive atmosphere",
    "typographic": "a bold typographic poster where the words themselves are the design",
    "illustration": "a custom illustration that tells the story of the offer",
    "shapes": "abstract geometric shapes and smooth gradients carrying the message",
    "pattern": "a branded repeating-pattern backdrop with strong graphic rhythm",
    "dish": "an appetizing plated-dish shot, restaurant-quality styling",
    "drink": "a refreshing drink shot with condensation, splash and fresh light",
    "ingredients": "fresh ingredients artfully arranged around the hero product",
    "custom": "the custom scene described by the client",
}

# CTA values -> the exact English button text.
CTA_LABELS = {
    "shop_now": "Shop Now",
    "order_now": "Order Now",
    "book_now": "Book Now",
    "learn_more": "Learn More",
    "dm": "Send us a message",
    "call": "Call Now",
    "whatsapp": "WhatsApp us",
    "follow": "Follow Us",
    "visit": "Visit Us",
}

CTA_PHRASES = {
    value: f'a clearly visible call-to-action button or banner reading "{text}"'
    for value, text in CTA_LABELS.items()
}
CTA_PHRASES["custom"] = (
    'a clearly visible call-to-action button or banner reading the exact '
    'text provided by the client'
)

# Language of the texts baked into the visual.
LANG_TEXT_PHRASES = {
    "en": "All text on the visual is in English only, spelled perfectly.",
    "fr": "All text on the visual is in French only, spelled perfectly.",
    "ar": (
        "All text on the visual is in Arabic only, written right-to-left "
        "with correct, natural letter connections and perfect spelling."
    ),
    "ar_en": (
        "The visual is bilingual: Arabic as the main text and English as "
        "the secondary line, both spelled perfectly and never mixed inside "
        "the same word."
    ),
    "fr_en": (
        "The visual is bilingual: French as the main text and English as "
        "the secondary line, both spelled perfectly and never mixed inside "
        "the same word."
    ),
    "none": (
        "Absolutely no text baked into the image: no words, no letters, no "
        "numbers, no fake lettering - the client will add the exact text "
        "later. Leave clean space where the text will go."
    ),
    "custom": (
        "The text on the visual follows the exact language request of the "
        "client, spelled perfectly."
    ),
}

# Logo integration behaviour.
LOGO_PHRASES = {
    "yes": (
        "The brand logo image is provided together with this prompt: "
        "integrate that exact logo cleanly on the composition, never "
        "distort, stretch, recolor or redraw it."
    ),
    "no": (
        "Do not invent a logo: leave a clean, uncluttered reserved area "
        "where the client will place his own logo later."
    ),
    "name_only": (
        "No logo image: set the brand name in clean professional type as "
        "the brand mark of the composition."
    ),
    "auto": (
        "Reserve a subtle corner area for the brand mark; if no logo "
        "image is provided together with the prompt, keep the composition "
        "balanced without inventing one."
    ),
}

# "You decide" CTA, derived from the goal leaf.
GOAL_DEFAULT_CTA = {
    "product": "shop_now",
    "discount": "order_now",
    "new": "learn_more",
    "flash": "order_now",
    "giveaway": "follow",
    "contest": "follow",
    "follow": "follow",
    "engage": "dm",
    "opening": "visit",
    "event": "dm",
    "rebrand": "learn_more",
    "info": "learn_more",
    "booking": "book_now",
    "order": "order_now",
    "visit": "visit",
    "download": "learn_more",
}

STYLE_PHRASES = logo_builder.STYLE_PHRASES
STYLE_KEYWORDS = logo_builder.STYLE_KEYWORDS
STYLE_LABELS = logo_builder.STYLE_LABELS
AUDIENCE_PHRASES = logo_builder.AUDIENCE_PHRASES
PALETTE_COLORS = logo_builder.PALETTE_COLORS
EXCLUSION_PHRASES = logo_builder.EXCLUSION_PHRASES

# Mandatory advertising restrictions (always applied).
BASE_NEGATIVE_ITEMS = [
    "gibberish text", "misspelled words", "invented extra text",
    "watermarks", "distorted or stretched logo", "blurry elements",
    "cluttered layout", "low resolution", "pixelated edges",
]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class AdSpec:
    """Fully resolved ad-creative specification (no 'auto' left)."""

    brand_name: str = ""
    username: str = ""
    offer: str = ""
    headline: str = ""              # "" when skipped / no-text mode
    headline_auto: bool = False     # user let the bot choose the line
    industry: str = "other"
    industry_text_raw: str = ""
    goal: str = "info"              # resolved goal leaf
    goal_custom: str = ""
    platform: str = "instagram"
    platform_custom: str = ""
    format: str = "square"
    format_custom: str = ""
    cta: str = "auto"               # resolved CTA value or "custom"/"none"
    cta_custom: str = ""
    lang_text: str = "en"
    lang_custom: str = ""
    visual: str = "studio"
    visual_custom: str = ""
    logo: str = "auto"              # yes / no / name_only / auto
    style: str = "modern"
    style_raw: str = ""
    colors: List[str] = field(default_factory=list)
    colors_raw: str = ""
    audience: str = "broad"
    audience_raw: str = ""
    exclusions: List[str] = field(default_factory=list)


@dataclass
class GeneratedPrompt:
    """Same deliverable shape as the logo builder (bot.py renders both).

    The extra ``logo`` field carries the client's answer so the renderer
    can adapt the how-to-use block (paste the logo vs. create it first).
    """

    design_type: str
    design_direction: str
    image_prompt: str
    restrictions: List[str]
    score: int = 0
    issues: List[str] = field(default_factory=list)
    subscores: Dict[str, int] = field(default_factory=dict)
    logo: str = ""                  # yes / no / name_only / auto (ads only)


# ---------------------------------------------------------------------------
# Stage 3 - resolve ambiguity
# ---------------------------------------------------------------------------

def _resolve_industry(spec: AdSpec, answers: Dict[str, str]) -> None:
    """Same two-level industry resolution as the logo builder."""
    group = answers.get("industry", "other") or "other"
    leaf = answers.get(f"industry_{group}", "") if group != "other" else ""
    typed = answers.get("industry_text", "").strip()

    if group in knowledge.INDUSTRY_DETAILS and group != "other":
        spec.industry = group
        return
    if leaf in knowledge.INDUSTRY_DETAILS and leaf != "other":
        spec.industry = leaf
        return
    if typed:
        spec.industry_text_raw = typed
        matched = knowledge.match_industry(typed)
        if matched:
            spec.industry = matched
            spec.industry_text_raw = ""
            return
    spec.industry = "other"


def _resolve_tree(
    answers: Dict[str, str],
    root_id: str,
    leaves: tuple,
    text_key: str,
    default: str,
) -> tuple:
    """Generic tree resolution -> (value, custom_text)."""
    group = answers.get(root_id, "") or ""
    leaf = answers.get(f"{root_id}_{group}", "") if group else ""
    if leaf in leaves and leaf != "other":
        return leaf, ""
    typed = (answers.get(text_key, "") or "").strip()
    if group == "other" or leaf == "other":
        return "custom", typed
    return default, typed


def resolve_ads_spec(
    answers: Dict[str, str],
    exclusions: Optional[Set[str]] = None,
) -> AdSpec:
    """Turn raw answers into a complete AdSpec (no 'auto' left)."""
    answers = answers or {}
    spec = AdSpec()

    def clean(key: str) -> str:
        value = (answers.get(key, "") or "").strip()
        return "" if value in ("", "skip") else value

    spec.brand_name = clean("ad_brand_name")
    spec.username = clean("ad_username")
    spec.offer = clean("ad_offer")

    # Headline: kept exactly as typed (case-sensitive), unless skipped.
    if answers.get("ad_lang_text", "") == "none":
        spec.headline = ""
    else:
        raw = (answers.get("ad_headline", "") or "").strip()
        if raw in ("", "skip"):
            spec.headline = ""
            spec.headline_auto = True
        else:
            spec.headline = raw

    _resolve_industry(spec, answers)

    # Goal tree.
    goal, goal_custom = _resolve_tree(
        answers, "ad_goal", AD_GOAL_LEAVES, "ad_goal_text", "info"
    )
    spec.goal, spec.goal_custom = goal, goal_custom

    # Platform.
    platform = answers.get("ad_platform", "")
    if not platform:
        spec.platform = "instagram"
    elif platform not in PLATFORM_PHRASES:
        typed = (answers.get("ad_platform_text", "") or "").strip()
        spec.platform = "custom"
        spec.platform_custom = typed or platform
    else:
        spec.platform = platform

    # Format.
    fmt = answers.get("ad_format", "")
    if fmt == "other":
        spec.format = "custom"
        spec.format_custom = (answers.get("ad_format_text", "") or "").strip()
    elif fmt not in FORMAT_PHRASES:
        spec.format = "square"
    else:
        spec.format = fmt

    # Call to action.
    cta = answers.get("ad_cta", "")
    if cta == "other":
        spec.cta = "custom"
        spec.cta_custom = (answers.get("ad_cta_text", "") or "").strip()
    elif cta in ("", "auto", None):
        spec.cta = GOAL_DEFAULT_CTA.get(spec.goal, "learn_more")
    elif cta in CTA_PHRASES:
        spec.cta = cta
    else:  # hardening: unknown value
        spec.cta = GOAL_DEFAULT_CTA.get(spec.goal, "learn_more")

    # Language of the on-image text.
    lang = answers.get("ad_lang_text", "")
    if lang == "other":
        spec.lang_text = "custom"
        spec.lang_custom = (answers.get("ad_lang_text_text", "") or "").strip()
    elif lang in LANG_TEXT_PHRASES:
        spec.lang_text = lang
    else:  # hardening: unknown value
        spec.lang_text = "en"

    # Visual scene tree.
    visual, visual_custom = _resolve_tree(
        answers, "ad_visual", AD_VISUAL_LEAVES, "ad_visual_text", "studio"
    )
    spec.visual, spec.visual_custom = visual, visual_custom

    # Logo.
    logo = answers.get("ad_logo", "auto")
    spec.logo = logo if logo in LOGO_PHRASES else "auto"

    # Style: industry-aware default when "auto"; typed Other is matched.
    style = answers.get("style", "auto")
    details = knowledge.INDUSTRY_DETAILS[spec.industry]
    if style == "other":
        spec.style_raw = (answers.get("style_text", "") or "").strip()
        matched = knowledge.match_style(spec.style_raw) if spec.style_raw else None
        style = matched or "auto"
    if style in ("", "auto", None):
        style = details["default_style"]
    if style not in STYLE_PHRASES:
        style = details["default_style"]
    spec.style = style

    # Colors.
    raw_colors = answers.get("colors", "surprise")
    if raw_colors == "other":
        typed = (answers.get("colors_text", "") or "").strip()
        spec.colors_raw = typed
        spec.colors = knowledge.extract_colors(typed) if typed else []
    elif raw_colors == "surprise":
        spec.colors = list(details["surprise_palette"])
    else:
        spec.colors = list(PALETTE_COLORS.get(raw_colors, []))

    # Audience.
    audience = answers.get("audience", "auto")
    if audience == "other":
        spec.audience_raw = (answers.get("audience_text", "") or "").strip()
        audience = "custom" if spec.audience_raw else "auto"
    if audience in ("", "auto", None):
        audience = "broad"
    if audience != "custom" and audience not in AUDIENCE_PHRASES:
        audience = "broad"
    if audience == "custom" and not spec.audience_raw:
        audience = "broad"
    spec.audience = audience

    # Exclusions, in the questionnaire's option order.
    order = ["neon", "gradients", "shadows", "decorations", "complex"]
    spec.exclusions = [e for e in order if e in (exclusions or set())]
    return spec


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _join_colors(colors: List[str]) -> str:
    if not colors:
        return ""
    if len(colors) == 1:
        return colors[0]
    if len(colors) == 2:
        return f"{colors[0]} and {colors[1]}"
    return ", ".join(colors[:-1]) + " and " + colors[-1]


# ---------------------------------------------------------------------------
# Stage 4 - build the ad prompt
# ---------------------------------------------------------------------------

def _headline_sentence(spec: AdSpec) -> str:
    if spec.lang_text == "none":
        return ""
    if spec.headline:
        return (
            f'Render the exact headline "{spec.headline}" as the dominant '
            "text of the composition, spelled exactly as written, with no "
            "additional words invented."
        )
    if spec.headline_auto:
        return (
            "Choose a very short punchy headline (2-4 words maximum) that "
            "matches the goal, spelled perfectly - it is the only headline."
        )
    return ""


def _brand_sentence(spec: AdSpec) -> str:
    parts: List[str] = []
    if spec.brand_name:
        parts.append(
            f'The brand name "{spec.brand_name}" must appear spelled '
            "exactly as written."
        )
    if spec.username:
        parts.append(
            f'The page username "{spec.username}" must appear spelled '
            "exactly as written (keep the @)."
        )
    return " ".join(parts)


def _composition_sentence(spec: AdSpec) -> str:
    hierarchy = (
        "Organize a clear advertising hierarchy: one dominant focal point, "
        "the headline in the strongest reading position, the brand name "
        "and logo clearly visible, and the call-to-action in a natural "
        "clicking zone."
    )
    if spec.logo == "no":
        hierarchy = (
            "Organize a clear advertising hierarchy: one dominant focal "
            "point, the headline in the strongest reading position, and a "
            "clean reserved area for the logo and the call-to-action."
        )
    return hierarchy


def build_ads_prompt(spec: AdSpec) -> str:
    """Assemble the complete English ad prompt (one professional paragraph)."""
    details = knowledge.INDUSTRY_DETAILS[spec.industry]

    # 1. Objective
    if spec.platform == "custom":
        objective = (
            "Design a professional, high-converting advertising visual for "
            f'the client\'s platform "{spec.platform_custom}"'
        )
    else:
        objective = (
            f"Design a professional, high-converting advertising visual: "
            f"{PLATFORM_PHRASES[spec.platform]}"
        )
    if spec.format == "custom":
        objective += f' in a custom format: "{spec.format_custom}"'
    else:
        objective += f" in {FORMAT_PHRASES[spec.format]}"
    objective += "."

    # 2. Goal & mood
    if spec.goal == "custom" and spec.goal_custom:
        goal_line = (
            f'Goal of the post: "{spec.goal_custom}" - the composition '
            "must serve this goal directly."
        )
        mood = "The mood matches this goal."
    else:
        goal_line = f"Goal of the post: {GOAL_PHRASES.get(spec.goal, GOAL_PHRASES['info'])}."
        mood = (
            f"The overall mood is {GOAL_MOODS.get(spec.goal, GOAL_MOODS['info'])}."
        )

    # 3. Brand context
    context = f"The brand is {details['context']}."
    if spec.industry_text_raw:
        context += f' The owner describes the activity as: "{spec.industry_text_raw}".'

    # 4. Scene / subject
    if spec.visual == "custom" and spec.visual_custom:
        scene = f'The visual shows: "{spec.visual_custom}".'
    else:
        scene = f"The visual shows {VISUAL_PHRASES.get(spec.visual, VISUAL_PHRASES['studio'])}."
    if spec.offer:
        scene += f' Truthfully showcase this offer: "{spec.offer}" - nothing invented.'

    # 5. Exact texts
    texts = _brand_sentence(spec)
    headline = _headline_sentence(spec)
    if headline:
        texts = (texts + " " + headline).strip()
    if spec.cta == "custom" and spec.cta_custom:
        cta_sentence = (
            "Add a clearly visible call-to-action button or banner reading "
            f'"{spec.cta_custom}", spelled exactly as written.'
        )
    elif spec.cta == "none":
        cta_sentence = ""
    elif spec.cta in CTA_PHRASES:
        cta_sentence = f"Add {CTA_PHRASES[spec.cta]}."
    else:
        cta_sentence = ""
    if spec.lang_text == "custom" and spec.lang_custom:
        lang_sentence = (
            "Text language on the visual: "
            f'"{spec.lang_custom}" - spelled perfectly, no mixed alphabets.'
        )
    else:
        lang_sentence = LANG_TEXT_PHRASES.get(spec.lang_text, LANG_TEXT_PHRASES["en"])
    if texts:
        texts = texts + " " + cta_sentence if cta_sentence else texts
    else:
        texts = cta_sentence
    if texts:
        texts = texts + " " + lang_sentence
    else:
        texts = lang_sentence

    # 6. Logo integration
    logo_line = LOGO_PHRASES.get(spec.logo, LOGO_PHRASES["auto"])

    # 7. Style
    style_line = f"Visual direction: {STYLE_PHRASES[spec.style]}."

    # 8. Composition & hierarchy
    composition = _composition_sentence(spec)
    if spec.audience == "custom":
        composition += (
            " Target audience: the owner describes it as "
            f'"{spec.audience_raw}".'
        )
    else:
        composition += f" Target audience: {AUDIENCE_PHRASES[spec.audience]}."

    # 9. Colors
    if spec.colors:
        palette = (
            f"Use a restrained color palette of {_join_colors(spec.colors)} "
            "with strong advertising contrast."
        )
    elif spec.colors_raw:
        palette = (
            "Use a professional color palette that follows the client's "
            f'color request: "{spec.colors_raw}", with strong contrast.'
        )
    else:
        palette = (
            "Use a restrained, professional color palette with strong "
            "advertising contrast."
        )

    # 10. Typography feel
    if spec.lang_text == "none":
        typography = ""
    else:
        font = logo_builder.STYLE_FONT_DEFAULT.get(spec.style, "modern_sans")
        typography = (
            f"Typography feel: {logo_builder.FONT_PHRASES[font]} - every "
            "word stays perfectly readable at first glance."
        )

    # 11. Quality requirements
    quality = (
        "The final visual must look like a professional advertising "
        "campaign asset: high resolution, crisp edges, realistic lighting, "
        "clean composition, ready to publish."
    )

    # 12. Negative constraints
    negative_items = list(BASE_NEGATIVE_ITEMS)
    for exclusion in spec.exclusions:
        negative_items.append(EXCLUSION_PHRASES[exclusion])
    negatives = "Strictly avoid: " + ", ".join(negative_items) + "."

    parts = [
        objective, goal_line, mood, context, scene, texts, logo_line,
        style_line, composition, palette, typography, quality, negatives,
    ]
    return " ".join(p for p in parts if p)


def build_ads_restrictions(spec: AdSpec) -> List[str]:
    """Internal quality-gate list (not displayed, mirrors the logo builder)."""
    lines = [
        "No watermarks, no stock-agency badges.",
        "No gibberish, misspelled or invented text anywhere.",
        "No distorted, stretched, recolored or redrawn client logo.",
        "No cluttered layout: one clear focal point and a clean hierarchy.",
        "No low-resolution or pixelated output.",
    ]
    if spec.lang_text == "none":
        lines.append(
            "No text baked into the image: the client adds the words later."
        )
    elif spec.headline:
        lines.append(
            "Use only the provided headline, brand name, username and "
            "call-to-action - no other words."
        )
    user = [EXCLUSION_PHRASES[e] for e in spec.exclusions]
    if user:
        lines.append("Also avoid: " + ", ".join(user) + ".")
    return lines


def build_ads_type(spec: AdSpec) -> str:
    """DESIGN TYPE line, e.g. "Instagram post - Story / Reels - Flash sale"."""
    platform = PLATFORM_LABELS.get(spec.platform, "Custom platform")
    if spec.platform == "custom" and spec.platform_custom:
        platform = spec.platform_custom.title()
    fmt = FORMAT_LABELS.get(spec.format, "Custom format")
    if spec.goal == "custom":
        goal = "Custom goal"
    else:
        goal = spec.goal.replace("_", " ").title()
    return f"{platform} - {fmt} - {goal}"


def build_ads_direction(spec: AdSpec) -> str:
    """Short DESIGN DIRECTION description."""
    style = STYLE_LABELS.get(spec.style, spec.style.title())
    details = knowledge.INDUSTRY_DETAILS[spec.industry]
    name_part = f' for "{spec.brand_name}"' if spec.brand_name else ""
    direction = f"{style} ad creative{name_part} - {details['context']}."
    if spec.colors:
        direction += f" Palette: {_join_colors(spec.colors)}."
    if spec.username:
        direction += f" Page: {spec.username}."
    return direction


# ---------------------------------------------------------------------------
# Stage 5 - 100-point validation
# ---------------------------------------------------------------------------

def validate_ads(spec: AdSpec, generated: GeneratedPrompt) -> GeneratedPrompt:
    """Score the ad prompt on the same 100-point philosophy.

    headline 15 | brand+username 15 | platform+format 15 | goal 10 |
    scene 10 | colors 10 | CTA 10 | language 5 | composition 5 |
    quality 5 = 100
    """
    issues: List[str] = []
    prompt = generated.image_prompt
    low = prompt.lower()
    sub: Dict[str, int] = {}

    # Exact headline (15) - case-SENSITIVE like the logo brand name.
    if spec.lang_text == "none":
        sub["headline"] = 15 if "no text baked into the image" in low else 0
        if sub["headline"] == 0:
            issues.append("text-free intent not clearly stated")
    elif spec.headline:
        sub["headline"] = 15 if spec.headline in prompt else 0
        if sub["headline"] == 0:
            issues.append("headline missing or altered in the prompt")
    else:
        sub["headline"] = 15 if "punchy headline" in low else 10
        if sub["headline"] < 15:
            issues.append("auto-headline intent not fully stated")

    # Brand + username (15) - case-SENSITIVE.
    score = 0
    if spec.brand_name:
        score += 8 if spec.brand_name in prompt else 0
    else:
        score += 8
    if spec.username:
        score += 7 if spec.username in prompt else 0
    else:
        score += 7
    sub["brand"] = score
    if score < 15:
        issues.append("brand name or username missing or altered")

    # Platform + format (15).
    score = 0
    if spec.platform == "custom":
        score += 8 if spec.platform_custom.lower() in low else 0
    else:
        score += 8 if PLATFORM_PHRASES[spec.platform].lower() in low else 0
    if spec.format == "custom":
        score += 7 if spec.format_custom.lower() in low else 0
    else:
        score += 7 if FORMAT_PHRASES[spec.format].lower() in low else 0
    sub["placement"] = score
    if score < 15:
        issues.append("platform or format requirement missing")

    # Goal (10).
    if spec.goal == "custom":
        sub["goal"] = 10 if spec.goal_custom.lower() in low else 0
    else:
        phrase = GOAL_PHRASES[spec.goal]
        keywords = [w for w in phrase.split() if len(w) >= 5]
        sub["goal"] = 10 if any(w in low for w in keywords) else 0
    if sub["goal"] == 0:
        issues.append("goal of the post not described")

    # Scene (10).
    if spec.visual == "custom":
        sub["scene"] = 10 if spec.visual_custom.lower() in low else 0
    else:
        phrase = VISUAL_PHRASES[spec.visual]
        keywords = [w for w in phrase.split() if len(w) >= 5]
        sub["scene"] = 10 if any(w in low for w in keywords) else 0
    if sub["scene"] == 0:
        issues.append("visual scene not described")

    # Colors (10).
    if spec.colors:
        hit = sum(1 for c in spec.colors if c.lower() in low)
        sub["colors"] = round(10 * hit / len(spec.colors))
        if sub["colors"] < 10:
            issues.append("some requested colors missing from the prompt")
    elif spec.colors_raw:
        sub["colors"] = 10 if spec.colors_raw.lower() in low else 0
        if sub["colors"] == 0:
            issues.append("raw color request not preserved")
    else:
        sub["colors"] = 10 if "color palette" in low else 0

    # CTA (10).
    if spec.lang_text == "none" or spec.cta == "none":
        sub["cta"] = 10  # legitimately absent
    elif spec.cta == "custom":
        sub["cta"] = 10 if spec.cta_custom in prompt else 0
    else:
        sub["cta"] = 10 if CTA_LABELS.get(spec.cta, "") in prompt else 0
    if sub["cta"] == 0:
        issues.append("call-to-action missing or altered")

    # Language of the texts (5).
    if spec.lang_text == "custom":
        sub["language"] = 5 if spec.lang_custom.lower() in low else 0
    else:
        sub["language"] = 5 if LANG_TEXT_PHRASES[spec.lang_text].lower() in low else 0
    if sub["language"] == 0:
        issues.append("text language instruction missing")

    # Composition & audience (5).
    sub["composition"] = 5 if "hierarchy" in low else 0
    if sub["composition"] == 0:
        issues.append("composition hierarchy missing")

    # Quality requirements (5).
    sub["quality"] = (
        (3 if "high resolution" in low else 0) + (2 if "professional" in low else 0)
    )
    if sub["quality"] < 5:
        issues.append("technical quality requirements incomplete")

    generated.subscores = sub
    generated.score = min(100, sum(sub.values()))
    generated.issues = issues
    return generated


# ---------------------------------------------------------------------------
# Stage 6 - one-call generation
# ---------------------------------------------------------------------------

def generate_ads_prompt(
    answers: Dict[str, str],
    exclusions: Optional[Set[str]] = None,
) -> GeneratedPrompt:
    """Full pipeline: ads answers -> validated deliverable."""
    spec = resolve_ads_spec(answers, exclusions)
    generated = GeneratedPrompt(
        design_type=build_ads_type(spec),
        design_direction=build_ads_direction(spec),
        image_prompt=build_ads_prompt(spec),
        restrictions=build_ads_restrictions(spec),
        logo=spec.logo,
    )
    return validate_ads(spec, generated)
