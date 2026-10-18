import asyncio
import os
import tempfile
import unittest

from rentbot.db import Database
from rentbot.matching import matches
from rentbot.render import format_card, format_filter

ANY = {"price_min": None, "price_max": None, "rooms": "", "districts": "", "pets": 0}
LISTING = {"price_usd": 450, "rooms": 2, "district": "arabkir", "pets": 1}


class MatchingTest(unittest.TestCase):
    def test_empty_filter_matches_all(self):
        self.assertTrue(matches(ANY, LISTING))

    def test_price(self):
        self.assertTrue(matches({**ANY, "price_min": 400, "price_max": 500}, LISTING))
        self.assertFalse(matches({**ANY, "price_max": 400}, LISTING))
        self.assertFalse(matches({**ANY, "price_min": 500}, LISTING))
        self.assertFalse(matches({**ANY, "price_max": 500}, {**LISTING, "price_usd": None}))

    def test_rooms_and_districts(self):
        self.assertTrue(matches({**ANY, "rooms": "1,2"}, LISTING))
        self.assertFalse(matches({**ANY, "rooms": "3"}, LISTING))
        self.assertTrue(matches({**ANY, "rooms": "5"}, {**LISTING, "rooms": 7}))
        self.assertTrue(matches({**ANY, "districts": "arabkir,kentron"}, LISTING))
        self.assertFalse(matches({**ANY, "districts": "kentron"}, LISTING))
        self.assertFalse(matches({**ANY, "districts": "kentron"}, {**LISTING, "district": None}))

    def test_pets(self):
        self.assertTrue(matches({**ANY, "pets": 1}, LISTING))
        self.assertFalse(matches({**ANY, "pets": 1}, {**LISTING, "pets": None}))


class DatabaseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Database(os.path.join(self.tmp.name, "sub", "t.db"))
        asyncio.run(self.db.connect())

    def tearDown(self):
        asyncio.run(self.db.close())
        self.tmp.cleanup()

    def test_flow(self):
        async def run():
            db = self.db
            self.assertEqual(await db.ensure_user(1, "ru"), ("ru", True))
            self.assertEqual(await db.ensure_user(1, "en"), ("ru", False))
            await db.ensure_user(2, None)
            await db.ensure_user(3, "en")
            await db.update_filter(1, price_max=500, districts="arabkir")
            await db.get_filter(2)
            await db.set_paused(2, True)
            subs = await db.subscribers()
            self.assertEqual([s["user_id"] for s in subs], [1])

            lid = await db.add_listing(source="bot", owner_id=3, district="arabkir", rooms=2,
                                       price_amount=450, currency="USD", price_usd=450, pets=1,
                                       description="<b>nice</b>", phone="37491123456", text_hash="h1")
            listing = await db.get_listing(lid)
            self.assertTrue(matches(subs[0], listing))
            self.assertTrue(await db.is_duplicate("h1", 0))
            self.assertEqual(await db.count_user_listings_since(3, 0), 1)

            card = format_card(listing, "hy")
            self.assertIn("Արաբկիր", card)
            self.assertIn("&lt;b&gt;nice", card)  # user text is escaped
            self.assertIn("+374 91 123 456", card)

            # reports: duplicates ignored, counted per phone across listings
            self.assertTrue(await db.add_report(lid, 1, "agent"))
            self.assertFalse(await db.add_report(lid, 1, "fake"))
            lid2 = await db.add_listing(source="channel", phone="37491123456", price_usd=400)
            await db.add_report(lid2, 2, "fake")
            self.assertEqual(await db.report_count(listing), 2)

            await db.blacklist_phone("37491123456", "test")
            self.assertTrue(await db.is_blacklisted("37491123456"))
            self.assertEqual((await db.get_listing(lid))["status"], "blocked")
            await db.unblacklist_phone("37491123456")
            self.assertFalse(await db.is_blacklisted("37491123456"))

            stats = await db.stats()
            self.assertEqual(stats["users"], 3)
            self.assertEqual(stats["subscribers"], 1)
            self.assertIn("Արաբկիր", format_filter(await db.get_filter(1), "hy"))

        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
