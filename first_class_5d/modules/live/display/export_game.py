from bin.mongodb import mongoclient
from modules.exportgame.export_innings import export_live_innings


def fetch_live_game():
    # Match details
    temp_match_details = mongoclient.live_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS
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
    temp_match = mongoclient.live_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS
    ).find_one(0)
    game = {
        "_id": temp_match["id"],
        "isTest": temp_match["isTest"],
        "follow_on_threshold": 200,
        "follow_on": bool(temp_match_details["follow_on_enabled"]),
        "wickets": temp_match["wickets"],
        "team1": temp_match["team1"],
        "team2": temp_match["team2"],
        "toss": int(temp_match["toss"]),
        "innings": innings,
        "sessions": [],
        "target": temp_match_details["target"],
        "winner": "",
        "margin": "",
        "player_of_the_match": ""
    }
    '''
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
    '''
    # Export
    return game
