"""Unit tests for the multilingual knowledge base (Steps 5-6).

The typed answers (activity, colors, category, style, usage, background)
may arrive in English, French, Arabic script, Darija or Arabizi - these
tests lock that understanding in.

Run from the project root:
    python -m unittest tests.test_knowledge -v
"""

from __future__ import annotations

import unittest

from engine.knowledge import (
    INDUSTRY_DETAILS,
    INDUSTRY_KEYS,
    detect_background_hint,
    extract_colors,
    match_category,
    match_industry,
    match_style,
    match_usage,
)


class TestColorExtraction(unittest.TestCase):
    def test_english(self):
        self.assertEqual(extract_colors("green and white"), ["green", "pure white"])
        self.assertEqual(extract_colors("black w gold"), ["pure black", "gold"])

    def test_french(self):
        self.assertEqual(extract_colors("vert et blanc"), ["green", "pure white"])
        self.assertEqual(extract_colors("noir et doré"), ["pure black", "gold"])
        self.assertEqual(extract_colors("vert et or"), ["green", "gold"])
        self.assertEqual(extract_colors("bleu ciel"), ["sky blue"])

    def test_arabic_script(self):
        self.assertEqual(extract_colors("أخضر وأبيض"), ["green", "pure white"])
        self.assertEqual(extract_colors("أسود وذهبي"), ["pure black", "gold"])
        self.assertEqual(extract_colors("الأخضر والذهبي"), ["green", "gold"])
        self.assertEqual(extract_colors("ذهبي"), ["gold"])
        self.assertEqual(extract_colors("فضي و أبيض"), ["silver", "pure white"])

    def test_arabizi_darija(self):
        self.assertEqual(extract_colors("akhdar w abyad"), ["green", "pure white"])
        self.assertEqual(extract_colors("a5dar w abyadh"), ["green", "pure white"])
        self.assertEqual(extract_colors("azrag smaoui"), ["sky blue"])
        self.assertEqual(extract_colors("azra9 malaki"), ["royal blue"])
        self.assertEqual(extract_colors("akhdar ghami9"), ["deep green"])

    def test_modifiers_both_orders(self):
        self.assertEqual(extract_colors("deep green"), ["deep green"])
        self.assertEqual(extract_colors("dark green"), ["deep green"])
        self.assertEqual(extract_colors("أخضر غامق"), ["deep green"])
        self.assertEqual(extract_colors("vert foncé"), ["deep green"])
        self.assertEqual(extract_colors("light blue"), ["light blue"])
        self.assertEqual(extract_colors("bleu roi"), ["royal blue"])

    def test_dedup_and_order(self):
        self.assertEqual(extract_colors("green vert akhdar"), ["green"])
        self.assertEqual(extract_colors("gold and green and gold"), ["gold", "green"])

    def test_palette_tones(self):
        self.assertEqual(extract_colors("pastel"), ["soft pastel tones"])
        self.assertEqual(extract_colors("pastel pink"), ["soft pastel pink"])
        self.assertEqual(extract_colors("muted"), ["muted tones"])
        self.assertEqual(extract_colors("9awi"), ["bold vivid tones"])

    def test_english_or_is_not_french_gold(self):
        # the English conjunction must never be read as French "or" = gold
        self.assertEqual(
            extract_colors("black or white"), ["pure black", "pure white"]
        )

    def test_unknown_words(self):
        self.assertEqual(extract_colors("xyzzy"), [])
        self.assertEqual(extract_colors(""), [])


class TestBackgroundHints(unittest.TestCase):
    def test_french_fond(self):
        self.assertEqual(detect_background_hint("noir et doré, fond noir"), "dark")
        self.assertEqual(detect_background_hint("fond blanc"), "white")

    def test_arabic_khalfia(self):
        self.assertEqual(detect_background_hint("أخضر، خلفية بيضاء"), "white")
        self.assertEqual(detect_background_hint("خلفية سوداء"), "dark")

    def test_english_background(self):
        self.assertEqual(detect_background_hint("gold on a black background"), "dark")

    def test_isolated_backgrounds(self):
        self.assertEqual(detect_background_hint("transparent background"), "isolated")
        self.assertEqual(detect_background_hint("fond transparent"), "isolated")
        self.assertEqual(detect_background_hint("خلفية شفافة"), "isolated")
        self.assertEqual(detect_background_hint("logo sans fond"), "isolated")

    def test_no_hint(self):
        self.assertIsNone(detect_background_hint("vert et blanc"))
        self.assertIsNone(detect_background_hint("akhdar w abyad"))
        self.assertIsNone(detect_background_hint(""))
        self.assertIsNone(detect_background_hint("fond bleu nuit"))


class TestIndustryMatching(unittest.TestCase):
    def test_english(self):
        self.assertEqual(match_industry("bot for downloading books"), "library")
        self.assertEqual(match_industry("coffee shop"), "cafe")
        self.assertEqual(match_industry("pizza and burgers"), "fastfood")
        self.assertEqual(match_industry("gym coach"), "gym")
        self.assertEqual(match_industry("real estate agency"), "realestate")
        self.assertEqual(match_industry("online store"), "shop")

    def test_french(self):
        self.assertEqual(
            match_industry("bot pour télécharger des livres"), "library"
        )
        # first keyword hit wins: "café" comes first in "café restaurant"
        self.assertEqual(match_industry("café restaurant"), "cafe")
        self.assertEqual(match_industry("agence immobiliere"), "realestate")
        self.assertEqual(match_industry("salle de sport"), "club")
        self.assertEqual(match_industry("livraison de colis"), "delivery")
        # ties go to the first keyword hit in the sentence ("apprendre")
        self.assertEqual(match_industry("app pour apprendre les maths"), "training")
        self.assertEqual(match_industry("boulangerie pâtisserie"), "bakery")

    def test_arabic_script(self):
        self.assertEqual(match_industry("بوت لتحميل الكتب"), "library")
        self.assertEqual(match_industry("متجر ملابس"), "clothing")
        self.assertEqual(match_industry("قهوة"), "cafe")
        self.assertEqual(match_industry("مطعم حلويات"), "restaurant")
        self.assertEqual(match_industry("تصوير منتجات"), "photo")

    def test_arabizi_darija(self):
        self.assertEqual(match_industry("9ahwa"), "cafe")
        self.assertEqual(
            match_industry("bghit logo ta3 brand clothing"), "clothing"
        )
        self.assertEqual(match_industry("mat3am pizza"), "restaurant")
        self.assertEqual(match_industry("livraison ta3 colis"), "delivery")

    def test_tech_medium_words_do_not_dominate(self):
        # "bot" / "app" describe the support, not the business
        self.assertEqual(match_industry("bot for downloading books"), "library")
        self.assertEqual(match_industry("app de recettes de cuisine"), "restaurant")

    def test_unknown(self):
        self.assertIsNone(match_industry("xyzzy"))
        self.assertIsNone(match_industry(""))

    def test_every_keyword_targets_a_known_specialty(self):
        for value in INDUSTRY_KEYS.values():
            self.assertIn(value, INDUSTRY_DETAILS, value)


class TestCategoryMatching(unittest.TestCase):
    def test_english(self):
        self.assertEqual(match_category("a clean icon"), "symbol")
        self.assertEqual(match_category("my initials in a circle"), "lettermark")
        self.assertEqual(match_category("just the name as text"), "wordmark")
        self.assertEqual(match_category("a badge for my staff"), "emblem")

    def test_french_and_darija(self):
        self.assertEqual(match_category("un blason avec mes initiales"), "emblem")
        self.assertEqual(match_category("un symbole simple"), "symbol")
        self.assertEqual(match_category("bghit monogramme"), "lettermark")

    def test_unrecognized(self):
        self.assertIsNone(match_category("something magical and rare"))
        self.assertIsNone(match_category(""))


class TestStyleMatching(unittest.TestCase):
    def test_english(self):
        self.assertEqual(match_style("minimalist and clean"), "minimalist")
        self.assertEqual(match_style("luxury premium feel"), "luxury")
        self.assertEqual(match_style("vintage but clean"), "vintage")
        self.assertEqual(match_style("artisanal handmade"), "handcrafted")

    def test_french_and_darija(self):
        self.assertEqual(match_style("un style rétro"), "vintage")
        self.assertEqual(match_style("ra9i w fakhm"), "luxury")
        self.assertEqual(match_style("futur"), "futuristic")

    def test_unrecognized(self):
        self.assertIsNone(match_style("like a dream"))
        self.assertIsNone(match_style(""))


class TestUsageMatching(unittest.TestCase):
    def test_english(self):
        self.assertEqual(match_usage("my telegram avatar"), "telegram_avatar")
        self.assertEqual(match_usage("website header"), "website")
        self.assertEqual(match_usage("instagram posts"), "social")
        self.assertEqual(match_usage("business card"), "print")

    def test_french(self):
        self.assertEqual(match_usage("carte de visite"), "print")
        self.assertEqual(match_usage("page facebook"), "social")

    def test_unrecognized(self):
        self.assertIsNone(match_usage("on the side of my trucks"))
        self.assertIsNone(match_usage(""))


if __name__ == "__main__":
    unittest.main()
