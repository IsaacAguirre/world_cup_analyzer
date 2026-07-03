import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from wc26_live_analyzer import run_match_combinatorics, run_team_matrix


class LiveAnalyzerPositionTests(unittest.TestCase):
    def test_match_combinatorics_include_position_metadata(self):
        groups = {
            "A": ["Mexico", "South Africa", "South Korea", "Czechia"],
            "B": ["Canada", "Bosnia and Herzegovina", "Qatar", "Switzerland"],
            "C": ["Brazil", "Morocco", "Haiti", "Scotland"],
            "D": ["United States", "Paraguay", "Australia", "Turkey"],
            "E": ["Germany", "Curaçao", "Ivory Coast", "Ecuador"],
            "F": ["Netherlands", "Japan", "Sweden", "Tunisia"],
            "G": ["Belgium", "Egypt", "Iran", "New Zealand"],
            "H": ["Spain", "Cape Verde", "Saudi Arabia", "Uruguay"],
            "I": ["France", "Senegal", "Iraq", "Norway"],
            "J": ["Argentina", "Algeria", "Austria", "Jordan"],
            "K": ["Portugal", "DR Congo", "Uzbekistan", "Colombia"],
            "L": ["England", "Croatia", "Ghana", "Panama"],
        }

        side_a, side_b, matchups = run_match_combinatorics(74, groups, set())

        self.assertTrue(side_a)
        self.assertTrue(side_b)
        self.assertTrue(matchups)
        self.assertIn("position", side_a[0])
        self.assertIn("position", side_b[0])
        self.assertIn("position", matchups[0])

    def test_team_matrix_can_limit_output_to_requested_position(self):
        groups = {
            "D": ["United States", "Paraguay", "Australia", "Turkey"],
        }

        result = run_team_matrix("United States", groups, set(), finish_position=2)

        self.assertEqual(result["requested_position"], 2)
        self.assertIn("pathway", result)
        self.assertNotIn("if_1st", result)
        self.assertNotIn("if_3rd", result)


if __name__ == "__main__":
    unittest.main()
