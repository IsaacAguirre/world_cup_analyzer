import json
import os
import argparse
import itertools

# 2026 Official Groups
GROUPS = {
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
    "L": ["England", "Croatia", "Ghana", "Panama"]
}

# Structural feeding mechanism for all knockout slots
# Format: (Group, Placement Position)
MATCH_FEEDERS = {
    73: {"side_a": [("A", 2)], "side_b": [("B", 2)]},
    74: {"side_a": [("E", 1)], "side_b": [("A", 3), ("B", 3), ("C", 3), ("D", 3), ("F", 3)]},
    75: {"side_a": [("F", 1)], "side_b": [("C", 2)]},
    76: {"side_a": [("C", 1)], "side_b": [("F", 2)]},
    77: {"side_a": [("I", 1)], "side_b": [("C", 3), ("D", 3), ("F", 3), ("G", 3), ("H", 3)]},
    78: {"side_a": [("E", 2)], "side_b": [("I", 2)]},
    79: {"side_a": [("A", 1)], "side_b": [("C", 3), ("E", 3), ("F", 3), ("H", 3), ("I", 3)]},
    80: {"side_a": [("L", 1)], "side_b": [("E", 3), ("H", 3), ("I", 3), ("J", 3), ("K", 3)]},
    81: {"side_a": [("D", 1)], "side_b": [("B", 3), ("E", 3), ("F", 3), ("I", 3), ("J", 3)]},
    82: {"side_a": [("G", 1)], "side_b": [("A", 3), ("E", 3), ("H", 3), ("I", 3), ("J", 3)]},
    83: {"side_a": [("K", 2)], "side_b": [("L", 2)]},
    84: {"side_a": [("H", 1)], "side_b": [("J", 2)]},
    85: {"side_a": [("B", 1)], "side_b": [("E", 3), ("F", 3), ("G", 3), ("I", 3), ("J", 3)]},
    86: {"side_a": [("J", 1)], "side_b": [("H", 2)]},
    87: {"side_a": [("K", 1)], "side_b": [("D", 3), ("E", 3), ("I", 3), ("J", 3), ("L", 3)]},
    88: {"side_a": [("D", 2)], "side_b": [("G", 2)]},
    
    # Advanced Knockouts point to parent match IDs
    89: {"side_a": 74, "side_b": 77},
    90: {"side_a": 73, "side_b": 75},
    91: {"side_a": 76, "side_b": 78},
    92: {"side_a": 79, "side_b": 80},
    93: {"side_a": 83, "side_b": 84},
    94: {"side_a": 81, "side_b": 82},
    95: {"side_a": 86, "side_b": 88},
    96: {"side_a": 85, "side_b": 87},
    
    97: {"side_a": 89, "side_b": 90},
    98: {"side_a": 93, "side_b": 94},
    99: {"side_a": 91, "side_b": 92},
    100: {"side_a": 95, "side_b": 96},
    
    101: {"side_a": 97, "side_b": 98},
    102: {"side_a": 99, "side_b": 100},
    104: {"side_a": 101, "side_b": 102}
}

def resolve_side_teams(match_target):
    """Recursively crawls backward to find all unique physical countries eligible for a bracket side."""
    if isinstance(match_target, list):
        teams = set()
        for group, pos in match_target:
            for country in GROUPS[group]:
                teams.add(f"{country} ({group}{pos})")
        return teams
    
    # If target points to a preceding match, combine both its branches
    parent_match = MATCH_FEEDERS[match_target]
    left = resolve_side_teams(parent_match["side_a"])
    right = resolve_side_teams(parent_match["side_b"])
    return left.union(right)

def get_all_matchups(match_id):
    if match_id not in MATCH_FEEDERS:
        return None
    
    feeder = MATCH_FEEDERS[match_id]
    side_a_teams = sorted(list(resolve_side_teams(feeder["side_a"])))
    side_b_teams = sorted(list(resolve_side_teams(feeder["side_b"])))
    
    raw_combinations = list(itertools.product(side_a_teams, side_b_teams))
    
    # Filter out impossible paradox matches (e.g. same physical country playing itself)
    clean_matchups = []
    for ta, tb in raw_combinations:
        country_a = ta.split(" (")[0]
        country_b = tb.split(" (")[0]
        if country_a != country_b:
            clean_matchups.append({"team_a": ta, "team_b": tb, "display": f"{country_a} vs {country_b}"})
            
    return side_a_teams, side_b_teams, clean_matchups

def main():
    parser = argparse.ArgumentParser(description="FIFA World Cup 2026 Pure Matchup Combinatorics Engine")
    parser.add_argument("--match", type=int, required=True, help="Knockout Match ID (73 to 104)")
    parser.add_argument("--expand", action="store_true", help="Print the comprehensive list of every single team pairing")
    args = parser.parse_args()

    result = get_all_matchups(args.match)
    if not result:
        print(f"Error: Match {args.match} is out of knockout bounds.")
        return

    side_a, side_b, matchups = result
    
    print("=========================================================================")
    print(f"💥 COMBINATORIAL ANALYSIS FOR MATCH {args.match} 💥")
    print("=========================================================================")
    print(f"• Total Candidate Countries on Side A: {len(side_a)}")
    print(f"• Total Candidate Countries on Side B: {len(side_b)}")
    print(f"• Total Mathematical Matchup Permutations: {len(matchups)}")
    print("=========================================================================\n")
    
    print("👉 SIDE A POOL (Group & Placement Trackers):")
    print(", ".join(side_a))
    print("\n👉 SIDE B POOL (Group & Placement Trackers):")
    print(", ".join(side_b))
    print("\n=========================================================================")
    
    if args.expand:
        print(f"\n📋 ALL {len(matchups)} POSSIBLE MATCH-UPS:")
        print("-------------------------------------------------------------------------")
        for idx, m in enumerate(matchups, start=1):
            print(f"{idx:03d}. {m['display']}  [{m['team_a']} vs {m['team_b']}]")
    else:
        print("\n💡 Run again with the '--expand' flag to output the complete list of specific matchups.")

if __name__ == "__main__":
    main()