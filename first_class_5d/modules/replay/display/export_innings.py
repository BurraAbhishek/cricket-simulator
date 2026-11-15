from bin.mongodb import mongoclient, mongoreplayclient


def export_live_innings(inning: int):
    # fetch the collection
    live_config = mongoclient.replay_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS1
    )
    live_config.update_one(
        {
            "_id": 1
        },
        {
            "$set": {
                "innings": inning
            }
        }
    )
    batter_stats = list(mongoreplayclient.get_batter_stat().find())
    bowler_stats = list(mongoreplayclient.get_bowler_stat().find())
    data = []
    commentary = list(mongoreplayclient.get_mid_commentary().find())
    # prep data
    data_collection_list = list(mongoreplayclient.get_past_balls().find())
    over = []
    current_over_number = 1
    previous_over_number = 1
    score = 0
    wickets = 0
    balls = 0
    extras = {
        "total": 0,
        "wide": 0,
        "no_ball": 0,
        "bye": 0,
        "leg_bye": 0,
        "penalty": 0
    }
    live_config = mongoclient.replay_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS2
    )
    follow_on = bool(live_config.find_one(2)["follow_on"])
    for i in data_collection_list:
        if i["legal_delivery"]:
            balls += 1
        score += i["score_int"]
        if i["wide"] > 0:
            extras["total"] += i["wide"]
            extras["wide"] += i["wide"]
        if i["no_ball"] > 0:
            extras["total"] += i["no_ball"]
            extras["no_ball"] += i["no_ball"]
        if i["bye"] > 0:
            extras["total"] += i["bye"]
            extras["bye"] += i["bye"]
        if i["leg_bye"] > 0:
            extras["total"] += i["leg_bye"]
            extras["leg_bye"] += i["leg_bye"]
        if i["penalty"] > 0:
            extras["total"] += i["penalty"]
            extras["penalty"] += i["penalty"]
        if i["dismissed_batter"] is not None and i["dismissed_batter"] != "":
            wickets += 1
        current_over_number = i["over"]
        if previous_over_number < current_over_number:
            data.append(over)
            over = []
            previous_over_number = i["over"]
        over.append(i)
    data.append(over)
    # Batting and bowling team
    live_config = mongoclient.replay_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS0
    )
    temp_match = live_config.find_one(0)
    live_config = mongoclient.replay_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS1
    )
    live_details = live_config.find_one(1)
    batting_team = temp_match["team1"]
    bowling_team = temp_match["team2"]
    if (
        inning == 2 
        or (inning == 4 and not follow_on) 
        or (inning == 3 and follow_on)
    ):
        batting_team = temp_match["team2"]
        bowling_team = temp_match["team1"]
    # Now get innings object
    innings = {
        "batting_team": batting_team,
        "bowling_team": bowling_team,
        "score": score,
        "wickets": wickets,
        "balls": balls,
        "declared": live_details["declaration"][inning - 1],
        "data": data,
        "batter_stats": batter_stats,
        "bowler_stats": bowler_stats,
        "commentary": commentary,
        "extras": extras
    }
    # return
    return innings
