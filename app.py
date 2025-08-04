from flask import Flask, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

API_KEY = "c8264285db854e90a9a86d56c24898e5"
BASE_URL = "https://api.football-data.org/v4"
headers = {"X-Auth-Token": API_KEY}


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
def get_next_match_and_form():
    match_url = f"{BASE_URL}/competitions/PL/matches?status=SCHEDULED&limit=1"
    match_res = requests.get(match_url, headers=headers).json()
    match = match_res['matches'][0]
    home = match['homeTeam']
    away = match['awayTeam']
    date = datetime.fromisoformat(match['utcDate'].replace("Z", "+00:00")).strftime('%Y-%m-%d %H:%M')

    home_form = get_team_recent_results(home['id'])
    away_form = get_team_recent_results(away['id'])

    betting_tips = {
        "high_prob": "Home Win" if home_form['wins'] >= 3 and away_form['losses'] >= 3 else
                     "Away Win" if away_form['wins'] >= 3 and home_form['losses'] >= 3 else
                     "Both Teams to Score",
        "medium_prob": "Over 2.5 Goals",
        "wild_card": "Exact Score 2-1 to Home"
    }

    return jsonify({
        "match": {
            "date": date,
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


import os

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)


