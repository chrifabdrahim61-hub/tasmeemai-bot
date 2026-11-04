"""Design knowledge base (Step 5).

This module is the "understanding" layer for typed answers. When the
questionnaire asks the user to type something (their activity, their
colors), the text can arrive in English, French, Modern Standard Arabic,
Algerian Darija (Arabic script), Arabizi (Latin letters + digits) or a
mix of all of them.

The matching works on the ``matchform`` produced by
``engine/normalizer.py`` (lowercase, Arabic transliterated to a Latin
skeleton, Arabizi digits folded, accents removed), plus spelling
variants and Arabic definite-article stripping.

Public API:
- ``extract_colors(text)``  -> ordered list of English color phrases
                              ("deep green", "sky blue", "gold", ...)
- ``match_industry(text)``  -> one of the specialty leaf values of the
                              industry tree ("restaurant", "cafe",
                              "library", ...), or None
- ``match_category(text)``  -> one of the logo-category values, or None
- ``match_style(text)``     -> one of the visual-style values, or None
- ``match_usage(text)``     -> one of the usage values, or None
- ``INDUSTRY_DETAILS``      -> professional design language per specialty
                              (used by the prompt builder)

Rule-based only: dictionaries + the normalizer, no AI services.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from engine import normalizer

# ---------------------------------------------------------------------------
# Color lexicon
# ---------------------------------------------------------------------------
# Keys are matchform tokens (see normalizer). The value is the canonical
# English color name. Spelling variants (y<->i, o<->u, trailing h/e,
# Arabizi digit folding) are generated at match time by lookup_forms().

COLOR_KEYS: Dict[str, str] = {
    # black
    "black": "black", "noir": "black", "noire": "black",
    "aswad": "black", "aswd": "black",
    "swda": "black", "sawda": "black",  # سوداء
    # white
    "white": "white", "blanc": "white", "blanche": "white",
    "abyad": "white", "abyadh": "white", "abyd": "white",
    "byda": "white", "baida": "white", "bayda": "white",  # بيضاء
    # gold
    "gold": "gold", "golden": "gold",
    "dore": "gold", "doree": "gold",
    "dahbi": "gold", "dehbi": "gold", "dhebi": "gold", "dhaby": "gold",
    "dhby": "gold",  # bare skeleton of ذهبي
    # silver
    "silver": "silver", "argent": "silver",
    "feddi": "silver", "fiddi": "silver", "fdy": "silver",
    # blue
    "blue": "blue", "bleu": "blue", "bleue": "blue",
    "azraq": "blue", "azrag": "blue", "azrak": "blue", "azrq": "blue",
    # green
    "green": "green", "vert": "green", "verde": "green",
    "akhdar": "green", "akhdr": "green", "khdar": "green",
    "khadar": "green", "khodr": "green", "khadr": "green",
    # red
    "red": "red", "rouge": "red",
    "ahmar": "red", "ahmer": "red", "hmar": "red", "ahmr": "red",
    # yellow
    "yellow": "yellow", "jaune": "yellow",
    "asfar": "yellow", "asfer": "yellow", "asfr": "yellow",
    # orange
    "orange": "orange",
    "bortqali": "orange", "brtqaly": "orange", "bortokali": "orange",
    # purple
    "purple": "purple", "violet": "purple", "mauve": "purple",
    "banafsaji": "purple", "bnfsjy": "purple",
    # pink
    "pink": "pink", "rose": "pink",
    "wardi": "pink", "wrdy": "pink",
    # brown
    "brown": "brown", "marron": "brown", "brun": "brown",
    "bny": "brown", "bonni": "brown",
    # gray
    "gray": "gray", "grey": "gray", "gris": "gray",
    "rmadi": "gray", "ramadi": "gray",
    # beige
    "beige": "beige", "bej": "beige", "byj": "beige",
    # navy
    "navy": "navy blue", "marine": "navy blue", "khly": "navy blue",
    # turquoise / teal
    "turquoise": "turquoise", "turkuaz": "turquoise", "trkwaz": "turquoise",
    "teal": "teal",
    # olive
    "olive": "olive green", "zaytouni": "olive green", "zytwyny": "olive green",
    # burgundy / bordeaux
    "burgundy": "burgundy", "bordeaux": "burgundy",
    "anaby": "burgundy", "anabi": "burgundy",
    # copper / bronze
    "copper": "copper", "bronze": "bronze",
    "nhas": "copper", "nahas": "copper", "nhasy": "copper",
    # cream
    "cream": "cream", "creme": "cream",
}

# Color modifiers: a word that refines the color next to it.
# Both orders are understood ("dark green" and "أخضر غامق").
MODIFIER_KEYS: Dict[str, str] = {
    # deep / dark
    "dark": "deep", "deep": "deep", "fonce": "deep",
    "ghamiq": "deep", "ghamq": "deep", "ghameq": "deep",
    # light / pale
    "light": "light", "pale": "light", "clair": "light", "claire": "light",
    "fateh": "light", "fath": "light",
    # pastel (also works standalone -> "soft pastel tones")
    "pastel": "soft pastel", "bastyl": "soft pastel",
    # sky
    "sky": "sky", "ciel": "sky", "samawi": "sky", "smaoui": "sky", "smawy": "sky",
    # royal
    "royal": "royal", "roi": "royal", "malaki": "royal", "mlaki": "royal",
    "mlky": "royal",
}

# Palette-tone words (not tied to one base color).
TONE_KEYS: Dict[str, str] = {
    "muted": "muted", "hadyh": "muted",
    "bold": "bold vivid", "vivid": "bold vivid",
    "strong": "bold vivid", "qawi": "bold vivid", "qwy": "bold vivid",
}

# French "or" (= gold) is intentionally NOT a key: in mixed messages the
# English word "or" is far more common and would create false matches.

# ---------------------------------------------------------------------------
# Industry lexicon (for the free-text activity description)
# ---------------------------------------------------------------------------
# Keys are matchform tokens; value = specialty leaf value (one theme per
# leaf, mirroring the questionnaire tree). Arabic definite article
# ("الكتب" -> "alktb") is stripped at match time.

INDUSTRY_KEYS: Dict[str, str] = {
    # library / bookstore / reading (field: education & books)
    "book": "library", "books": "library", "livre": "library",
    "livres": "library", "library": "library", "bookstore": "library",
    "librairie": "library", "bibliotheque": "library",
    "ktb": "library", "ktob": "library", "kotob": "library",
    "kutub": "library", "mktbh": "library", "maktaba": "library",
    "reading": "library", "novel": "library", "novels": "library",
    # restaurant (field: food & drink)
    "restaurant": "restaurant", "resto": "restaurant", "restau": "restaurant",
    "matam": "restaurant", "mtam": "restaurant", "food": "restaurant",
    "cuisine": "restaurant", "kitchen": "restaurant", "traiteur": "restaurant",
    # cafe / coffee shop (field: food & drink)
    "cafe": "cafe", "coffee": "cafe", "qahwa": "cafe", "kahwa": "cafe",
    "qhwh": "cafe", "mqhy": "cafe", "cafeteria": "cafe",
    # fast food (field: food & drink)
    "pizza": "fastfood", "burger": "fastfood", "tacos": "fastfood",
    "taco": "fastfood", "snack": "fastfood", "sandwich": "fastfood",
    "kebab": "fastfood", "shawarma": "fastfood", "fastfood": "fastfood",
    # bakery / pastry (field: food & drink)
    "patisserie": "bakery", "boulangerie": "bakery", "gateau": "bakery",
    "gateaux": "bakery", "hlou": "bakery", "hlwa": "bakery",
    "halwa": "bakery", "hlwyat": "bakery", "bread": "bakery",
    # juice / cold drinks (field: food & drink)
    "juice": "juice", "jus": "juice", "smoothie": "juice",
    "cocktail": "juice", "limonade": "juice", "lemonade": "juice",
    # clothing / fashion (field: fashion & beauty)
    "clothing": "clothing", "clothes": "clothing", "fashion": "clothing",
    "mode": "clothing", "vetement": "clothing", "vetements": "clothing",
    "habillement": "clothing", "lbas": "clothing", "mlabs": "clothing",
    "hwayj": "clothing", "couture": "clothing", "tailleur": "clothing",
    # beauty / cosmetics (field: fashion & beauty)
    "beauty": "beauty", "cosmetic": "beauty", "cosmetics": "beauty",
    "beaute": "beauty", "makeup": "beauty", "maquillage": "beauty",
    "skincare": "beauty", "henna": "beauty", "jmal": "beauty",
    "tjmyl": "beauty", "zynh": "beauty", "zina": "beauty",
    # barber / hair salon (field: fashion & beauty)
    "salon": "barber", "coiffure": "barber", "barber": "barber",
    "barbier": "barber", "haircut": "barber",
    # perfume / fragrance (field: fashion & beauty)
    "parfum": "perfume", "perfume": "perfume", "fragrance": "perfume",
    "atriy": "perfume", "atir": "perfume",
    # jewelry / accessories (field: fashion & beauty)
    "jewelry": "jewelry", "jewellery": "jewelry", "bijou": "jewelry",
    "bijoux": "jewelry", "bijouterie": "jewelry",
    # tech / AI startup (field: tech & digital)
    "tech": "startup", "technology": "startup", "technologie": "startup",
    "tknwljya": "startup", "ai": "startup", "ia": "startup",
    "startup": "startup", "startups": "startup", "intelligence": "startup",
    "artificielle": "startup", "data": "startup",
    # app / software development (field: tech & digital)
    "app": "dev", "application": "dev", "bot": "dev", "bwt": "dev",
    "software": "dev", "logiciel": "dev", "developpement": "dev",
    "development": "dev", "developer": "dev", "code": "dev",
    "programmer": "dev", "programmation": "dev",
    "informatique": "dev",
    # web agency / digital services (field: tech & digital)
    "web": "web", "website": "web", "site": "web", "internet": "web",
    "online": "web", "digital": "web", "numerique": "web", "seo": "web",
    "hosting": "web", "hebergement": "web",
    # IT / cybersecurity (field: tech & digital)
    "cyber": "cyber", "cybersecurite": "cyber", "security": "cyber",
    "securite": "cyber", "hacker": "cyber", "reseau": "cyber",
    "reseaux": "cyber",
    # gym / fitness (field: sports & fitness)
    "gym": "gym", "fitness": "gym", "musculation": "gym",
    "workout": "gym", "bodybuilding": "gym",
    # sports club / team (field: sports & fitness)
    "sport": "club", "sports": "club", "club": "club", "team": "club",
    "equipe": "club", "football": "club", "soccer": "club",
    "basket": "club", "basketball": "club", "handball": "club",
    "volleyball": "club", "boxing": "club", "boxe": "club",
    "karate": "club", "judo": "club", "natation": "club",
    # personal coach (field: sports & fitness)
    "coach": "coach", "coaching": "coach", "entraineur": "coach",
    "trainer": "coach", "mentor": "coach",
    # delivery / transport (field: business & services)
    "delivery": "delivery", "livraison": "delivery", "livreur": "delivery",
    "transport": "delivery", "taxi": "delivery", "shipping": "delivery",
    "courrier": "delivery", "colis": "delivery", "freight": "delivery",
    "twstyl": "delivery", "twsyl": "delivery", "tawstyl": "delivery",
    # real estate (field: business & services)
    "immobilier": "realestate", "immobiliere": "realestate",
    "estate": "realestate", "property": "realestate",
    "properties": "realestate", "aqar": "realestate", "aqarat": "realestate",
    # construction / BTP (field: business & services)
    "construction": "construction", "constructeur": "construction",
    "promoteur": "construction", "btp": "construction", "bna": "construction",
    "architecture": "construction", "architecte": "construction",
    "batiment": "construction", "travaux": "construction",
    # shop / e-commerce (field: business & services)
    "shop": "shop", "store": "shop", "boutique": "shop",
    "ecommerce": "shop", "commerce": "shop", "magasin": "shop",
    "marche": "shop", "souk": "shop", "hanout": "shop", "market": "shop",
    # school / tutoring (field: education & books)
    "school": "school", "ecole": "school", "college": "school",
    "lycee": "school", "university": "school", "universite": "school",
    "prof": "school", "professeur": "school", "teacher": "school",
    "student": "school", "etudiant": "school", "mdrsh": "school",
    "madrasa": "school", "talim": "school", "talym": "school",
    "math": "school", "maths": "school", "mathematiques": "school",
    "etude": "school", "etudes": "school", "studies": "school",
    "soutien": "school",
    # courses / training (field: education & books)
    "education": "training", "formation": "training", "cours": "training",
    "course": "training", "learn": "training", "learning": "training",
    "apprendre": "training", "atelier": "training", "workshop": "training",
    # photography (field: media & creative)
    "photo": "photo", "photos": "photo", "photography": "photo",
    "photographe": "photo", "photographie": "photo", "camera": "photo",
    "appareil": "photo", "studio": "photo",
    "tswyr": "photo", "tsawer": "photo", "tsawr": "photo",
    # video / filming (field: media & creative)
    "video": "video", "videos": "video", "filming": "video",
    "cinema": "video", "montage": "video", "editing": "video",
    "reel": "video", "reels": "video", "youtube": "video",
    # graphic design (field: media & creative)
    "design": "design", "designer": "design", "graphisme": "design",
    "graphic": "design", "graphiste": "design", "illustration": "design",
    # marketing / social media (field: media & creative)
    "marketing": "marketing", "pub": "marketing", "publicite": "marketing",
    "social": "marketing", "media": "marketing", "insta": "marketing",
    "instagram": "marketing", "facebook": "marketing", "tiktok": "marketing",
    # gaming brand / esports team (field: gaming & esports)
    "gaming": "team", "game": "team", "games": "team", "gamer": "team",
    "jeu": "team", "jeux": "team", "esport": "team", "esports": "team",
    "console": "team", "playstation": "team", "xbox": "team",
    "twitch": "team", "streamer": "team", "stream": "team",
    "alaab": "team", "ala3ab": "team",
    # game studio / developer (field: gaming & esports)
    "unity": "studio", "unreal": "studio", "gamedev": "studio",
}

# Specialty leaves that belong to the tech field: generic tech-medium words
# ("bot", "app", "website"...) describe the SUPPORT of a business, not the
# business itself, so they count with a reduced weight (see match_industry).
TECH_LEAVES = {"startup", "dev", "web", "cyber"}

# ---------------------------------------------------------------------------
# Professional design language per specialty (used by the prompt builder)
# ---------------------------------------------------------------------------
# One entry per specialty leaf of the questionnaire tree, plus "other".
# Keys mirror questions.INDUSTRY_GROUPS leaves exactly.

INDUSTRY_DETAILS: Dict[str, Dict[str, object]] = {
    # ---- Food & Drink -----------------------------------------------------
    "restaurant": {
        "context": "a restaurant brand",
        "motifs": "appetite and warmth, table and dish silhouettes, steam and chef-inspired geometric shapes",
        "values": "appetite, freshness and welcoming hospitality",
        "default_style": "modern",
        "surprise_palette": ("terracotta orange", "cream"),
    },
    "cafe": {
        "context": "a cafe and coffee-shop brand",
        "motifs": "coffee beans, steam curls, cup silhouettes and cozy rounded geometry",
        "values": "warmth, energy and everyday comfort",
        "default_style": "modern",
        "surprise_palette": ("coffee brown", "warm cream"),
    },
    "fastfood": {
        "context": "a fast-food and street-food brand",
        "motifs": "bold burger and wrap silhouettes, flame geometry, speed lines and chunky rounded shapes",
        "values": "fun, speed and generous flavor",
        "default_style": "modern",
        "surprise_palette": ("vivid red", "golden yellow"),
    },
    "bakery": {
        "context": "a bakery and pastry brand",
        "motifs": "wheat ears, oven-fresh bread silhouettes, rolling-pin geometry and warm rounded shapes",
        "values": "warmth, tradition and homemade quality",
        "default_style": "handcrafted",
        "surprise_palette": ("wheat gold", "chocolate brown"),
    },
    "juice": {
        "context": "a juice-bar and fresh-drinks brand",
        "motifs": "fruit slices, droplets, splash curves and fresh rounded shapes",
        "values": "freshness, health and vibrant energy",
        "default_style": "modern",
        "surprise_palette": ("orange", "lime green"),
    },
    # ---- Fashion & Beauty ---------------------------------------------------
    "clothing": {
        "context": "a clothing and fashion brand",
        "motifs": "elegant letterforms, needle-and-thread geometry, fabric folds and refined monogram structure",
        "values": "style, exclusivity and timeless elegance",
        "default_style": "luxury",
        "surprise_palette": ("black", "gold"),
    },
    "beauty": {
        "context": "a beauty and cosmetics brand",
        "motifs": "delicate botanical curves, droplet and petal geometry, refined symmetry",
        "values": "elegance, care and sensorial softness",
        "default_style": "minimalist",
        "surprise_palette": ("dusty rose", "champagne"),
    },
    "barber": {
        "context": "a barbershop and hair-salon brand",
        "motifs": "razor and scissor geometry, comb line patterns and classic barbershop emblem shapes",
        "values": "craft, confidence and sharp style",
        "default_style": "vintage",
        "surprise_palette": ("deep navy", "crisp white"),
    },
    "perfume": {
        "context": "a perfume and fragrance brand",
        "motifs": "bottle silhouettes, vapor swirls and delicate floral geometry",
        "values": "allure, sophistication and sensory luxury",
        "default_style": "luxury",
        "surprise_palette": ("deep purple", "soft gold"),
    },
    "jewelry": {
        "context": "a jewelry and accessories brand",
        "motifs": "gem facets, ring circles, delicate chain curves and sparkle geometry",
        "values": "preciousness, brilliance and timeless worth",
        "default_style": "luxury",
        "surprise_palette": ("champagne gold", "deep black"),
    },
    # ---- Tech & Digital ------------------------------------------------------
    "startup": {
        "context": "a technology and artificial-intelligence startup brand",
        "motifs": "modular geometric forms, circuit-like structure, nodes and abstract computation",
        "values": "intelligence, innovation and forward motion",
        "default_style": "futuristic",
        "surprise_palette": ("electric blue", "white"),
    },
    "dev": {
        "context": "an app, bot and software development brand",
        "motifs": "code brackets, modular blocks, interface windows and clean pixel geometry",
        "values": "efficiency, reliability and smart engineering",
        "default_style": "modern",
        "surprise_palette": ("tech blue", "graphite gray"),
    },
    "web": {
        "context": "a web agency and digital-services brand",
        "motifs": "browser frames, connection nodes, cursor arrows and flowing link lines",
        "values": "connectivity, clarity and digital reach",
        "default_style": "modern",
        "surprise_palette": ("royal blue", "cyan"),
    },
    "cyber": {
        "context": "an IT-services and cybersecurity brand",
        "motifs": "shield geometry, lock shapes, circuit grids and protective hexagons",
        "values": "security, vigilance and technical mastery",
        "default_style": "futuristic",
        "surprise_palette": ("cyber teal", "steel gray"),
    },
    # ---- Media & Creative ------------------------------------------------------
    "photo": {
        "context": "a photography and photo-studio brand",
        "motifs": "lens geometry, aperture blades and abstract light framing",
        "values": "precision, focus and visual storytelling",
        "default_style": "minimalist",
        "surprise_palette": ("matte black", "white"),
    },
    "video": {
        "context": "a video-production and filming brand",
        "motifs": "play-button triangles, clapperboard geometry, frame lines and light beams",
        "values": "motion, emotion and cinematic impact",
        "default_style": "modern",
        "surprise_palette": ("cinema black", "vivid orange"),
    },
    "design": {
        "context": "a graphic-design and creative-studio brand",
        "motifs": "overlapping shapes, pen-tool curves, color-wheel geometry and clever negative space",
        "values": "creativity, precision and bold originality",
        "default_style": "modern",
        "surprise_palette": ("coral", "deep indigo"),
    },
    "marketing": {
        "context": "a marketing and social-media brand",
        "motifs": "growth arrows, megaphone silhouettes, network nodes and rising graphs",
        "values": "growth, influence and clear messaging",
        "default_style": "modern",
        "surprise_palette": ("vivid purple", "lime green"),
    },
    # ---- Education & Books -------------------------------------------------------
    "school": {
        "context": "a school and tutoring brand",
        "motifs": "graduation caps, open-book geometry, rising steps and pencil lines",
        "values": "growth, guidance and trust",
        "default_style": "minimalist",
        "surprise_palette": ("royal blue", "yellow"),
    },
    "library": {
        "context": "a library, bookstore and reading brand",
        "motifs": "the structure of an open book, stacked pages, bookmarks and the flow of stories",
        "values": "knowledge, discovery and calm intellectual confidence",
        "default_style": "minimalist",
        "surprise_palette": ("forest green", "warm cream"),
    },
    "training": {
        "context": "a training and online-courses brand",
        "motifs": "rising steps, progress arrows, lightbulb geometry and layered modules",
        "values": "progress, skills and achievement",
        "default_style": "modern",
        "surprise_palette": ("energetic blue", "orange"),
    },
    # ---- Sports & Fitness ------------------------------------------------------------
    "gym": {
        "context": "a gym and fitness brand",
        "motifs": "dumbbell and barbell geometry, dynamic diagonal force lines and shield shapes",
        "values": "strength, discipline and momentum",
        "default_style": "modern",
        "surprise_palette": ("bold red", "black"),
    },
    "club": {
        "context": "a sports club and team brand",
        "motifs": "shield emblems, ball geometry, wing shapes and bold heraldic forms",
        "values": "pride, team spirit and competitive fire",
        "default_style": "modern",
        "surprise_palette": ("deep green", "gold"),
    },
    "coach": {
        "context": "a personal-coaching and training brand",
        "motifs": "upward arrows, stopwatch geometry and abstract motion lines",
        "values": "progress, motivation and personal achievement",
        "default_style": "minimalist",
        "surprise_palette": ("energetic teal", "charcoal"),
    },
    # ---- Business & Services -------------------------------------------------------------
    "delivery": {
        "context": "a delivery and transport brand",
        "motifs": "forward arrows, route and motion lines, abstract speed geometry",
        "values": "speed, reliability and coverage",
        "default_style": "modern",
        "surprise_palette": ("vivid orange", "navy blue"),
    },
    "realestate": {
        "context": "a real-estate brand",
        "motifs": "roofline and building silhouettes, structural grids and stable geometric foundations",
        "values": "trust, solidity and premium living",
        "default_style": "luxury",
        "surprise_palette": ("deep navy", "copper"),
    },
    "construction": {
        "context": "a construction and building company",
        "motifs": "crane silhouettes, brick grids, hard-hat geometry and solid structural frames",
        "values": "strength, precision and dependable execution",
        "default_style": "modern",
        "surprise_palette": ("safety orange", "concrete gray"),
    },
    "shop": {
        "context": "a shop and e-commerce brand",
        "motifs": "shopping-bag silhouettes, storefront geometry, tag shapes and playful curves",
        "values": "variety, accessibility and friendly service",
        "default_style": "modern",
        "surprise_palette": ("fuchsia", "warm yellow"),
    },
    # ---- Gaming & Esports ---------------------------------------------------------------------
    "team": {
        "context": "an esports team and gaming brand",
        "motifs": "angular controller-inspired geometry, sharp facets and aggressive symmetric energy",
        "values": "competition, adrenaline and digital culture",
        "default_style": "futuristic",
        "surprise_palette": ("violet purple", "electric cyan"),
    },
    "studio": {
        "context": "a game-development studio brand",
        "motifs": "pixel grids, controller curves, joystick geometry and playful abstract shapes",
        "values": "imagination, play and digital craftsmanship",
        "default_style": "futuristic",
        "surprise_palette": ("neon green", "deep violet"),
    },
    # ---- Other ------------------------------------------------------------------------------------
    "other": {
        "context": "a modern professional brand",
        "motifs": "clean abstract geometry tailored to the brand's activity",
        "values": "professionalism, clarity and distinction",
        "default_style": "modern",
        "surprise_palette": ("deep teal", "warm gold"),
    },
}

# ---------------------------------------------------------------------------
# Token candidate generation
# ---------------------------------------------------------------------------

def _prefix_stripped(token: str) -> List[str]:
    """Strip attached Arabic prefixes (matching only, applied iteratively):

    - "w"     : conjunction "and", glued to the word (وأبيض -> abyd)
    - "al"    : definite article (الكتب -> ktb)
    - "l"     : Darija article (لكتب -> ktb)
    - "wal"   : and + article (والأخضر -> akhdr)

    Only applied when the remainder stays a plausible token (long enough).
    """
    out = {token}
    frontier = {token}
    for _ in range(2):  # at most two prefixes stacked (w + al)
        nxt = set()
        for form in frontier:
            if form.startswith("wal") and len(form) >= 6:
                nxt.add(form[3:])
            if form.startswith("al") and len(form) >= 5:
                nxt.add(form[2:])
            if form.startswith("w") and len(form) >= 4:
                nxt.add(form[1:])
            if form.startswith("l") and len(form) >= 4 and not form.startswith("ll"):
                nxt.add(form[1:])
        nxt -= out
        if not nxt:
            break
        out |= nxt
        frontier = nxt
    return sorted(out)


def token_candidates(token: str) -> List[str]:
    """All dictionary keys that could correspond to one matchform token.

    Includes the token itself, its prefix-stripped forms, and the
    Arabizi/spelling variants of all of those.
    """
    forms = set()
    for stripped in _prefix_stripped(token):
        forms.update(normalizer.lookup_forms(stripped))
    return sorted(forms)


def _first_dict_hit(token: str, dictionary: Dict[str, str]) -> Optional[str]:
    for form in token_candidates(token):
        hit = dictionary.get(form)
        if hit is not None:
            return hit
    return None


# ---------------------------------------------------------------------------
# Color extraction
# ---------------------------------------------------------------------------

def extract_colors(text: str) -> List[str]:
    """Extract the colors mentioned in ``text``, in order, deduplicated.

    Understands English, French, Arabic script, Darija and Arabizi, plus
    modifiers in any position: "dark green" == "أخضر غامق" == "vert fonce"
    == "akhdar ghami9" -> ["deep green"].

    Returns English phrases ready for a professional prompt, e.g.
    ["deep green", "pure white"]. Empty list when nothing is recognized.
    """
    tokens = normalizer.tokenize(normalizer.normalize(text))
    if not tokens:
        return []

    found: List[List[str]] = []  # rows: [base_color, modifier_or_""]
    pending_modifier: Optional[str] = None

    # Words that can introduce a color ("vert et or" -> green and gold).
    # The bare French word "or" (= gold) is only accepted as a color when
    # such a connector comes right before it, so the English conjunction
    # "black or white" is never misread as gold.
    connectors = {"et", "and", "w", "avec", "m3a", "with"}

    for index, token in enumerate(tokens):
        base: Optional[str]
        if token == "or" and index > 0 and tokens[index - 1] in connectors and found:
            base = "gold"
        else:
            base = _first_dict_hit(token, COLOR_KEYS)
        if base is not None:
            modifier = pending_modifier
            pending_modifier = None
            if not modifier and base in ("white", "black"):
                modifier = "pure"  # the master skill: "pure white", "pure black"
            index = next(
                (i for i, row in enumerate(found) if row[0] == base), None
            )
            if index is None:
                found.append([base, modifier or ""])
            elif modifier:
                found[index][1] = modifier  # upgrade an already-listed color
            continue

        modifier = _first_dict_hit(token, MODIFIER_KEYS)
        if modifier is not None:
            if found and not found[-1][1]:
                # e.g. "أخضر غامق": color first, modifier after
                found[-1][1] = modifier
            else:
                pending_modifier = modifier
            continue

        tone = _first_dict_hit(token, TONE_KEYS)
        if tone is not None and not found and pending_modifier is None:
            found.append([f"{tone} tones", ""])

    # A palette word typed alone (e.g. just "pastel")
    if pending_modifier == "soft pastel" and not found:
        found.append(["soft pastel tones", ""])

    return [f"{m} {b}".strip() if m else b for b, m in found]


# ---------------------------------------------------------------------------
# Background hints typed inside the color description
# ---------------------------------------------------------------------------

# "fond noir", "خلفية بيضاء", "white background" - users often type the
# background together with the colors. These words introduce it.
BACKGROUND_HINT_WORDS = {
    "fond", "background", "khlfyh", "khalfia", "khalfya", "khelfia",
}

# Words that mean "no visible background" on their own, without a color
# next to them ("transparent background", "isolated", "خلفية شفافة").
ISOLATED_HINT_WORDS = {
    "transparent", "transparente", "isolated", "isole",
    "chfaf", "chfafh", "chafaf", "chafah", "chaffaf",  # شفاف / شفافة
}

# Words that negate the background word ("sans fond", "without background").
NEGATION_WORDS = {"sans", "without", "bla", "blash"}


def detect_background_hint(text: str) -> Optional[str]:
    """Detect a background preference typed inside a color description.

    "fond noir" / "خلفية سوداء" -> "dark", "fond blanc" / "خلفية بيضاء"
    -> "white", "transparent" / "sans fond" -> "isolated". Returns None
    when no clear background is mentioned (any other color stays a logo
    color, not a background).
    """
    tokens = normalizer.tokenize(normalizer.normalize(text))
    for token in tokens:
        if token in ISOLATED_HINT_WORDS:
            return "isolated"
    for index, token in enumerate(tokens):
        if token not in BACKGROUND_HINT_WORDS:
            continue
        neighbors = tokens[index + 1 : index + 3] + tokens[max(0, index - 1) : index]
        for neighbor in neighbors:
            if neighbor in NEGATION_WORDS:
                return "isolated"
            base = _first_dict_hit(neighbor, COLOR_KEYS)
            if base == "white":
                return "white"
            if base == "black":
                return "dark"
    return None


# ---------------------------------------------------------------------------
# Industry matching
# ---------------------------------------------------------------------------

def _best_dict_match(text: str, dictionary: Dict[str, str]) -> Optional[str]:
    """Shared scoring for the free-text matchers: count keyword hits and
    return the best-matching value (first hit wins on ties)."""
    tokens = normalizer.tokenize(normalizer.normalize(text))
    if not tokens:
        return None

    hits: Dict[str, float] = {}
    for token in tokens:
        value = _first_dict_hit(token, dictionary)
        if value is None:
            continue
        hits[value] = hits.get(value, 0.0) + 1.0

    best_value: Optional[str] = None
    best_weight = 0.0
    for value, weight in hits.items():  # insertion order = first hit wins
        if weight > best_weight:
            best_value, best_weight = value, weight
    return best_value


def match_industry(text: str) -> Optional[str]:
    """Map a free-text activity description to a specialty leaf value.

    Returns one of the leaf values of the industry tree ("restaurant",
    "cafe", "library", ...) or None when nothing is recognized. The user
    may write in any of the supported languages; keyword hits are counted
    and the best match wins (first hit wins on ties).
    """
    tokens = normalizer.tokenize(normalizer.normalize(text))
    if not tokens:
        return None

    # Generic tech-medium words ("bot", "app", "website"...) describe the
    # SUPPORT of the business, not the business itself. They count for the
    # tech leaves with a reduced weight so that "bot for downloading
    # books" is read as LIBRARY, not as a tech specialty.
    tech_medium_words = {
        "bot", "bwt", "app", "application", "site", "web", "website",
        "online", "digital", "internet", "data", "code", "cyber",
    }

    hits: Dict[str, float] = {}
    for token in tokens:
        industry = _first_dict_hit(token, INDUSTRY_KEYS)
        if industry is None:
            continue
        weight = (
            0.5
            if (industry in TECH_LEAVES and token in tech_medium_words)
            else 1.0
        )
        hits[industry] = hits.get(industry, 0.0) + weight

    if not hits:
        return None

    best_industry: Optional[str] = None
    best_weight = 0.0
    for industry, weight in hits.items():  # insertion order = first hit wins
        if weight > best_weight:
            best_industry, best_weight = industry, weight
    return best_industry


# ---------------------------------------------------------------------------
# Free-text matchers for the "Other" inputs (category / style / usage)
# ---------------------------------------------------------------------------

# Typed logo-type descriptions -> questionnaire category values.
CATEGORY_KEYS: Dict[str, str] = {
    "icon": "symbol", "icone": "symbol", "symbol": "symbol",
    "symbole": "symbol", "pictogram": "symbol", "pictogramme": "symbol",
    "letter": "lettermark", "letters": "lettermark",
    "lettermark": "lettermark", "initial": "lettermark",
    "initials": "lettermark", "initiale": "lettermark",
    "initiales": "lettermark", "monogram": "lettermark",
    "monogramme": "lettermark", "horuf": "lettermark",
    "name": "wordmark", "nom": "wordmark", "word": "wordmark",
    "wordmark": "wordmark", "text": "wordmark",
    "combination": "combination", "combo": "combination",
    "both": "combination", "les": "combination", "deux": "combination",
    "badge": "emblem", "emblem": "emblem", "embleme": "emblem",
    "crest": "emblem", "shield": "emblem", "stamp": "emblem",
    "cachet": "emblem", "blason": "emblem", "dr3a": "emblem",
    "abstract": "abstract", "abstrait": "abstract",
}

# Typed style descriptions -> questionnaire style values.
STYLE_KEYS: Dict[str, str] = {
    "minimalist": "minimalist", "minimal": "minimalist",
    "minimale": "minimalist", "simple": "minimalist", "clean": "minimalist",
    "maximalist": "maximalist", "maximal": "maximalist",
    "detailed": "maximalist", "detaille": "maximalist",
    "rich": "maximalist", "riche": "maximalist",
    "modern": "modern", "moderne": "modern",
    "luxury": "luxury", "luxe": "luxury", "premium": "luxury",
    "fancy": "luxury", "raqi": "luxury", "fakhm": "luxury",
    "futuristic": "futuristic", "futur": "futuristic",
    "future": "futuristic", "futuriste": "futuristic",
    "vintage": "vintage", "retro": "vintage", "classic": "vintage",
    "classique": "vintage", "qdim": "vintage", "9dim": "vintage",
    "traditionnel": "vintage", "traditional": "vintage",
    "handcrafted": "handcrafted", "artisanal": "handcrafted",
    "handmade": "handcrafted", "organic": "handcrafted",
}

# Typed usage descriptions -> questionnaire usage values.
USAGE_KEYS: Dict[str, str] = {
    "avatar": "telegram_avatar", "telegram": "telegram_avatar",
    "profile": "telegram_avatar", "profil": "telegram_avatar",
    "pdp": "telegram_avatar",
    "website": "website", "web": "website", "site": "website",
    "header": "website", "blog": "website",
    "social": "social", "instagram": "social", "insta": "social",
    "facebook": "social", "tiktok": "social", "post": "social",
    "posts": "social", "reel": "social", "reels": "social",
    "story": "social", "snapchat": "social", "whatsapp": "social",
    "print": "print", "flyer": "print", "flyers": "print",
    "poster": "print", "affiche": "print", "packaging": "print",
    "card": "print", "cards": "print", "carte": "print",
    "cartes": "print", "shirt": "print", "tshirt": "print",
    "everywhere": "everywhere", "all": "everywhere", "tout": "everywhere",
}


def match_category(text: str) -> Optional[str]:
    """Map a typed logo-type description to a category value, or None."""
    return _best_dict_match(text, CATEGORY_KEYS)


def match_style(text: str) -> Optional[str]:
    """Map a typed style description to a style value, or None."""
    return _best_dict_match(text, STYLE_KEYS)


def match_usage(text: str) -> Optional[str]:
    """Map a typed usage description to a usage value, or None."""
    return _best_dict_match(text, USAGE_KEYS)


# ---------------------------------------------------------------------------
# Typed answers on button questions: text -> option value (any language)
# ---------------------------------------------------------------------------
# The user may TYPE his answer instead of tapping a button - and he may
# type it in English, French, Arabic script, Darija or Arabizi. These
# matchers map such a free-text answer to the option value it describes
# (or None when nothing is recognized: the bot then falls back to the
# "Other" typed-description flow).

def _match_by_priority(tokens: List[str], ordered: Dict[str, Tuple[str, ...]]) -> Optional[str]:
    """First table row that contains one of the tokens wins."""
    for value, keywords in ordered.items():
        for keyword in keywords:
            if keyword in tokens:
                return value
    return None


AUDIENCE_KEYS: Dict[str, Tuple[str, ...]] = {
    "young": (
        "young", "youth", "jeune", "jeunes", "trendy", "sghar", "sgar",
        "chabab", "chbab", "shbab", "ctar", "sabar",
    ),
    "family": (
        "family", "families", "famille", "familles", "3aila", "ayla",
        "aila", "aylat", "aylh", "parents", "children", "kids", "atfal",
    ),
    "business": (
        "business", "company", "companies", "professional",
        "professionals", "entreprise", "entreprises", "b2b", "corporate",
        "charikat", "sharikat", "chrkat", "societe", "societes",
    ),
    "premium": (
        "premium", "upscale", "luxe", "gamme", "raqi", "ragi", "fakhm",
        "ghani",
    ),
    "local": (
        "local", "locale", "communaute", "quartier", "neighborhood",
        "neighbourhood", "7ouma", "houma", "homa", "7oma", "mhli",
    ),
    "broad": (
        "broad", "everyone", "everybody", "tout", "tous", "monde",
        "kulchi", "kolchi", "ga3", "kul", "kol",
    ),
}

DIMENSION_KEYS: Dict[str, Tuple[str, ...]] = {
    "slight_3d": (
        "slight", "slightly", "semi", "subtle", "half", "khfif", "leger",
        "legere", "legerement",
    ),
    "full_3d": (
        "3d", "threed", "thlathi", "volume", "volumetric", "relief",
    ),
    "flat": (
        "flat", "2d", "plat", "plane", "vector", "vektur", "msth",
    ),
}

TYPOGRAPHY_TEXT_WORDS = {
    "text", "texte", "letters", "lettres", "letter", "writing",
    "typography", "typographie", "ktaba", "ktabh", "ns", "hruf",
    "horuf", "huruf", "hrwf", "name", "nom", "ism", "asm", "esm",
}

TYPOGRAPHY_NEGATIONS = {"no", "not", "sans", "bla", "without", "bdwn"}

TYPOGRAPHY_BARE_NONE = {"no", "nothing", "none", "walu", "walou", "walw",
                        "la", "walch"}


def _match_typography(text: str) -> Optional[str]:
    """Typed text-content answer: none / name / initials / name_under."""
    tokens = normalizer.tokenize(normalizer.normalize(text))
    if not tokens:
        return None
    # "no text" / "sans texte" / "bla ktaba" -> no text at all
    for i in range(len(tokens) - 1):
        if tokens[i] in TYPOGRAPHY_NEGATIONS and tokens[i + 1] in TYPOGRAPHY_TEXT_WORDS:
            return "none"
    if any(w in tokens for w in ("under", "below", "taht", "tht", "sous")):
        return "name_under"
    if any(w in tokens for w in ("initial", "initials", "monogram",
                                 "monogramme", "horuf", "huruf", "ahrf",
                                 "hrwf")):
        return "initials"
    if all(w in TYPOGRAPHY_BARE_NONE for w in tokens):
        return "none"
    if any(w in tokens for w in ("name", "nom", "ism", "asm", "esm")):
        return "name"
    return None


FONT_KEYS: Dict[str, Tuple[str, ...]] = {
    "script": (
        "script", "handwritten", "handwriting", "hand", "cursive",
        "calligraphy", "calligraphie", "khat", "kht", "signature",
    ),
    "rounded": (
        "rounded", "round", "soft", "friendly", "rond", "arrondi",
        "mstdir",
    ),
    "classic_serif": (
        "serif", "classic", "classique", "klasiki", "romain",
    ),
    "geometric": (
        "geometric", "geometrique", "hndsi", "hndsy", "circle",
        "circles",
    ),
    "modern_sans": (
        "modern", "moderne", "clean", "simple", "hadith", "3asri",
        "asri", "net",
    ),
}

PERSONALITY_KEYS: Dict[str, Tuple[str, ...]] = {
    "bold": (
        "bold", "strong", "puissant", "fort", "powerful", "qawi",
        "9wi", "9awi", "qwi", "qwy",
    ),
    "calm": (
        "calm", "calme", "serious", "serieux", "trust", "trustworthy",
        "hadi", "wadi3",
    ),
    "playful": (
        "playful", "fun", "funny", "ludique", "friendly", "amical",
        "marih", "mrh", "farah",
    ),
    "elegant": (
        "elegant", "elegante", "refined", "rafine", "chic", "classy",
        "aniq", "anyq",
    ),
    "innovative": (
        "innovative", "innovant", "creative", "creatif", "modern",
        "jadid", "mbtkr",
    ),
}

MOTIF_KEYS: Dict[str, Tuple[str, ...]] = {
    "letter": (
        "letter", "letters", "initial", "initials", "lettre", "harf",
        "hruf", "hrwf", "ahrf", "monogram",
    ),
    "premium": (
        "crown", "star", "taj", "laurel", "royal", "king", "premium",
        "couronne", "najmh", "najma",
    ),
    "nature": (
        "nature", "tbyah", "leaf", "leaves", "wrqh", "awraq",
        "mountain", "jbl", "wave", "mwj", "sun", "chms", "shams",
        "tree", "flower", "zhrh",
    ),
    "geometric": (
        "geometric", "geometrique", "hndsi", "hndsy", "shape",
        "shapes", "circle", "triangle", "hexagon", "line", "lines",
    ),
    "object": (
        "object", "cup", "kas", "glass", "tool", "phone", "bag", "box",
    ),
}


def _match_background_option(text: str) -> Optional[str]:
    """Typed background answer: white / dark / isolated (or None)."""
    return detect_background_hint(text)


def _match_colors_option(text: str) -> Optional[str]:
    """Typed colors: a known palette when the extracted colors fit it.

    "black and gold" -> black_gold directly; anything the palettes do not
    cover ("vert et or", "deep teal") returns None so the answer takes
    the Other path and the raw words reach the prompt verbatim.
    """
    extracted = extract_colors(text)
    if not extracted:
        return None
    from engine.builder import PALETTE_COLORS  # lazy: builder imports knowledge

    bases = {phrase.split()[-1].lower() for phrase in extracted}
    best: Optional[str] = None
    best_hits = 0
    for value, colors in PALETTE_COLORS.items():
        needed = {color.split()[-1].lower() for color in colors}
        if needed and needed <= bases and len(needed) > best_hits:
            best, best_hits = value, len(needed)
    return best


def _match_by_labels(
    question_id: str, text: str, exact_only: bool = False
) -> Optional[str]:
    """Last-resort match against the option labels themselves (EN/FR/AR).

    A typed answer that simply repeats (part of) a button caption in any
    interface language is mapped back to that option. The "other" option
    is only matched by an explicit word for "other", never by containment.

    With ``exact_only`` (used for the colors question) the typed words
    must be exactly the label's words: a partial hit like "vert" inside
    "vert et or" must NOT select "Green & white" - such free color
    phrases belong to the Other path where extract_colors understands
    them fully.
    """
    from engine import i18n  # local import: i18n is pure data, no cycle

    mf_text = normalizer.normalize(text)
    if not mf_text:
        return None
    tokens = set(normalizer.tokenize(mf_text))

    other_words = {"other", "autre", "ukhra", "okhra", "akhra", "akhri",
                   "akhry", "ohra", "o5ra"}
    auto_words = {"auto", "decide", "decider", "choisis", "choix",
                  "khtar", "akhtr", "antar"}

    best: Optional[str] = None
    best_score = 0.0
    for lang in i18n.LANGS:
        for value in _label_values(question_id):
            label = i18n.get(lang, f"opt_{question_id}_{value}") or ""
            mf_label = normalizer.normalize(label)
            if not mf_label:
                continue
            score = 0.0
            if tokens == set(normalizer.tokenize(mf_label)):
                score = 5.0
            elif not exact_only:
                if mf_text in mf_label and len(mf_text) >= 5:
                    score = 3.0
                elif mf_label in mf_text and len(mf_label) >= 5:
                    score = 3.0
                else:
                    label_tokens = set(normalizer.tokenize(mf_label))
                    common = tokens & label_tokens
                    strong = {t for t in common if len(t) >= 4}
                    if strong:
                        score = 2.0
            if value == "other":
                # only an explicit word for "other" selects the Other button
                score = 5.0 if tokens & other_words else 0.0
            if value == "auto":
                score = max(score, 5.0) if tokens & auto_words else 0.0
            if score > best_score:
                best, best_score = value, score
    return best


def _label_values(question_id: str) -> Tuple[str, ...]:
    """Option values of a button question, read from the registry."""
    try:
        from engine.questions import QUESTIONS_BY_ID  # no import cycle at load time
    except Exception:  # pragma: no cover - defensive
        return ()
    question = QUESTIONS_BY_ID.get(question_id)
    if question is None:
        return ()
    return tuple(option.value for option in question.options)


_OPTION_MATCHERS = {
    "industry": match_industry,
    "category": match_category,
    "style": match_style,
    "usage": match_usage,
    "background": _match_background_option,
    "colors": _match_colors_option,
    "typography": _match_typography,
}

# question id -> keyword table for the remaining button questions
_PRIORITY_TABLES = {
    "audience": AUDIENCE_KEYS,
    "dimension": DIMENSION_KEYS,
    "font_style": FONT_KEYS,
    "personality": PERSONALITY_KEYS,
    "motif": MOTIF_KEYS,
}


def label_exact_match(question_id: str, text: str) -> Optional[str]:
    """Option whose label (any interface language) is EXACTLY the text."""
    return _match_by_labels(question_id, text, exact_only=True)


def match_option(question_id: str, text: str) -> Optional[str]:
    """Map a typed answer to the option value it describes, or None.

    Used when the user TYPES on a question that normally shows buttons.
    The matchers understand English, French, Arabic script, Darija and
    Arabizi. The returned value is not necessarily one of the question's
    options (e.g. typing "coffee shop" on the field question matches the
    "cafe" leaf - the caller maps it back to the tree); the caller checks
    membership and falls back to the "Other" typed-description flow.
    """
    if not (text or "").strip():
        return None
    matcher = _OPTION_MATCHERS.get(question_id)
    if matcher is not None:
        hit = matcher(text)
        if hit:
            return hit
    table = _PRIORITY_TABLES.get(question_id)
    if table is not None:
        tokens = normalizer.tokenize(normalizer.normalize(text))
        hit = _match_by_priority(tokens, table)
        if hit:
            return hit
    return _match_by_labels(
        question_id, text, exact_only=(question_id == "colors")
    )
