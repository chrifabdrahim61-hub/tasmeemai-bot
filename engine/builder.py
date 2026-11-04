"""Prompt builder and validator (Steps 5-6).

Turns the questionnaire answers into a professional, ready-to-use
image-generation prompt for LOGOS ONLY, following the "Logo Prompt
Engineer" master skill:

- Stage 2 (normalize)  : done by engine/knowledge.py for typed answers
- Stage 3 (ambiguity)  : "auto" answers and "Other" free-text inputs are
                         resolved with industry-aware creative decisions
                         (resolve_spec) using the multilingual matchers
- Stage 4 (build)      : the prompt describes the 12 required parts
                         (section 11 of the master skill), enriched with
                         the v2 brief: motif, brand character, target
                         audience, typography feel and optional tagline
- Stage 5 (validate)   : 100-point quality scoring (section 15)
- Stage 6 (deliver)    : the bot displays DESIGN TYPE / DESIGN DIRECTION /
                         IMAGE GENERATION PROMPT (copyable block). The
                         RESTRICTIONS block is still built and scored
                         internally (it feeds the validator) but it is no
                         longer shown to the user: the negative
                         constraints already live inside the prompt
                         itself ("Strictly avoid: ...").

The final prompt is always professional English (section 12). Brand
names and taglines are never translated and keep their exact
spelling/capitalization (section 8). Rule-based only - no AI services.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set

from engine import knowledge

# ---------------------------------------------------------------------------
# Phrase tables (master skill sections 5-9)
# ---------------------------------------------------------------------------

CATEGORY_LABELS = {
    "symbol": "Symbol mark",
    "lettermark": "Lettermark",
    "wordmark": "Wordmark",
    "combination": "Combination mark",
    "abstract": "Abstract mark",
    "emblem": "Emblem",
}

CATEGORY_PHRASES = {
    "symbol": "a symbol mark (one isolated icon without any text)",
    "lettermark": "a lettermark (a custom monogram built from the brand initials)",
    "wordmark": "a wordmark (the brand name itself set as the logo)",
    "combination": "a combination mark (a symbol paired with the brand name)",
    "abstract": "an abstract mark (a distinctive conceptual geometric symbol)",
    "emblem": "an emblem (a badge-style contained logo)",
}

STYLE_PHRASES = {
    "minimalist": "minimalist visual construction with a precise, uncluttered composition",
    "maximalist": "maximalist visual richness with layered detail kept in perfect balance",
    "modern": "a contemporary visual language with clean modern styling",
    "luxury": "a premium, refined identity with an exclusive elegant feel",
    "futuristic": "a forward-looking geometric design with a high-tech futuristic aesthetic",
    "vintage": "a vintage-inspired visual construction with timeless character and retro restraint",
    "handcrafted": "an organic handcrafted visual construction with a warm artisanal character",
}

# keyword each style phrase must contain (used by the validator)
STYLE_KEYWORDS = {
    "minimalist": "minimalist",
    "maximalist": "maximalist",
    "modern": "contemporary",
    "luxury": "premium",
    "futuristic": "futuristic",
    "vintage": "vintage",
    "handcrafted": "handcrafted",
}

STYLE_LABELS = {
    "minimalist": "Minimalist",
    "maximalist": "Maximalist",
    "modern": "Modern",
    "luxury": "Premium luxury",
    "futuristic": "Futuristic",
    "vintage": "Vintage",
    "handcrafted": "Handcrafted",
}

# "You decide" personality, derived from the chosen style
STYLE_PERSONALITY = {
    "minimalist": "calm",
    "maximalist": "bold",
    "modern": "innovative",
    "luxury": "elegant",
    "futuristic": "innovative",
    "vintage": "calm",
    "handcrafted": "calm",
}

# "You decide" typography feel, derived from the chosen style
STYLE_FONT_DEFAULT = {
    "minimalist": "geometric",
    "maximalist": "modern_sans",
    "modern": "modern_sans",
    "luxury": "classic_serif",
    "futuristic": "geometric",
    "vintage": "classic_serif",
    "handcrafted": "script",
}

PERSONALITY_PHRASES = {
    "bold": "bold, powerful and confident",
    "calm": "calm, trustworthy and reassuring",
    "playful": "playful, friendly and approachable",
    "elegant": "elegant, refined and discreet",
    "innovative": "innovative, sharp and forward-thinking",
}

AUDIENCE_PHRASES = {
    "young": "a young, trend-aware audience",
    "family": "families and a broad local community",
    "business": "professionals, companies and institutional clients",
    "premium": "an upscale, high-end clientele",
    "local": "the local neighborhood community",
    "broad": "a broad general audience",
}

FONT_PHRASES = {
    "modern_sans": "a clean modern sans-serif lettering with balanced spacing",
    "classic_serif": "a classic serif lettering with timeless elegance",
    "rounded": "a rounded, friendly lettering with soft terminals",
    "script": "a fluid script or handwritten lettering, kept perfectly legible",
    "geometric": "a geometric lettering built from circles and precise strokes",
}

MOTIF_PHRASES = {
    "object": (
        "an emblem-like object taken directly from the brand activity, "
        "simplified into one clean geometric silhouette"
    ),
    "letter": "the brand initial reshaped into a distinctive pictorial sign",
    "geometric": (
        "pure abstract geometry: circles, angles, lines and balanced "
        "negative space"
    ),
    "nature": (
        "a nature-inspired element such as a leaf, mountain, wave or sun, "
        "drawn with clean minimalist lines"
    ),
    "premium": (
        "a refined premium emblem: crown, star or laurel-inspired geometry "
        "kept minimal"
    ),
}

DIMENSION_PHRASES = {
    "flat": (
        "flat vector style - two-dimensional construction, clean vector "
        "geometry, consistent edges, flat color application, no heavy effects"
    ),
    "slight_3d": (
        "subtle three-dimensional depth - controlled extrusion, restrained "
        "shading, clean surface treatment, with the logo silhouette preserved"
    ),
    "full_3d": (
        "premium full 3D rendering - refined material definition, controlled "
        "highlights, subtle reflections and intentional lighting with precise "
        "proportions"
    ),
}

BACKGROUND_PHRASES = {
    "white": "a pure white background",
    "dark": "a dark background with strong contrast between the logo and its dark background",
    "isolated": "an isolated presentation with no visible background, ready for transparent use",
    "custom": "a custom background that follows the client request",
}

USAGE_PHRASES = {
    "telegram_avatar": (
        "compose for a square avatar with central safe margins, optimized to "
        "stay readable as a small circular Telegram profile picture"
    ),
    "website": "compose for a website header with a balanced, horizontal-friendly layout",
    "social": "compose for square social media posts with a strong central presence",
    "print": "compose for print and packaging with crisp, print-ready edges",
    "everywhere": (
        "compose for versatile use everywhere, from a tiny avatar to a large "
        "print, keeping a strong recognizable silhouette"
    ),
}

TYPOGRAPHY_PHRASES = {
    "none": (
        "Absolutely no typography: no letters, no words, no numbers anywhere "
        "in the logo."
    ),
    "name": (
        'Render the brand name "{name}" as the only text, spelled exactly as '
        "written, with a clean custom lettering treatment. Never invent "
        "slogans, subtitles or additional words."
    ),
    "initials": (
        'Render only the initials "{initials}" as a custom monogram; no other '
        "text anywhere. Never invent slogans or additional words."
    ),
    "name_under": (
        'Place the brand name "{name}" centered under the symbol, spelled '
        "exactly as written, in a clean complementary typeface. Never invent "
        "slogans or additional words."
    ),
}

# Same sentences, adjusted for when the user provides his own tagline:
# the "never add words" rule becomes "nothing beyond name + tagline".
TYPOGRAPHY_PHRASES_TAGLINE = {
    "name": (
        'Render the brand name "{name}" as the main text, spelled exactly as '
        "written, with a clean custom lettering treatment. Do not add any "
        "words beyond the brand name and the tagline."
    ),
    "initials": (
        'Render only the initials "{initials}" as a custom monogram; no '
        "other text besides the tagline."
    ),
    "name_under": (
        'Place the brand name "{name}" centered under the symbol, spelled '
        "exactly as written, in a clean complementary typeface. Do not add "
        "any words beyond the brand name and the tagline."
    ),
}

TAGLINE_PHRASE = (
    'Render the tagline "{tagline}" in smaller letters directly under it, '
    "spelled exactly as written - it is the only additional text allowed."
)

# Button palette values -> professional color phrases
PALETTE_COLORS = {
    "blue_white": ["blue", "pure white"],
    "green_white": ["green", "pure white"],
    "black_gold": ["pure black", "gold"],
    "red_white": ["red", "pure white"],
    "dark_premium": ["deep black", "premium gold"],
    "soft_pastel": ["soft pastel tones"],
    "bold_vivid": ["bold vivid tones"],
}

# User exclusions -> professional negative phrases
EXCLUSION_PHRASES = {
    "neon": "neon lighting",
    "gradients": "gradients",
    "shadows": "drop shadows",
    "decorations": "unnecessary decorations",
    "complex": "excessive complexity",
}

# Mandatory safety restrictions (master skill section 10)
MANDATORY_RESTRICTION_LINES = [
    "No humans, no human figures, no human faces, no facial features "
    "(no eyes, noses, mouths or ears).",
    "No animals, birds, insects or fish - no living creatures of any kind.",
    "No humanoid characters and no anthropomorphic objects.",
    "No sexual content, nudity or suggestive imagery.",
    "No mockups, product photography or watermarks.",
]

# Condensed in-prompt negative items (part 12)
BASE_NEGATIVE_ITEMS = [
    "humans", "human figures", "faces", "facial features",
    "animals", "birds", "insects", "fish", "living creatures",
    "humanoid characters", "anthropomorphic objects",
    "sexual content", "nudity",
    "mockups", "product photography", "watermarks",
]


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class LogoSpec:
    """Fully resolved design specification (no 'auto' left)."""

    brand_name: str = ""            # "" when the user skipped the name
    tagline: str = ""               # user-provided slogan ("" when skipped)
    industry: str = "other"         # resolved specialty leaf value
    industry_from_typed: bool = False
    industry_text_raw: str = ""     # raw typed activity description
    category: str = "symbol"        # resolved category
    category_raw: str = ""          # typed category description (if any)
    motif: str = "auto"             # resolved motif direction
    motif_raw: str = ""             # typed motif description (if any)
    typography: str = "none"        # resolved typography
    font_style: str = "none"        # resolved typography feel
    colors: List[str] = field(default_factory=list)
    colors_raw: str = ""            # raw typed colors (fallback)
    style: str = "modern"
    style_raw: str = ""             # typed style description (if any)
    audience: str = "broad"
    audience_raw: str = ""          # typed audience description (if any)
    personality: str = "innovative"
    personality_raw: str = ""       # typed personality description (if any)
    dimension: str = "flat"
    background: str = "white"
    background_raw: str = ""        # typed background description (if any)
    usage: str = "everywhere"
    usage_raw: str = ""             # typed usage description (if any)
    exclusions: List[str] = field(default_factory=list)


@dataclass
class GeneratedPrompt:
    """Final deliverable (restrictions kept for the validator only)."""

    design_type: str
    design_direction: str
    image_prompt: str
    restrictions: List[str]
    score: int = 0
    issues: List[str] = field(default_factory=list)
    subscores: Dict[str, int] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Stage 3 - resolve ambiguity (creative decisions)
# ---------------------------------------------------------------------------

def resolve_initials(brand_name: str) -> str:
    """Initials of a brand name: "amine ben ali" -> "ABA".

    A single short word ("AB", "KZ") IS the monogram itself.
    """
    brand = (brand_name or "").strip()
    if not brand:
        return ""
    words = brand.split()
    if len(words) == 1 and len(words[0]) <= 3:
        return words[0].upper()
    letters = [w[0] for w in words if w and w[0].isalpha()]
    return "".join(letters).upper()


def _resolve_industry(spec: LogoSpec, answers: Dict[str, str]) -> None:
    """Industry resolution for the two-level tree (plus flat values).

    - a valid specialty leaf given directly wins (API/test convenience)
    - otherwise the leaf stored under industry_<group> wins
    - "other" (group or leaf) opens the typed description, understood by
      the multilingual knowledge base
    """
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
            spec.industry_from_typed = True
            spec.industry_text_raw = ""
            return
    spec.industry = "other"


def resolve_spec(
    answers: Dict[str, str],
    exclusions: Optional[Set[str]] = None,
) -> LogoSpec:
    """Turn raw answers into a complete LogoSpec (no 'auto' left)."""
    answers = answers or {}
    spec = LogoSpec()

    # Brand name and tagline: kept exactly as typed (master skill section 8)
    brand = answers.get("brand_name", "").strip()
    spec.brand_name = "" if brand in ("", "skip") else brand
    tagline = answers.get("tagline", "").strip()
    spec.tagline = "" if tagline in ("", "skip") else tagline

    _resolve_industry(spec, answers)
    return _finish_spec(spec, answers, exclusions)


def _finish_spec(
    spec: LogoSpec,
    answers: Dict[str, str],
    exclusions: Optional[Set[str]],
) -> LogoSpec:
    details = knowledge.INDUSTRY_DETAILS[spec.industry]

    # Category (master skill section 5: pick the most suitable one).
    # A typed "Other" description is mapped through the knowledge base;
    # when nothing is recognized the industry-aware default applies.
    category = answers.get("category", "auto")
    if category == "other":
        spec.category_raw = answers.get("category_text", "").strip()
        matched = knowledge.match_category(spec.category_raw) if spec.category_raw else None
        category = matched or "auto"
    if category == "auto":
        if not spec.brand_name:
            category = "symbol"
        elif len(spec.brand_name.replace(" ", "")) <= 3:
            category = "lettermark"
        else:
            category = "combination"

    # A lettermark/wordmark/combination is impossible without a name
    if category in ("lettermark", "wordmark", "combination") and not spec.brand_name:
        category = "symbol"
    if category not in CATEGORY_PHRASES:  # hardening: unknown value
        category = "symbol"
    spec.category = category

    # Motif: what the symbol should evoke.
    motif = answers.get("motif", "auto")
    if motif == "other":
        spec.motif_raw = answers.get("motif_text", "").strip()
        motif = "custom" if spec.motif_raw else "auto"
    if category in ("wordmark", "lettermark"):
        motif = "none"  # pure text logos have no symbol to describe
    elif motif == "letter" and category in ("symbol", "abstract"):
        motif = "geometric"  # keep the prompt free of text/icon contradictions
    if motif not in MOTIF_PHRASES and motif not in ("auto", "none", "custom"):
        motif = "auto"  # hardening: unknown value
    spec.motif = motif

    # Typography (the question is skipped for symbol/abstract)
    typography = answers.get("typography", "auto")
    if category in ("symbol", "abstract"):
        typography = "none"
    elif typography in ("", "auto", None):
        typography = {
            "wordmark": "name",
            "lettermark": "initials",
            "combination": "name_under",
            "emblem": "name_under",
        }.get(category, "name")
    elif typography == "none" and category == "wordmark":
        typography = "name"  # a wordmark IS text
    if spec.tagline and typography == "none":
        typography = "name"  # the user typed a slogan: text is wanted
    if typography not in TYPOGRAPHY_PHRASES:  # hardening: unknown value
        typography = "name"
    spec.typography = typography

    # Style: intelligent default per industry when "auto"; a typed "Other"
    # description is mapped through the knowledge base.
    style = answers.get("style", "auto")
    if style == "other":
        spec.style_raw = answers.get("style_text", "").strip()
        matched = knowledge.match_style(spec.style_raw) if spec.style_raw else None
        style = matched or "auto"
    if style in ("", "auto", None):
        style = details["default_style"]
    if style not in STYLE_PHRASES:  # hardening: unknown value
        style = details["default_style"]
    spec.style = style

    # Typography feel: only meaningful when text is rendered
    font = answers.get("font_style", "auto")
    if spec.typography == "none":
        font = "none"
    elif font in ("", "auto", None):
        font = STYLE_FONT_DEFAULT.get(style, "modern_sans")
    if font != "none" and font not in FONT_PHRASES:  # hardening
        font = STYLE_FONT_DEFAULT.get(style, "modern_sans")
    spec.font_style = font

    # Audience / personality (personality follows the style when "auto")
    # A typed audience description ("Other" or typed directly on the
    # question) is embedded verbatim - the same policy as the usage.
    audience = answers.get("audience", "auto")
    if audience == "other":
        spec.audience_raw = answers.get("audience_text", "").strip()
        audience = "custom" if spec.audience_raw else "auto"
    if audience in ("", "auto", None):
        audience = "broad"
    if audience != "custom" and audience not in AUDIENCE_PHRASES:
        audience = "broad"  # hardening: unknown value
    if audience == "custom" and not spec.audience_raw:
        audience = "broad"  # hardening: custom needs its raw text
    spec.audience = audience

    personality = answers.get("personality", "auto")
    if personality == "other":
        spec.personality_raw = answers.get("personality_text", "").strip()
        personality = "custom" if spec.personality_raw else "auto"
    if personality in ("", "auto", None):
        personality = STYLE_PERSONALITY.get(style, "innovative")
    if personality != "custom" and personality not in PERSONALITY_PHRASES:
        personality = STYLE_PERSONALITY.get(style, "innovative")  # hardening
    spec.personality = personality

    # Colors
    raw_colors = answers.get("colors", "surprise")
    if raw_colors == "other":
        typed = answers.get("colors_text", "").strip()
        spec.colors_raw = typed
        spec.colors = knowledge.extract_colors(typed) if typed else []
    elif raw_colors == "surprise":
        spec.colors = list(details["surprise_palette"])
    else:
        spec.colors = list(PALETTE_COLORS.get(raw_colors, []))

    # Dimension: never assume "professional" means 3D (master skill 9)
    dimension = answers.get("dimension", "auto")
    if dimension in ("", "auto", None):
        dimension = "slight_3d" if style in ("luxury", "maximalist") else "flat"
    if dimension not in DIMENSION_PHRASES:  # hardening: unknown value
        dimension = "flat"
    spec.dimension = dimension

    # Background. An "Other" description is understood by the background
    # hints (white / dark / isolated); anything else becomes a custom
    # background rendered from the client's own words. When the user left
    # the background on "auto" but typed it inside the color description
    # ("fond noir", "خلفية بيضاء"), the knowledge base hint wins.
    background = answers.get("background", "auto")
    if background == "other":
        typed_bg = answers.get("background_text", "").strip()
        hint = knowledge.detect_background_hint(typed_bg) if typed_bg else None
        if hint:
            background = hint
        elif typed_bg:
            background = "custom"
            spec.background_raw = typed_bg
        else:
            background = "white"
    if background in ("", "auto", None):
        background = "white"
        if raw_colors == "other":
            hint = knowledge.detect_background_hint(answers.get("colors_text", ""))
            if hint:
                background = hint
    if background not in BACKGROUND_PHRASES:  # hardening: unknown value
        background = "white"
    spec.background = background

    # Usage. A typed "Other" description is mapped through the knowledge
    # base; when nothing is recognized the client's words are embedded
    # verbatim as the main-use instruction.
    usage = answers.get("usage", "everywhere")
    if usage == "other":
        typed_usage = answers.get("usage_text", "").strip()
        matched = knowledge.match_usage(typed_usage) if typed_usage else None
        if matched:
            usage = matched
        elif typed_usage:
            usage = "custom"
            spec.usage_raw = typed_usage
        else:
            usage = "everywhere"
    if usage == "custom" and not spec.usage_raw:
        usage = "everywhere"  # hardening: custom needs its raw text
    if usage != "custom" and usage not in USAGE_PHRASES:
        usage = "everywhere"  # hardening: unknown or stale value ("auto")
    spec.usage = usage

    # Exclusions, in the questionnaire's option order
    order = ["neon", "gradients", "shadows", "decorations", "complex"]
    spec.exclusions = [e for e in order if e in (exclusions or set())]
    return spec


# ---------------------------------------------------------------------------
# Stage 4 - build the 12-part prompt
# ---------------------------------------------------------------------------

def _join_colors(colors: List[str]) -> str:
    if not colors:
        return ""
    if len(colors) == 1:
        return colors[0]
    if len(colors) == 2:
        return f"{colors[0]} and {colors[1]}"
    return ", ".join(colors[:-1]) + " and " + colors[-1]


def _typography_sentence(spec: LogoSpec) -> str:
    templates = TYPOGRAPHY_PHRASES_TAGLINE if spec.tagline else TYPOGRAPHY_PHRASES
    key = spec.typography
    if spec.tagline and key == "none":  # defensive; resolve_spec upgrades it
        key = "name"
    sentence = templates[key].format(
        name=spec.brand_name, initials=resolve_initials(spec.brand_name)
    )
    if spec.tagline:
        sentence += " " + TAGLINE_PHRASE.format(tagline=spec.tagline)
    return sentence


def build_prompt(spec: LogoSpec) -> str:
    """Assemble the complete English prompt (12 parts, one paragraph)."""
    details = knowledge.INDUSTRY_DETAILS[spec.industry]

    # 1. Design objective
    if spec.brand_name:
        objective = (
            f'Create a professional logo: {CATEGORY_PHRASES[spec.category]} '
            f'for the brand "{spec.brand_name}".'
        )
    else:
        objective = (
            f"Create a professional logo: {CATEGORY_PHRASES[spec.category]} "
            "for a brand that carries no name in its logo."
        )

    # 2. Visual direction (style)
    style_line = f"Visual direction: {STYLE_PHRASES[spec.style]}."

    # 3. Brand context
    context = f"The brand is {details['context']}."
    if spec.industry_text_raw:
        context += f' The owner describes the activity as: "{spec.industry_text_raw}".'

    # 3b. Brand character (personality)
    if spec.personality == "custom":
        character = (
            "Brand character: the owner describes the brand as "
            f'"{spec.personality_raw}".'
        )
    else:
        character = f"Brand character: {PERSONALITY_PHRASES[spec.personality]}."

    # 4. Logo concept (+ motif direction)
    concept = (
        f"Develop an original, distinctive concept inspired by "
        f"{details['motifs']}, communicating {details['values']}."
    )
    if spec.motif == "custom":
        concept += f' The client wants the symbol to evoke: "{spec.motif_raw}".'
    elif spec.motif in MOTIF_PHRASES:
        concept += f" The symbol should evoke {MOTIF_PHRASES[spec.motif]}."

    # 5. Logo category
    category_line = f"Logo category: {CATEGORY_LABELS[spec.category]}."

    # 6. Visual construction
    construction = (
        "Construct a balanced, memorable silhouette from clean geometric "
        "shapes, precise proportions and carefully controlled negative space."
    )

    # 7. Composition (keep inner capitalization like "Telegram" intact)
    if spec.usage == "custom":
        composition = f'Main use: "{spec.usage_raw}".'
    else:
        usage_phrase = USAGE_PHRASES[spec.usage]
        composition = usage_phrase[0].upper() + usage_phrase[1:] + "."
    if spec.audience == "custom":
        composition += (
            " Target audience: the owner describes it as "
            f'"{spec.audience_raw}".'
        )
    else:
        composition += f" Target audience: {AUDIENCE_PHRASES[spec.audience]}."
    if spec.typography == "name_under":
        composition += " Place the brand name centered under the symbol."

    # 8. Color palette
    if spec.colors:
        palette = (
            f"Use a restrained color palette of {_join_colors(spec.colors)} "
            "with balanced contrast."
        )
    elif spec.colors_raw:
        palette = (
            "Use a professional color palette that follows the client's "
            f'color request: "{spec.colors_raw}", with balanced contrast.'
        )
    else:
        palette = (
            "Use a restrained, professional color palette with balanced "
            "contrast."
        )

    # 9. Typography (+ feel + tagline)
    typography = _typography_sentence(spec)
    if spec.typography != "none":
        typography += f" Typography feel: {FONT_PHRASES[spec.font_style]}."

    # 10. Background
    if spec.background == "custom":
        background = (
            "Place the logo on "
            f'{BACKGROUND_PHRASES["custom"]}: "{spec.background_raw}".'
        )
    else:
        background = f"Place the logo on {BACKGROUND_PHRASES[spec.background]}."

    # 11. Rendering style
    rendering = f"Rendering: {DIMENSION_PHRASES[spec.dimension]}."

    # 12. Quality requirements
    quality = (
        "The final logo must look professional, stay perfectly scalable, "
        "remain recognizable at very small sizes, and show crisp edges with "
        "clean, precise execution."
    )

    # 13. Negative constraints
    negative_items = list(BASE_NEGATIVE_ITEMS)
    for exclusion in spec.exclusions:
        negative_items.append(EXCLUSION_PHRASES[exclusion])
    if spec.typography == "none":
        negative_items.append("typography or any lettering")
    negatives = "Strictly avoid: " + ", ".join(negative_items) + "."

    parts = [
        objective, style_line, context, character, concept, category_line,
        construction, composition, palette, typography, background,
        rendering, quality, negatives,
    ]
    return " ".join(parts)


def build_restrictions(spec: LogoSpec) -> List[str]:
    """RESTRICTIONS list: mandatory lines + conditional + user exclusions.

    Kept for the internal quality gate; the bot no longer displays it.
    """
    lines = list(MANDATORY_RESTRICTION_LINES)
    if spec.typography == "none":
        lines.append("No typography of any kind: no letters, no words, no numbers.")
    elif spec.tagline:
        lines.append(
            "Use only the brand name and the provided tagline - no other words."
        )
    if spec.background == "white":
        lines.append(
            "Pure white background only: no colored background, no environmental scenery."
        )
    if spec.style == "minimalist":
        lines.append("No unnecessary decorations, no random elements, no visual clutter.")
    user = [EXCLUSION_PHRASES[e] for e in spec.exclusions]
    if user:
        lines.append("Also avoid: " + ", ".join(user) + ".")
    return lines


def build_direction(spec: LogoSpec) -> str:
    """Short DESIGN DIRECTION description."""
    style = STYLE_LABELS.get(spec.style, spec.style.title())
    category = CATEGORY_LABELS[spec.category]
    context = knowledge.INDUSTRY_DETAILS[spec.industry]["context"]
    name_part = f' for "{spec.brand_name}"' if spec.brand_name else ""
    direction = f"{style} {category.lower()}{name_part} - {context}."
    if spec.colors:
        direction += f" Palette: {_join_colors(spec.colors)}."
    direction += " Built to stay crisp from a small avatar to large print."
    return direction


# ---------------------------------------------------------------------------
# Stage 5 - 100-point validation (master skill section 15)
# ---------------------------------------------------------------------------

def validate(spec: LogoSpec, generated: GeneratedPrompt) -> GeneratedPrompt:
    """Score the generated prompt against the master-skill criteria.

    Mutates ``generated`` (score, issues, subscores) and returns it.
    The weights mirror section 15 of the master skill:
    brand 15 | concept 15 | composition 15 | geometry 10 | colors 10 |
    typography 10 | requirements 10 | technical 5 | negatives 10 = 100
    """
    issues: List[str] = []
    prompt = generated.image_prompt
    low = prompt.lower()
    sub: Dict[str, int] = {}

    # Brand understanding (15) - case-SENSITIVE: the exact spelling and
    # capitalization of the brand name must be preserved (section 8)
    if spec.brand_name:
        sub["brand"] = 15 if spec.brand_name in prompt else 0
        if sub["brand"] == 0:
            issues.append("brand name missing or altered in the prompt")
    else:
        sub["brand"] = 15 if "no typography" in low or "no name" in low else 5
        if sub["brand"] < 15:
            issues.append("nameless-brand intent not clearly stated")

    # Concept clarity (15)
    details = knowledge.INDUSTRY_DETAILS[spec.industry]
    score = 5 if "develop an original" in low else 0
    motif_words = [w for w in details["motifs"].replace(",", " ").split() if len(w) >= 4]
    if any(w in low for w in motif_words):
        score += 10
    sub["concept"] = score
    if score == 0:
        issues.append("logo concept not described")

    # Visual composition (15) - usage phrase or the client's typed words
    if spec.usage == "custom":
        sub["composition"] = 15 if spec.usage_raw.lower() in low else 0
    else:
        sub["composition"] = 15 if USAGE_PHRASES[spec.usage].lower() in low else 0
    if sub["composition"] == 0:
        issues.append("composition/usage requirement missing")

    # Geometry and structure (10)
    sub["geometry"] = (5 if "geometric" in low else 0) + (5 if "negative space" in low else 0)
    if sub["geometry"] == 0:
        issues.append("geometry instructions missing")

    # Color specification (10)
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

    # Typography accuracy (10) - the feel sentence is required for text logos
    typography = spec.typography
    if typography == "none":
        sub["typography"] = 10 if "no typography" in low else 0
    elif typography == "name":
        ok = (
            spec.brand_name in prompt
            and "exactly as written" in low
            and "typography feel" in low
        )
        sub["typography"] = 10 if ok else 0
    elif typography == "initials":
        ok = resolve_initials(spec.brand_name) in prompt and "typography feel" in low
        sub["typography"] = 10 if ok else 0
    else:  # name_under
        ok = (
            spec.brand_name in prompt
            and "under the symbol" in low
            and "typography feel" in low
        )
        sub["typography"] = 10 if ok else 0
    if spec.tagline and sub["typography"] == 10 and spec.tagline not in prompt:
        sub["typography"] = 5
        issues.append("tagline missing from the prompt")
    if sub["typography"] == 0:
        issues.append("typography requirement missing or wrong")

    # User requirement preservation (10)
    score = 4 if STYLE_KEYWORDS.get(spec.style, "") in low else 0
    score += 3 if DIMENSION_PHRASES[spec.dimension].split(":")[0].lower() in low else 0
    score += 3 if BACKGROUND_PHRASES[spec.background].split(",")[0].split(" with ")[0].lower() in low else 0
    sub["requirements"] = score
    if score < 10:
        issues.append("style/dimension/background not fully preserved")

    # Technical quality (5)
    sub["technical"] = (3 if "scalable" in low else 0) + (2 if "professional" in low else 0)
    if sub["technical"] < 5:
        issues.append("technical quality requirements incomplete")

    # Negative constraints (10): 2 points per core item in the prompt
    core = ["humans", "faces", "animals", "living creatures", "sexual content"]
    sub["negatives"] = sum(2 for item in core if item in low)
    if not generated.restrictions:
        sub["negatives"] = 0
        issues.append("RESTRICTIONS block is empty")

    generated.subscores = sub
    generated.score = min(100, sum(sub.values()))
    generated.issues = issues
    return generated


# ---------------------------------------------------------------------------
# Stage 6 - one-call generation
# ---------------------------------------------------------------------------

def generate_prompt(
    answers: Dict[str, str],
    exclusions: Optional[Set[str]] = None,
) -> GeneratedPrompt:
    """Full pipeline: answers -> validated deliverable."""
    spec = resolve_spec(answers, exclusions)
    generated = GeneratedPrompt(
        design_type=CATEGORY_LABELS[spec.category],
        design_direction=build_direction(spec),
        image_prompt=build_prompt(spec),
        restrictions=build_restrictions(spec),
    )
    return validate(spec, generated)
