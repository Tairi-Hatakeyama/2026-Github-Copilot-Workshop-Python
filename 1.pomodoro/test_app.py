import unittest

from app import create_app


class BasicFlaskAppTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.client = create_app().test_client()

    def test_index_returns_200(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_index_body(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.data.decode("utf-8"), "Pomodoro Timer App")


if __name__ == "__main__":
    unittest.main()
