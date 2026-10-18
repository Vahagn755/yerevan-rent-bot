import unittest

from rentbot.parser import (format_phone, normalize_phone, parse_district, parse_listing,
                            parse_pets, parse_price, parse_price_input, parse_price_range,
                            parse_rooms)

RATE = 390.0


class PriceTest(unittest.TestCase):
    def test_usd_forms(self):
        for text in ["Цена 450$", "գինը՝ $450", "450 usd", "450 դոլար", "450 долларов"]:
            p = parse_price(text, RATE)
            self.assertIsNotNone(p, text)
            self.assertEqual((p.amount, p.currency), (450, "USD"), text)

    def test_amd_forms(self):
        for text in ["200 000 драм", "200000 դրամ", "200,000 ֏", "200к драм", "200 հազ. դրամ"]:
            p = parse_price(text, RATE)
            self.assertIsNotNone(p, text)
            self.assertEqual((p.amount, p.currency), (200_000, "AMD"), text)
            self.assertAlmostEqual(p.usd, 512.82, places=2)

    def test_floor_number_not_glued_to_price(self):
        p = parse_price("Этаж 3, 450 $", RATE)
        self.assertEqual(p.amount, 450)

    def test_out_of_range_ignored(self):
        self.assertIsNone(parse_price("площадь 30$", RATE))

    def test_bare_input(self):
        self.assertEqual(parse_price_input("450", RATE).currency, "USD")
        self.assertEqual(parse_price_input("180000", RATE).currency, "AMD")
        self.assertIsNone(parse_price_input("abc", RATE))

    def test_ranges(self):
        self.assertEqual(parse_price_range("300-600", RATE), (300, 600))
        self.assertEqual(parse_price_range("600 - 300 $", RATE), (300, 600))
        self.assertEqual(parse_price_range("до 500", RATE), (None, 500))
        self.assertEqual(parse_price_range("մինչև 500", RATE), (None, 500))
        self.assertEqual(parse_price_range("от 400", RATE), (400, None))
        self.assertEqual(parse_price_range("150000-250000 դրամ", RATE), (385, 641))
        self.assertEqual(parse_price_range("0", RATE), (None, None))
        self.assertIsNone(parse_price_range("дешево", RATE))


class FieldsTest(unittest.TestCase):
    def test_rooms(self):
        cases = {"2 սենյականոց բնակարան": 2, "3-комн. квартира": 3, "2-х комнатная": 2,
                 "двушка в центре": 2, "1 bedroom flat": 1, "студия": 1, "եռասենյակ": 3}
        for text, n in cases.items():
            self.assertEqual(parse_rooms(text), n, text)
        self.assertIsNone(parse_rooms("квартира 450$"))

    def test_districts(self):
        cases = {"Արաբկիր, Կոմիտաս": "arabkir", "Сдаётся в Нор-Норке": "nor_nork",
                 "Норк Мараш": "nork_marash", "Kentron, near Cascade": "kentron",
                 "Шенгавит, рядом с центром": "shengavit", "Ավանում": "avan",
                 "Малатия": "malatia"}
        for text, key in cases.items():
            self.assertEqual(parse_district(text), key, text)

    def test_deposit_is_not_avan(self):
        self.assertIsNone(parse_district("ավանդ 1 ամիս"))
        self.assertIsNone(parse_district("аванс за 2 месяца"))

    def test_phone(self):
        for text in ["091 12 34 56", "+374 91 123456", "(091) 12-34-56", "37491123456", "091123456"]:
            self.assertEqual(normalize_phone(text), "37491123456", text)
        self.assertIsNone(normalize_phone("12345"))
        self.assertEqual(format_phone("37491123456"), "+374 91 123 456")

    def test_pets(self):
        self.assertEqual(parse_pets("можно с животными"), 1)
        self.assertEqual(parse_pets("без животных"), 0)
        self.assertEqual(parse_pets("կենդանիներ թույլատրվում են"), 1)
        self.assertIsNone(parse_pets("хорошая квартира"))


class ListingTest(unittest.TestCase):
    def test_full_post(self):
        text = ("🏠 Сдается 2-комн. квартира, Арабкир\nЕвроремонт, 5/9 этаж\n"
                "Цена: 550$\nМожно с животными\n📞 094 11 22 33")
        p = parse_listing(text, RATE)
        self.assertEqual((p.rooms, p.district, p.price.amount, p.pets, p.phone),
                         (2, "arabkir", 550, 1, "37494112233"))

    def test_armenian_post(self):
        p = parse_listing("Վարձով է տրվում 3 սենյականոց բնակարան Կենտրոնում, 300000 դրամ", RATE)
        self.assertEqual((p.rooms, p.district, p.price.currency), (3, "kentron", "AMD"))

    def test_demand_and_sale_skipped(self):
        self.assertIsNone(parse_listing("Сниму 2-комн. в Арабкире до 500$", RATE))
        self.assertIsNone(parse_listing("Վաճառվում է 2 սենյակ Արաբկիր 90000$", RATE))

    def test_not_enough_info(self):
        self.assertIsNone(parse_listing("Всем привет! 500$", RATE))


if __name__ == "__main__":
    unittest.main()
