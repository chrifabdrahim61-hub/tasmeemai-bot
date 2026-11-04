"""Smoke tests: modules import, settings work, the app builds.

Run from the project root:
    python -m unittest tests.test_smoke -v
"""

from __future__ import annotations

import os

os.environ.setdefault("TASMEEM_DB", ":memory:")  # keep tests off the real DB

import unittest
from unittest import mock


class TestBasics(unittest.TestCase):
    def test_modules_import(self):
        import bot  # noqa: F401
        import config  # noqa: F401
        import user_settings  # noqa: F401
        from engine import builder, i18n, knowledge, normalizer  # noqa: F401
        from engine import questions  # noqa: F401

    def test_token_detection(self):
        import config

        with mock.patch.object(config, "BOT_TOKEN", ""):
            self.assertFalse(config.token_is_set())
        with mock.patch.object(config, "BOT_TOKEN", "123:abc"):
            self.assertTrue(config.token_is_set())

    def test_language_aliases(self):
        from user_settings import normalize_code

        self.assertEqual(normalize_code("  EN "), "en")
        self.assertEqual(normalize_code("french"), "fr")
        self.assertEqual(normalize_code("Français"), "fr")
        self.assertEqual(normalize_code("darija"), "ar")
        self.assertEqual(normalize_code("عربي"), "ar")
        self.assertEqual(normalize_code("klingon"), "")
        self.assertEqual(normalize_code(""), "")

    def test_user_settings_roundtrip(self):
        import user_settings as us

        self.assertEqual(us.get_lang(999999), "en")  # unknown user -> English
        self.assertTrue(us.set_lang(42, "fr"))
        self.assertEqual(us.get_lang(42), "fr")
        self.assertFalse(us.set_lang(42, "xx"))
        self.assertFalse(us.set_lang(42, "auto"))  # no auto for UI language
        self.assertEqual(us.get_lang(42), "fr")  # unchanged after bad set


class TestBotAssembly(unittest.TestCase):
    def test_texts_branded(self):
        from engine import i18n

        for lang in i18n.LANGS:
            self.assertIn("TASMEEM AI", i18n.t(lang, "menu_text"))
        self.assertIn("/lang", i18n.t("en", "menu_text"))
        self.assertIn("/cancel", i18n.t("en", "menu_text"))

    def test_conversation_handler_builds_with_all_states(self):
        import bot
        from telegram.ext import Application

        app = Application.builder().token("123456:TEST-TOKEN").build()
        conversation = bot.build_conversation_handler()
        app.add_handler(conversation)
        self.assertIsNotNone(app)

        from engine.questions import QUESTION_IDS

        for question_id in QUESTION_IDS:
            self.assertIn(question_id, conversation.states)


class TestGeneratedOutput(unittest.TestCase):
    def test_restrictions_block_not_displayed(self):
        # the RESTRICTIONS guidelines are no longer part of the message:
        # the negative constraints live inside the prompt itself
        import bot
        from engine.builder import generate_prompt

        result = generate_prompt(
            {
                "brand_name": "Maktabati",
                "industry": "food",
                "industry_food": "cafe",
                "category": "symbol",
                "colors": "green_white",
                "style": "minimalist",
                "usage": "telegram_avatar",
            },
            {"neon"},
        )
        for lang in ("en", "fr", "ar"):
            rendered = bot.render_prompt_html(result, lang)
            self.assertNotIn("RESTRICTIONS", rendered)
            self.assertNotIn("القيود", rendered)
            self.assertIn("DESIGN TYPE", rendered)
            self.assertIn("DESIGN DIRECTION", rendered)
            self.assertIn("IMAGE GENERATION PROMPT", rendered)
            # the negative constraints remain embedded in the prompt
            self.assertIn("Strictly avoid:", result.image_prompt)

    def test_full_flow_through_every_question_state(self):
        # the conversation handler exposes one state per question,
        # including every specialty of the industry tree
        import bot
        from engine.questions import INDUSTRY_GROUPS

        conversation = bot.build_conversation_handler()
        for group in INDUSTRY_GROUPS:
            self.assertIn(f"industry_{group}", conversation.states)


if __name__ == "__main__":
    unittest.main()
