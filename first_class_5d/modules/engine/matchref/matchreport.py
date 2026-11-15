from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from bin.models.team import Team, AbstractPlayer
from bin.mongoinserts.load_games import fetch_game
from modules.stat.all_games import get_match_name


def render_match_report(request, clas, id):
    game = fetch_game(clas, id)
    if game is None:
        raise PermissionDenied
    if game.get("margin") is None:
        raise PermissionDenied
    if str(game.get("margin")).lower() in ["advancement", "walkover", "match cancelled"]:
        raise PermissionDenied
    report = retrieve_report(game)
    # Now the actual stuff
    return render(
        request,
        "matchreport.html",
        {
            "clas": clas,
            "id": id,
            "data": report
        }
    )


def retrieve_report(game):
    match_name = str(
        get_match_name(game["_id"])
        + ", "
        + Team(game["team1"]).name()
        + " vs. "
        + Team(game["team2"]).name()
    )
    try:
        assessment = game["assessment"]
    except KeyError:
        integrity_value = 1
        if game["winner"] == game["team1"]:
            result = [1, 0]
        elif game["winner"] == game["team2"]:
            result = [0, 1]
        elif game["margin"].lower() == "double forfeit":
            result = [0, 0]
            integrity_value = 0.1
        else:
            result = [0.5, 0.5]
        assessment = {
            "nomination": {
                "integrity_clearance": True,
                "roster_clearance": True
            },
            "integrity": integrity_value,
            "result": result,
            "result_valid": True,
            "pitch": 1,
            "outfield": 1,
            "violations": {
                "summary": [],
                "behavior": [],
                "stop_clock": [],
                "ball": [],
                "park": [],
                "cheat": [],
                "fixing": []
            },
            "executive": "The match reached its natural conclusion based solely on player merit. No breaches detected.",
            "remarks": []
    }
    for i in assessment["violations"]["summary"]:
        i["player_name"] = AbstractPlayer(i["player_id"]).name()
    for i in assessment["violations"].keys():
        if i != "summary":
            i0 = assessment["violations"][i]
            for j in i0:
                player_names = ""
                for j0, k0 in enumerate(j["players"]):
                    player_names += AbstractPlayer(k0).name()
                    if j0 < len(j["players"]) - 1:
                        player_names += ", "
                j["player_names"] = player_names
    # Metadata
    report = {
        "match_id": game["_id"],
        "match_name": match_name,
        "integrity_clearance": True,
        "integrity_reason": None,
        "roster_clearance": True,
        "roster_reason": None,
        "executive_summary": assessment["executive"],
        "integrity_percent": assessment["integrity"] * 100,
        "pitch": assessment["pitch"] * 100,
        "outfield": assessment["outfield"] * 100,
        "violations": assessment["violations"],
        "remarks": assessment["remarks"],
        "result_valid": assessment["result_valid"],
        "result": format_winstring(game["winner"], game["margin"])
    }
    return report


def format_winstring(winner, margin):
    # Tie case
    if (winner is None or winner == ""):
        return margin
    elif margin.lower() in ["disciplinary forfeit", "rules infraction"]:
        return str(
            "Cheat Detected • "
            + Team(winner).name()
            + " are victorious"
        )
    else:
        return str(
            Team(winner).name()
            + " won by "
            + margin
        )