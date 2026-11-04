"""Unit tests for the i18n module (Step 4).

Run from the project root:
    python -m unittest tests.test_i18n -v
"""

from __future__ import annotations

import unittest

from engine import i18n, modes
from engine.questions import summary_key


def expected_keys() -> set:
    """Every key the questionnaires and interface require (both modes)."""
    keys = {
        "menu_text", "menu_button", "lang_set", "lang_usage", "lang_unknown",
        "cancel_text", "outside_text", "need_input_text", "invalid_text",
        "stale_question", "custom_noted", "type_instead_hint",
        "summary_note",
        "prompt_intro", "prompt_score", "prompt_warning",
        "btn_generate", "btn_restart", "btn_new", "btn_done",
        "summary_avoid", "summary_empty",
        # Step 7: help, support, credits, referral, force-sub, donations
        "help_text", "support_text", "menu_credits", "credits_text",
        "not_enough", "ref_bonus_notify", "fs_required", "fs_still",
        "btn_join", "btn_check", "btn_donate", "btn_support",
        "donate_intro", "donate_desc", "donate_thanks", "out_credits",
        # Step 8: two modes, ads how-to, support tag after the output
        "btn_mode_logo", "btn_mode_ads", "prompt_intro_ads",
        "ads_howto", "ads_howto_nologo", "out_support", "sum_ad_leaf",
    }
    for question in modes.all_questions():
        keys.add(f"q_{question.id}")
        for option in question.options:
            keys.add(f"opt_{question.id}_{option.value}")
        if question.kind != "toggle":
            keys.add(summary_key(question.id))
    return keys


class TestI18nParity(unittest.TestCase):
    def test_all_languages_present(self):
        self.assertEqual(set(i18n.STRINGS.keys()), set(i18n.LANGS))

    def test_key_parity_across_languages(self):
        expected = expected_keys()
        for lang in i18n.LANGS:
            actual = set(i18n.STRINGS[lang].keys())
            missing = expected - actual
            extra = actual - expected
            self.assertFalse(missing, f"{lang} missing: {sorted(missing)}")
            self.assertFalse(extra, f"{lang} extra: {sorted(extra)}")

    def test_no_empty_strings(self):
        for lang, table in i18n.STRINGS.items():
            for key, value in table.items():
                self.assertTrue(value.strip(), f"{lang}.{key} is empty")

    def test_format_placeholders_consistent(self):
        # keys that use format placeholders must use the same ones everywhere
        placeholder_map = {
            "lang_set": {"label"},
            "lang_usage": {"current"},
            "invalid_text": {"max_len"},
            "summary_note": {"summary"},
            "prompt_score": {"score"},
            # Step 7
            "help_text": {"refill", "bonus", "support"},
            "support_text": {"support"},
            "menu_credits": {"credits", "refill"},
            "credits_text": {"credits", "refill", "bonus", "link"},
            "not_enough": {"cost", "credits", "refill", "bonus"},
            "ref_bonus_notify": {"bonus"},
            "fs_required": {"channel_link"},
            "donate_thanks": {"stars"},
            "out_credits": {"credits", "refill"},
            # Step 8
            "out_support": {"support"},
        }
        import re

        for key, expected_fields in placeholder_map.items():
            for lang in i18n.LANGS:
                template = i18n.STRINGS[lang][key]
                fields = set(re.findall(r"{(\w+)}", template))
                self.assertEqual(
                    fields, expected_fields, f"{lang}.{key} placeholders"
                )

    def test_question_prompts_match_catalogue(self):
        for question in modes.all_questions():
            for lang in i18n.LANGS:
                self.assertTrue(
                    i18n.get(lang, f"q_{question.id}"),
                    f"missing prompt for {question.id} in {lang}",
                )

    def test_option_labels_match_catalogue(self):
        for question in modes.all_questions():
            for option in question.options:
                for lang in i18n.LANGS:
                    self.assertTrue(
                        i18n.get(lang, f"opt_{question.id}_{option.value}"),
                        f"missing opt_{question.id}_{option.value} in {lang}",
                    )


class TestI18nBehaviour(unittest.TestCase):
    def test_t_exact(self):
        self.assertEqual(i18n.t("en", "btn_done"), "Done")
        self.assertEqual(i18n.t("fr", "btn_done"), "Terminé")
        self.assertEqual(i18n.t("ar", "btn_done"), "تم")

    def test_t_fallback_to_english(self):
        # simulate a missing key in one language
        saved = i18n.STRINGS["ar"].pop("btn_done")
        try:
            self.assertEqual(i18n.t("ar", "btn_done"), "Done")
        finally:
            i18n.STRINGS["ar"]["btn_done"] = saved

    def test_t_with_formatting(self):
        result = i18n.t("fr", "invalid_text", max_len=40)
        self.assertIn("40", result)

    def test_t_missing_key_returns_key(self):
        self.assertEqual(i18n.t("en", "no_such_key"), "no_such_key")

    def test_get_returns_none_for_missing(self):
        self.assertIsNone(i18n.get("en", "no_such_key"))
        self.assertIsNone(i18n.get("xx", "menu_text"))

    def test_arabic_strings_are_arabic(self):
        # smoke-check that RTL strings really contain Arabic characters
        menu = i18n.STRINGS["ar"]["menu_text"]
        self.assertTrue(any("\u0600" <= ch <= "\u06FF" for ch in menu))

    def test_multilingual_summary(self):
        from engine.questions import build_answers_summary

        answers = {
            "brand_name": "Maktabati",
            "industry": "food",
            "industry_food": "restaurant",
            "style": "minimalist",
        }
        summary_en = build_answers_summary(answers, {"neon"}, lang="en")
        summary_fr = build_answers_summary(answers, {"neon"}, lang="fr")
        summary_ar = build_answers_summary(answers, {"neon"}, lang="ar")

        self.assertIn("Brand name: Maktabati", summary_en)
        self.assertIn("Nom de la marque: Maktabati", summary_fr)
        self.assertIn("اسم العلامة: Maktabati", summary_ar)
        self.assertIn("Field: Food & Drink", summary_en)
        self.assertIn("Specialty: Restaurant", summary_en)
        self.assertIn("Domaine: Food & Drink", summary_fr)
        self.assertIn("Spécialité: Restaurant", summary_fr)
        self.assertIn("المجال: طعام وشراب", summary_ar)
        self.assertIn("التخصص: مطعم", summary_ar)
        self.assertIn("Minimalist", summary_en)
        self.assertIn("Minimaliste", summary_fr)
        self.assertIn("بسيط (مينيمال)", summary_ar)

    def test_option_label_multilingual(self):
        from engine.questions import option_label

        self.assertEqual(option_label("colors", "green_white", "en"), "Green & white")
        self.assertEqual(option_label("colors", "green_white", "fr"), "Vert & blanc")
        self.assertEqual(option_label("colors", "green_white", "ar"), "أخضر وأبيض")


if __name__ == "__main__":
    unittest.main()
