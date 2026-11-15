from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from bin.models.team import Team, AbstractPlayer
from bin.mongoinserts.load_games import fetch_game
from modules.stat.all_games import get_match_name


def render_nomination(request, clas, id, index):
    game = fetch_game(clas, id)
    if game is None:
        raise PermissionDenied
    if index == 1:
        nomination = retrieve_nomination(game, game["team1"])
    elif index == 2:
        nomination = retrieve_nomination(game, game["team2"])
    else:
        nomination = None
    try:
        team1_name = Team(game.get("team1")).name()
    except AttributeError:
        team1_name = "Team 1"
    try:
        team2_name = Team(game.get("team2")).name()
    except AttributeError:
        team2_name = "Team 2"
    # Now the actual stuff
    return render(
        request,
        "nomination.html",
        {
            "clas": clas,
            "id": id,
            "data": nomination,
            "team1": team1_name,
            "team2": team2_name
        }
    )


def retrieve_nomination(game, team_id):
    match_name = str(
        get_match_name(game["_id"])
        + ", "
        + Team(game["team1"]).name()
        + " vs. "
        + Team(game["team2"]).name()
    )
    nomination = {
        "match_id": game["_id"],
        "match_name": match_name,
        "team_name": Team(team_id).name(),
        "starting_11": [],
        "substitutions": [],
        "replacements": [
            {
                "role": "Specialist Batter",
                "id": None,
                "name": None,
                "avatar": None,
                "player_title": None,
            },
            {
                "role": "Specialist Pace Bowler",
                "id": None,
                "name": None,
                "avatar": None,
                "player_title": None,
            },
            {
                "role": "Specialist Spin Bowler",
                "id": None,
                "name": None,
                "avatar": None,
                "player_title": None,
            },
            {
                "role": "Specialist Wicketkeeper",
                "id": None,
                "name": None,
                "avatar": None,
                "player_title": None,
            },
            {
                "role": "All-Rounder",
                "id": None,
                "name": None,
                "avatar": None,
                "player_title": None,
            },
        ],
        "integrity_clearance": True,
        "integrity_reason": None,
        "roster_clearance": True,
        "roster_reason": None
    }
    prenoms = Team(team_id).nominations()
    try:
        starting_11 = game["nomination"][team_id]["default"]
    except KeyError:
        starting_11 = prenoms["default"]
    try:
        subs = game["nomination"][team_id]["substitutes"]
    except KeyError:
        subs = prenoms["substitutes"]
    try:
        csubs = game["nomination"][team_id]["replacements"]
    except KeyError:
        csubs = prenoms["replacements"]
    try:
        nom = game["assessment"]["nomination"]
        nomination["integrity_clearance"] = nom.get("integrity_clearance", True)
        nomination["integrity_reason"] = nom.get("integrity_reason", None)
        nomination["roster_clearance"] = nom.get("roster_clearance", True)
        nomination["roster_reason"] = nom.get("roster_reason", None)
    except KeyError:
        pass
    try:
        captain = game["nomination"][team_id]["captain"]
    except KeyError:
        captain = Team(team_id).captain()
    for i in starting_11:
        pl = AbstractPlayer(i)
        role = ""
        if i == captain and pl.get("wicketkeeper", False):
            role = "Captain, Wicketkeeper"
        elif i == captain:
            role = "Captain"
        elif pl.get("wicketkeeper", False):
            role = "Wicketkeeper"
        nomination["starting_11"].append({
            "id": i,
            "name": pl.name(),
            "avatar": pl.avatar(),
            "player_title": pl.rating_title(),
            "role": role
        })
    for i in subs:
        pl = AbstractPlayer(i)
        nomination["substitutions"].append({
            "id": i,
            "name": pl.name(),
            "avatar": pl.avatar(),
            "player_title": pl.rating_title(),
            "role": role
        })
    for i in csubs.keys():
        if csubs[i] is not None:
            pl = AbstractPlayer(csubs[i])
            pl_index = 4
            if i == "bat":
                pl_index = 0
            elif i == "pace":
                pl_index = 1
            elif i == "spin":
                pl_index = 2
            elif i == "keeper":
                pl_index = 3
            nomination["replacements"][pl_index]["id"] = csubs[i]
            nomination["replacements"][pl_index]["name"] = pl.name()
            nomination["replacements"][pl_index]["avatar"] = pl.avatar()
            nomination["replacements"][pl_index]["player_title"] = pl.rating_title()
    return nomination
