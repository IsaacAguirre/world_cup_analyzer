import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from wc26_matchup_simulator import get_all_matchups


class MatchupSimulatorPositionTests(unittest.TestCase):
    def test_matchup_simulator_includes_position_metadata(self):
        side_a, side_b, matchups = get_all_matchups(74)

        self.assertTrue(side_a)
        self.assertTrue(side_b)
        self.assertTrue(matchups)
        self.assertIn("position", side_a[0])
        self.assertIn("position", side_b[0])
        self.assertIn("position", matchups[0])


if __name__ == "__main__":
    unittest.main()
