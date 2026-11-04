"""Unit tests for the questionnaire logic (Step 6, pro edition).

Run from the project root:
    python -m unittest tests.test_questions -v
"""

from __future__ import annotations

import unittest

from engine import knowledge
from engine.questions import (
    ALL_LEAF_VALUES,
    INDUSTRY_GROUPS,
    QUESTIONS,
    QUESTIONS_BY_ID,
    QUESTION_IDS,
    build_answers_summary,
    first_question_id,
    next_question_id,
    option_label,
    option_rows,
    summary_key,
    toggle_exclusions,
    validate_text_answer,
)


def answers_flow(values: dict) -> list:
    """Walk the questionnaire with given answers, return visited ids."""
    visited = []
    current = None
    while True:
        current = next_question_id(current, values)
        if current is None:
            return visited
        visited.append(current)
        # pretend the question was answered so the flow continues
        values.setdefault(current, "x")


class TestQuestionCatalogue(unittest.TestCase):
    def test_unique_ids(self):
        self.assertEqual(len(QUESTION_IDS), len(set(QUESTION_IDS)))

    def test_buttons_questions_have_options(self):
        for question in QUESTIONS:
            if question.kind in ("buttons", "toggle"):
                self.assertGreaterEqual(len(question.options), 2, question.id)
                values = [o.value for o in question.options]
                self.assertEqual(len(values), len(set(values)), question.id)
                for option in question.options:
                    self.assertTrue(option.label.strip(), question.id)

    def test_kinds_are_known(self):
        for question in QUESTIONS:
            self.assertIn(
                question.kind, ("text", "text_with_skip", "buttons", "toggle")
            )

    def test_callback_data_within_telegram_limit(self):
        # callback_data carries the option VALUE itself
        for question in QUESTIONS:
            for option in question.options:
                data = f"ans:{question.id}:{option.value}"
                self.assertLessEqual(len(data.encode()), 64, data)


class TestIndustryTree(unittest.TestCase):
    def test_one_specialty_question_per_group(self):
        for group in INDUSTRY_GROUPS:
            question = QUESTIONS_BY_ID[f"industry_{group}"]
            values = [o.value for o in question.options]
            # every leaf of the group is a button, plus the Other escape
            for leaf in INDUSTRY_GROUPS[group]:
                self.assertIn(leaf, values)
            self.assertEqual(values[-1], "other")

    def test_every_leaf_has_knowledge_details(self):
        for leaf in ALL_LEAF_VALUES:
            self.assertIn(leaf, knowledge.INDUSTRY_DETAILS, leaf)

    def test_leaf_values_are_single_themes(self):
        # the old combined values must be gone
        for old in ("books", "tech", "sports", "education", "gaming",
                    "photography", "restaurant/cafe"):
            self.assertNotIn(old, ALL_LEAF_VALUES)

    def test_other_option_on_creative_questions(self):
        # every question that offers "Other" also has a typed-input twin
        for question_id in ("industry", "category", "motif", "colors",
                            "style", "audience", "personality",
                            "background", "usage"):
            values = [o.value for o in QUESTIONS_BY_ID[question_id].options]
            self.assertIn("other", values, question_id)
            self.assertIn(f"{question_id}_text", QUESTIONS_BY_ID, question_id)

    def test_new_professional_questions_exist(self):
        for question_id in ("motif", "audience", "personality",
                            "font_style", "tagline"):
            self.assertIn(question_id, QUESTIONS_BY_ID)


class TestFlow(unittest.TestCase):
    def test_food_path_visits_only_food_specialty(self):
        values = {"industry": "food"}
        visited = answers_flow(dict(values))
        self.assertIn("industry_food", visited)
        for other in ("industry_fashion", "industry_tech", "industry_gaming"):
            self.assertNotIn(other, visited)
        self.assertNotIn("industry_text", visited)

    def test_pre_filled_specialty_skips_the_subtree(self):
        # typing the specialty on the field question fills the subtree:
        # the specialty question is not asked again
        values = {"industry": "food", "industry_food": "restaurant"}
        visited = answers_flow(dict(values))
        self.assertNotIn("industry_food", visited)

    def test_other_group_opens_typed_description(self):
        values = {"industry": "other"}
        visited = answers_flow(dict(values))
        self.assertIn("industry_text", visited)
        for group in INDUSTRY_GROUPS:
            self.assertNotIn(f"industry_{group}", visited)

    def test_other_leaf_opens_typed_description(self):
        values = {"industry": "food", "industry_food": "other"}
        visited = answers_flow(dict(values))
        self.assertIn("industry_text", visited)

    def test_typography_block_skipped_for_symbol(self):
        values = {"category": "symbol"}
        visited = answers_flow(dict(values))
        for question_id in ("typography", "font_style", "tagline"):
            self.assertNotIn(question_id, visited)
        self.assertIn("motif", visited)

    def test_motif_skipped_for_wordmark(self):
        values = {"category": "wordmark", "brand_name": "Acme"}
        visited = answers_flow(dict(values))
        self.assertNotIn("motif", visited)
        self.assertIn("typography", visited)

    def test_font_style_skipped_when_no_text(self):
        values = {"category": "combination", "typography": "none",
                  "brand_name": "Acme"}
        visited = answers_flow(dict(values))
        self.assertNotIn("font_style", visited)
        self.assertNotIn("tagline", visited)

    def test_tagline_needs_a_name(self):
        values = {"category": "combination", "brand_name": "skip"}
        visited = answers_flow(dict(values))
        self.assertNotIn("tagline", visited)

        values = {"category": "combination", "brand_name": "Acme"}
        visited = answers_flow(dict(values))
        self.assertIn("tagline", visited)

    def test_conditional_text_questions_follow_other(self):
        for question_id in ("category", "motif", "colors", "style",
                            "personality", "background", "usage"):
            values = {question_id: "other"}
            visited = answers_flow(dict(values))
            self.assertIn(f"{question_id}_text", visited, question_id)

            values = {question_id: "auto"}
            visited = answers_flow(dict(values))
            self.assertNotIn(f"{question_id}_text", visited, question_id)

    def test_typed_description_skips_the_extra_question(self):
        # typing the description directly on the button question must not
        # trigger the typed-input twin again
        for question_id in ("category", "motif", "colors", "style",
                            "personality", "background", "usage"):
            values = {
                question_id: "other",
                f"{question_id}_text": "my own words",
            }
            visited = answers_flow(dict(values))
            self.assertNotIn(f"{question_id}_text", visited, question_id)

    def test_typed_industry_description_skips_the_extra_question(self):
        values = {
            "industry": "other",
            "industry_text": "bot for downloading books",
        }
        visited = answers_flow(dict(values))
        self.assertNotIn("industry_text", visited)

        values = {
            "industry": "food",
            "industry_food": "other",
            "industry_text": "grilled chicken delivery",
        }
        visited = answers_flow(dict(values))
        self.assertNotIn("industry_text", visited)

    def test_audience_other_opens_typed_description(self):
        values = {"audience": "other"}
        visited = answers_flow(dict(values))
        self.assertIn("audience_text", visited)

        values = {"audience": "other", "audience_text": "university students"}
        visited = answers_flow(dict(values))
        self.assertNotIn("audience_text", visited)

    def test_first_question(self):
        self.assertEqual(first_question_id({}), "brand_name")


class TestTextValidation(unittest.TestCase):
    def test_clean_and_accept(self):
        question = QUESTIONS_BY_ID["brand_name"]
        self.assertEqual(validate_text_answer(question, "  Maktabati  "), "Maktabati")

    def test_reject_empty(self):
        question = QUESTIONS_BY_ID["brand_name"]
        self.assertIsNone(validate_text_answer(question, "   "))

    def test_reject_too_long(self):
        question = QUESTIONS_BY_ID["brand_name"]  # max 40
        self.assertIsNone(validate_text_answer(question, "x" * 41))

    def test_tagline_length(self):
        question = QUESTIONS_BY_ID["tagline"]  # max 60
        self.assertIsNotNone(validate_text_answer(question, "x" * 60))
        self.assertIsNone(validate_text_answer(question, "x" * 61))

    def test_activity_allows_longer(self):
        question = QUESTIONS_BY_ID["industry_text"]  # max 120
        self.assertIsNotNone(validate_text_answer(question, "x" * 100))
        self.assertIsNone(validate_text_answer(question, "x" * 121))


class TestTogglesAndSummary(unittest.TestCase):
    def test_toggle_on_off(self):
        selected = toggle_exclusions(set(), "neon")
        self.assertIn("neon", selected)
        selected = toggle_exclusions(selected, "neon")
        self.assertNotIn("neon", selected)

    def test_toggle_ignores_unknown_values(self):
        # a stale/unknown button value must never corrupt the set
        self.assertEqual(toggle_exclusions({"neon"}, "hack"), {"neon"})
        self.assertEqual(toggle_exclusions(set(), "done"), set())

    def test_summary_shows_field_then_specialty(self):
        summary = build_answers_summary(
            {
                "brand_name": "Maktabati",
                "industry": "food",
                "industry_food": "restaurant",
                "category": "symbol",
                "colors": "green_white",
                "style": "minimalist",
            },
            exclusions={"neon"},
        )
        self.assertIn("Brand name: Maktabati", summary)
        self.assertIn("Field: Food & Drink", summary)
        self.assertIn("Specialty: Restaurant", summary)
        self.assertIn("Symbol only (icon)", summary)
        self.assertIn("Green & white", summary)
        self.assertIn("Minimalist", summary)
        self.assertIn("Neon effects", summary)

    def test_summary_with_typed_answers(self):
        summary = build_answers_summary(
            {"industry": "other", "industry_text": "bot for downloading books"},
            exclusions=set(),
        )
        self.assertIn("bot for downloading books", summary)

    def test_summary_empty(self):
        self.assertIn("no answers yet", build_answers_summary({}, set()))

    def test_option_label_roundtrip(self):
        self.assertEqual(option_label("style", "luxury"), "Luxury / premium")
        self.assertEqual(option_label("style", "unknown_value"), "unknown_value")

    def test_summary_key_overrides(self):
        self.assertEqual(summary_key("industry"), "sum_industry")
        self.assertEqual(summary_key("industry_food"), "sum_industry_leaf")
        self.assertEqual(summary_key("style"), "sum_style")


class TestKeyboardRows(unittest.TestCase):
    def test_rows_of_two(self):
        question = QUESTIONS_BY_ID["industry"]
        rows = option_rows(question.options, per_row=2)
        self.assertEqual(len(rows), 5)
        self.assertEqual(len(rows[0]), 2)

    def test_specialty_keyboard_rows(self):
        question = QUESTIONS_BY_ID["industry_food"]
        rows = option_rows(question.options, per_row=2)
        self.assertEqual(len(rows), 3)


if __name__ == "__main__":
    unittest.main()
