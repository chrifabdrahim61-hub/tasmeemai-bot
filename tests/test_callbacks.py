"""Regression tests for the button-selection bugs (Step 6 hotfix).

The user reported:
- pressing "3D" selected "2D", pressing "coffee" selected "restaurant":
  the old keyboards encoded the ROW-LOCAL index in callback_data, so every
  button not on the first row resolved to the wrong option;
- pressing "Other" jumped straight to the next question: the buggy index
  stored the FIRST option instead of "other", so the typed-input question
  was skipped;
- a clothing questionnaire generated a book brand (same root cause).

These tests lock the contract: every button carries the option VALUE in
its callback_data, the tapped label and the stored value can never
diverge, and typed answers are accepted on button questions.

Run from the project root:
    python -m unittest tests.test_callbacks -v
"""

from __future__ import annotations

import os

os.environ.setdefault("TASMEEM_DB", ":memory:")  # keep tests off the real DB

import unittest

from telegram import InlineKeyboardMarkup

import bot
from engine import i18n, knowledge
from engine.builder import resolve_spec
from engine.questions import (
    INDUSTRY_GROUPS,
    QUESTIONS_BY_ID,
    option_label,
)


def _answer_buttons(markup: InlineKeyboardMarkup):
    """All (text, callback_data) pairs of an inline keyboard."""
    for row in markup.inline_keyboard:
        for button in row:
            yield button.text, button.callback_data


class TestKeyboardValueContract(unittest.TestCase):
    """The killer regression: label shown == value stored, for EVERY button."""

    BUTTON_QUESTIONS = tuple(
        q.id for q in QUESTIONS_BY_ID.values() if q.kind == "buttons"
    )

    def test_every_button_callback_resolves_to_its_own_label(self):
        for question_id in self.BUTTON_QUESTIONS:
            for lang in i18n.LANGS:
                markup = bot._buttons_keyboard(lang, question_id)
                for text, data in _answer_buttons(markup):
                    self.assertTrue(data.startswith(f"ans:{question_id}:"), data)
                    value = data.split(":", 2)[2]
                    # the value must be a real option of THIS question
                    self.assertIn(
                        value,
                        [o.value for o in QUESTIONS_BY_ID[question_id].options],
                        f"{question_id}:{value} ({lang})",
                    )
                    # and the label must be the caption of that same value
                    self.assertEqual(
                        option_label(question_id, value, lang),
                        text,
                        f"{question_id}:{value} ({lang})",
                    )

    def test_reported_bug_3d_button_stores_3d(self):
        markup = bot._buttons_keyboard("en", "dimension")
        mapping = dict(_answer_buttons(markup))
        full_3d = option_label("dimension", "full_3d", "en")
        self.assertIn(full_3d, mapping)
        self.assertEqual(mapping[full_3d], "ans:dimension:full_3d")
        # ...and never the flat value the old bug produced
        self.assertNotIn("ans:dimension:0", "".join(mapping.values()))
        self.assertNotIn("ans:dimension:2", "".join(mapping.values()))

    def test_reported_bug_cafe_button_stores_cafe(self):
        markup = bot._buttons_keyboard("en", "industry_food")
        mapping = dict(_answer_buttons(markup))
        cafe = option_label("industry_food", "cafe", "en")
        self.assertEqual(mapping[cafe], "ans:industry_food:cafe")
        restaurant = option_label("industry_food", "restaurant", "en")
        self.assertEqual(mapping[restaurant], "ans:industry_food:restaurant")

    def test_reported_bug_other_button_stores_other(self):
        for question_id in ("industry", "category", "colors", "style",
                            "audience", "usage"):
            markup = bot._buttons_keyboard("en", question_id)
            mapping = dict(_answer_buttons(markup))
            other = option_label(question_id, "other", "en")
            self.assertEqual(
                mapping[other],
                f"ans:{question_id}:other",
                f"the Other button of {question_id} must store 'other'",
            )

    def test_callback_data_byte_limit(self):
        for question_id in self.BUTTON_QUESTIONS:
            markup = bot._buttons_keyboard("en", question_id)
            for _, data in _answer_buttons(markup):
                self.assertLessEqual(len(data.encode()), 64, data)

    def test_skip_keyboard_uses_values(self):
        markup = bot._skip_keyboard("en", "brand_name")
        for _, data in _answer_buttons(markup):
            self.assertEqual(data, "ans:brand_name:skip")

    def test_toggle_keyboard_uses_values(self):
        markup = bot._toggle_keyboard("en", {"neon"})
        texts = []
        for text, data in _answer_buttons(markup):
            texts.append(text)
            if data == "tog:done":
                continue
            self.assertTrue(data.startswith("tog:"), data)
            value = data.split(":", 1)[1]
            self.assertIn(
                value,
                [o.value for o in QUESTIONS_BY_ID["exclusions"].options],
            )
        neon = option_label("exclusions", "neon", "en")
        neon_line = next(t for t in texts if neon in t)
        self.assertTrue(neon_line.startswith("[x] "))
        gradients = option_label("exclusions", "gradients", "en")
        gradients_line = next(t for t in texts if gradients in t)
        self.assertTrue(gradients_line.startswith("[ ] "))

    def test_tap_uses_cafe_and_stores_cafe(self):
        """Simulate the reported flow: tap Cafe -> answers hold 'cafe'."""
        markup = bot._buttons_keyboard("en", "industry_food")
        mapping = dict(_answer_buttons(markup))
        cafe = option_label("industry_food", "cafe", "en")
        value = mapping[cafe].split(":", 2)[2]
        answers = {"industry": "food", "industry_food": value}
        spec = resolve_spec(answers)
        self.assertEqual(spec.industry, "cafe")
        self.assertIn("cafe and coffee-shop brand", spec_prompt_context(spec))

    def test_tap_3d_and_stores_3d(self):
        markup = bot._buttons_keyboard("en", "dimension")
        mapping = dict(_answer_buttons(markup))
        full_3d = option_label("dimension", "full_3d", "en")
        value = mapping[full_3d].split(":", 2)[2]
        self.assertEqual(value, "full_3d")

    def test_clothing_questionnaire_never_produces_a_book_brand(self):
        """The reported 'clothes logo -> book brand' scenario, end to end."""
        markup_field = bot._buttons_keyboard("en", "industry")
        mapping_field = dict(_answer_buttons(markup_field))
        fashion = option_label("industry", "fashion", "en")
        group = mapping_field[fashion].split(":", 2)[2]

        markup_leaf = bot._buttons_keyboard("en", "industry_fashion")
        mapping_leaf = dict(_answer_buttons(markup_leaf))
        clothing = option_label("industry_fashion", "clothing", "en")
        leaf = mapping_leaf[clothing].split(":", 2)[2]

        self.assertEqual(group, "fashion")
        self.assertEqual(leaf, "clothing")
        spec = resolve_spec({"industry": group, "industry_fashion": leaf})
        self.assertEqual(spec.industry, "clothing")
        self.assertIn("clothing and fashion brand", spec_prompt_context(spec))
        self.assertNotIn("book", spec_prompt_context(spec).lower())
        self.assertNotIn("library", spec_prompt_context(spec).lower())


def spec_prompt_context(spec) -> str:
    from engine.builder import build_prompt

    return build_prompt(spec)


class TestTypedAnswersOnButtons(unittest.TestCase):
    """Typing is accepted whenever the list does not contain the choice."""

    def test_typed_specialty_fills_the_subtree(self):
        value = knowledge.match_option("industry", "coffee shop")
        self.assertEqual(value, "cafe")
        self.assertIn("cafe", INDUSTRY_GROUPS["food"])

    def test_typed_arabic_specialty(self):
        value = knowledge.match_option("industry_food", "قهوة")
        self.assertEqual(value, "cafe")

    def test_typed_french_clothing(self):
        value = knowledge.match_option("industry_fashion", "vêtements")
        self.assertEqual(value, "clothing")

    def test_typed_multilingual_samples(self):
        cases = [
            ("dimension", "3d", "full_3d"),
            ("dimension", "2d flat", "flat"),
            ("dimension", "slightly 3d", "slight_3d"),
            ("typography", "no text", "none"),
            ("typography", "بدون كتابة", "none"),
            ("typography", "monogram of my initials", "initials"),
            ("typography", "name under the symbol", "name_under"),
            ("typography", "just the name", "name"),
            ("audience", "families", "family"),
            ("audience", "شباب", "young"),
            ("audience", "haut de gamme", "premium"),
            ("style", "vintage but clean", "vintage"),
            ("usage", "business card", "print"),
            ("motif", "a crown", "premium"),
            ("motif", "something with a leaf", "nature"),
            ("background", "fond transparent", "isolated"),
            ("personality", "fun and friendly", "playful"),
            ("font_style", "old serif", "classic_serif"),
            ("font_style", "handwritten style", "script"),
        ]
        for question_id, text, expected in cases:
            self.assertEqual(
                knowledge.match_option(question_id, text),
                expected,
                f"{question_id} <- {text!r}",
            )

    def test_unknown_text_returns_none(self):
        self.assertIsNone(knowledge.match_option("audience", "university students"))
        self.assertIsNone(knowledge.match_option("colors", "vert et or"))
        self.assertIsNone(knowledge.match_option("dimension", "qqquantum"))

    def test_other_word_selects_other(self):
        for text in ("other", "Other", "autre", "أخرى"):
            self.assertEqual(
                knowledge.match_option("category", text),
                "other",
                f"{text!r} should select the Other button",
            )

    def test_you_decide_selects_auto(self):
        self.assertEqual(knowledge.match_option("dimension", "you decide"), "auto")
        self.assertEqual(knowledge.match_option("audience", "اختر أنت"), "auto")


class TestCustomAnswersReachThePrompt(unittest.TestCase):
    def test_typed_custom_audience(self):
        spec = resolve_spec(
            {"audience": "other", "audience_text": "university students"}
        )
        self.assertEqual(spec.audience, "custom")
        self.assertEqual(spec.audience_raw, "university students")

    def test_typed_custom_audience_in_prompt(self):
        from engine.builder import build_prompt

        spec = resolve_spec(
            {"audience": "other", "audience_text": "university students"}
        )
        self.assertIn("university students", build_prompt(spec))

    def test_unmatched_typed_activity_is_kept_verbatim(self):
        from engine.builder import build_prompt

        answers = {
            "industry": "other",
            "industry_text": "xyzzy qqquantum drone repairs",
        }
        spec = resolve_spec(answers)
        self.assertEqual(spec.industry, "other")
        prompt = build_prompt(spec)
        self.assertIn("xyzzy qqquantum drone repairs", prompt)

    def test_matched_typed_activity_resolves_the_industry(self):
        answers = {
            "industry": "food",
            "industry_food": "other",
            "industry_text": "قهوة",
        }
        spec = resolve_spec(answers)
        self.assertEqual(spec.industry, "cafe")

    def test_full_clothing_flow_with_typed_answers(self):
        """Tap-free flow: everything typed, still a clothing brand."""
        from engine.builder import generate_prompt

        result = generate_prompt(
            {
                "brand_name": "Zina",
                "industry": "fashion",
                "industry_fashion": "clothing",
                "category": "combination",
                "colors": "other",
                "colors_text": "أسود وذهبي",
                "style": "modern",
                "audience": "other",
                "audience_text": "young women",
                "dimension": "flat",
                "usage": "instagram",
            }
        )
        self.assertEqual(result.design_type, "Combination mark")
        self.assertGreaterEqual(result.score, 90)
        self.assertIn("Zina", result.image_prompt)
        self.assertIn("clothing and fashion brand", result.image_prompt)


if __name__ == "__main__":
    unittest.main()
