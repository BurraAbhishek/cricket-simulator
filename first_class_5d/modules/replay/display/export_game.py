from bin.mongodb import mongoclient
from modules.replay.display.export_innings import export_live_innings


def fetch_live_game():
    # Match details
    temp_match_details = mongoclient.replay_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS1
    ).find_one(1)
    # fetch innings
    innings = []
    innings1 = export_live_innings(1)
    innings.append(innings1)
    if temp_match_details["stage"] > 1:
        innings2 = export_live_innings(2)
        innings.append(innings2)
    if temp_match_details["stage"] > 2:
        innings3 = export_live_innings(3)
        innings.append(innings3)
    if temp_match_details["stage"] > 3:
        innings4 = export_live_innings(4)
        innings.append(innings4)
    # Match
    temp_match = mongoclient.replay_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS0
    ).find_one(0)
    game = {
        "_id": temp_match["id"],
        "isTest": temp_match["isTest"],
        "wickets": temp_match["wickets"],
        "follow_on": temp_match_details["follow_on_enabled"],
        "team1": temp_match["team1"],
        "team2": temp_match["team2"],
        "toss": temp_match["toss"],
        "nomination": temp_match["nomination"],
        "innings": innings,
        "target": innings1["score"] + 1,
        "winner": "",
        "margin": "",
        "player_of_the_match": ""
    }
    if temp_match_details.get("replay_stage") == 0:
        try:
            temp_result = mongoclient.replay_db_get_collection(
                mongoclient.CURRENT_MATCH_DETAILS2
            ).find_one(2)
            game["winner"] = temp_result["winner"]
            game["margin"] = temp_result["margin"]
        except KeyError:
            nbInnings = len(innings)
            follow_on = temp_match_details["follow_on_enabled"]
            if nbInnings > 2:
                if temp_match_details["net_score"] > 0:
                    if nbInnings == 3:
                        game["margin"] = "an innings and "
                    else:
                        game["margin"] = ""
                    game["winner"] = temp_match["team1"]
                    game["margin"] += str(temp_match_details["net_score"]) + " run"
                    if temp_match_details["net_score"] != 1:
                        game["margin"] += "s"
                    if follow_on and nbInnings == 4:
                        game["margin"] = str(temp_match["wickets"] - innings4["wickets"]) + " wicket"
                        if temp_match["wickets"] - innings4["wickets"] != 1:
                            game["margin"] += "s"
                elif temp_match_details["net_score"] < 0:
                    game["winner"] = temp_match["team2"]
                    if nbInnings == 3:
                        game["margin"] = "an innings and "
                        game["margin"] += str(0 - temp_match_details["net_score"]) + " run"
                        if temp_match_details["net_score"] != -1:
                            game["margin"] += "s"
                    else:
                        game["margin"] = str(temp_match["wickets"] - innings4["wickets"]) + " wicket"
                        if temp_match["wickets"] - innings4["wickets"] != 1:
                            game["margin"] += "s"
                    if follow_on and nbInnings == 4:
                        game["margin"] = str(0 - temp_match_details["net_score"]) + " run"
                        if temp_match_details["net_score"] != -1:
                            game["margin"] += "s"
                else:
                    game["margin"] = "Match Tied"
            else:
                game["margin"] = "Draw"
    # Export
    return game
