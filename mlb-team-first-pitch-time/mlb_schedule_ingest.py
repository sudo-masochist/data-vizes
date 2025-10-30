import requests
from datetime import datetime
import pytz
import csv


def get_mlb_schedule():
    """
    Fetches the 2025 MLB regular season schedule, saves it to a CSV file,
    and prints each game with its start time converted to the local time of the ballpark.
    """
    # Define the start and end dates for the 2025 MLB regular season.
    # We use a broad range to ensure we capture all games, including any potential make-up games.
    start_date = "2025-03-01"
    end_date = "2025-09-30"

    # The MLB Stats API endpoint for schedule information.
    api_url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate={start_date}&endDate={end_date}"

    # A dictionary mapping MLB venue names to their corresponding IANA timezone.
    # This is crucial for converting UTC times to the correct local time.
    venue_timezones = {
        # AL East
        'Oriole Park at Camden Yards': 'America/New_York',
        'Fenway Park': 'America/New_York',
        'Yankee Stadium': 'America/New_York',
        'Tropicana Field': 'America/New_York',
        'Rogers Centre': 'America/Toronto',
        # AL Central
        'Rate Field': 'America/Chicago',
        'Progressive Field': 'America/New_York',
        'Comerica Park': 'America/New_York',
        'Kauffman Stadium': 'America/Chicago',
        'Target Field': 'America/Chicago',
        # AL West
        'Angel Stadium': 'America/Los_Angeles',
        'Oakland-Alameda County Coliseum': 'America/Los_Angeles',
        'Sutter Health Park': 'America/Los_Angeles',
        'T-Mobile Park': 'America/Los_Angeles',
        'Globe Life Field': 'America/Chicago',
        'Daikin Park': 'America/Chicago',
        # NL East
        'Truist Park': 'America/New_York',
        'loanDepot park': 'America/New_York',
        'Citi Field': 'America/New_York',
        'Citizens Bank Park': 'America/New_York',
        'Nationals Park': 'America/New_York',
        # NL Central
        'Wrigley Field': 'America/Chicago',
        'Great American Ball Park': 'America/New_York',
        'American Family Field': 'America/Chicago',
        'PNC Park': 'America/New_York',
        'Busch Stadium': 'America/Chicago',
        # NL West
        'Chase Field': 'America/Phoenix',
        'Coors Field': 'America/Denver',
        'Dodger Stadium': 'America/Los_Angeles',
        'Petco Park': 'America/Los_Angeles',
        'Oracle Park': 'America/Los_Angeles',
        # International & Special Event Venues
        'London Stadium': 'Europe/London',
        'Estadio Alfredo Harp Helú': 'America/Mexico_City',
        'Hiram Bithorn Stadium': 'America/Puerto_Rico',
        'Tokyo Dome': 'Asia/Tokyo',
        'George M. Steinbrenner Field': 'America/New_York',  # Spring Training
        'Bristol Motor Speedway': 'America/New_York',  # Special Event
        'Journey Bank Ballpark': 'America/New_York',  # Little League Classic
        'Muncy Bank Ballpark at Historic Bowman Field': 'America/New_York',  # Official Name for LL Classic
        'Minute Maid Park': 'America/Chicago'
    }

    try:
        print("Fetching MLB schedule for 2025...")
        response = requests.get(api_url, timeout=20)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        schedule_data = response.json()
        print("Schedule fetched successfully. Processing games...\n")

        processed_games = set()
        output_filename = 'data/mlb_schedule_2025.csv'

        with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(['Date', 'Local Start Time', 'Away Team', 'Home Team', 'Venue'])

            game_count = 0
            if schedule_data.get("dates"):
                for date_info in schedule_data["dates"]:
                    for game in date_info["games"]:
                        game_pk = game['gamePk']
                        # Ensure the game is a regular season game and not a duplicate
                        if game.get("gameType") != "R" or game_pk in processed_games:
                            continue

                        processed_games.add(game_pk)
                        game_count += 1

                        # Extract game details
                        game_utc_time_str = game["gameDate"]
                        away_team = game["teams"]["away"]["team"]["name"]
                        home_team = game["teams"]["home"]["team"]["name"]
                        venue = game["venue"]["name"]

                        # Convert UTC time string to a datetime object
                        utc_dt = datetime.fromisoformat(game_utc_time_str.replace('Z', '+00:00'))

                        # Get the timezone for the venue
                        home_timezone_str = venue_timezones.get(venue, "UTC")
                        if home_timezone_str == "UTC":
                            print(f"Warning: Timezone not found for venue '{venue}'. Defaulting to UTC.")
                        home_timezone = pytz.timezone(home_timezone_str)

                        # Convert UTC datetime to the local timezone of the home team
                        local_dt = utc_dt.astimezone(home_timezone)

                        # Format the output for readability
                        date_str = local_dt.strftime("%Y-%m-%d")
                        time_str = local_dt.strftime("%I:%M %p %Z")  # e.g., 07:05 PM EDT

                        csv_writer.writerow([date_str, time_str, away_team, home_team, venue])

            if game_count == 0:
                print("No regular season games found for the specified date range.")
                print("The 2025 schedule may not be available yet from the API.")
            else:
                print(f"\nProcessed a total of {game_count} games.")
                print(f"Schedule saved to {output_filename}")

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching data from the API: {e}")
    except KeyError as e:
        print(f"Could not parse the API response. Unexpected data structure: Missing key {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    get_mlb_schedule()
