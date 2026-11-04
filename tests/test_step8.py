"""Step 8 tests: second mode (Social media ads), support tag, admin IDs.

Run from the project root:
    python -m unittest tests.test_step8 -v
"""

from __future__ import annotations

import os

os.environ.setdefault("TASMEEM_DB", ":memory:")  # keep tests off the real DB

import asyncio
import unittest
from unittest import mock

import bot
import config
import store
from engine import i18n, modes
from engine.builder_ads import generate_ads_prompt
from engine.questions_ads import AD_GOAL_GROUPS, AD_VISUAL_GROUPS, ADS_QUESTIONS


# ---------------------------------------------------------------------------
# Fakes (same shape as test_step7)
# ---------------------------------------------------------------------------

class FakeMessage:
    def __init__(self, chat_id: int = 777):
        self.chat_id = chat_id
        self.message_id = 1
        self.sent: list = []
        self.replies: list = []

    async def reply_text(self, text, reply_markup=None, parse_mode=None, **kwargs):
        self.sent.append(text)
        self.replies.append(reply_markup)
        return FakeMessage()

    async def reply_html(self, text, reply_markup=None):
        self.sent.append(text)
        self.replies.append(reply_markup)
        return FakeMessage()


class FakeQuery:
    def __init__(self, data: str, user_id: int, chat_id: int = 777):
        self.data = data
        self.from_user = mock.Mock(id=user_id, username=None)
        self.message = FakeMessage(chat_id=chat_id)
        self.answered_with = None

    async def answer(self, text=None, show_alert=False):
        self.answered_with = (text, show_alert)

    async def edit_message_reply_markup(self, reply_markup=None):
        return None


class FakeUpdate:
    def __init__(self, query: FakeQuery = None, message: FakeMessage = None,
                 user_id: int = 42):
        self.callback_query = query
        self._message = message or FakeMessage()
        self.effective_user = mock.Mock(id=user_id, username=None)

    @property
    def effective_message(self):
        return self._message if self.callback_query is None else self.callback_query.message

    @property
    def message(self):
        return None if self.callback_query is not None else self._message


class FakeBot:
    def __init__(self, member_ids=(), username="tasmeem_bot"):
        self._members = set(member_ids)
        self._username = username
        self.edits: list = []
        self.sent_messages: list = []

    async def get_chat_member(self, chat_id=None, user_id=None):
        status = "member" if user_id in self._members else "left"
        return mock.Mock(status=status)

    async def get_me(self):
        return mock.Mock(username=self._username)

    async def edit_message_reply_markup(self, chat_id=None, message_id=None,
                                        reply_markup=None):
        self.edits.append((chat_id, message_id, reply_markup))

    async def send_message(self, chat_id, text, **kwargs):
        self.sent_messages.append((chat_id, text))


class FakeContext:
    def __init__(self, bot: FakeBot = None):
        self.user_data = {}
        self.bot_data = {}
        self.bot = bot or FakeBot()
        self.args = []


def run(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Admin IDs
# ---------------------------------------------------------------------------

class TestAdminIds(unittest.TestCase):
    def test_owner_id_is_registered(self):
        self.assertIn(8974969463, config.ADMIN_IDS)

    def test_admin_unlocks_by_numeric_id_even_with_any_username(self):
        user = mock.Mock(id=8974969463, username="someone_else")
        self.assertTrue(bot._is_owner(user))

    def test_admin_unlocks_by_username(self):
        user = mock.Mock(id=111, username="vxgix")
        self.assertTrue(bot._is_owner(user))

    def test_stranger_is_not_owner(self):
        user = mock.Mock(id=222, username="random")
        self.assertFalse(bot._is_owner(user))

    def test_admin_dashboard_answers_to_the_numeric_id(self):
        message = FakeMessage()
        update = mock.Mock(
            effective_message=message,
            effective_user=mock.Mock(id=8974969463, username="not_vxgix"),
        )
        run(bot.cmd_admin(update, FakeContext()))
        self.assertEqual(len(message.sent), 1)
        self.assertIn("Users:", message.sent[0])


# ---------------------------------------------------------------------------
# @vxgix after the output
# ---------------------------------------------------------------------------

class TestSupportAfterOutput(unittest.TestCase):
    LOGO_ANSWERS = {
        "brand_name": "Zina",
        "industry": "fashion",
        "industry_fashion": "clothing",
        "category": "combination",
    }

    ADS_ANSWERS = {
        "ad_brand_name": "Gifthub",
        "ad_username": "@gifthubai",
        "industry": "tech",
        "industry_tech": "startup",
        "ad_goal": "sales",
        "ad_goal_sales": "discount",
        "ad_platform": "instagram",
        "ad_format": "story",
        "ad_offer": "50% off everything",
        "ad_cta": "shop_now",
        "ad_lang_text": "en",
        "ad_headline": "MEGA SALE -50%",
        "ad_visual": "product",
        "ad_visual_product": "studio",
        "ad_logo": "yes",
    }

    def test_logo_output_ends_with_the_support_tag(self):
        result = modes.mode_of("logo").builder(self.LOGO_ANSWERS, set())
        rendered = bot.render_prompt_html(result, "en", mode="logo")
        self.assertIn("@vxgix", rendered)
        self.assertIn(i18n.t("en", "out_support", support=""), rendered.replace(
            '<a href="https://t.me/vxgix">@vxgix</a>', ""
        ))

    def test_ads_output_ends_with_the_support_tag(self):
        result = generate_ads_prompt(self.ADS_ANSWERS, set())
        rendered = bot.render_prompt_html(result, "en", mode="ads")
        self.assertIn("@vxgix", rendered)
        self.assertIn("How to use it", rendered)

    def test_ads_output_tells_to_paste_the_logo_with_the_prompt(self):
        result = generate_ads_prompt(self.ADS_ANSWERS, set())
        rendered = bot.render_prompt_html(result, "en", mode="ads")
        howto = i18n.t("en", "ads_howto")
        self.assertIn(howto, rendered)
        self.assertIn("logo image together with the prompt", howto)

    def test_ads_output_suggests_logo_mode_when_no_logo(self):
        answers = dict(self.ADS_ANSWERS, ad_logo="no")
        result = generate_ads_prompt(answers, set())
        self.assertEqual(result.logo, "no")
        rendered = bot.render_prompt_html(result, "en", mode="ads")
        self.assertIn(i18n.t("en", "ads_howto_nologo"), rendered)

    def test_support_button_sits_under_the_output(self):
        markup = bot._new_prompt_keyboard("en", modes.MODE_ADS)
        buttons = [b for row in markup.inline_keyboard for b in row]
        callbacks = [b.callback_data for b in buttons]
        self.assertIn("donate:open", callbacks)
        self.assertIn(config.SUPPORT_URL, [b.url for b in buttons if b.url])
        # "Create another one" re-enters the same mode
        new_btn = next(b for b in buttons if b.callback_data.startswith("q:start"))
        self.assertEqual(new_btn.callback_data, "q:start:ads")


# ---------------------------------------------------------------------------
# Menu with the two mode buttons
# ---------------------------------------------------------------------------

class TestModeMenu(unittest.TestCase):
    def test_menu_has_logo_and_ads_buttons(self):
        markup = bot._menu_keyboard("en")
        rows = markup.inline_keyboard
        mode_row = rows[1]
        self.assertEqual(
            [(b.text, b.callback_data) for b in mode_row],
            [
                (i18n.t("en", "btn_mode_logo"), "q:start:logo"),
                (i18n.t("en", "btn_mode_ads"), "q:start:ads"),
            ],
        )

    def test_menu_start_with_ads_opens_the_first_ads_question(self):
        store.get_or_create(8101)
        bot._member_cache.clear()
        query = FakeQuery("q:start:ads", user_id=8101)
        context = FakeContext(FakeBot(member_ids={8101}))
        state = run(bot.menu_start_cb(FakeUpdate(query=query), context))
        self.assertEqual(state, "ad_brand_name")
        self.assertEqual(context.user_data["mode"], "ads")

    def test_menu_start_with_logo_opens_the_first_logo_question(self):
        store.get_or_create(8102)
        bot._member_cache.clear()
        query = FakeQuery("q:start:logo", user_id=8102)
        context = FakeContext(FakeBot(member_ids={8102}))
        state = run(bot.menu_start_cb(FakeUpdate(query=query), context))
        self.assertEqual(state, "brand_name")
        self.assertEqual(context.user_data["mode"], "logo")

    def test_legacy_q_start_opens_the_logo_mode(self):
        store.get_or_create(8103)
        bot._member_cache.clear()
        query = FakeQuery("q:start", user_id=8103)
        context = FakeContext(FakeBot(member_ids={8103}))
        state = run(bot.menu_start_cb(FakeUpdate(query=query), context))
        self.assertEqual(state, "brand_name")
        self.assertEqual(context.user_data["mode"], "logo")


# ---------------------------------------------------------------------------
# Ads questionnaire structure & flow
# ---------------------------------------------------------------------------

class TestAdsQuestionnaire(unittest.TestCase):
    def test_ads_mode_has_trees_and_asks_brand_then_username(self):
        ads = modes.mode_of("ads")
        self.assertEqual(ads.first_question_id({}), "ad_brand_name")
        nxt = ads.next_question_id("ad_brand_name", {"ad_brand_name": "X"})
        self.assertEqual(nxt, "ad_username")

    def test_goal_tree_leaves_are_unique_per_group(self):
        all_leaves = [leaf for leaves in AD_GOAL_GROUPS.values() for leaf in leaves]
        self.assertEqual(len(all_leaves), len(set(all_leaves)))
        self.assertIn("flash", all_leaves)

    def test_visual_tree_contains_food_and_product_families(self):
        self.assertIn("product", AD_VISUAL_GROUPS)
        self.assertIn("food", AD_VISUAL_GROUPS)
        self.assertIn("studio", AD_VISUAL_GROUPS["product"])

    def test_typing_a_goal_leaf_fills_the_subtree_at_once(self):
        message = FakeMessage()
        message.text = "giveaway"
        update = FakeUpdate(message=message)
        context = FakeContext(FakeBot())
        context.user_data["current_question"] = "ad_goal"
        context.user_data["mode"] = "ads"
        context.user_data["answers"] = {}
        state = run(bot.handle_buttons_text(update, context))
        self.assertEqual(context.user_data["answers"]["ad_goal"], "growth")
        self.assertEqual(context.user_data["answers"]["ad_goal_growth"], "giveaway")
        self.assertEqual(state, "ad_platform")

    def test_headline_skipped_when_visual_has_no_text(self):
        ads = modes.mode_of("ads")
        # "No text on the visual" -> the headline question is skipped
        self.assertEqual(
            ads.next_question_id("ad_lang_text", {"ad_lang_text": "none"}),
            "ad_visual",
        )
        # a text language -> the headline question is asked
        self.assertEqual(
            ads.next_question_id("ad_lang_text", {"ad_lang_text": "en"}),
            "ad_headline",
        )

    def test_typical_ads_walk_covers_all_key_questions(self):
        ads = modes.mode_of("ads")
        answers = {}
        walk = []
        current = ads.first_question_id(answers)
        while current:
            walk.append(current)
            if current == "industry":
                answers["industry"] = "food"
            elif current.startswith("industry_") and current != "industry_text":
                answers[current] = "restaurant"
            elif current == "ad_goal":
                answers[current] = "sales"
            elif current.startswith("ad_goal_") and current != "ad_goal_text":
                answers[current] = "discount"
            elif current == "ad_visual":
                answers[current] = "product"
            elif current.startswith("ad_visual_") and current != "ad_visual_text":
                answers[current] = "studio"
            else:
                answers[current] = "x"
            current = ads.next_question_id(current, answers)
        for required in (
            "ad_brand_name", "ad_username", "industry", "industry_food",
            "ad_goal", "ad_goal_sales", "ad_platform", "ad_format",
            "ad_offer", "ad_cta", "ad_lang_text", "ad_headline",
            "ad_visual", "ad_visual_product", "ad_logo", "style", "colors",
            "audience", "exclusions",
        ):
            self.assertIn(required, walk)


# ---------------------------------------------------------------------------
# Ads prompt builder & validator
# ---------------------------------------------------------------------------

class TestAdsBuilder(unittest.TestCase):
    FULL = {
        "ad_brand_name": "Gifthub",
        "ad_username": "@gifthubai",
        "industry": "tech",
        "industry_tech": "startup",
        "ad_goal": "sales",
        "ad_goal_sales": "flash",
        "ad_platform": "instagram",
        "ad_format": "story",
        "ad_offer": "50% off everything, today only",
        "ad_cta": "shop_now",
        "ad_lang_text": "en",
        "ad_headline": "FLASH SALE -50%",
        "ad_visual": "product",
        "ad_visual_product": "studio",
        "ad_logo": "yes",
        "style": "modern",
        "colors": "black_gold",
        "audience": "young",
    }

    def test_full_answers_score_100(self):
        result = generate_ads_prompt(self.FULL, set())
        self.assertEqual(result.score, 100, result.issues)
        self.assertIn("FLASH SALE -50%", result.image_prompt)
        self.assertIn("Gifthub", result.image_prompt)
        self.assertIn("@gifthubai", result.image_prompt)

    def test_headline_is_case_sensitive(self):
        result = generate_ads_prompt(self.FULL, set())
        self.assertNotIn("flash sale -50%", result.image_prompt)

    def test_logo_yes_tells_the_model_the_image_is_provided(self):
        result = generate_ads_prompt(self.FULL, set())
        self.assertIn("provided together with this prompt", result.image_prompt)

    def test_logo_no_reserves_a_clean_area(self):
        result = generate_ads_prompt(dict(self.FULL, ad_logo="no"), set())
        self.assertIn("Do not invent a logo", result.image_prompt)

    def test_no_text_mode_removes_all_text_requirements(self):
        answers = dict(self.FULL, ad_lang_text="none")
        answers.pop("ad_headline", None)
        result = generate_ads_prompt(answers, set())
        self.assertEqual(result.score, 100, result.issues)
        self.assertIn("no text baked into the image", result.image_prompt.lower())

    def test_custom_goal_and_visual_embed_the_typed_words(self):
        answers = {
            "ad_goal": "other",
            "ad_goal_text": "RAMADAN OFFER",
            "ad_visual": "other",
            "ad_visual_text": "my blue sneaker floating with paint splashes",
        }
        result = generate_ads_prompt(answers, set())
        self.assertIn('RAMADAN OFFER', result.image_prompt)
        self.assertIn("my blue sneaker floating with paint splashes", result.image_prompt)
        self.assertGreaterEqual(result.score, 90, result.issues)

    def test_design_type_names_platform_format_and_goal(self):
        result = generate_ads_prompt(self.FULL, set())
        self.assertEqual(
            result.design_type, "Instagram post - Story / Reels - Flash"
        )

    def test_negative_constraints_are_always_embedded(self):
        result = generate_ads_prompt({"industry": "food"}, set())
        low = result.image_prompt.lower()
        for item in ("gibberish text", "watermarks", "distorted or stretched logo"):
            self.assertIn(item, low)

    def test_minimal_answers_still_score_high(self):
        result = generate_ads_prompt({"industry": "food"}, set())
        self.assertGreaterEqual(result.score, 90, result.issues)


# ---------------------------------------------------------------------------
# End-to-end: full ads flow through the handlers (gates + credits)
# ---------------------------------------------------------------------------

class TestAdsEndToEnd(unittest.TestCase):
    ANSWERS = {
        "ad_brand_name": "Gifthub",
        "ad_username": "@gifthubai",
        "industry": "tech",
        "industry_tech": "startup",
        "ad_goal": "sales",
        "ad_goal_sales": "discount",
        "ad_platform": "instagram",
        "ad_format": "story",
        "ad_offer": "50% off everything",
        "ad_cta": "shop_now",
        "ad_lang_text": "en",
        "ad_headline": "MEGA SALE -50%",
        "ad_visual": "product",
        "ad_visual_product": "studio",
        "ad_logo": "yes",
        "style": "luxury",
        "colors": "black_gold",
        "audience": "young",
        "exclusions": "done",
    }

    def test_full_ads_generation_spends_one_credit_and_delivers(self):
        bot._member_cache.clear()
        user_id = 8201
        store.get_or_create(user_id)
        before = store.snapshot(user_id)["credits"]

        context = FakeContext(FakeBot(member_ids={user_id}))
        context.user_data["mode"] = "ads"
        context.user_data["answers"] = dict(self.ANSWERS)
        context.user_data["exclusions"] = set()
        query = FakeQuery("q:generate", user_id=user_id)
        state = run(bot.confirm_cb(FakeUpdate(query=query), context))

        self.assertEqual(state, bot.ConversationHandler.END)
        self.assertEqual(
            store.snapshot(user_id)["credits"], before - config.GENERATION_COST
        )
        output = "\n".join(query.message.sent)
        self.assertIn("IMAGE GENERATION PROMPT", output)
        self.assertIn("MEGA SALE -50%", output)
        self.assertIn("How to use it", output)
        self.assertIn("@vxgix", output)

    def test_logo_generation_still_works_and_shows_the_support_tag(self):
        bot._member_cache.clear()
        user_id = 8202
        store.get_or_create(user_id)
        context = FakeContext(FakeBot(member_ids={user_id}))
        context.user_data["mode"] = "logo"
        context.user_data["answers"] = {
            "brand_name": "Zina",
            "industry": "fashion",
            "industry_fashion": "clothing",
            "category": "combination",
        }
        context.user_data["exclusions"] = set()
        query = FakeQuery("q:generate", user_id=user_id)
        state = run(bot.confirm_cb(FakeUpdate(query=query), context))
        self.assertEqual(state, bot.ConversationHandler.END)
        output = "\n".join(query.message.sent)
        self.assertIn("IMAGE GENERATION PROMPT", output)
        self.assertNotIn("HOW TO USE IT", output)  # logo mode has no how-to
        self.assertIn("@vxgix", output)

    def test_summary_covers_ads_answers(self):
        summary = modes.build_answers_summary(
            "ads",
            dict(self.ANSWERS, exclusions=None),
            set(),
            "en",
        )
        self.assertIn("Brand / page name: Gifthub", summary)
        self.assertIn("Page username: @gifthubai", summary)
        self.assertIn("Post goal: Sell & promote", summary)
        self.assertIn("Details: Sale / discount / promo code", summary)
        self.assertIn("Headline: MEGA SALE -50%", summary)


if __name__ == "__main__":
    unittest.main()
