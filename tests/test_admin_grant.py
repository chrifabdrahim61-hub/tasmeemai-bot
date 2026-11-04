"""Admin credit-grant tests (Step 8 hotfix): the owner can top himself up.

The bug: /admin only accepted the exact form "/admin add <user_id> <amount>",
so the owner typing "/admin <8974969463><45>" got nothing - no error, no
credits. The parser now tolerates every natural way of typing it:

- "/admin add 8974969463 45"      (classic)
- "/admin 8974969463 45"          (no keyword)
- "/admin <8974969463><45>"       (brackets, the exact reported input)
- "/admin 8974969463, 45"         (comma)
- "/admin 45 8974969463"          (amount and id swapped)
- "/admin 45" / "/admin add 45"   (no id -> the sender himself)
- "/addcredits ..."               (same grammar, dedicated command)
- "/admin 8974969463 -10"         (negative amount removes credits)

plus the one-tap "＋N ⚡ me" dashboard buttons.

Run from the project root:
    python -m unittest tests.test_admin_grant -v
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


OWNER_ID = 8974969463
OTHER_ID = 111222333


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

    async def edit_message_text(self, text, reply_markup=None, **kwargs):
        self.sent.append(text)
        return FakeMessage()


class FakeQuery:
    def __init__(self, data: str, user_id: int):
        self.data = data
        self.from_user = mock.Mock(id=user_id, username=None)
        self.message = FakeMessage()
        self.answered_with = None
        self.edited_text = None

    async def answer(self, text=None, show_alert=False):
        self.answered_with = (text, show_alert)

    async def edit_message_text(self, text, reply_markup=None, **kwargs):
        self.edited_text = text


class FakeUpdate:
    def __init__(self, query: FakeQuery = None, user_id: int = OWNER_ID):
        self.callback_query = query
        self._message = FakeMessage()
        self.effective_user = mock.Mock(id=user_id, username=None)

    @property
    def effective_message(self):
        return self._message if self.callback_query is None else self.callback_query.message


class FakeContext:
    def __init__(self, args=()):
        self.user_data = {}
        self.bot_data = {}
        self.args = list(args)


def run(coro):
    return asyncio.run(coro)


class TestParseGrantArgs(unittest.TestCase):
    """The parser alone - every syntax the owner may type."""

    def test_exact_reported_input_with_brackets(self):
        # what the owner actually typed in the bug report
        self.assertEqual(
            bot._parse_grant_args(["<8974969463><45>"]), (8974969463, 45)
        )

    def test_classic_add_form(self):
        self.assertEqual(
            bot._parse_grant_args(["add", "8974969463", "45"]), (8974969463, 45)
        )

    def test_no_add_keyword(self):
        self.assertEqual(
            bot._parse_grant_args(["8974969463", "45"]), (8974969463, 45)
        )

    def test_comma_and_mixed_brackets(self):
        self.assertEqual(
            bot._parse_grant_args(["<8974969463>,", "45"]), (8974969463, 45)
        )
        self.assertEqual(
            bot._parse_grant_args(["add", "[8974969463]", "(45)"]), (8974969463, 45)
        )

    def test_amount_first_is_swapped(self):
        self.assertEqual(
            bot._parse_grant_args(["45", "8974969463"]), (8974969463, 45)
        )

    def test_single_number_means_myself(self):
        self.assertEqual(bot._parse_grant_args(["45"]), (None, 45))
        self.assertEqual(bot._parse_grant_args(["add", "45"]), (None, 45))

    def test_negative_amount_removes(self):
        self.assertEqual(
            bot._parse_grant_args(["add", "8974969463", "-10"]), (8974969463, -10)
        )
        self.assertEqual(bot._parse_grant_args(["-10"]), (None, -10))
        # amount written first, id second
        self.assertEqual(
            bot._parse_grant_args(["-10", "8974969463"]), (8974969463, -10)
        )

    def test_garbage_returns_none(self):
        self.assertIsNone(bot._parse_grant_args([]))
        self.assertIsNone(bot._parse_grant_args(["add", "hello"]))
        self.assertIsNone(bot._parse_grant_args(["???"]))


class TestAdminGrantFlow(unittest.TestCase):
    """The handlers: /admin, /addcredits and the quick buttons."""

    def setUp(self):
        store.close()
        store.configure()

    def tearDown(self):
        store.close()

    def test_cmd_admin_self_grant(self):
        before = store.get_or_create(OWNER_ID)["credits"]
        update = FakeUpdate(user_id=OWNER_ID)
        run(bot.cmd_admin(update, FakeContext(args=["45"])))
        after = store.get_or_create(OWNER_ID)["credits"]
        self.assertEqual(after, before + 45)
        self.assertIn("granted 45 credits", update.effective_message.sent[-1])
        self.assertIn(str(OWNER_ID), update.effective_message.sent[-1])

    def test_cmd_admin_bracket_syntax_grants_other_user(self):
        target = 555123456
        before = store.get_or_create(target)["credits"]
        update = FakeUpdate(user_id=OWNER_ID)
        run(bot.cmd_admin(update, FakeContext(args=[f"<{target}><45>"])))
        after = store.get_or_create(target)["credits"]
        self.assertEqual(after, before + 45)

    def test_cmd_admin_without_args_shows_usage(self):
        update = FakeUpdate(user_id=OWNER_ID)
        run(bot.cmd_admin(update, FakeContext(args=[])))
        text = update.effective_message.sent[-1]
        self.assertIn("owner dashboard", text)
        self.assertIn("/admin add 8974969463 45", text)  # usage explained
        # ...and the one-tap buttons are there
        markup = update.effective_message.replies[-1]
        callbacks = [b.callback_data for row in markup.inline_keyboard for b in row]
        self.assertEqual(callbacks, ["admcred:10", "admcred:50", "admcred:100"])

    def test_addcredits_command_grants_to_self(self):
        before = store.get_or_create(OWNER_ID)["credits"]
        update = FakeUpdate(user_id=OWNER_ID)
        run(bot.cmd_addcredits(update, FakeContext(args=["25"])))
        after = store.get_or_create(OWNER_ID)["credits"]
        self.assertEqual(after, before + 25)
        self.assertIn("Balance now", update.effective_message.sent[-1])

    def test_addcredits_without_args_shows_usage(self):
        update = FakeUpdate(user_id=OWNER_ID)
        run(bot.cmd_addcredits(update, FakeContext(args=[])))
        self.assertIn("ANY of these works", update.effective_message.sent[-1])

    def test_non_owner_is_silently_ignored(self):
        update = FakeUpdate(user_id=OTHER_ID)
        run(bot.cmd_admin(update, FakeContext(args=["45"])))
        self.assertEqual(update.effective_message.sent, [])
        run(bot.cmd_addcredits(update, FakeContext(args=["45"])))
        self.assertEqual(update.effective_message.sent, [])

    def test_quick_button_tops_up_the_owner(self):
        before = store.get_or_create(OWNER_ID)["credits"]
        query = FakeQuery("admcred:50", user_id=OWNER_ID)
        run(bot.admin_credit_cb(FakeUpdate(query=query), FakeContext()))
        after = store.get_or_create(OWNER_ID)["credits"]
        self.assertEqual(after, before + 50)
        self.assertIn("+50 credits", query.answered_with[0])
        self.assertIn("owner dashboard", query.edited_text or "")

    def test_quick_button_ignored_for_non_owner(self):
        query = FakeQuery("admcred:50", user_id=OTHER_ID)
        run(bot.admin_credit_cb(FakeUpdate(query=query), FakeContext()))
        # the tap created the row (starting balance) but granted nothing
        self.assertEqual(
            store.get_or_create(OTHER_ID)["credits"], config.START_CREDITS
        )
        self.assertIsNone(query.answered_with[0])  # answered silently

    def test_owner_match_by_numeric_id(self):
        self.assertTrue(bot._is_owner(mock.Mock(id=8974969463, username=None)))
        self.assertFalse(bot._is_owner(mock.Mock(id=1, username="someone_else")))


class TestStoreGrants(unittest.TestCase):
    """The store layer underneath (sanity: grants survive, apply cleanly)."""

    def setUp(self):
        store.close()
        store.configure()

    def tearDown(self):
        store.close()

    def test_add_credits_creates_and_accumulates(self):
        # a fresh row starts with START_CREDITS, then the grant is added
        user = store.add_credits(OTHER_ID, 45)
        self.assertEqual(user["credits"], config.START_CREDITS + 45)
        user = store.add_credits(OTHER_ID, 5)
        self.assertEqual(user["credits"], config.START_CREDITS + 50)

    def test_remove_credits_can_go_negative_safely(self):
        store.add_credits(OTHER_ID, 1)
        user = store.add_credits(OTHER_ID, -100)
        self.assertEqual(user["credits"], config.START_CREDITS + 1 - 100)


if __name__ == "__main__":
    unittest.main()
