"""Unit tests for the prompt builder and validator (Steps 5-6).

Run from the project root:
    python -m unittest tests.test_builder -v
"""

from __future__ import annotations

import unittest

from engine import builder
from engine.builder import (
    GeneratedPrompt,
    build_direction,
    build_prompt,
    build_restrictions,
    generate_prompt,
    resolve_initials,
    resolve_spec,
    validate,
)


def full_answers(**overrides) -> dict:
    """A complete, typical answer set (tree edition)."""
    answers = {
        "brand_name": "Maktabati",
        "industry": "education",
        "industry_education": "library",
        "category": "symbol",
        "typography": "none",
        "colors": "green_white",
        "style": "minimalist",
        "dimension": "flat",
        "background": "white",
        "usage": "telegram_avatar",
    }
    answers.update(overrides)
    return answers


class TestResolveSpec(unittest.TestCase):
    def test_tree_answers_resolve_the_leaf(self):
        spec = resolve_spec(full_answers())
        self.assertEqual(spec.industry, "library")

    def test_flat_industry_value_accepted(self):
        spec = resolve_spec({"industry": "cafe"})
        self.assertEqual(spec.industry, "cafe")

    def test_auto_category_with_long_name(self):
        spec = resolve_spec({"brand_name": "Maktabati", "category": "auto"})
        self.assertEqual(spec.category, "combination")

    def test_auto_category_with_short_name(self):
        spec = resolve_spec({"brand_name": "AB", "category": "auto"})
        self.assertEqual(spec.category, "lettermark")

    def test_auto_category_without_name(self):
        spec = resolve_spec({"brand_name": "skip", "category": "auto"})
        self.assertEqual(spec.category, "symbol")

    def test_text_categories_impossible_without_name(self):
        for category in ("lettermark", "wordmark", "combination"):
            spec = resolve_spec({"brand_name": "skip", "category": category})
            self.assertEqual(spec.category, "symbol")

    def test_typed_category_understood(self):
        spec = resolve_spec(
            {"category": "other", "category_text": "a shield with my initials"}
        )
        self.assertEqual(spec.category, "emblem")

    def test_typed_category_unrecognized_falls_back_to_auto(self):
        spec = resolve_spec(
            {"brand_name": "Maktabati", "category": "other",
             "category_text": "something magical and rare"}
        )
        self.assertEqual(spec.category, "combination")

    def test_typography_skipped_for_symbol_and_abstract(self):
        for category in ("symbol", "abstract"):
            spec = resolve_spec({"category": category})
            self.assertEqual(spec.typography, "none")

    def test_typography_auto_follows_category(self):
        self.assertEqual(
            resolve_spec({"brand_name": "Acme Corp", "category": "wordmark"}).typography,
            "name",
        )
        self.assertEqual(
            resolve_spec({"brand_name": "AB", "category": "lettermark"}).typography,
            "initials",
        )
        self.assertEqual(
            resolve_spec({"brand_name": "Acme Corp", "category": "combination"}).typography,
            "name_under",
        )

    def test_wordmark_forces_text(self):
        spec = resolve_spec(
            {"brand_name": "Acme", "category": "wordmark", "typography": "none"}
        )
        self.assertEqual(spec.typography, "name")

    def test_tagline_upgrades_no_text(self):
        spec = resolve_spec(
            {"brand_name": "Acme", "category": "combination",
             "typography": "none", "tagline": "Fresh every day"}
        )
        self.assertEqual(spec.typography, "name")
        self.assertEqual(spec.tagline, "Fresh every day")

    def test_tagline_skip_value_ignored(self):
        spec = resolve_spec({"brand_name": "Acme", "tagline": "skip"})
        self.assertEqual(spec.tagline, "")

    def test_style_auto_uses_specialty_default(self):
        spec = resolve_spec({"industry": "startup", "style": "auto"})
        self.assertEqual(spec.style, "futuristic")
        spec = resolve_spec({"industry": "library", "style": "auto"})
        self.assertEqual(spec.style, "minimalist")
        spec = resolve_spec({"industry": "barber", "style": "auto"})
        self.assertEqual(spec.style, "vintage")

    def test_typed_style_understood(self):
        spec = resolve_spec({"style": "other", "style_text": "vintage but clean"})
        self.assertEqual(spec.style, "vintage")

    def test_font_style_follows_style_when_auto(self):
        spec = resolve_spec(
            {"brand_name": "Acme", "category": "combination",
             "style": "luxury", "font_style": "auto"}
        )
        self.assertEqual(spec.font_style, "classic_serif")
        spec = resolve_spec(
            {"brand_name": "Acme", "category": "combination",
             "style": "handcrafted", "font_style": "auto"}
        )
        self.assertEqual(spec.font_style, "script")

    def test_font_style_none_without_text(self):
        spec = resolve_spec({"category": "symbol"})
        self.assertEqual(spec.font_style, "none")

    def test_personality_follows_style_when_auto(self):
        spec = resolve_spec({"style": "luxury", "personality": "auto"})
        self.assertEqual(spec.personality, "elegant")

    def test_typed_personality_kept_verbatim(self):
        spec = resolve_spec(
            {"personality": "other", "personality_text": "serious but friendly"}
        )
        self.assertEqual(spec.personality, "custom")
        self.assertEqual(spec.personality_raw, "serious but friendly")

    def test_motif_letter_coerced_for_symbol(self):
        spec = resolve_spec({"category": "symbol", "motif": "letter"})
        self.assertEqual(spec.motif, "geometric")

    def test_motif_letter_kept_for_combination(self):
        spec = resolve_spec({"brand_name": "Acme", "category": "combination",
                             "motif": "letter"})
        self.assertEqual(spec.motif, "letter")

    def test_motif_ignored_for_wordmark(self):
        spec = resolve_spec({"brand_name": "Acme Corp", "category": "wordmark",
                             "motif": "nature"})
        self.assertEqual(spec.motif, "none")

    def test_typed_motif_kept_verbatim(self):
        spec = resolve_spec({"category": "symbol", "motif": "other",
                             "motif_text": "a lighthouse made of books"})
        self.assertEqual(spec.motif, "custom")
        self.assertEqual(spec.motif_raw, "a lighthouse made of books")

    def test_dimension_auto_never_full_3d(self):
        spec = resolve_spec({"industry": "library", "style": "auto", "dimension": "auto"})
        self.assertIn(spec.dimension, ("flat", "slight_3d"))
        spec = resolve_spec({"industry": "clothing", "style": "auto", "dimension": "auto"})
        self.assertIn(spec.dimension, ("flat", "slight_3d"))

    def test_surprise_palette_is_specialty_aware(self):
        spec = resolve_spec({"industry": "startup", "colors": "surprise"})
        self.assertTrue(spec.colors)

    def test_typed_colors_understood_multilingual(self):
        spec = resolve_spec(
            {"colors": "other", "colors_text": "akhdar w abyad"}
        )
        self.assertEqual(spec.colors, ["green", "pure white"])

        spec = resolve_spec({"colors": "other", "colors_text": "vert et or"})
        self.assertEqual(spec.colors, ["green", "gold"])

        spec = resolve_spec({"colors": "other", "colors_text": "أسود وذهبي"})
        self.assertEqual(spec.colors, ["pure black", "gold"])

    def test_typed_industry_understood_multilingual(self):
        spec = resolve_spec(
            {"industry": "other", "industry_text": "بوت لتحميل الكتب"}
        )
        self.assertEqual(spec.industry, "library")
        self.assertTrue(spec.industry_from_typed)

        spec = resolve_spec(
            {"industry": "food", "industry_food": "other",
             "industry_text": "bghit logo ta3 brand clothing"}
        )
        self.assertEqual(spec.industry, "clothing")

    def test_unrecognized_typed_industry_keeps_raw_text(self):
        spec = resolve_spec(
            {"industry": "other", "industry_text": "my weird unicorn farm"}
        )
        self.assertEqual(spec.industry, "other")
        self.assertEqual(spec.industry_text_raw, "my weird unicorn farm")

    def test_typed_background_understood(self):
        spec = resolve_spec(
            {"background": "other", "background_text": "fond bleu nuit"}
        )
        self.assertEqual(spec.background, "custom")
        self.assertEqual(spec.background_raw, "fond bleu nuit")

        spec = resolve_spec(
            {"background": "other", "background_text": "transparent background"}
        )
        self.assertEqual(spec.background, "isolated")

        spec = resolve_spec(
            {"background": "other", "background_text": "fond noir"}
        )
        self.assertEqual(spec.background, "dark")

    def test_typed_usage_understood(self):
        spec = resolve_spec(
            {"usage": "other", "usage_text": "mainly my business card"}
        )
        self.assertEqual(spec.usage, "print")

        spec = resolve_spec(
            {"usage": "other", "usage_text": "on the side of my trucks"}
        )
        self.assertEqual(spec.usage, "custom")
        self.assertEqual(spec.usage_raw, "on the side of my trucks")

    def test_background_hint_from_typed_colors(self):
        # "fond noir" typed inside the colors overrides an "auto" background
        spec = resolve_spec(
            {"colors": "other", "colors_text": "noir et doré, fond noir",
             "background": "auto"}
        )
        self.assertEqual(spec.background, "dark")

    def test_explicit_background_beats_typed_hint(self):
        spec = resolve_spec(
            {"colors": "other", "colors_text": "fond noir", "background": "white"}
        )
        self.assertEqual(spec.background, "white")

    def test_initials(self):
        self.assertEqual(resolve_initials("amine ben ali"), "ABA")
        self.assertEqual(resolve_initials("AB"), "AB")
        self.assertEqual(resolve_initials(""), "")


class TestBuildPrompt(unittest.TestCase):
    def setUp(self):
        self.spec = resolve_spec(full_answers(), {"neon"})
        self.prompt = build_prompt(self.spec)

    def test_contains_all_twelve_master_parts(self):
        p = self.prompt.lower()
        checks = {
            "1 design objective": "create a professional logo",
            "2 brand context": "the brand is",
            "3 logo concept": "develop an original",
            "4 logo category": "logo category:",
            "5 visual construction": "geometric shapes",
            "6 composition": "compose for",
            "7 color palette": "color palette",
            "8 typography": "no typography",
            "9 background": "background",
            "10 rendering style": "rendering:",
            "11 quality requirements": "scalable",
            "12 negative constraints": "strictly avoid:",
        }
        for part, needle in checks.items():
            self.assertIn(needle, p, part)

    def test_contains_the_new_brief_sentences(self):
        p = self.prompt.lower()
        self.assertIn("brand character:", p)
        self.assertIn("target audience:", p)

    def test_typed_personality_embedded(self):
        spec = resolve_spec(
            full_answers(personality="other", personality_text="serious but friendly")
        )
        self.assertIn("serious but friendly", build_prompt(spec))

    def test_typed_motif_embedded(self):
        spec = resolve_spec(
            full_answers(motif="other", motif_text="a lighthouse made of books")
        )
        prompt = build_prompt(spec)
        self.assertIn("a lighthouse made of books", prompt)
        self.assertIn("evoke", prompt.lower())

    def test_structured_motif_embedded(self):
        spec = resolve_spec(full_answers(motif="nature"))
        self.assertIn("leaf", build_prompt(spec))

    def test_no_motif_sentence_for_wordmark(self):
        spec = resolve_spec(
            {"brand_name": "Acme Corp", "category": "wordmark", "motif": "nature"}
        )
        self.assertNotIn("evoke", build_prompt(spec).lower())

    def test_typography_feel_sentence_for_text_logos(self):
        spec = resolve_spec(
            full_answers(category="combination", typography="name_under")
        )
        prompt = build_prompt(spec)
        self.assertIn("Typography feel:", prompt)

    def test_tagline_rendered(self):
        spec = resolve_spec(
            full_answers(category="combination", typography="name_under",
                         tagline="Knowledge for everyone")
        )
        prompt = build_prompt(spec)
        self.assertIn("Knowledge for everyone", prompt)
        self.assertIn("tagline", prompt.lower())

    def test_brand_name_preserved_exactly(self):
        spec = resolve_spec({"brand_name": "MakTabati", "category": "symbol"})
        self.assertIn('MakTabati', build_prompt(spec))

    def test_colors_present(self):
        self.assertIn("green", self.prompt)
        self.assertIn("pure white", self.prompt)

    def test_typed_arabic_colors_present(self):
        spec = resolve_spec(
            {"colors": "other", "colors_text": "akhdar w abyad", "category": "symbol"}
        )
        prompt = build_prompt(spec)
        self.assertIn("green", prompt)
        self.assertIn("pure white", prompt)

    def test_flat_rendering_has_no_3d_words(self):
        self.assertNotIn("three-dimensional", self.prompt.lower())
        self.assertNotIn("3d", self.prompt.lower())

    def test_full_3d_mentioned_when_asked(self):
        spec = resolve_spec(full_answers(dimension="full_3d"))
        self.assertIn("3D", build_prompt(spec))

    def test_symbol_only_bans_typography(self):
        self.assertIn("no typography", self.prompt.lower())
        self.assertIn("typography or any lettering", self.prompt.lower())

    def test_initials_rendered(self):
        spec = resolve_spec({"brand_name": "amine ben", "category": "lettermark"})
        prompt = build_prompt(spec)
        self.assertIn("AB", prompt)

    def test_custom_background_embedded(self):
        spec = resolve_spec(
            {"background": "other", "background_text": "deep blue background"}
        )
        prompt = build_prompt(spec)
        self.assertIn("deep blue background", prompt)
        self.assertIn("custom background", prompt)

    def test_custom_usage_embedded(self):
        spec = resolve_spec(
            {"usage": "other", "usage_text": "on the side of my trucks"}
        )
        self.assertIn("on the side of my trucks", build_prompt(spec))

    def test_unrecognized_activity_kept_verbatim(self):
        spec = resolve_spec(
            {"industry": "other", "industry_text": "my weird unicorn farm",
             "category": "symbol"}
        )
        self.assertIn("my weird unicorn farm", build_prompt(spec))


class TestRestrictions(unittest.TestCase):
    def test_mandatory_lines_always_present(self):
        spec = resolve_spec(full_answers(), set())
        restrictions = build_restrictions(spec)
        joined = " ".join(restrictions).lower()
        for needle in (
            "no humans", "no human faces", "no animals",
            "no living creatures", "no sexual content",
        ):
            self.assertIn(needle, joined)

    def test_user_exclusions_added(self):
        spec = resolve_spec(full_answers(), {"neon", "gradients"})
        joined = " ".join(build_restrictions(spec))
        self.assertIn("neon lighting", joined)
        self.assertIn("gradients", joined)

    def test_white_background_extra_restriction(self):
        spec = resolve_spec(full_answers(background="white"), set())
        joined = " ".join(build_restrictions(spec)).lower()
        self.assertIn("no colored background", joined)

    def test_symbol_only_typography_restriction(self):
        spec = resolve_spec(full_answers(category="symbol"), set())
        joined = " ".join(build_restrictions(spec)).lower()
        self.assertIn("no typography", joined)

    def test_tagline_restriction(self):
        spec = resolve_spec(
            full_answers(category="combination", typography="name_under",
                         tagline="Knowledge for everyone")
        )
        joined = " ".join(build_restrictions(spec)).lower()
        self.assertIn("only the brand name and the provided tagline", joined)


class TestValidate(unittest.TestCase):
    def test_generated_prompts_score_at_least_90(self):
        scenarios = [
            (full_answers(), {"neon"}),
            (full_answers(
                brand_name="AB", industry="fashion", industry_fashion="clothing",
                category="lettermark", typography="initials", colors="black_gold",
                style="luxury", dimension="slight_3d", background="dark",
                usage="print",
            ), set()),
            (full_answers(
                brand_name="skip", industry="other",
                industry_text="مطعم حلويات", category="emblem",
                typography="auto", colors="other",
                colors_text="vert et or", style="auto", dimension="auto",
                background="dark", usage="social",
            ), {"gradients", "shadows", "complex"}),
            (full_answers(
                category="combination", typography="name_under",
                tagline="Knowledge for everyone", font_style="classic_serif",
                motif="nature", audience="family", personality="calm",
            ), set()),
            (full_answers(
                usage="other", usage_text="on the side of my trucks",
                background="other", background_text="deep blue background",
            ), set()),
        ]
        for answers, exclusions in scenarios:
            result = generate_prompt(answers, exclusions)
            self.assertGreaterEqual(result.score, 90, result.issues)
            self.assertEqual(result.issues, [])

    def test_score_is_100_for_standard_answers(self):
        result = generate_prompt(full_answers(), {"neon"})
        self.assertEqual(result.score, 100)
        self.assertEqual(sum(result.subscores.values()), 100)

    def test_broken_prompt_loses_points(self):
        spec = resolve_spec(full_answers(), set())
        generated = GeneratedPrompt(
            design_type="Symbol mark",
            design_direction="...",
            image_prompt="Just make something nice.",  # deliberately empty
            restrictions=[],
        )
        result = validate(spec, generated)
        self.assertLess(result.score, 50)
        self.assertTrue(result.issues)

    def test_altered_brand_name_detected(self):
        spec = resolve_spec(full_answers(), set())
        generated = GeneratedPrompt(
            design_type="Symbol mark",
            design_direction="...",
            image_prompt=build_prompt(spec).replace("Maktabati", "MAKTABATI"),
            restrictions=build_restrictions(spec),
        )
        result = validate(spec, generated)
        self.assertIn("brand name missing or altered in the prompt", result.issues)

    def test_missing_tagline_detected(self):
        spec = resolve_spec(
            full_answers(category="combination", typography="name_under",
                         tagline="Knowledge for everyone")
        )
        prompt = build_prompt(spec).replace("Knowledge for everyone", "REDACTED")
        generated = GeneratedPrompt(
            design_type="Combination mark",
            design_direction="...",
            image_prompt=prompt,
            restrictions=build_restrictions(spec),
        )
        result = validate(spec, generated)
        self.assertLess(result.score, 100)
        self.assertTrue(result.issues)


class TestGeneratePrompt(unittest.TestCase):
    def test_fields_present(self):
        result = generate_prompt(full_answers(), set())
        self.assertIn("Symbol", result.design_type)
        self.assertTrue(result.design_direction)
        self.assertTrue(result.image_prompt)
        self.assertTrue(result.restrictions)  # internal, still validated

    def test_direction_mentions_brand_and_palette(self):
        result = generate_prompt(full_answers(), set())
        self.assertIn("Maktabati", result.design_direction)
        self.assertIn("green", result.design_direction)

    def test_custom_unmatched_colors_fallback_kept(self):
        result = generate_prompt(
            full_answers(colors="other", colors_text="sea foam dream"), set()
        )
        self.assertIn("sea foam dream", result.image_prompt)

    def test_prompt_is_reasonably_sized_for_telegram(self):
        result = generate_prompt(
            full_answers(tagline="Knowledge for everyone"), {"neon", "gradients"}
        )
        self.assertLess(len(result.image_prompt), 3000)
        self.assertLess(
            len(result.image_prompt)
            + len(build_direction(resolve_spec(full_answers())))
            + 1500,
            4000,
        )


if __name__ == "__main__":
    unittest.main()
