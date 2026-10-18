import json
import time
import unittest

from rentbot.webauth import sign_init_data, validate_init_data

TOKEN = "123456:TEST-token"


def make(user=None, auth_date=None, token=TOKEN):
    fields = {
        "query_id": "AAH",
        "user": json.dumps(user or {"id": 42, "first_name": "Վահագն", "language_code": "hy"},
                           ensure_ascii=False, separators=(",", ":")),
        "auth_date": str(int(auth_date if auth_date is not None else time.time())),
        "signature": "abc",
    }
    return sign_init_data(fields, token)


class WebAuthTest(unittest.TestCase):
    def test_valid(self):
        user = validate_init_data(make(), TOKEN)
        self.assertEqual(user["id"], 42)
        self.assertEqual(user["first_name"], "Վահագն")

    def test_wrong_token(self):
        self.assertIsNone(validate_init_data(make(token="999:other"), TOKEN))

    def test_tampered(self):
        data = make().replace("42", "43")
        self.assertIsNone(validate_init_data(data, TOKEN))

    def test_expired(self):
        self.assertIsNone(validate_init_data(make(auth_date=time.time() - 3 * 86400), TOKEN))

    def test_garbage(self):
        for bad in ["", "abc", "hash=", "user=1&hash=deadbeef"]:
            self.assertIsNone(validate_init_data(bad, TOKEN), bad)


if __name__ == "__main__":
    unittest.main()
