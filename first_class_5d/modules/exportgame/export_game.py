import json
from django.http import HttpResponseRedirect
from django.contrib.staticfiles import finders
from bin.mongodb import mongoclient
from modules.exportgame.export_innings import export_live_innings
from modules.exportgame.potm import get_potm
from modules.exportgame.paginator import get_raw_sessions


def export_live_game(request, force_end=0):
    # Match
    temp_match_collection = mongoclient.live_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS
    )
    temp_match = temp_match_collection.find_one(0)
    temp_details = temp_match_collection.find_one(1)
    nbInnings = temp_details["stage"]
    # fetch innings
    innings = []
    innings1 = export_live_innings(1)
    innings.append(innings1)
    if nbInnings > 1:
        innings2 = export_live_innings(2)
        innings.append(innings2)
    if nbInnings > 2:
        innings3 = export_live_innings(3)
        innings.append(innings3)
    if nbInnings > 3:
        innings4 = export_live_innings(4)
        innings.append(innings4)
    # fetch sessions
    game_sessions = []
    game_session_collection = mongoclient.live_db_get_collection(
        mongoclient.CURRENT_MATCH_PHASE
    )
    game_sessions_output = game_session_collection.find()
    if game_sessions_output is not None:
        game_sessions = list(game_sessions_output)
    if len(game_sessions) < 1:
        game_sessions_update = get_raw_sessions(innings, temp_match["id"], temp_match["wickets"])
        innings = game_sessions_update["innings"]
        game_sessions = game_sessions_update["sessions"]
    # game
    follow_on = bool(temp_details["follow_on_enabled"])
    game = {
        "_id": temp_match["id"],
        "isTest": temp_match["isTest"],
        "follow_on_threshold": 200,
        "follow_on": follow_on,
        "wickets": temp_match["wickets"],
        "team1": temp_match["team1"],
        "team2": temp_match["team2"],
        "toss": int(temp_match["toss"]),
        "innings": innings,
        "sessions": game_sessions,
        "target": temp_details["target"],
        "winner": "",
        "margin": "",
        "player_of_the_match": ""
    }
    if nbInnings > 2:
        if temp_details["net_score"] > 0:
            if nbInnings == 3:
                game["margin"] = "an innings and "
            else:
                game["margin"] = ""
            game["winner"] = temp_match["team1"]
            game["margin"] += str(temp_details["net_score"]) + " run"
            if temp_details["net_score"] != 1:
                game["margin"] += "s"
            if follow_on and nbInnings == 4:
                game["margin"] = str(temp_match["wickets"] - innings4["wickets"]) + " wicket"
                if temp_match["wickets"] - innings4["wickets"] != 1:
                    game["margin"] += "s"
        elif temp_details["net_score"] < 0:
            game["winner"] = temp_match["team2"]
            if nbInnings == 3:
                game["margin"] = "an innings and "
                game["margin"] += str(0 - temp_details["net_score"]) + " run"
                if temp_details["net_score"] != -1:
                    game["margin"] += "s"
            else:
                game["margin"] = str(temp_match["wickets"] - innings4["wickets"]) + " wicket"
                if temp_match["wickets"] - innings4["wickets"] != 1:
                    game["margin"] += "s"
            if follow_on and nbInnings == 4:
                game["margin"] = str(0 - temp_details["net_score"]) + " run"
                if temp_details["net_score"] != -1:
                    game["margin"] += "s"
        else:
            game["margin"] = "Match Tied"
    else:
        game["margin"] = "Draw"
    # Force draw if any
    if force_end == 1:
        # Draw
        game["margin"] = "Draw"
        game["winner"] = ""
    # Force double forfeit if only 1 inning played
    if nbInnings < 2:
        game["margin"] = "Double Forfeit"
        game["winner"] = ""
        game["player_of_the_match"] = ""
    if temp_match["isFinal"]:
        # Change later if required
        game["player_of_the_tournament"] = "" # manual, please refer to export_game_automated for auto-setting
    potm = get_potm(game)
    game["player_of_the_match"] = potm
    # Commentary clean up
    for i in game["innings"]:
        for i0 in i["data"]:
            for j in i0:
                s = str(j["commentary"])
                s = s.strip()
                s = " ".join([k for k in s.split(" ") if k != ""])
                j["commentary"] = s
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
