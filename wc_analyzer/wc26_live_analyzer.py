import json
import os
import argparse
import itertools
import sys

# Case-insensitive alias dictionary to handle input variances seamlessly
ALIASES = {
    "usa": "United States", "us": "United States", "united states": "United States",
    "uk": "England", "england": "England",
    "south korea": "South Korea", "korea republic": "South Korea", "korea": "South Korea",
    "czech republic": "Czechia", "czechia": "Czechia",
    "turkey": "Turkey", "türkiye": "Turkey",
    "cote d'ivoire": "Ivory Coast", "ivory coast": "Ivory Coast",
    "cape verde": "Cape Verde", "cabo verde": "Cape Verde",
    "dr congo": "DR Congo", "congo dr": "DR Congo"
}

MATCH_DETAILS = {
    73: {"label": "Runner-up Group A vs. Runner-up Group B", "city": "Los Angeles (SoFi Stadium)"},
    74: {"label": "Winner Group E vs. 3rd Group A/B/C/D/F", "city": "Boston (Gillette Stadium)"},
    75: {"label": "Winner Group F vs. Runner-up Group C", "city": "Monterrey (Estadio BBVA)"},
    76: {"label": "Winner Group C vs. Runner-up Group F", "city": "Houston (NRG Stadium)"},
    77: {"label": "Winner Group I vs. 3rd Group C/D/F/G/H", "city": "New York/New Jersey (MetLife Stadium)"},
    78: {"label": "Runner-up Group E vs. Runner-up Group I", "city": "Dallas (AT&T Stadium)"},
    79: {"label": "Winner Group A vs. 3rd Group C/E/F/H/I", "city": "Mexico City (Estadio Azteca)"},
    80: {"label": "Winner Group L vs. 3rd Group E/H/I/J/K", "city": "Atlanta (Mercedes-Benz Stadium)"},
    81: {"label": "Winner Group D vs. 3rd Group B/E/F/I/J", "city": "San Francisco Bay Area (Levi's Stadium)"},
    82: {"label": "Winner Group G vs. 3rd Group A/E/H/I/J", "city": "Seattle (Lumen Field)"},
    83: {"label": "Runner-up Group K vs. Runner-up Group L", "city": "Toronto (BMO Field)"},
    84: {"label": "Winner Group H vs. Runner-up Group J", "city": "Los Angeles (SoFi Stadium)"},
    85: {"label": "Winner Group B vs. 3rd Group E/F/G/I/J", "city": "Vancouver (BC Place)"},
    86: {"label": "Winner Group J vs. Runner-up Group H", "city": "Miami (Hard Rock Stadium)"},
    87: {"label": "Winner Group K vs. 3rd Group D/E/I/J/L", "city": "Kansas City (Arrowhead Stadium)"},
    88: {"label": "Runner-up Group D vs. Runner-up Group G", "city": "Dallas (AT&T Stadium)"},
    
    89: {"label": "Winner Match 74 vs. Winner Match 77", "city": "Philadelphia (Lincoln Financial Field)"},
    90: {"label": "Winner Match 73 vs. Winner Match 75", "city": "Houston (NRG Stadium)"},
    91: {"label": "Winner Match 76 vs. Winner Match 78", "city": "New York/New Jersey (MetLife Stadium)"},
    92: {"label": "Winner Match 79 vs. Winner Match 80", "city": "Mexico City (Estadio Azteca)"},
    93: {"label": "Winner Match 83 vs. Winner Match 84", "city": "Dallas (AT&T Stadium)"},
    94: {"label": "Winner Match 81 vs. Winner Match 82", "city": "Seattle (Lumen Field)"},
    95: {"label": "Winner Match 86 vs. Winner Match 88", "city": "Atlanta (Mercedes-Benz Stadium)"},
    96: {"label": "Winner Match 85 vs. Winner Match 87", "city": "Vancouver (BC Place)"},
    
    97: {"label": "Winner Match 89 vs. Winner Match 90", "city": "Boston (Gillette Stadium)"},
    98: {"label": "Winner Match 93 vs. Winner Match 94", "city": "Los Angeles (SoFi Stadium)"},
    99: {"label": "Winner Match 91 vs. Winner Match 92", "city": "Miami (Hard Rock Stadium)"},
    100: {"label": "Winner Match 95 vs. Winner Match 96", "city": "Kansas City (Arrowhead Stadium)"},
    
    101: {"label": "Winner Match 97 vs. Winner Match 98", "city": "Dallas (AT&T Stadium)"},
    102: {"label": "Winner Match 99 vs. Winner Match 100", "city": "Atlanta (Mercedes-Benz Stadium)"},
    103: {"label": "Loser Match 101 vs. Loser Match 102 (Third-Place Match)", "city": "Miami (Hard Rock Stadium)"},
    104: {"label": "Winner Match 101 vs. Winner Match 102 (Final)", "city": "New York/New Jersey (MetLife Stadium)"}
}

NEXT_MATCH = {
    73: 90, 75: 90, 74: 89, 77: 89, 76: 91, 78: 91, 79: 92, 80: 92,
    81: 94, 82: 94, 83: 93, 84: 93, 85: 96, 87: 96, 86: 95, 88: 95,
    89: 97, 90: 97, 91: 99, 92: 99, 93: 98, 94: 98, 95: 100, 96: 100,
    97: 101, 98: 101, 99: 102, 100: 102, 101: 104, 102: 104
}

GROUP_INITIAL_MATCHES = {
    "A": {1: 79, 2: 73, 3: [74, 82]}, "B": {1: 85, 2: 73, 3: [74, 81]},
    "C": {1: 76, 2: 75, 3: [74, 77, 79]}, "D": {1: 81, 2: 88, 3: [74, 77, 87]},
    "E": {1: 74, 2: 78, 3: [79, 80, 81, 82, 85, 87]}, "F": {1: 75, 2: 76, 3: [74, 77, 79, 81, 85]},
    "G": {1: 82, 2: 88, 3: [77, 85]}, "H": {1: 84, 2: 86, 3: [77, 79, 80, 82]},
    "I": {1: 77, 2: 78, 3: [79, 80, 81, 82, 85, 87]}, "J": {1: 86, 2: 84, 3: [80, 81, 82, 85, 87]},
    "K": {1: 87, 2: 83, 3: [80]}, "L": {1: 80, 2: 83, 3: [87]}
}

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
    
    89: {"side_a": 74, "side_b": 77}, 90: {"side_a": 73, "side_b": 75},
    91: {"side_a": 76, "side_b": 78}, 92: {"side_a": 79, "side_b": 80},
    93: {"side_a": 83, "side_b": 84}, 94: {"side_a": 81, "side_b": 82},
    95: {"side_a": 86, "side_b": 88}, 96: {"side_a": 85, "side_b": 87},
    
    97: {"side_a": 89, "side_b": 90}, 98: {"side_a": 93, "side_b": 94},
    99: {"side_a": 91, "side_b": 92}, 100: {"side_a": 95, "side_b": 96},
    
    101: {"side_a": 97, "side_b": 98}, 102: {"side_a": 99, "side_b": 100},
    104: {"side_a": 101, "side_b": 102}
}

def load_json_data():
    # Load Groups Draw
    groups = {}
    if os.path.exists("groups.json"):
        with open("groups.json", "r", encoding="utf-8") as f:
            groups = json.load(f)
    else:
        print("Error: groups.json is missing! Please create it to run simulations.")
        sys.exit(1)
        
    # Load Eliminated Teams Tracker
    eliminated = set()
    if os.path.exists("eliminated.json"):
        with open("eliminated.json", "r", encoding="utf-8") as f:
            try:
                raw_list = json.load(f)
                for team in raw_list:
                    cleaned = team.lower().strip()
                    # Resolve aliases to match internal official names
                    official_name = ALIASES.get(cleaned, cleaned)
                    eliminated.add(official_name.lower())
            except Exception as e:
                print(f"Warning: Failed to parse eliminated.json ({e}). Proceeding with no eliminations.")
                
    return groups, eliminated

def resolve_normalized_name(input_name):
    cleaned = input_name.lower().strip()
    return ALIASES.get(cleaned, cleaned).lower()

def trace_individual_path(match_id):
    path = {}
    rounds = ["Round of 32", "Round of 16", "Quarter-finals", "Semi-finals"]
    curr = match_id
    
    for r_name in rounds:
        path[r_name] = {"match": f"Match {curr}", "label": MATCH_DETAILS[curr]["label"], "city": MATCH_DETAILS[curr]["city"]}
        curr = NEXT_MATCH.get(curr)
        
    path["If Win Semi-final (Final)"] = {"match": "Match 104", "label": MATCH_DETAILS[104]["label"], "city": MATCH_DETAILS[104]["city"]}
    path["If Lose Semi-final (3rd Place)"] = {"match": "Match 103", "label": MATCH_DETAILS[103]["label"], "city": MATCH_DETAILS[103]["city"]}
    return path

def run_team_matrix(team_query, groups, eliminated):
    target_norm = resolve_normalized_name(team_query)
    found_group, official_name = None, None
    
    for g_letter, teams in groups.items():
        for t in teams:
            if t.lower() == target_norm:
                found_group, official_name = g_letter, t
                break
                
    if not found_group:
        return {"error": f"Team '{team_query}' was not identified in the groups system."}
        
    if official_name.lower() in eliminated:
        return {
            "country_entered": official_name,
            "status": "ELIMINATED",
            "message": "This team has been knocked out of the tournament."
        }
        
    slots = GROUP_INITIAL_MATCHES[found_group]
    matrix = {
        "country_entered": official_name,
        "group": found_group,
        "status": "ACTIVE",
        "if_1st": trace_individual_path(slots[1]),
        "if_2nd": trace_individual_path(slots[2]),
        "if_3rd": [],
        "if_4th": "Eliminated in the Group Stage"
    }
    
    for match_id in slots[3]:
        matrix["if_3rd"].append({f"potential_allocation_match_{match_id}": trace_individual_path(match_id)})
    return matrix

def resolve_side_teams(match_target, groups, eliminated):
    """Recursively resolves bracket paths to build pools of remaining valid live countries."""
    if isinstance(match_target, list):
        teams = set()
        for group, pos in match_target:
            for country in groups[group]:
                if country.lower() in eliminated:
                    continue
                teams.add(f"{country} ({group}{pos})")
        return teams
    
    parent_match = MATCH_FEEDERS[match_target]
    left = resolve_side_teams(parent_match["side_a"], groups, eliminated)
    right = resolve_side_teams(parent_match["side_b"], groups, eliminated)
    return left.union(right)

def run_match_combinatorics(match_id, groups, eliminated):
    if match_id not in MATCH_FEEDERS:
        return None
        
    feeder = MATCH_FEEDERS[match_id]
    side_a_teams = sorted(list(resolve_side_teams(feeder["side_a"], groups, eliminated)))
    side_b_teams = sorted(list(resolve_side_teams(feeder["side_b"], groups, eliminated)))
    
    raw_combinations = list(itertools.product(side_a_teams, side_b_teams))
    clean_matchups = []
    
    for ta, tb in raw_combinations:
        country_a = ta.split(" (")[0]
        country_b = tb.split(" (")[0]
        if country_a != country_b:
            clean_matchups.append({"display": f"{country_a} vs {country_b}", "meta": f"[{ta} vs {tb}]"})
            
    return side_a_teams, side_b_teams, clean_matchups

def main():
    parser = argparse.ArgumentParser(description="Live-Updating FIFA World Cup 2026 Analytical Simulation Graph Engine")
    parser.add_argument("--team", type=str, help="Analyze the prospective pathway vectors of a specific country")
    parser.add_argument("--match", type=int, help="Extract combinations and available pools feeding a precise Knockout Match ID")
    parser.add_argument("--expand", action="store_true", help="Print the full scannable array of explicit matchups")
    args = parser.parse_args()

    groups, eliminated = load_json_data()

    if args.team:
        output = run_team_matrix(args.team, groups, eliminated)
        print(json.dumps(output, indent=2))

    elif args.match:
        res = run_match_combinatorics(args.match, groups, eliminated)
        if not res:
            print(f"Error: Match {args.match} falls outside active knockout mapping criteria.")
            return
            
        side_a, side_b, matchups = res
        print("=========================================================================")
        print(f"💥 LIVE TOURNAMENT MATRIX PERMUTATIONS FOR MATCH {args.match} 💥")
        print(f"📍 Venue Location: {MATCH_DETAILS[args.match]['city']}")
        print(f"📉 Total Active Eliminated Teams Loaded: {len(eliminated)}")
        print("=========================================================================")
        print(f"• Remaining Pool Size on Side A: {len(side_a)}")
        print(f"• Remaining Pool Size on Side B: {len(side_b)}")
        print(f"• Current Active Combinatorial Matchups Left: {len(matchups)}")
        print("=========================================================================\n")
        
        print("👉 LIVE SIDE A CANDIDATES:")
        print(", ".join(side_a) if side_a else "[⚠️ Pool Completely Empty Due To Eliminations]")
        print("\n👉 LIVE SIDE B CANDIDATES:")
        print(", ".join(side_b) if side_b else "[⚠️ Pool Completely Empty Due To Eliminations]")
        print("\n=========================================================================")
        
        if args.expand and matchups:
            print(f"\n📋 ESTIMATED POTENTIAL MATCHUPS ({len(matchups)} TOTAL):")
            print("-------------------------------------------------------------------------")
            for idx, m in enumerate(matchups, start=1):
                print(f"{idx:03d}. {m['display']:<35} {m['meta']}")
        elif not args.expand:
            print("\n💡 Run your request back appending '--expand' to list every exact country combination.")
            
    else:
        parser.print_help()

if __name__ == "__main__":
    main()