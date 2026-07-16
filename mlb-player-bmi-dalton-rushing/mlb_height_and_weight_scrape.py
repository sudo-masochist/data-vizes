import requests
import pandas as pd
import time
from pathlib import Path

# ============================================
# CONFIG
# ============================================
SEASON = 2026
OUTPUT_FILE = Path(f"mlb_{SEASON}_player_heights_weights.csv")

BASE_URL = "https://statsapi.mlb.com/api/v1"

# Current MLB team IDs (30 teams)
TEAM_IDS = [
    108, 109, 110, 111, 112, 113, 114, 115, 116, 117,
    118, 119, 120, 121, 133, 134, 135, 136, 137, 138,
    139, 140, 141, 142, 143, 144, 145, 146, 147, 158
]

# ============================================
# HELPERS
# ============================================

def safe_get(url, params=None, retries=3, delay=1):
    """Simple retry wrapper for requests."""
    for attempt in range(retries):
        try:
            r = requests.get(url, params=params, timeout=20)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            print(f"Request failed ({attempt+1}/{retries}): {e}")
            time.sleep(delay)
    return None


def height_to_inches(height_str):
    """
    Convert MLB height format like 6' 3" into total inches.
    Returns None if parsing fails.
    """
    if not height_str:
        return None

    try:
        parts = height_str.replace('"', "").split("'")
        feet = int(parts[0].strip())
        inches = int(parts[1].strip())
        return feet * 12 + inches
    except:
        return None


def get_team_roster(team_id, season):
    """
    Pull 40-man roster for a team.
    You can switch rosterType to active if needed.
    """
    url = f"{BASE_URL}/teams/{team_id}/roster"
    params = {
        "rosterType": "40Man",
        "season": season
    }

    data = safe_get(url, params=params)
    if not data:
        return []

    return data.get("roster", [])


def get_player_details(player_id):
    """
    Pull player bio info including height/weight.
    """
    url = f"{BASE_URL}/people/{player_id}"
    data = safe_get(url)

    if not data or "people" not in data or not data["people"]:
        return None

    p = data["people"][0]

    return {
        "player_id": p.get("id"),
        "full_name": p.get("fullName"),
        "first_name": p.get("firstName"),
        "last_name": p.get("lastName"),
        "birth_date": p.get("birthDate"),
        "current_age": p.get("currentAge"),
        "height_raw": p.get("height"),
        "height_inches": height_to_inches(p.get("height")),
        "weight_lbs": p.get("weight"),
        "bat_side": p.get("batSide", {}).get("description"),
        "pitch_hand": p.get("pitchHand", {}).get("description"),
        "position": p.get("primaryPosition", {}).get("abbreviation"),
        "mlb_debut_date": p.get("mlbDebutDate"),
    }


# ============================================
# MAIN
# ============================================

def main():
    all_players = {}
    team_map = {}

    print(f"Fetching {SEASON} rosters...")

    for team_id in TEAM_IDS:
        roster = get_team_roster(team_id, SEASON)

        print(f"Team {team_id}: {len(roster)} players")

        for player in roster:
            pid = player["person"]["id"]
            pname = player["person"]["fullName"]

            if pid not in all_players:
                all_players[pid] = pname
                team_map[pid] = []

            team_map[pid].append(team_id)

        time.sleep(0.5)

    print(f"Unique players found: {len(all_players)}")
    print("Fetching player details...")

    rows = []

    for i, pid in enumerate(all_players.keys(), start=1):
        print(f"[{i}/{len(all_players)}] Player ID {pid}")

        details = get_player_details(pid)

        if details:
            details["team_ids"] = ",".join(map(str, team_map[pid]))
            rows.append(details)

        time.sleep(0.25)

    df = pd.DataFrame(rows)

    df.sort_values(["full_name"], inplace=True)

    df.to_csv(OUTPUT_FILE, index=False)

    print(f"\nSaved {len(df)} players to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()