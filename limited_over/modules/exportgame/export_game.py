import json
from django.http import HttpResponseRedirect
from bin.mongodb import mongoclient
from modules.exportgame.export_innings import export_live_innings
from django.contrib.staticfiles import finders, handlers


def export_live_game(request):
    # fetch innings
    innings = []
    innings1 = export_live_innings(1)
    innings2 = export_live_innings(2)
    innings.append(innings1)
    innings.append(innings2)
    # Match
    temp_match = mongoclient.live_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS
    ).find_one(0)
    game = {
        "_id": temp_match["id"],
        "isTest": temp_match["isTest"],
        "overs": temp_match["overs"],
        "wickets": temp_match["wickets"],
        "team1": temp_match["team1"],
        "team2": temp_match["team2"],
        "toss": int(temp_match["toss"]),
        "innings": innings,
        "target": innings1["score"] + 1,
        "winner": "",
        "margin": "",
        "player_of_the_match": ""
    }
    if temp_match["isFinal"]:
        # Change later if required
        game["player_of_the_tournament"] = "P1"
    if innings1["score"] > innings2["score"]:
        game["winner"] = temp_match["team1"]
        game["margin"] = str(innings1["score"] - innings2["score"]) + " run"
        if innings1["score"] - innings2["score"] != 1:
            game["margin"] += "s"
    elif innings1["score"] < innings2["score"]:
        game["winner"] = temp_match["team2"]
        game["margin"] = str(temp_match["wickets"] - innings2["wickets"]) + " wicket"
        if temp_match["wickets"] - innings2["wickets"] != 1:
            game["margin"] += "s"
    else:
        game["margin"] = "Match Tied"
    # Export
    match_path = finders.find('temp/live/completed.json')
    if match_path is None:
        mp = str(finders.searched_locations[0])
        f = open(mp + "/temp/live/completed.json", "w")
        f.write('{}')
        f.close()
    match_path = finders.find('temp/live/completed.json')
    f = open(match_path, "w+")
    json.dump(game, f, indent=2)
    f.close()
    return HttpResponseRedirect("/")
