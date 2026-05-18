import sys
import json
import os
import argparse

# Common aliases for ease of searching
ALIASES = {
    "usa": "United States",
    "us": "United States",
    "uk": "England",
    "south korea": "South Korea",
    "korea republic": "South Korea",
    "korea": "South Korea",
    "czech republic": "Czechia",
    "czechia": "Czechia",
    "turkey": "Turkey",
    "türkiye": "Turkey",
    "cote d'ivoire": "Ivory Coast",
    "ivory coast": "Ivory Coast",
    "cape verde": "Cape Verde",
    "cabo verde": "Cape Verde",
    "dr congo": "DR Congo",
    "congo dr": "DR Congo"
}

# Complete list of 2026 Knockout matches with official labels and cities
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

# Graph linkages pointing from a lower knockout match to the subsequent round
NEXT_MATCH = {
    73: 90, 75: 90,
    74: 89, 77: 89,
    76: 91, 78: 91,
    79: 92, 80: 92,
    81: 94, 82: 94,
    83: 93, 84: 93,
    85: 96, 87: 96,
    86: 95, 88: 95,
    
    89: 97, 90: 97,
    91: 99, 92: 99,
    93: 98, 94: 98,
    95: 100, 96: 100,
    
    97: 101, 98: 101,
    99: 102, 100: 102,
    
    101: 104,
    102: 104
}

# Group Stage placement slots linked to their initial Round of 32 match ID
GROUP_INITIAL_MATCHES = {
    "A": {1: 79, 2: 73, 3: [74, 82]},
    "B": {1: 85, 2: 73, 3: [74, 81]},
    "C": {1: 76, 2: 75, 3: [74, 77, 79]},
    "D": {1: 81, 2: 88, 3: [74, 77, 87]},
    "E": {1: 74, 2: 78, 3: [79, 80, 81, 82, 85, 87]},
    "F": {1: 75, 2: 76, 3: [74, 77, 79, 81, 85]},
    "G": {1: 82, 2: 88, 3: [77, 85]},
    "H": {1: 84, 2: 86, 3: [77, 79, 80, 82]},
    "I": {1: 77, 2: 78, 3: [79, 80, 81, 82, 85, 87]},
    "J": {1: 86, 2: 84, 3: [80, 81, 82, 85, 87]},
    "K": {1: 87, 2: 83, 3: [80]},
    "L": {1: 80, 2: 83, 3: [87]}
}

# Structural feeding definition for backward lineage trace requests
MATCH_ORIGINS = {
    73: "Runner-up Group A vs. Runner-up Group B",
    74: "Winner Group E vs. 3rd Group A/B/C/D/F",
    75: "Winner Group F vs. Runner-up Group C",
    76: "Winner Group C vs. Runner-up Group F",
    77: "Winner Group I vs. 3rd Group C/D/F/G/H",
    78: "Runner-up Group E vs. Runner-up Group I",
    79: "Winner Group A vs. 3rd Group C/E/F/H/I",
    80: "Winner Group L vs. 3rd Group E/H/I/J/K",
    81: "Winner Group D vs. 3rd Group B/E/F/I/J",
    82: "Winner Group G vs. 3rd Group A/E/H/I/J",
    83: "Runner-up Group K vs. Runner-up Group L",
    84: "Winner Group H vs. Runner-up Group J",
    85: "Winner Group B vs. 3rd Group E/F/G/I/J",
    86: "Winner Group J vs. Runner-up Group H",
    87: "Winner Group K vs. 3rd Group D/E/I/J/L",
    88: "Runner-up Group D vs. Runner-up Group G",
    
    89: (74, 77), 90: (73, 75), 91: (76, 78), 92: (79, 80),
    93: (83, 84), 94: (81, 82), 95: (86, 88), 96: (85, 87),
    
    97: (89, 90), 98: (93, 94), 99: (91, 92), 100: (95, 96),
    101: (97, 98), 102: (99, 100),
    103: ("Loser Match 101", "Loser Match 102"),
    104: (101, 102)
}

def load_groups():
    if os.path.exists("groups.json"):
        with open("groups.json", "r", encoding="utf-8") as f:
            return json.load(f)
    print("Warning: groups.json not found. Using internal data fallback.")
    return {
        "A": ["Mexico", "South Africa", "South Korea", "Czechia"],
        "D": ["United States", "Paraguay", "Australia", "Turkey"]
    }

def find_team_group(team_name, groups):
    query = team_name.lower().strip()
    if query in ALIASES:
        query = ALIASES[query].lower()
        
    for group_letter, teams in groups.items():
        for t in teams:
            if query in t.lower() or t.lower() in query:
                return group_letter, t
    return None, None

def trace_path(match_id):
    path = {}
    curr = match_id
    
    path["Round of 32"] = {"match": f"Match {curr}", "label": MATCH_DETAILS[curr]["label"], "city": MATCH_DETAILS[curr]["city"]}
    curr = NEXT_MATCH[curr]
    path["Round of 16"] = {"match": f"Match {curr}", "label": MATCH_DETAILS[curr]["label"], "city": MATCH_DETAILS[curr]["city"]}
    curr = NEXT_MATCH[curr]
    path["Quarter-finals"] = {"match": f"Match {curr}", "label": MATCH_DETAILS[curr]["label"], "city": MATCH_DETAILS[curr]["city"]}
    curr = NEXT_MATCH[curr]
    path["Semi-finals"] = {"match": f"Match {curr}", "label": MATCH_DETAILS[curr]["label"], "city": MATCH_DETAILS[curr]["city"]}
    
    path["If Win Semi-final (Final)"] = {"match": "Match 104", "label": MATCH_DETAILS[104]["label"], "city": MATCH_DETAILS[104]["city"]}
    path["If Lose Semi-final (3rd Place)"] = {"match": "Match 103", "label": MATCH_DETAILS[103]["label"], "city": MATCH_DETAILS[103]["city"]}
    return path

def get_team_matrix(group_letter, team_real_name):
    slots = GROUP_INITIAL_MATCHES[group_letter]
    output = {
        "country_entered": team_real_name,
        "group": group_letter,
        "if_1st": trace_path(slots[1]),
        "if_2nd": trace_path(slots[2]),
        "if_3rd": [],
        "if_4th": "Eliminated in the Group Stage"
    }
    
    # Trace every conditional path if the team finishes as an advancing 3rd-placed team
    for match_id in slots[3]:
        output["if_3rd"].append({
            f"potential_allocation_match_{match_id}": trace_path(match_id)
        })
    return output

def trace_match_tree(match_id):
    origins = MATCH_ORIGINS.get(match_id)
    if not origins:
        return "Unknown Match ID"
    if isinstance(origins, str):
        return origins
    
    m1, m2 = origins
    if match_id == 103:
        return {
            "Match 103 (Third-Place Match)": {
                "From Semi-final 1 (Loser)": trace_match_tree(101),
                "From Semi-final 2 (Loser)": trace_match_tree(102)
            }
        }
    return {
        f"Match {match_id} ({MATCH_DETAILS[match_id]['label']})": {
            f"Side A (Winner of Match {m1})": trace_match_tree(m1),
            f"Side B (Winner of Match {m2})": trace_match_tree(m2)
        }
    }

def main():
    parser = argparse.ArgumentParser(description="FIFA World Cup 2026 Knockout Path Matrix Analyzer")
    parser.add_argument("--team", type=str, help="Name of the country to analyze (e.g. 'United States' or 'USA')")
    parser.add_argument("--match", type=int, help="Knockout Match ID to trace backwards (73 to 104)")
    args = parser.parse_args()

    groups = load_groups()

    if args.team:
        group_letter, real_name = find_team_group(args.team, groups)
        if not group_letter:
            print(json.dumps({"error": f"Team '{args.team}' not recognized in 2026 World Cup draw."}, indent=2))
            sys.exit(1)
        matrix = get_team_matrix(group_letter, real_name)
        print(json.dumps(matrix, indent=2))

    elif args.match:
        if args.match not in MATCH_DETAILS:
            print(json.dumps({"error": "Invalid Match ID. Enter a number between 73 and 104."}, indent=2))
            sys.exit(1)
        tree = trace_match_tree(args.match)
        print(json.dumps(tree, indent=2))
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()