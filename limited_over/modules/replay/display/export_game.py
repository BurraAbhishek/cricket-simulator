from bin.mongodb import mongoclient
from modules.replay.display.export_innings import export_live_innings


def fetch_live_game():
    # Match details
    temp_match_details = mongoclient.replay_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS
    ).find_one(1)
    # fetch innings
    innings = []
    innings1 = export_live_innings(1)
    innings.append(innings1)
    if temp_match_details["stage"] > 1:
        innings2 = export_live_innings(2)
        innings.append(innings2)
    # Match
    temp_match = mongoclient.replay_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS
    ).find_one(0)
    game = {
        "_id": temp_match["id"],
        "isTest": temp_match["isTest"],
        "overs": temp_match["overs"],
        "wickets": temp_match["wickets"],
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
    return game
