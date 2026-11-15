from django.shortcuts import render
from bin.models.team import Team
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS
from modules.stat.all_games import get_all_games, get_match_name, get_match_link, innings_verbose


def fetch_team_name(id: str):
    return Team(id).get("name")


def fetch_team_rating(id: str):
    return Team(id).get("rating_glicko2").get("rating")


def fetch_team_flag(id: str):
    return Team(id).get("flag")


def fetch_team_color(id: str):
    return Team(id).get("color")


def format_score(score: int, wickets: int) -> str:
    if wickets >= 10:
        return str(score)
    else:
        return str(score) + "/" + str(wickets)


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


def render_max_totals(request):
    max_totals = []
    games = get_all_games()
    for i in games:
        for k, j in enumerate(i["innings"], start=1):
            result_class = ""
            if i["winner"] == j["batting_team"]:
                result = 1
                result_class = "win"
            elif i["winner"] == j["bowling_team"]:
                result = -1
                result_class = "loss"
            elif i["winner"] == "" and i["margin"] == "Match Tied":
                result = 0
                result_class = "draw"
            elif i["margin"].lower() == "double forfeit":
                result = -2
            else:
                result = 0
            inning_name = innings_verbose(k)
            max_totals.append(
                {
                    "id": i["_id"],
                    "match_name": get_match_name(i["_id"]),
                    "match_link": get_match_link(i["_id"]),
                    "rank": 0,
                    "inning": k,
                    "team": j["batting_team"],
                    "team_name": fetch_team_name(
                        j["batting_team"]
                    ),
                    "team_flag": fetch_team_flag(
                        j["batting_team"]
                    ),
                    "team_color": fetch_team_color(
                        j["batting_team"]
                    ),
                    "team_rating": fetch_team_rating(
                        j["batting_team"]
                    ),
                    "score": j["score"],
                    "wickets": j["wickets"],
                    "formatted_score": format_score(
                        j["score"],
                        j["wickets"],
                    ),
                    "formatted_overs": format_overs(
                        j["balls"]
                    ),
                    "run_rate": format_run_rate(
                        j["score"],
                        j["balls"],
                    ),
                    "balls": j["balls"],
                    "opposition": j["bowling_team"],
                    "opposition_name": fetch_team_name(
                        j["bowling_team"]
                    ),
                    "opposition_flag": fetch_team_flag(
                        j["bowling_team"]
                    ),
                    "opposition_color": fetch_team_color(
                        j["bowling_team"]
                    ),
                    "opposition_rating": fetch_team_rating(
                        j["bowling_team"]
                    ),
                    "innings_position": inning_name,
                    "result": result,
                    "result_class": result_class
                }
            )
    # Sort!
    max_totals.sort(key=lambda x: x["inning"], reverse=True)
    max_totals.sort(key=lambda x: x["team_rating"])
    max_totals.sort(key=lambda x: x["opposition_rating"], reverse=True)
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
        "stat/max_totals.html",
        {
            "stat": max_totals,
            "settings": TOURNAMENT_SETTINGS
        }
    )
