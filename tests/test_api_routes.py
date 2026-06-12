import unittest

from fastapi.testclient import TestClient

from backend.app.main import create_app


class ApiRoutesTest(unittest.TestCase):
    def test_matches_endpoint_returns_current_seed_schedule_without_tbd(self) -> None:
        client = TestClient(create_app())

        response = client.get("/matches")

        self.assertEqual(response.status_code, 200)
        matches = response.json()
        self.assertGreater(len(matches), 0)
        self.assertFalse(any("TBD" in {match.get("team_a"), match.get("team_b")} for match in matches))


if __name__ == "__main__":
    unittest.main()
