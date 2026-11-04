"""Text normalizer and language detector (Step 2).

This module turns any incoming message (English, French, Arabic script,
Darija, Arabizi, emoji, mixed scripts) into forms the rest of the engine
can work with:

- ``light``      : lightly cleaned text (emoji removed, Arabic punctuation
                   and digits unified) - used for detection and display.
- ``matchform``  : the matching form used by the knowledge-base
                   dictionaries in Step 3:
                     * lowercase
                     * Arabic diacritics removed, letter variants unified
                       (أ إ آ -> ا, ة -> ه, ى -> ي, ...)
                     * Arabic-Indic digits -> 0-9
                     * Latin accents folded (é -> e, ç -> c, ...)
                     * Arabic script transliterated into a Latin
                       letter-skeleton (no short vowels, by design)
                     * Arabizi digits folded inside words (7 -> h, 3 -> a,
                       9 -> q, 5 -> kh, ...)
                     * punctuation replaced by spaces

IMPORTANT: matchform is ONLY for dictionary matching. It is never shown
to the user as output and never used for brand names (the original text
is preserved for that purpose in Step 4).

- ``detect_language`` : heuristic keyword-based detector returning one of
  "arabic_script", "arabizi", "french", "english", "mixed", "unknown".
  It can be forced with a hint coming from the /lang command.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import List, Optional

# ---------------------------------------------------------------------------
# Character ranges and regexes
# ---------------------------------------------------------------------------

ARABIC_BLOCK = "\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF"

RE_ARABIC_CHAR = re.compile(f"[{ARABIC_BLOCK}]")
RE_ARABIC_DIACRITICS = re.compile("[\u064B-\u0655\u0670\u0640]")  # tashkeel + dagger alif + tatweel
RE_LATIN_LETTER = re.compile("[A-Za-z]")
RE_NON_ALNUM = re.compile(r"[^a-z0-9]+")
RE_WHITESPACE = re.compile(r"\s+")
RE_DOUBLE_LETTER = re.compile(r"(.)\1+")

# Word made of letters AND at least one digit, e.g. "ta3", "7lou", "3andi".
RE_TOKEN_WITH_DIGIT = re.compile(r"^(?=.*[a-z])(?=.*\d)[a-z\d]+$")

RE_EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\U00002700-\U000027BF\U0001F1E6-\U0001F1FF"
    "\u2600-\u26FF\u2B00-\u2BFF\u2190-\u21FF\uFE0F\u200D]+"
)

# ---------------------------------------------------------------------------
# Mapping tables
# ---------------------------------------------------------------------------

# Unify Arabic letter variants so that spelling differences disappear
# (applies to matching only, never to output).
ARABIC_LETTER_UNIFICATION = {
    "أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا",
    "ة": "ه",
    "ى": "ي",
    "ؤ": "و",
    "ئ": "ي",
}

# Arabic punctuation and digits -> Latin equivalents.
ARABIC_PUNCT_DIGITS = {
    "،": ",", "؛": ";", "؟": "?",
    "٠": "0", "١": "1", "٢": "2", "٣": "3", "٤": "4",
    "٥": "5", "٦": "6", "٧": "7", "٨": "8", "٩": "9",
    "۰": "0", "۱": "1", "۲": "2", "۳": "3", "۴": "4",
    "۵": "5", "۶": "6", "۷": "7", "۸": "8", "۹": "9",
}

# Arabic script -> Latin letter skeleton (no short vowels by design).
ARABIC_TO_LATIN = {
    "ا": "a", "ب": "b", "ت": "t", "ث": "th", "ج": "j", "ح": "h",
    "خ": "kh", "د": "d", "ذ": "dh", "ر": "r", "ز": "z", "س": "s",
    "ش": "ch", "ص": "s", "ض": "d", "ط": "t", "ظ": "z", "ع": "a",
    "غ": "gh", "ف": "f", "ق": "q", "ك": "k", "ل": "l", "م": "m",
    "ن": "n", "ه": "h", "و": "w", "ي": "y", "ء": "", "ٱ": "a",
    # Persian/Maghreb extension letters, just in case
    "پ": "p", "چ": "ch", "ژ": "j", "گ": "g", "ڤ": "v",
}

# Arabizi digits -> Latin letters (Algerian conventions).
# Applied only inside tokens that mix letters and digits, so standalone
# numbers like "3 colors" are untouched.
ARABIZI_DIGIT_TO_LETTER = {
    "2": "", "3": "a", "5": "kh", "6": "t", "7": "h", "8": "gh", "9": "q",
}

# Tokens that look like Arabizi but are real design terms - never fold.
ARABIZI_KEEP = {"3d", "2d"}

# ---------------------------------------------------------------------------
# Language detection keyword sets (matchform-style tokens)
# ---------------------------------------------------------------------------

ARABIZI_MARKERS = {
    # verbs / common Darija words (see master skill section 2)
    "dirli", "diro", "dir", "bghit", "bghina",
    "nheb", "n7eb", "manhebch", "ma7ebch", "man7ebch",
    "mafihch", "machfihch", "fihch",
    "khalli", "khaliha", "khalih", "khallih",
    "hott", "7ot", "zid", "gir", "bark",
    "chwiya", "chwaya", "chouia", "shwiya", "chway",
    "ta3", "te3", "t3", "dyal", "dial", "deyal", "mte3", "mta3",
    "wach", "wesh", "wella", "wla", "bla",
    "kima", "kif", "kifach",
    "fih", "fiha", "fihom", "fihum",
    "3la", "3lih", "3liha", "m3a", "m3ak", "m3aha",
    "kayen", "kayna", "kayn",
    "machi", "mouch", "mach",
    "liya", "lia", "lih", "lihom",
    "khouya", "khoya", "sahbi",
    "wa7da", "wa7d",
    "3andi", "3andk", "andi", "andik",
    "chnou", "chno",
    "w",
}

# Decisive Darija function words that never appear in normal English or
# French text. Each hit counts DOUBLE in detection scoring, so a sentence
# like "bghit logo ta3 brand clothing, black w gold" is correctly read as
# Darija even when it borrows many English design words.
ARABIZI_STRONG_MARKERS = {
    "dirli", "diro", "bghit", "bghina",
    "nheb", "n7eb", "manhebch", "ma7ebch", "man7ebch",
    "mafihch", "machfihch", "fihch",
    "khalli", "khaliha", "khalih", "khallih",
    "chwiya", "chwaya", "chouia", "shwiya", "chway",
    "ta3", "te3", "t3", "dyal", "dial", "deyal", "mte3", "mta3",
    "wach", "wesh", "wella", "wla", "bla",
    "kifach", "khouya", "khoya", "sahbi",
    "liya", "wa7da", "wa7d",
    "3andi", "3andk", "andik",
    "chnou", "chno", "hott", "7ot", "bark", "zid",
    "kima", "kayen", "kayna", "kayn", "machi", "mouch",
}

FRENCH_MARKERS = {
    # pronouns / verbs
    "je", "tu", "vous", "moi",
    "veux", "veut", "voudrais", "aimerais", "jaime", "jai", "jaimerais",
    "cest", "faire", "cree", "creer",
    # articles / prepositions
    "un", "une", "des", "du", "de", "le", "la", "les",
    "pour", "avec", "sans", "au", "aux", "et", "est",
    # possessives
    "mon", "ma", "mes", "ton", "tes", "notre", "votre",
    # design vocabulary
    "couleur", "couleurs", "fond", "blanc", "blanche", "noir", "noire",
    "dore", "doree", "moderne", "texte", "police", "ecriture",
    "centre", "milieu", "elegant", "elegante",
}

ENGLISH_MARKERS = {
    # verbs / pronouns
    "make", "made", "create", "created", "design",
    "want", "need", "give", "please",
    "i", "im", "its", "my", "me", "you",
    "a", "an", "the", "and", "for", "with", "without",
    "should", "must", "have",
    # design vocabulary
    "style", "styles", "simple", "clean", "modern", "minimalist", "minimal",
    "luxury", "futuristic", "background", "color", "colors",
    "text", "font", "fonts", "professional", "startup", "business",
    "brand", "company", "shop", "store", "cafe", "coffee", "restaurant",
    "dark", "light", "flat", "vector", "icon", "symbol",
    "lettermark", "wordmark", "emblem",
    "black", "white", "green", "blue", "gold", "red", "grey", "gray",
    "purple", "orange", "yellow",
}

LANGUAGE_LABELS = {
    "arabic_script": "Arabic script (MSA / Darija)",
    "arabizi": "Arabizi (Darija in Latin letters)",
    "french": "French",
    "english": "English",
    "mixed": "Mixed Arabic + Latin",
    "unknown": "Unknown",
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Detection:
    """Result of language detection."""

    language: str
    confidence: float
    signals: List[str] = field(default_factory=list)
    forced: bool = False

    @property
    def label(self) -> str:
        return LANGUAGE_LABELS.get(self.language, self.language)


@dataclass
class NormalizedText:
    """Full normalization result for one incoming message."""

    original: str
    light: str
    matchform: str
    tokens: List[str]
    detection: Detection


# ---------------------------------------------------------------------------
# Low-level helpers
# ---------------------------------------------------------------------------

def strip_emoji(text: str) -> str:
    """Remove emoji, symbols and variation selectors."""
    return RE_EMOJI.sub(" ", text or "")


def remove_diacritics(text: str) -> str:
    """Remove Arabic tashkeel and tatweel."""
    return RE_ARABIC_DIACRITICS.sub("", text or "")


def unify_arabic_letters(text: str) -> str:
    """Fold Arabic letter variants (matching-only normalization)."""
    for src, dst in ARABIC_LETTER_UNIFICATION.items():
        text = text.replace(src, dst)
    return text


def unify_arabic_punct_digits(text: str) -> str:
    """Convert Arabic punctuation and Arabic-Indic digits to Latin ones."""
    for src, dst in ARABIC_PUNCT_DIGITS.items():
        text = text.replace(src, dst)
    return text


def fold_latin_accents(text: str) -> str:
    """Fold Latin accents: é -> e, ç -> c, œ -> oe, ..."""
    text = (text or "").replace("œ", "oe").replace("Œ", "oe")
    text = text.replace("æ", "ae").replace("Æ", "ae")
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def transliterate_arabic(text: str) -> str:
    """Arabic script -> Latin letter skeleton (per character)."""
    out = []
    for ch in text or "":
        out.append(ARABIC_TO_LATIN.get(ch, ch))
    return "".join(out)


def _fold_mixed_token(token: str) -> str:
    """Fold Arabizi digits inside a token that mixes letters and digits."""
    if token in ARABIZI_KEEP or not RE_TOKEN_WITH_DIGIT.match(token):
        return token
    return "".join(ARABIZI_DIGIT_TO_LETTER.get(ch, ch) for ch in token)


# ---------------------------------------------------------------------------
# Public normalization API
# ---------------------------------------------------------------------------

def normalize(text: str) -> str:
    """Return the full matching form (matchform) of the input text."""
    if not text:
        return ""
    t = strip_emoji(text)
    t = unify_arabic_punct_digits(t)
    t = remove_diacritics(t)
    t = unify_arabic_letters(t)
    t = t.lower()
    t = fold_latin_accents(t)
    t = transliterate_arabic(t)
    t = RE_NON_ALNUM.sub(" ", t)
    tokens = [_fold_mixed_token(tok) for tok in t.split()]
    return RE_WHITESPACE.sub(" ", " ".join(tokens)).strip()


def tokenize(matchform_text: str) -> List[str]:
    """Split a matchform string into tokens."""
    return [tok for tok in (matchform_text or "").split() if tok]


def variant_forms(word: str) -> List[str]:
    """Generate common spelling variants of a Latin token.

    Covers frequent Arabizi/Darija alternations so that dictionary
    lookups tolerate spelling differences:
      y <-> i, o <-> u, dropped trailing h/e, collapsed double letters.
    """
    word = (word or "").strip().lower()
    if not word:
        return []
    forms = {word}
    for _ in range(3):  # a few passes to combine transformations
        for form in list(forms):
            if "y" in form:
                forms.add(form.replace("y", "i"))
            if "i" in form:
                forms.add(form.replace("i", "y"))
            if "o" in form:
                forms.add(form.replace("o", "u"))
            if "u" in form:
                forms.add(form.replace("u", "o"))
            if len(form) > 2 and form.endswith("h"):
                forms.add(form[:-1])
            if len(form) > 2 and form.endswith("e"):
                forms.add(form[:-1])
            collapsed = RE_DOUBLE_LETTER.sub(r"\1", form)
            if collapsed != form:
                forms.add(collapsed)
    return sorted(forms)[:12]


def lookup_forms(token: str) -> List[str]:
    """All forms to check against a dictionary key for one token.

    Includes the raw token, its digit-folded form and all spelling
    variants of both. Used by the Step 3 knowledge base.
    """
    token = (token or "").strip().lower()
    if not token:
        return []
    forms = {token, _fold_mixed_token(token)}
    for form in list(forms):
        forms.update(variant_forms(form))
    return sorted(forms)


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------

def _light_tokens(text: str) -> List[str]:
    """Lowercase tokens with accents folded and apostrophes removed."""
    t = strip_emoji(text or "")
    t = unify_arabic_punct_digits(t)
    t = fold_latin_accents(t.lower().replace("'", ""))
    t = re.sub(r"[^a-z0-9 ]+", " ", t)
    return t.split()


def detect_language(text: str, lang_hint: Optional[str] = None) -> Detection:
    """Detect the input language (or apply the forced /lang hint)."""
    if lang_hint in ("en", "fr", "ar"):
        if lang_hint == "en":
            return Detection("english", 1.0, ["forced by /lang en"], forced=True)
        if lang_hint == "fr":
            return Detection("french", 1.0, ["forced by /lang fr"], forced=True)
        has_arabic = bool(RE_ARABIC_CHAR.search(text or ""))
        language = "arabic_script" if has_arabic else "arabizi"
        return Detection(language, 1.0, ["forced by /lang ar"], forced=True)

    if not text or not text.strip():
        return Detection("unknown", 0.0, ["empty input"])

    light = unify_arabic_punct_digits(strip_emoji(text))
    n_arabic = len(RE_ARABIC_CHAR.findall(light))
    n_latin = len(RE_LATIN_LETTER.findall(light))

    if n_arabic > 0:
        language = "mixed" if (n_arabic >= 2 and n_latin >= 3) else "arabic_script"
        signals = [f"arabic-script characters: {n_arabic}"]
        if n_latin:
            signals.append(f"latin characters: {n_latin}")
        confidence = 0.7 if language == "mixed" else 0.9
        return Detection(language, confidence, signals)

    tokens = _light_tokens(text)
    arabizi_hits = [
        t for t in tokens
        if t in ARABIZI_MARKERS or RE_TOKEN_WITH_DIGIT.match(t)
    ]
    french_hits = [t for t in tokens if t in FRENCH_MARKERS]
    english_hits = [t for t in tokens if t in ENGLISH_MARKERS]

    # Weighted Darija score: decisive markers and Arabizi digit-words
    # count double (see ARABIZI_STRONG_MARKERS).
    a = sum(
        2 if (t in ARABIZI_STRONG_MARKERS or RE_TOKEN_WITH_DIGIT.match(t)) else 1
        for t in arabizi_hits
    )

    n_accents = sum(1 for ch in light if ch in "àâäéèêëîïôöùûüç")
    if n_accents:
        french_hits.append(f"{n_accents} accented letters")

    f, e = len(french_hits), len(english_hits)

    signals = []
    if arabizi_hits:
        signals.append("darija/arabizi markers: " + ", ".join(arabizi_hits[:5]))
    if french_hits:
        signals.append("french markers: " + ", ".join(str(x) for x in french_hits[:5]))
    if english_hits:
        signals.append("english markers: " + ", ".join(english_hits[:5]))

    if a and a >= max(f, e):
        language = "arabizi"
        confidence = 0.55 + 0.08 * min(3, a - max(f, e)) + 0.03 * min(4, a)
    elif f > e:
        language = "french"
        confidence = 0.55 + 0.1 * min(4, f - e) + 0.05 * min(2, f)
    else:
        language = "english"
        if e or f:
            confidence = 0.55 + 0.1 * min(4, e - f) + 0.05 * min(2, e)
        else:
            confidence = 0.35

    confidence = max(0.35, min(0.95, confidence))
    return Detection(language, round(confidence, 2), signals)


# ---------------------------------------------------------------------------
# One-shot analysis
# ---------------------------------------------------------------------------

def analyze(text: str, lang_hint: Optional[str] = None) -> NormalizedText:
    """Run the full Step 2 pipeline: detection + normalization."""
    original = text or ""
    light = RE_WHITESPACE.sub(" ", unify_arabic_punct_digits(strip_emoji(original))).strip()
    detection = detect_language(original, lang_hint=lang_hint)
    matchform = normalize(original)
    return NormalizedText(
        original=original,
        light=light,
        matchform=matchform,
        tokens=tokenize(matchform),
        detection=detection,
    )
