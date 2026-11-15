from django.shortcuts import render
from bin.models.team import Team, TeamCollection, AbstractPlayer
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS
from modules.stat.all_games import get_all_games, get_match_name, get_match_link, innings_verbose



team_collection_master = {}


def fetch_team_name(id: str):
    return Team(id).get("name")


def fetch_team_rating(id: str):
    return Team(id).get("rating_glicko2").get("rating")


def fetch_team_flag(id: str):
    return Team(id).get("flag")


def fetch_team_color(id: str):
    return Team(id).get("color")


def fetch_player_name(id: str):
    return TeamCollection().fetch_player_map(id).get("player_name")


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


def render_highest_partnership1(request):
    max_totals = []
    # From all games
    games = get_all_games()
    for i in games:
        for k0, j0 in enumerate(i["innings"], start=1):
            result = "draw"
            if i["winner"] == j0["bowling_team"]:
                result = "loss"
            if i["winner"] == j0["batting_team"]:
                result = "win"
            if i["winner"] == "" and i["margin"] == "Match Tied":
                result = "tie"
            inning_name = innings_verbose(k0)
            for k, j in enumerate(j0["partnerships"], start=1):
                j1 = False
                j2 = False
                for k1 in j0["batter_stats"]:
                    if k1["_id"] == j["p1"]:
                        j1 = bool(k1["dismissed"])
                    elif k1["_id"] == j["p2"]:
                        j2 = bool(k1["dismissed"])
                opposition = Team(j0["bowling_team"])
                wicket_suffix = "th"
                if k == 1:
                    wicket_suffix = "st"
                if k == 2:
                    wicket_suffix = "nd"
                if k == 3:
                    wicket_suffix = "rd"
                max_totals.append(
                    {
                        "match_id": i["_id"],
                        "match_name": get_match_name(i["_id"]),
                        "match_link": get_match_link(i["_id"]),
                        "inning": k0,
                        "wicket": k,
                        "wicket_verbose": str(k) + wicket_suffix + " Wicket",
                        "p1": j["p1"],
                        "p2": j["p2"],
                        "p1_name": fetch_player_name(
                            j["p1"]
                        ),
                        "p2_name": fetch_player_name(
                            j["p2"]
                        ),
                        "bat_runs": j["p1_runs"] + j["p2_runs"],
                        "runs": j["p1_runs"] + j["p2_runs"] + j.get("extra", 0),
                        "balls": j["p1_balls"] + j["p2_balls"],
                        "extra": j.get("extra", 0),
                        "p1_runs": j["p1_runs"],
                        "p2_runs": j["p2_runs"],
                        "p1_balls": j["p1_balls"],
                        "p2_balls": j["p2_balls"],
                        "p1_suffix": ('*' if not j1 else ''),
                        "p2_suffix": ('*' if not j2 else ''),
                        "p1_player_title": AbstractPlayer(j["p1"]).rating_title(),
                        "p2_player_title": AbstractPlayer(j["p2"]).rating_title(),
                        "team": j0["batting_team"],
                        "team_name": fetch_team_name(
                            j0["batting_team"]
                        ),
                        "team_color": fetch_team_color(
                            j0["batting_team"]
                        ),
                        "team_flag": fetch_team_flag(
                            j0["batting_team"]
                        ),
                        "suffix": ('*' if ((not j1) and (not j2)) else ''),
                        "opposition": j0["bowling_team"],
                        "opposition_name": fetch_team_name(
                            j0["bowling_team"]
                        ),
                        "opposition_name": opposition.get("name"),
                        "opposition_color": opposition.get("color"),
                        "opposition_flag": opposition.get("flag"),
                        "opposition_rating": fetch_team_rating(j0["bowling_team"]),
                        "result": bool(True if i["winner"] == j0["batting_team"] else False),
                        "result_class": result,
                        "innings_position": inning_name,
                        "margin": i["margin"]
                    }
                )
    # Sort!
    max_totals.sort(key=lambda x: x["opposition_rating"], reverse=True)
    max_totals.sort(key=lambda x: 1 if x["result"] else 0, reverse=True)
    max_totals.sort(key=lambda x: 0 if x["suffix"] == "*" else 1)
    max_totals.sort(key=lambda x: x["balls"])
    max_totals.sort(key=lambda x: x["runs"], reverse=True)
    rank = 1
    skip = 0
    runs = max_totals[0]["runs"]
    for i in max_totals:
        if i["runs"] < runs:
            rank += 1
            skip = 1
        else:
            skip += 1
        i["rank"] = rank
        runs = i["runs"]
    # Now render
    return render(
        request,
        "stat/highest_partnership1.html",
        {
            "stat": max_totals,
            "settings": TOURNAMENT_SETTINGS
        }
    )
