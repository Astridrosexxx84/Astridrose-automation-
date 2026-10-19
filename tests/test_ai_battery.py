import tempfile
import unittest
from pathlib import Path

from ai_battery import classify_error, empty_ledger, load_ledger, record_event, render_markdown, route_candidates, save_ledger


class BatteryTests(unittest.TestCase):
    def test_classifies_quota_and_auth_errors(self):
        self.assertEqual(classify_error("API returned HTTP 429: quota exceeded"), ("LOW_OR_COOLDOWN", "429"))
        self.assertEqual(classify_error("API returned HTTP 401: invalid api key"), ("DISCONNECTED", "401"))

    def test_success_does_not_claim_quota_percentage(self):
        ledger = empty_ledger()
        record_event(ledger, "gemini", "success", model="test-model", free_route="verified_zero_price", now="2026-10-20T00:00:00+00:00")
        item = ledger["providers"]["gemini"]
        self.assertEqual(item["status"], "AVAILABLE")
        self.assertEqual(item["quota_remaining"], "not exposed")

    def test_router_excludes_known_blocked_and_unverified_paid_routes(self):
        ledger = empty_ledger()
        record_event(ledger, "gemini", "quota", free_route="verified_zero_price")
        record_event(ledger, "groq", "success", free_route="verified_zero_price")
        record_event(ledger, "openrouter", "success", free_route="unknown")
        self.assertEqual(route_candidates(["gemini", "groq", "openrouter"], ledger), ["groq"])

    def test_ledger_round_trip_and_no_raw_error_body(self):
        ledger = empty_ledger()
        record_event(ledger, "groq", "quota", error="API returned HTTP 429: secret-provider-detail", free_route="unknown")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.json"
            save_ledger(ledger, path)
            loaded = load_ledger(path)
        self.assertEqual(loaded["providers"]["groq"]["http_or_error_category"], "HTTP 429")
        self.assertNotIn("secret-provider-detail", str(loaded))

    def test_unknown_provider_rejected(self):
        with self.assertRaises(ValueError):
            record_event(empty_ledger(), "imaginary", "success")


if __name__ == "__main__":
    unittest.main()
