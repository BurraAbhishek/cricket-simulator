from django.shortcuts import render
from bin.models.team import Team
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS
from modules.stat.all_games import get_all_games, get_match_name, get_match_link



def fetch_team_name(id: str):
    return Team(id).get("name")


def fetch_team_rating(id: str):
    return Team(id).get("rating_glicko2").get("rating")


def fetch_team_flag(id: str):
    return Team(id).get("flag")


def fetch_team_color(id: str):
    return Team(id).get("color")


def format_overs(balls: int):
    if balls % 6 == 0:
        return str(balls // 6)
    else:
        return str(balls // 6) + "." + str(balls % 6)


def format_run_rate(score: int, balls: int):
    if balls == 0:
        return 0
    else:
        return score * 6 / balls


def render_max_aggregates(request):
    max_totals = []
    # Search all matches
    games = get_all_games()
    for i in games:
        if i["margin"] not in [
            "Walkover",
            "Match Cancelled",
            "Disciplinary Forfeit",
            "Double Forfeit"
        ]:
            winner_id = i["winner"]
            winner_name = ""
            if winner_id != "":
                winner_name = fetch_team_name(i["winner"])
            tie = False
            if winner_id == "" and i["margin"] == "Match Tied":
                tie = True
            aggscore = 0
            aggballs = 0
            aggwickets = 0
            for j in i["innings"]:
                aggscore += j["score"]
                aggballs += j["balls"]
                aggwickets += j["wickets"]
            max_totals.append(
                {
                    "id": i["_id"],
                    "match_name": get_match_name(i["_id"]),
                    "match_link": get_match_link(i["_id"]),
                    "rank": 0,
                    "inning": 1,
                    "team1": i["team1"],
                    "team1_name": fetch_team_name(
                        i["team1"]
                    ),
                    "team1_flag": fetch_team_flag(
                        i["team1"]
                    ),
                    "team1_color": fetch_team_color(
                        i["team1"]
                    ),
                    "team1_rating": fetch_team_rating(
                        i["team1"]
                    ),
                    "team2": i["team2"],
                    "team2_name": fetch_team_name(
                        i["team2"]
                    ),
                    "team2_flag": fetch_team_flag(
                        i["team2"]
                    ),
                    "team2_color": fetch_team_color(
                        i["team2"]
                    ),
                    "team2_rating": fetch_team_rating(
                        i["team2"]
                    ),
                    "score": aggscore,
                    "wickets": aggwickets,
                    "formatted_overs": format_overs(
                        aggballs
                    ),
                    "balls": aggballs,
                    "winner_id": winner_id,
                    "winner_name": winner_name,
                    "tie": tie,
                    "margin": i["margin"]
                }
            )
    # Sort!
    max_totals.sort(key=lambda x: x["team1_rating"] + x["team2_rating"])
    max_totals.sort(key=lambda x: abs(x["team1_rating"] - x["team2_rating"]))
    max_totals.sort(key=lambda x: x["wickets"])
    max_totals.sort(key=lambda x: x["balls"])
    max_totals.sort(key=lambda x: x["score"], reverse=True)
    # ranking
    if len(max_totals) > 0:
        score = max_totals[0]["score"]
        rank = 1
        for i in max_totals:
            if i["score"] < score:
                rank += 1
            i["rank"] = rank
            score = i["score"]
    # Now render
    return render(
        request,
        "stat/max_aggregates.html",
        {
            "stat": max_totals,
            "settings": TOURNAMENT_SETTINGS,
            "title": "Highest match aggregates"
        }
    )
