"""Step 7 handler tests: gates, credits flow, referral link, donations.

Simulates the new Telegram handlers with fakes:
- the force-subscribe gate blocks a non-member and lets a member pass
- starting the questionnaire needs at least one credit
- generating spends exactly one credit and shows the balance left
- a broke user gets the not-enough message instead of a prompt
- /start ref<id> credits the inviter once
- the donation keyboard offers 25/50/75/100 Stars and an invoice is sent
- a successful payment is recorded and thanked

Run from the project root:
    python -m unittest tests.test_step7 -v
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
from engine import i18n


# ---------------------------------------------------------------------------
# Minimal Telegram fakes (self-contained on purpose)
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


class FakeQuery:
    def __init__(self, data: str, user_id: int, chat_id: int = 777):
        self.data = data
        self.from_user = mock.Mock(id=user_id, username=None)
        self.message = FakeMessage(chat_id=chat_id)
        self.answered_with = None

    async def answer(self, text=None, show_alert=False):
        self.answered_with = (text, show_alert)


class FakeUpdate:
    def __init__(self, query: FakeQuery = None, message: FakeMessage = None,
                 user_id: int = 42):
        self.callback_query = query
        self._message = message or FakeMessage()
        self.effective_user = mock.Mock(id=user_id, username=None)

    @property
    def effective_message(self):
        return self._message if self.callback_query is None else self.callback_query.message


class FakeBot:
    """A bot that knows a channel membership for each user."""

    def __init__(self, member_ids=(), username="tasmeem_bot"):
        self._members = set(member_ids)
        self._username = username
        self.invoices: list = []
        self.sent_messages: list = []

    async def get_chat_member(self, chat_id=None, user_id=None):
        status = "member" if user_id in self._members else "left"
        return mock.Mock(status=status)

    async def get_me(self):
        return mock.Mock(username=self._username)

    async def send_invoice(self, **kwargs):
        self.invoices.append(kwargs)

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


def drain(user_id: int) -> None:
    """Bring a user's balance to exactly 0."""
    store.get_or_create(user_id)
    while store.spend(user_id):
        pass


# ---------------------------------------------------------------------------
# Keyboards
# ---------------------------------------------------------------------------

class TestKeyboards(unittest.TestCase):
    def test_donate_keyboard_shows_the_four_star_amounts(self):
        markup = bot._donate_keyboard()
        data = [
            (btn.text, btn.callback_data)
            for row in markup.inline_keyboard
            for btn in row
        ]
        self.assertEqual(
            data,
            [("⭐ 25", "donate:25"), ("⭐ 50", "donate:50"),
             ("⭐ 75", "donate:75"), ("⭐ 100", "donate:100")],
        )

    def test_output_keyboard_has_the_white_heart_donate_button(self):
        markup = bot._new_prompt_keyboard("en")
        texts = [btn.text for row in markup.inline_keyboard for btn in row]
        callbacks = [btn.callback_data for row in markup.inline_keyboard for btn in row]
        self.assertIn(i18n.t("en", "btn_donate"), texts)
        self.assertIn("🤍", i18n.t("en", "btn_donate"))
        self.assertIn("donate:open", callbacks)

    def test_menu_keyboard_has_donate_and_support(self):
        markup = bot._menu_keyboard("en")
        rows = markup.inline_keyboard
        donate_btn, support_btn = rows[-1]
        self.assertEqual(donate_btn.callback_data, "donate:open")
        self.assertEqual(support_btn.url, config.SUPPORT_URL)
        self.assertEqual(config.SUPPORT_URL, "https://t.me/vxgix")

    def test_force_sub_keyboard_links_the_required_channel(self):
        markup = bot._force_sub_keyboard("en")
        (join_btn,) = markup.inline_keyboard[0]
        (check_btn,) = markup.inline_keyboard[1]
        self.assertEqual(join_btn.url, config.CHANNEL_URL)
        self.assertEqual(config.CHANNEL_URL, "https://t.me/gifthubai")
        self.assertEqual(check_btn.callback_data, "fs:check")


# ---------------------------------------------------------------------------
# Force-subscribe gate
# ---------------------------------------------------------------------------

class TestForceSubscribeGate(unittest.TestCase):
    def setUp(self):
        bot._member_cache.clear()

    def test_non_member_is_blocked_with_join_message(self):
        query = FakeQuery("q:start", user_id=7001)
        context = FakeContext(FakeBot(member_ids=()))  # 7001 is NOT a member
        state = run(bot.menu_start_cb(FakeUpdate(query=query), context))
        self.assertEqual(state, "menu")
        self.assertIn(
            i18n.t("en", "fs_required", channel_link=config.CHANNEL_URL),
            query.message.sent,
        )
        # no question was asked
        self.assertNotIn("current_question", context.user_data)

    def test_member_passes_straight_to_the_first_question(self):
        store.get_or_create(7002)
        query = FakeQuery("q:start", user_id=7002)
        context = FakeContext(FakeBot(member_ids={7002}))
        state = run(bot.menu_start_cb(FakeUpdate(query=query), context))
        self.assertNotEqual(state, "menu")
        self.assertEqual(state, bot.first_question_id({}))

    def test_check_button_opens_the_menu_after_joining(self):
        query = FakeQuery("fs:check", user_id=7003)
        context = FakeContext(FakeBot(member_ids={7003}))
        run(bot.fs_check_cb(FakeUpdate(query=query), context))
        menu_sent = query.message.sent[0]
        self.assertTrue(menu_sent.startswith(i18n.t("en", "menu_text")))
        # the credits line is part of the menu now
        self.assertIn(
            i18n.t("en", "menu_credits", credits=5, refill=3), menu_sent
        )

    def test_check_button_alerts_when_still_not_a_member(self):
        query = FakeQuery("fs:check", user_id=7004)
        context = FakeContext(FakeBot(member_ids=()))
        run(bot.fs_check_cb(FakeUpdate(query=query), context))
        self.assertEqual(
            query.answered_with, (i18n.t("en", "fs_still"), True)
        )


# ---------------------------------------------------------------------------
# Credits flow
# ---------------------------------------------------------------------------

class TestCreditsFlow(unittest.TestCase):
    def setUp(self):
        bot._member_cache.clear()

    def test_starting_the_questionnaire_needs_one_credit(self):
        drain(7101)
        query = FakeQuery("q:start", user_id=7101)
        context = FakeContext(FakeBot(member_ids={7101}))
        state = run(bot.menu_start_cb(FakeUpdate(query=query), context))
        self.assertEqual(state, "menu")
        expected = i18n.t(
            "en", "not_enough", cost=config.GENERATION_COST,
            credits=0, refill=config.DAILY_REFILL, bonus=config.REFERRAL_BONUS,
        )
        self.assertIn(expected, query.message.sent)

    def test_generate_spends_one_credit_and_shows_the_leftover(self):
        store.get_or_create(7102)
        query = FakeQuery("q:generate", user_id=7102)
        context = FakeContext(FakeBot(member_ids={7102}))
        context.user_data["answers"] = {
            "brand_name": "Zina",
            "industry": "fashion",
            "industry_fashion": "clothing",
            "category": "combination",
        }
        context.user_data["exclusions"] = set()
        before = store.snapshot(7102)["credits"]
        state = run(bot.confirm_cb(FakeUpdate(query=query), context))
        self.assertEqual(state, bot.ConversationHandler.END)
        self.assertEqual(
            store.snapshot(7102)["credits"], before - config.GENERATION_COST
        )
        rendered = "\n".join(query.message.sent)
        self.assertIn(
            i18n.t("en", "out_credits",
                   credits=before - config.GENERATION_COST,
                   refill=config.DAILY_REFILL),
            rendered,
        )

    def test_generate_with_zero_credits_is_blocked(self):
        drain(7103)
        query = FakeQuery("q:generate", user_id=7103)
        context = FakeContext(FakeBot(member_ids={7103}))
        context.user_data["answers"] = {"industry": "food"}
        context.user_data["exclusions"] = set()
        state = run(bot.confirm_cb(FakeUpdate(query=query), context))
        self.assertEqual(state, "confirm")
        self.assertNotIn("DESIGN TYPE", "\n".join(query.message.sent))
        self.assertIn("0", "\n".join(query.message.sent))


# ---------------------------------------------------------------------------
# Referral deep link
# ---------------------------------------------------------------------------

class TestReferralDeepLink(unittest.TestCase):
    def setUp(self):
        bot._member_cache.clear()

    def test_start_with_ref_link_credits_the_inviter_once(self):
        inviter_before = store.snapshot(7201)["credits"]
        bot_obj = FakeBot(member_ids={7202})
        update = FakeUpdate(message=FakeMessage(), user_id=7202)
        context = FakeContext(bot_obj)
        context.args = ["ref7201"]
        run(bot.cmd_start(update, context))
        # the inviter gained exactly the bonus
        self.assertEqual(
            store.snapshot(7201)["credits"],
            inviter_before + config.REFERRAL_BONUS,
        )
        # the new user is marked as referred
        self.assertEqual(store.get_or_create(7202)["referrer_id"], 7201)
        # and the inviter was notified
        self.assertEqual(len(bot_obj.sent_messages), 1)
        self.assertEqual(bot_obj.sent_messages[0][0], 7201)

    def test_second_start_with_the_same_link_pays_nothing(self):
        store.get_or_create(7211)
        inviter_before = store.snapshot(7210)["credits"]
        update = FakeUpdate(message=FakeMessage(), user_id=7211)
        context = FakeContext(FakeBot(member_ids={7211}))
        context.args = ["ref7210"]
        run(bot.cmd_start(update, context))
        self.assertEqual(
            store.snapshot(7210)["credits"], inviter_before
        )

    def test_menu_shows_the_credits_line(self):
        user = store.snapshot(7220)
        update = FakeUpdate(message=FakeMessage(), user_id=7220)
        context = FakeContext(FakeBot(member_ids={7220}))
        run(bot.cmd_start(update, context))
        sent = update.effective_message.sent[0]
        self.assertIn(i18n.t("en", "menu_text"), sent)
        self.assertIn(
            i18n.t("en", "menu_credits", credits=user["credits"],
                   refill=config.DAILY_REFILL),
            sent,
        )


# ---------------------------------------------------------------------------
# Donations (Telegram Stars)
# ---------------------------------------------------------------------------

class TestDonations(unittest.TestCase):
    def test_choosing_an_amount_sends_an_xtr_invoice(self):
        query = FakeQuery("donate:50", user_id=7301)
        context = FakeContext(FakeBot(member_ids={7301}))
        run(bot.donate_cb(FakeUpdate(query=query), context))
        self.assertEqual(len(context.bot.invoices), 1)
        invoice = context.bot.invoices[0]
        self.assertEqual(invoice["currency"], "XTR")
        self.assertEqual(invoice["provider_token"], "")
        self.assertEqual(invoice["payload"], "donate:50")
        self.assertEqual(invoice["prices"][0].amount, 50)

    def test_donate_open_shows_the_amount_buttons(self):
        query = FakeQuery("donate:open", user_id=7302)
        context = FakeContext(FakeBot())
        run(bot.donate_cb(FakeUpdate(query=query), context))
        markup = query.message.replies[0]
        callbacks = [
            btn.callback_data for row in markup.inline_keyboard for btn in row
        ]
        self.assertEqual(
            callbacks, ["donate:25", "donate:50", "donate:75", "donate:100"]
        )
        # no invoice before an amount is chosen
        self.assertEqual(len(context.bot.invoices), 0)

    def test_unknown_amount_sends_nothing(self):
        query = FakeQuery("donate:9999", user_id=7303)
        context = FakeContext(FakeBot())
        run(bot.donate_cb(FakeUpdate(query=query), context))
        self.assertEqual(len(context.bot.invoices), 0)

    def test_precheckout_approves_donate_payloads(self):
        query = mock.AsyncMock(invoice_payload="donate:75")
        update = mock.Mock(pre_checkout_query=query)
        run(bot.on_precheckout(update, mock.Mock()))
        query.answer.assert_awaited_once_with(ok=True)

    def test_precheckout_rejects_foreign_payloads(self):
        query = mock.AsyncMock(invoice_payload="hack:1")
        update = mock.Mock(pre_checkout_query=query)
        run(bot.on_precheckout(update, mock.Mock()))
        query.answer.assert_awaited_once_with(ok=False, error_message=mock.ANY)

    def test_successful_payment_is_recorded_and_thanked(self):
        message = FakeMessage()
        message.successful_payment = mock.Mock(total_amount=100)
        update = mock.Mock(message=message, effective_user=mock.Mock(id=7304))
        update.effective_user.id = 7304
        context = FakeContext(FakeBot())
        run(bot.on_successful_payment(update, context))
        self.assertEqual(store.get_or_create(7304)["donated_stars"], 100)
        expected = i18n.t("en", "donate_thanks", stars=100)
        self.assertIn(expected, message.sent)


# ---------------------------------------------------------------------------
# Support & owner
# ---------------------------------------------------------------------------

class TestSupportAndOwner(unittest.TestCase):
    def test_help_mentions_the_support_handle(self):
        message = FakeMessage()
        update = mock.Mock(
            effective_message=message, effective_user=mock.Mock(id=7401)
        )
        run(bot.cmd_help(update, FakeContext()))
        self.assertIn("@vxgix", message.sent[0])
        self.assertIn("/credits", message.sent[0])

    def test_admin_is_silent_for_strangers(self):
        message = FakeMessage()
        update = mock.Mock(
            effective_message=message,
            effective_user=mock.Mock(id=7402, username="random"),
        )
        run(bot.cmd_admin(update, FakeContext()))
        self.assertEqual(message.sent, [])

    def test_admin_dashboard_for_the_owner(self):
        message = FakeMessage()
        update = mock.Mock(
            effective_message=message,
            effective_user=mock.Mock(id=7403, username="vxgix"),
        )
        run(bot.cmd_admin(update, FakeContext()))
        self.assertEqual(len(message.sent), 1)
        self.assertIn("Users:", message.sent[0])

    def test_admin_add_grants_credits(self):
        store.get_or_create(7404)
        message = FakeMessage()
        update = mock.Mock(
            effective_message=message,
            effective_user=mock.Mock(id=7405, username="vxgix"),
        )
        context = FakeContext()
        context.args = ["add", "7404", "10"]
        run(bot.cmd_admin(update, context))
        self.assertEqual(store.snapshot(7404)["credits"], 5 + 10)


# ---------------------------------------------------------------------------
# Output rendering
# ---------------------------------------------------------------------------

class TestRenderWithCredits(unittest.TestCase):
    def test_output_ends_with_the_credits_line(self):
        from engine.builder import generate_prompt

        result = generate_prompt(
            {
                "brand_name": "Zina",
                "industry": "fashion",
                "industry_fashion": "clothing",
                "category": "combination",
            }
        )
        rendered = bot.render_prompt_html(result, "en", credits_left=4)
        self.assertIn("4", rendered)
        self.assertIn("Credits left", rendered)

    def test_render_without_credits_argument_is_unchanged(self):
        from engine.builder import generate_prompt

        result = generate_prompt(
            {
                "brand_name": "Zina",
                "industry": "fashion",
                "industry_fashion": "clothing",
                "category": "combination",
            }
        )
        rendered = bot.render_prompt_html(result, "en")
        self.assertNotIn("Credits left", rendered)


if __name__ == "__main__":
    unittest.main()
