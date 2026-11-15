from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from bin.models.team import TeamCollection, AbstractPlayer
from bin.mongoinserts.load_games import fetch_game
from modules.index.summary import get_summary


WIDTH_MULTIPLIER = 30


def get_partnerships(request, clas, id, innings):
    game = fetch_game(clas, id)
    if game is None:
        raise PermissionDenied
    summary = get_summary(game)
    innings -= 1
    # render
    if innings == -1:
        return render(
            request,
            "partnerships.html",
            {
                "summary": summary,
                "clas": clas,
                "id": id,
                "c": list(range(1, len(game["innings"]) + 1)),
                "innings": innings
            }
        )
    else:
        team = TeamCollection()
        batter_collection = team.get(
            game["innings"][innings]["batting_team"]
        )
        partnerships = get_partnership_list(
            game["innings"][innings]["partnerships"],
            batter_collection
        )
        batters_team_data = team.find_one(game["innings"][innings]["batting_team"])
        batting_team_name = batters_team_data["name"]
        partner_color = batters_team_data["color"]
        return render(
            request,
            "partnerships.html",
            {
                "summary": summary,
                "clas": clas,
                "id": id,
                "c": list(range(1, len(game["innings"]) + 1)),
                "innings": innings,
                "batting_team": batting_team_name,
                "partnerships": partnerships,
                "partner_color": partner_color
            }
        )


def get_partnership_list(og_partnerships, batting_team):
    partnerships = []
    max_contribution = 0
    for i in og_partnerships:
        partnerships.append(partnership_element(i, batting_team))
        if max(i["p1_runs"], i["p2_runs"]) > max_contribution:
            max_contribution = max(i["p1_runs"], i["p2_runs"])
    for i in partnerships:
        if max_contribution < 1:
            i["p1_width"] = 0
            i["p2_width"] = 0
            i["p1_left_width"] = WIDTH_MULTIPLIER
            i["p2_left_width"] = WIDTH_MULTIPLIER
        else:
            i["p1_width"] = WIDTH_MULTIPLIER * i["p1_runs"] / max_contribution
            i["p2_width"] = WIDTH_MULTIPLIER * i["p2_runs"] / max_contribution
            i["p1_left_width"] = WIDTH_MULTIPLIER - i["p1_width"]
            i["p2_left_width"] = WIDTH_MULTIPLIER - i["p2_width"]
    return partnerships
    

def partnership_element(i, batter_collection):
    p1_dict = batter_collection.find_one(i["p1"])
    p2_dict = batter_collection.find_one(i["p2"])
    return {
        "p1": i["p1"],
        "p2": i["p2"],
        "p1_name": p1_dict["name"],
        "p2_name": p2_dict["name"],
        "p1_runs": i["p1_runs"],
        "p1_balls": i["p1_balls"],
        "p2_runs": i["p2_runs"],
        "p2_balls": i["p2_balls"],
        "p1_avatar": AbstractPlayer(i["p1"]).avatar(),
        "p2_avatar": AbstractPlayer(i["p2"]).avatar(),
        "p1_player_title": AbstractPlayer(i["p1"]).rating_title(),
        "p2_player_title": AbstractPlayer(i["p2"]).rating_title(),
        "total_runs": i["p1_runs"] + i["p2_runs"] + i.get("extra", 0),
        "total_balls": i["p1_balls"] + i["p2_balls"],
        "p1_width": 0,
        "p2_width": 0,
        "p1_left_width": 0,
        "p2_left_width": 0
    }
