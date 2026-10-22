import unittest

from brain_relay_chain import stage_for_turn


class CouncilStageTests(unittest.TestCase):
    def test_three_provider_chain_has_distinct_roles(self):
        self.assertEqual(stage_for_turn(0, 3, False, "create"), ("primary", "create"))
        self.assertEqual(stage_for_turn(1, 3, True, "create"), ("critic", "review"))
        self.assertEqual(stage_for_turn(2, 3, True, "create"), ("integrator", "continue"))

    def test_failed_early_workers_trigger_recovery_builder(self):
        self.assertEqual(stage_for_turn(1, 3, False, "create"), ("recovery", "create"))
        self.assertEqual(stage_for_turn(2, 3, False, "review"), ("recovery", "review"))

    def test_existing_packet_is_continued_then_reviewed(self):
        self.assertEqual(stage_for_turn(0, 3, True, "continue"), ("primary", "continue"))
        self.assertEqual(stage_for_turn(1, 3, True, "continue"), ("critic", "review"))

    def test_single_provider_keeps_requested_role(self):
        self.assertEqual(stage_for_turn(0, 1, False, "create"), ("primary", "create"))


if __name__ == "__main__":
    unittest.main()
