"""Unit tests for the Step 7 store: credits, referrals, donations, language.

The economy contract:
- a brand-new user starts with exactly START_CREDITS (5) credits
- +DAILY_REFILL (3) once per UTC day, never twice
- each generated prompt costs GENERATION_COST (1) credit
- a referral pays REFERRAL_BONUS (2) to the inviter, exactly once,
  self-invites and re-clicks pay nothing

Run from the project root:
    python -m unittest tests.test_store -v
"""

from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

os.environ.setdefault("TASMEEM_DB", ":memory:")

import config  # noqa: E402
import store  # noqa: E402


class TestStore(unittest.TestCase):
    def setUp(self):
        # a fresh file-based DB per test (exercises the real DDL path)
        self._tmp = tempfile.TemporaryDirectory()
        store.configure(os.path.join(self._tmp.name, "test.db"))

    def tearDown(self):
        store.close()
        self._tmp.cleanup()

    # -- starting credits ---------------------------------------------------

    def test_new_user_starts_with_five_credits(self):
        user = store.get_or_create(1001)
        self.assertEqual(user["credits"], 5)
        # reading twice must not grant twice
        self.assertEqual(store.get_or_create(1001)["credits"], 5)

    def test_start_credits_follow_the_config(self):
        self.assertEqual(
            store.get_or_create(1002)["credits"], config.START_CREDITS
        )

    # -- spending -----------------------------------------------------------

    def test_spend_deducts_one_credit(self):
        store.get_or_create(1003)
        self.assertTrue(store.spend(1003))
        self.assertEqual(
            store.snapshot(1003)["credits"],
            config.START_CREDITS - config.GENERATION_COST,
        )

    def test_spend_fails_when_balance_too_low(self):
        store.get_or_create(1004)
        while store.spend(1004):
            pass  # drain the balance
        self.assertFalse(store.spend(1004))
        self.assertEqual(store.snapshot(1004)["credits"], 0)

    # -- daily refill -------------------------------------------------------

    def test_new_user_gets_no_extra_refill_on_day_one(self):
        user = store.snapshot(1005)
        self.assertEqual(user["credits"], config.START_CREDITS)
        self.assertEqual(user["last_refill"], datetime.now(timezone.utc).strftime("%Y-%m-%d"))

    def test_daily_refill_adds_three_once_per_day(self):
        store.get_or_create(1006)
        before = store.snapshot(1006)["credits"]
        yesterday = (
            datetime.now(timezone.utc) - timedelta(days=1)
        ).strftime("%Y-%m-%d")
        with store._lock:
            conn = store._connection()
            conn.execute(
                "UPDATE users SET last_refill = ? WHERE user_id = ?",
                (yesterday, 1006),
            )
            conn.commit()
        after = store.snapshot(1006)["credits"]
        self.assertEqual(after, before + config.DAILY_REFILL)
        # a second call the same day must not refill again
        self.assertEqual(store.snapshot(1006)["credits"], after)

    # -- referrals ----------------------------------------------------------

    def test_referral_pays_the_referrer_once(self):
        referrer = store.get_or_create(2001)
        base = referrer["credits"]
        self.assertTrue(store.register_referral(2002, 2001))
        self.assertEqual(
            store.get_or_create(2001)["credits"], base + config.REFERRAL_BONUS
        )
        self.assertEqual(store.get_or_create(2002)["referrer_id"], 2001)
        # the invited user gets the normal starting credits, no more
        self.assertEqual(store.get_or_create(2002)["credits"], config.START_CREDITS)
        # clicking the same link again pays nothing
        self.assertFalse(store.register_referral(2002, 2001))
        self.assertEqual(
            store.get_or_create(2001)["credits"], base + config.REFERRAL_BONUS
        )

    def test_self_referral_is_refused(self):
        store.get_or_create(2003)
        self.assertFalse(store.register_referral(2003, 2003))
        self.assertEqual(store.get_or_create(2003)["credits"], config.START_CREDITS)

    def test_referral_of_an_existing_user_pays_nothing(self):
        store.get_or_create(2004)
        referrer = store.get_or_create(2005)
        base = referrer["credits"]
        self.assertFalse(store.register_referral(2004, 2005))
        self.assertEqual(store.get_or_create(2005)["credits"], base)

    def test_referrer_who_never_started_the_bot_still_gets_paid(self):
        # 3001 has never interacted with the store before
        self.assertTrue(store.register_referral(3002, 3001))
        self.assertEqual(
            store.get_or_create(3001)["credits"],
            config.START_CREDITS + config.REFERRAL_BONUS,
        )

    # -- donations ----------------------------------------------------------

    def test_record_donation_accumulates(self):
        store.record_donation(4001, 25)
        store.record_donation(4001, 50)
        self.assertEqual(store.get_or_create(4001)["donated_stars"], 75)

    # -- language persistence -----------------------------------------------

    def test_language_persists_in_the_store(self):
        store.set_lang(5001, "ar")
        self.assertEqual(store.get_lang(5001), "ar")
        self.assertIsNone(store.get_lang(5999))  # unknown user

    # -- owner statistics ---------------------------------------------------

    def test_stats_counts_users_referrals_and_stars(self):
        store.get_or_create(6001)
        store.register_referral(6002, 6001)
        store.record_donation(6001, 100)
        s = store.stats()
        self.assertGreaterEqual(s["users"], 2)
        self.assertGreaterEqual(s["referred_users"], 1)
        self.assertGreaterEqual(s["donated_stars"], 100)
        self.assertGreaterEqual(s["credits_outstanding"], 0)


if __name__ == "__main__":
    unittest.main()
