"""End-to-end handler simulations with mocked Telegram objects.

Replays the reported bugs as real handler calls:

1. tap "Full premium 3D" -> answers["dimension"] == "full_3d" (was "flat")
2. tap "Other" -> the typed-input question is ASKED (was skipped)
3. typed custom answer on a button question -> accepted, described, next
4. typed "3d" -> recognized as the 3D button
5. typed "coffee shop" on the field question -> subtree filled at once
6. a stale button never stores anything
7. toggles and skip keep working with value-based callback_data

Run from the project root:
    python -m unittest tests.test_flow_sim -v
"""

from __future__ import annotations

import os

os.environ.setdefault("TASMEEM_DB", ":memory:")  # keep tests off the real DB

import asyncio
import unittest
from unittest import mock

import bot
from engine import i18n


class FakeMessage:
    def __init__(self, message_id: int = 1, text: str = ""):
        self.message_id = message_id
        self.chat_id = 777
        self.text = text
        self.sent: list = []

    async def reply_text(self, text, reply_markup=None, parse_mode=None):
        self.sent.append(text)
        return FakeMessage(message_id=self.message_id + len(self.sent), text=text)

    async def reply_html(self, text, reply_markup=None):
        self.sent.append(text)
        return FakeMessage(message_id=self.message_id + len(self.sent), text=text)


class FakeQuery:
    def __init__(self, data: str):
        self.data = data
        self.from_user = mock.Mock(id=42)
        self.message = FakeMessage(message_id=100)
        self.edited = None

    async def answer(self):
        return None

    async def edit_message_reply_markup(self, reply_markup=None):
        self.edited = reply_markup


class FakeUser:
    def __init__(self, user_id: int = 42):
        self.id = user_id


class FakeUpdate:
    def __init__(self, query: FakeQuery = None, message: FakeMessage = None,
                 user_id: int = 42):
        self.callback_query = query
        self._message = message or FakeMessage()
        self.effective_user = FakeUser(user_id)

    @property
    def effective_message(self):
        return self._message if self.callback_query is None else self.callback_query.message

    @property
    def message(self):
        # like the real Update: the message itself (None on callback updates)
        return None if self.callback_query is not None else self._message


class FakeBot:
    def __init__(self):
        self.edits: list = []

    async def edit_message_reply_markup(self, chat_id=None, message_id=None,
                                        reply_markup=None):
        self.edits.append((chat_id, message_id, reply_markup))


class FakeContext:
    def __init__(self):
        self.user_data = {}
        self.bot = FakeBot()


def run(coro):
    return asyncio.run(coro)


class TestTapFlows(unittest.TestCase):
    def test_tap_full_3d_stores_full_3d(self):
        update = FakeUpdate(query=FakeQuery("ans:dimension:full_3d"))
        context = FakeContext()
        context.user_data["current_question"] = "dimension"
        context.user_data["answers"] = {}
        state = run(bot.handle_answer_button(update, context))
        self.assertEqual(context.user_data["answers"]["dimension"], "full_3d")
        # the next question (background) was asked
        self.assertEqual(state, "background")

    def test_tap_cafe_stores_cafe(self):
        update = FakeUpdate(query=FakeQuery("ans:industry_food:cafe"))
        context = FakeContext()
        context.user_data["current_question"] = "industry_food"
        context.user_data["answers"] = {"industry": "food"}
        run(bot.handle_answer_button(update, context))
        self.assertEqual(context.user_data["answers"]["industry_food"], "cafe")

    def test_tap_other_opens_the_typed_input(self):
        update = FakeUpdate(query=FakeQuery("ans:usage:other"))
        context = FakeContext()
        context.user_data["current_question"] = "usage"
        context.user_data["answers"] = {}
        state = run(bot.handle_answer_button(update, context))
        # the typed-input follow-up question was asked - not skipped
        self.assertEqual(state, "usage_text")
        self.assertEqual(context.user_data["current_question"], "usage_text")
        self.assertIn(i18n.t("en", "q_usage_text"), update.callback_query.message.sent)

    def test_tap_other_on_field_opens_typed_input(self):
        update = FakeUpdate(query=FakeQuery("ans:industry:other"))
        context = FakeContext()
        context.user_data["current_question"] = "industry"
        context.user_data["answers"] = {}
        state = run(bot.handle_answer_button(update, context))
        self.assertEqual(state, "industry_text")
        self.assertEqual(context.user_data["answers"]["industry"], "other")

    def test_skip_button_stores_skip(self):
        update = FakeUpdate(query=FakeQuery("ans:brand_name:skip"))
        context = FakeContext()
        context.user_data["current_question"] = "brand_name"
        context.user_data["answers"] = {}
        state = run(bot.handle_skip_button(update, context))
        self.assertEqual(context.user_data["answers"]["brand_name"], "skip")
        self.assertEqual(state, "industry")

    def test_stale_button_stores_nothing(self):
        update = FakeUpdate(query=FakeQuery("ans:industry:other"))
        context = FakeContext()
        context.user_data["current_question"] = "category"
        context.user_data["answers"] = {}
        state = run(bot.handle_answer_button(update, context))
        self.assertNotIn("industry", context.user_data["answers"])
        self.assertEqual(state, "category")  # re-asked the current question

    def test_toggle_values_and_done(self):
        update = FakeUpdate(query=FakeQuery("tog:gradients"))
        context = FakeContext()
        context.user_data["current_question"] = "exclusions"
        context.user_data["answers"] = {}
        run(bot.handle_toggle(update, context))
        self.assertEqual(context.user_data["exclusions"], {"gradients"})

        update = FakeUpdate(query=FakeQuery("tog:gradients"))
        run(bot.handle_toggle(update, context))
        self.assertEqual(context.user_data["exclusions"], set())

        update = FakeUpdate(query=FakeQuery("tog:done"))
        state = run(bot.handle_toggle(update, context))
        # all questions answered -> straight to the confirm screen
        self.assertEqual(state, "confirm")


class TestTypedFlows(unittest.TestCase):
    def test_typed_custom_answer_is_kept(self):
        update = FakeUpdate(message=FakeMessage(text="university students"))
        context = FakeContext()
        context.user_data["current_question"] = "audience"
        context.user_data["answers"] = {}
        state = run(bot.handle_buttons_text(update, context))
        answers = context.user_data["answers"]
        self.assertEqual(answers["audience"], "other")
        self.assertEqual(answers["audience_text"], "university students")
        # audience_text is already answered -> straight to personality
        self.assertEqual(state, "personality")
        # the user got the acknowledgment
        self.assertIn("university students", update.effective_message.sent[0])

    def test_typed_3d_selects_the_3d_button(self):
        update = FakeUpdate(message=FakeMessage(text="3d"))
        context = FakeContext()
        context.user_data["current_question"] = "dimension"
        context.user_data["answers"] = {}
        state = run(bot.handle_buttons_text(update, context))
        self.assertEqual(context.user_data["answers"]["dimension"], "full_3d")
        self.assertEqual(state, "background")

    def test_typed_coffee_shop_fills_the_subtree(self):
        update = FakeUpdate(message=FakeMessage(text="coffee shop"))
        context = FakeContext()
        context.user_data["current_question"] = "industry"
        context.user_data["answers"] = {}
        state = run(bot.handle_buttons_text(update, context))
        answers = context.user_data["answers"]
        self.assertEqual(answers["industry"], "food")
        self.assertEqual(answers["industry_food"], "cafe")
        # the specialty subtree is already answered -> category is next
        self.assertEqual(state, "category")

    def test_typed_field_name_opens_the_subtree(self):
        # typing the exact FIELD name behaves like the tap: the specialty
        # question is asked next (no leaf guessed)
        update = FakeUpdate(message=FakeMessage(text="Food & Drink"))
        context = FakeContext()
        context.user_data["current_question"] = "industry"
        context.user_data["answers"] = {}
        state = run(bot.handle_buttons_text(update, context))
        self.assertEqual(context.user_data["answers"]["industry"], "food")
        self.assertNotIn("industry_food", context.user_data["answers"])
        self.assertEqual(state, "industry_food")

    def test_typed_text_on_text_question_still_works(self):
        update = FakeUpdate(message=FakeMessage(text="  Maktabati  "))
        context = FakeContext()
        context.user_data["current_question"] = "brand_name"
        context.user_data["answers"] = {}
        state = run(bot.handle_answer_text(update, context))
        self.assertEqual(context.user_data["answers"]["brand_name"], "Maktabati")
        self.assertEqual(state, "industry")


class TestConfirmFlow(unittest.TestCase):
    def test_generate_renders_without_restrictions_block(self):
        update = FakeUpdate(query=FakeQuery("q:generate"))
        context = FakeContext()
        context.user_data["answers"] = {
            "brand_name": "Zina",
            "industry": "fashion",
            "industry_fashion": "clothing",
            "category": "combination",
        }
        context.user_data["exclusions"] = set()
        state = run(bot.confirm_cb(update, context))
        self.assertEqual(state, bot.ConversationHandler.END)
        rendered = "\n".join(update.callback_query.message.sent)
        self.assertIn("DESIGN TYPE", rendered)
        self.assertIn("IMAGE GENERATION PROMPT", rendered)
        self.assertNotIn("RESTRICTIONS", rendered)
        self.assertIn("Zina", rendered)
        self.assertIn("clothing and fashion brand", rendered)


if __name__ == "__main__":
    unittest.main()
