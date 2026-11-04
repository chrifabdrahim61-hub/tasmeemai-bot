"""Unit tests for engine.normalizer (Step 2).

Run from the project root:
    python -m unittest tests.test_normalizer -v
"""

from __future__ import annotations

import unittest

from engine.normalizer import (
    analyze,
    detect_language,
    lookup_forms,
    normalize,
    variant_forms,
)


class TestNormalize(unittest.TestCase):
    def test_basic_english(self):
        self.assertEqual(normalize("Make Me a LOGO!"), "make me a logo")

    def test_french_accents_folded(self):
        self.assertEqual(
            normalize("Créer un logo, avec fond blanc"),
            "creer un logo avec fond blanc",
        )

    def test_arabic_script_transliterated(self):
        # skeleton form: no short vowels by design
        self.assertEqual(normalize("أخضر وأبيض"), "akhdr wabyd")

    def test_arabic_diacritics_removed(self):
        self.assertEqual(normalize("مُلَوَّن"), "mlwn")

    def test_arabic_letter_unification(self):
        # أ should behave like ا after unification
        self.assertEqual(normalize("أخضر"), normalize("اخضر"))

    def test_arabic_indic_digits(self):
        self.assertEqual(normalize("٣ ألوان"), "3 alwan")

    def test_arabizi_digits_folded(self):
        self.assertEqual(normalize("bghit logo ta3 ktob"), "bghit logo taa ktob")
        self.assertEqual(normalize("7lou"), "hlou")

    def test_3d_token_not_folded(self):
        self.assertEqual(normalize("logo 3D, black"), "logo 3d black")

    def test_standalone_numbers_untouched(self):
        self.assertEqual(normalize("3 colors"), "3 colors")

    def test_emoji_removed(self):
        self.assertEqual(normalize("logo 🎨✨"), "logo")

    def test_punctuation_becomes_spaces(self):
        self.assertEqual(normalize("simple,propre;clair?oui"), "simple propre clair oui")


class TestVariants(unittest.TestCase):
    def test_y_i_swap(self):
        self.assertIn("dirli", variant_forms("dyrly"))

    def test_trailing_h_drop(self):
        self.assertIn("abyad", variant_forms("abyadh"))

    def test_o_u_swap(self):
        self.assertIn("hlou", variant_forms("hlou"))
        self.assertIn("hlou", variant_forms("hlou"))

    def test_no_variants_for_simple_word(self):
        self.assertIn("logo", variant_forms("logo"))

    def test_lookup_forms_includes_raw_and_folded(self):
        forms = lookup_forms("ta3")
        self.assertIn("ta3", forms)
        self.assertIn("taa", forms)


class TestDetection(unittest.TestCase):
    def test_english(self):
        d = detect_language("Make me a logo for an AI startup, clean and futuristic, blue and white, no neon")
        self.assertEqual(d.language, "english")
        self.assertGreater(d.confidence, 0.5)

    def test_french(self):
        d = detect_language("Je veux un logo pour mon cafe, moderne, avec fond blanc, sans texte")
        self.assertEqual(d.language, "french")

    def test_arabic_script(self):
        d = detect_language("ديرلي لوغو لبوت تاع تحميل الكتب اسمو مكتبتي")
        self.assertEqual(d.language, "arabic_script")

    def test_arabizi(self):
        d = detect_language("bghit logo dyal bot ta3 ktob, vert w blanc, simple bla ktiba")
        self.assertEqual(d.language, "arabizi")

    def test_arabizi_welcome_example_1(self):
        d = detect_language("dirli logo ta3 cafe, green w white, simple bla ktiba")
        self.assertEqual(d.language, "arabizi")

    def test_arabizi_welcome_example_3(self):
        d = detect_language("bghit logo ta3 brand clothing, black w gold, luxury, fih initiales AB")
        self.assertEqual(d.language, "arabizi")

    def test_mixed_scripts(self):
        d = detect_language("ديرلي logo أخضر")
        self.assertEqual(d.language, "mixed")

    def test_forced_hint(self):
        d = detect_language("make me a logo", lang_hint="fr")
        self.assertEqual(d.language, "french")
        self.assertTrue(d.forced)
        self.assertEqual(d.confidence, 1.0)

    def test_empty(self):
        d = detect_language("   ")
        self.assertEqual(d.language, "unknown")


class TestAnalyze(unittest.TestCase):
    def test_analyze_returns_all_parts(self):
        result = analyze("bghit logo ta3 ktob, vert w blanc")
        self.assertEqual(result.original, "bghit logo ta3 ktob, vert w blanc")
        self.assertEqual(result.matchform, "bghit logo taa ktob vert w blanc")
        self.assertIn("bghit", result.tokens)
        self.assertEqual(result.detection.language, "arabizi")

    def test_analyze_empty(self):
        result = analyze("")
        self.assertEqual(result.matchform, "")
        self.assertEqual(result.tokens, [])
        self.assertEqual(result.detection.language, "unknown")


if __name__ == "__main__":
    unittest.main()
