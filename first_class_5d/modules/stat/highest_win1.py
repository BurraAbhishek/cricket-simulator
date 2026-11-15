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


def render_highest_win1(request):
    max_totals = []
    # Search all matches
    games = get_all_games()
    for i in games:
        slot = 0
        slot_object = {
            "inning_win": "innings" in i["margin"],
            "chase": "wickets" in i["margin"],
            "by_wicket": 10 - i["innings"][-1]["wickets"],
            "double_forfeit": i["margin"].lower() == "double forfeit",
            "by_run": 0,
            "slot_weight": 0
        }
        if "innings" in i["margin"]:
            slot = 12
        elif "runs" in i["margin"]:
            slot = 11
            slot_object["by_run"] = int(i["margin"].split()[-2])
        elif "wickets" in i["margin"]:
            slot = 10 - i["innings"][3]["wickets"]
        elif i["margin"].lower() == "double forfeit":
            slot = -1
        max_totals.append(
            {
                "id": i["_id"],
                "match_name": get_match_name(i["_id"]),
                "match_link": get_match_link(i["_id"]),
                "rank": 0,
                "inning": 1,
                "team": i["innings"][0]["batting_team"],
                "team_name": fetch_team_name(
                    i["innings"][0]["batting_team"]
                ),
                "team_flag": fetch_team_flag(
                    i["innings"][0]["batting_team"]
                ),
                "team_color": fetch_team_color(
                    i["innings"][0]["batting_team"]
                ),
                "team_rating": fetch_team_rating(
                    i["innings"][0]["batting_team"]
                ),
                "score": i["innings"][0]["score"] - i["innings"][1]["score"],
                "wickets": i["innings"][0]["wickets"] - i["innings"][1]["wickets"],
                "margin": i["margin"],
                "opposition": i["innings"][0]["bowling_team"],
                "opposition_name": fetch_team_name(
                    i["innings"][0]["bowling_team"]
                ),
                "opposition_flag": fetch_team_flag(
                    i["innings"][0]["bowling_team"]
                ),
                "opposition_color": fetch_team_color(
                    i["innings"][0]["bowling_team"]
                ),
                "opposition_rating": fetch_team_rating(
                    i["innings"][0]["bowling_team"]
                ),
                "slot_object": slot_object
            }
        )
    # Sort!
    max_totals.sort(key=lambda x: x["team_rating"])
    max_totals.sort(key=lambda x: x["opposition_rating"], reverse=True)
    max_totals.sort(key=lambda x: x["wickets"])
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
        "stat/highest_win1.html",
        {
            "stat": max_totals,
            "settings": TOURNAMENT_SETTINGS
        }
    )
