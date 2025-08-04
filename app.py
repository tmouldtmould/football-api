from flask import Flask, jsonify
import requests
from datetime import datetime, timedelta
import os

app = Flask(__name__)

API_KEY = "c8264285db854e90a9a86d56c24898e5"
BASE_URL = "https://api.football-data.org/v4"
headers = {"X-Auth-Token": API_KEY}

# Leagues to pull (official codes)
LEAGUES = [
    "CL",    # UEFA Champions League
    "BL1",   # Bundesliga
    "DED",   # Eredivisie
    "BSA",   # Campeonato Brasileiro Série A
    "PD",    # Primera Division (La Liga)
    "FL1",   # Ligue 1
    "ELC",   # Championship
    "PPL",   # Primeira Liga
    "EC",    # European Championship
    "SA",    # Serie A
    "PL"     # Premier League
]

def get_team_recent_results(team_id, limit=5):
    url = f"{BASE_URL}/teams/{team_id}/matches?status=FINISHED&limit={limit}"
    res = requests.get(url, headers=headers)
    matches = res.json().get("matches", [])
    form = {"wins": 0, "draws": 0, "losses": 0, "goals_for": 0, "goals_against": 0}

    for match in matches:
        is_home = match['homeTeam']['id'] == team_id
        goals_for = match['score']['fullTime']['home'] if is_home else match['score']['fullTime']['away']
        goals_against = match['score']['fullTime']['away'] if is_home else match['score']['fullTime']['home']
        form['goals_for'] += goals_for
        form['goals_against'] += goals_against

        result = match['score']['winner']
        if result == "DRAW":
            form['draws'] += 1
        elif (result == "HOME_TEAM" and is_home) or (result == "AWAY_TEAM" and not is_home):
            form['wins'] += 1
        else:
            form['losses'] += 1

    return form

@app.route('/next-match-analysis', methods=['GET'])
def get_weekly_fixtures_analysis():
    results = []
    today = datetime.utcnow().date()
    next_week = today + timedelta(days=7)

    for league in LEAGUES:
        try:
            url = (f"{BASE_URL}/competitions/{league}/matches"
                   f"?status=SCHEDULED&dateFrom={today.isoformat()}&dateTo={next_week.isoformat()}")
            res = requests.get(url, headers=headers)
            print(f"[DEBUG] League {league}: Status {res.status_code}")

            if res.status_code != 200:
                print(f"[ERROR] Failed to fetch matches for {league}. Response: {res.text}")
                results.append({
                    "competition": league,
                    "error": f"API error {res.status_code}: {res.text}"
                })
                continue

            matches = res.json().get("matches", [])
            print(f"[DEBUG] League {league}: Found {len(matches)} matches.")

            for match in matches:
                match_date = datetime.fromisoformat(match['utcDate'].replace("Z", "+00:00")).date()
                date_str = datetime.fromisoformat(match['utcDate'].replace("Z", "+00:00")).strftime('%Y-%m-%d %H:%M')

                home = match['homeTeam']
                away = match['awayTeam']

                home_form = get_team_recent_results(home['id'])
                away_form = get_team_recent_results(away['id'])

                betting_tips = {
                    "high_prob": "Home Win" if home_form['wins'] >= 3 and away_form['losses'] >= 3 else
                                 "Away Win" if away_form['wins'] >= 3 and home_form['losses'] >= 3 else
                                 "Both Teams to Score",
                    "medium_prob": "Over 2.5 Goals",
                    "wild_card": "Exact Score 2-1 to Home"
                }

                results.append({
                    "competition": league,
                    "match": {
                        "date": date_str,
                        "home": home['name'],
                        "away": away['name']
                    },
                    "form": {
                        home['name']: home_form,
                        away['name']: away_form
                    },
                    "betting_tips": betting_tips,
                    "note": "Always bet responsibly and within your means."
                })

        except Exception as e:
            print(f"[EXCEPTION] League {league}: {str(e)}")
            results.append({
                "competition": league,
                "error": str(e)
            })

    return jsonify(results)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)



