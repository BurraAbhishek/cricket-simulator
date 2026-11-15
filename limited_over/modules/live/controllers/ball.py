from bin.mongodb import mongoclient, mongolivematchclient


def new_batter(batter_id):
    return {
        "_id": batter_id,
        "runs": 0,
        "balls": 0,
        "scoring": [0] * 7,
        "dismissed": False
    }


def new_bowler(bowler_id):
    return {
        "_id": bowler_id,
        "balls": 0,
        "dots": 0,
        "maidens": 0,
        "runs": 0,
        "wickets": 0
    }


def new_partnership(batter1_id, batter2_id):
    object_id = str(sorted([batter1_id, batter2_id]))
    return {
        "_id": object_id,
        "p1": batter1_id,
        "p2": batter2_id,
        "p1_runs": 0,
        "p2_runs": 0,
        "p1_balls": 0,
        "p2_balls": 0,
        "extra": 0
    }


def process_ball(data: dict):
    # batter and bowler stats
    batter_stats = mongolivematchclient.get_batter_stat()
    bowler_stats = mongolivematchclient.get_bowler_stat()
    progression = mongolivematchclient.get_past_balls()
    # Update live TV stat
    live_match = mongoclient.live_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS
    )
    live_details = live_match.find_one(1)
    # Fetch ball id
    ball_id = str(
        str(live_details["current_ball_id"][0])
        + "."
        + str(live_details["current_ball_id"][1])
        + "."
        + str(live_details["current_ball_id"][2])
    )
    # fetch progression
    progression_object = progression.find_one(ball_id)
    # Fetch players
    if data["batter"] is None or data["batter"] == "":
        current_batter = live_details["batter"]
    else:
        current_batter = data["batter"]
    if data["bowler"] is None or data["bowler"] == "":
        current_bowler = live_details["bowler"]
    else:
        current_bowler = data["bowler"]
    if data["nonstriker"] is None or data["nonstriker"] == "":
        current_nonstriker = live_details["nonstriker"]
    else:
        current_nonstriker = data["nonstriker"]
    # And prepare
    batter1_data = batter_stats.find_one(current_batter)
    if batter1_data is None:
        batter_stats.insert_one(new_batter(current_batter))
        batter1_data = batter_stats.find_one(current_batter)
    batter2_data = batter_stats.find_one(current_nonstriker)
    if batter2_data is None:
        batter_stats.insert_one(new_batter(current_nonstriker))
        batter2_data = batter_stats.find_one(current_nonstriker)
    bowler_data = bowler_stats.find_one(current_bowler)
    if bowler_data is None:
        bowler_stats.insert_one(new_bowler(current_bowler))
        bowler_data = bowler_stats.find_one(current_bowler)
    # update partnership
    partnership_collection = mongolivematchclient.get_live_partnership()
    partnership_id = str(sorted([current_batter, current_nonstriker]))
    previous_partnership_id = live_match.find_one(1)["previousPartnership"]
    partnership_object = partnership_collection.find_one(
        partnership_id
    )
    if partnership_object is None:
        if previous_partnership_id is None:
            partnership_object = new_partnership(
                current_batter,
                current_nonstriker
            )
        else:
            previous_partnership = partnership_collection.find_one(
                previous_partnership_id
            )
            if (
                previous_partnership["p2"] == current_batter
                or previous_partnership["p1"] == current_nonstriker
            ):
                partnership_object = new_partnership(
                    current_nonstriker,
                    current_batter
                )
            else:
                partnership_object = new_partnership(
                    current_batter,
                    current_nonstriker
                )
        partnership_collection.insert_one(partnership_object)
    partnership_collection = mongolivematchclient.get_live_partnership()
    partnership_object = partnership_collection.find_one(
        partnership_id
    )
    # Runs and balls
    batter_runs = int(data["score_bat"])
    batter1_data["runs"] += batter_runs
    if current_batter == partnership_object["p2"]:
        partnership_object["p2_runs"] += batter_runs
    else:
        partnership_object["p1_runs"] += batter_runs
    # Scoring
    score_int = int(data["score_int"])
    live_details["score"] += score_int
    live_details["partnership"] += score_int
    # Extra runs in partnership
    extra_runs = score_int - batter_runs
    partnership_object["extra"] += extra_runs
    # Milestones
    current_batter_runs = batter_stats.find_one(current_batter)["runs"]
    current_bat1_flag = live_details["bat50flag"][current_batter]
    bat50flags = live_details["bat50flag"]
    if current_batter_runs % 50 < 6 and (current_batter_runs // 50) > current_bat1_flag:
        bat50flags[current_batter] += 1
        progression_object["batter_50_milestone"] = current_batter_runs // 50
        live_details["bat50flag"] = bat50flags
    bowler_runs = batter_runs + data["wide"] + data["no_ball"]
    bowler_data["runs"] += bowler_runs
    current_total = live_match.find_one(1)["score"]
    current_total_flag = live_match.find_one(1)["team50flag"]
    if current_total % 50 < 6 and (current_total // 50) > current_total_flag:
        progression_object["batting_team_50_milestone"] = current_total // 50
        live_details["team50flag"] += 1
    current_stand = live_match.find_one(1)["partnership"]
    current_stand_flag = live_match.find_one(1)["partnershipflag"]
    if current_stand % 50 < 6 and (current_stand // 50) > current_stand_flag:
        progression_object["batting_stand_50_milestone"] = current_stand // 50
        live_details["partnershipflag"] += 1
    # No ball, 1 run to win. While ICC counts batter ball, we don't.
    noball_cheater = False
    if live_details["innings"] > 1:
        if live_details["target"] - live_details["score"] == 1:
            noball_cheater = True
    # Stats
    if (bowler_runs == 0) and data["legal_delivery"]:
        bowler_data["dots"] += 1
    if batter_runs >= 6:
        batter1_data["scoring"][6] += 1
    elif data["legal_delivery"] or (data["no_ball"] > 0 and not noball_cheater):
        batter1_data["scoring"][batter_runs] += 1
    # Balls faced
    if data["legal_delivery"] is True:
        batter1_data["balls"] += 1
        bowler_data["balls"] += 1
        live_details["balls"] += 1
        if current_batter == partnership_object["p2"]:
            partnership_object["p2_balls"] += 1
        else:
            partnership_object["p1_balls"] += 1
    elif data["no_ball"] > 0 and not noball_cheater:
        batter1_data["balls"] += 1
        if current_batter == partnership_object["p2"]:
            partnership_object["p2_balls"] += 1
        else:
            partnership_object["p1_balls"] += 1
    # update all batter stats
    batter_stats.update_one(
        {"_id": current_batter},
        {"$set": batter1_data}
    )
    batter_stats.update_one(
        {"_id": current_nonstriker},
        {"$set": batter2_data}
    )
    partnership_collection.update_one(
        {"_id": partnership_id},
        {"$set": partnership_object}
    )
    # What if the batter is out?
    if data["is_batter_out"] is True:
        dismissal = {
            "mode": data["dismissal"],
            "fielder": data["fielder"],
            "bowler": current_bowler
        }
        batter_stats.update_one(
            {
                "_id": data["dismissed_batter"],
            },
            {
                '$set': {
                    'dismissed': True,
                    'dismissal': dismissal
                }
            }
        )
        if (
            data["dismissal"] == "b"
            or data["dismissal"] == "c"
            or data["dismissal"] == "lbw"
            or data["dismissal"] == "st"
            or data["dismissal"] == "hitwicket"
        ):
            bowler_data["wickets"] += 1
            bowler_wickets = bowler_data["wickets"]
            progression_object["bowler_wicket_milestone"] = bowler_wickets
    # update
    if data["batter"] is not None and data["batter"] != "":
        live_details["batter"] = data["batter"]
    if data["bowler"] is not None and data["bowler"] != "":
        live_details["bowler"] = data["bowler"]
    if data["nonstriker"] is not None and data["nonstriker"] != "":
        live_details["nonstriker"] = data["nonstriker"]
    if data["dismissed_batter"] is not None and data["dismissed_batter"] != "":
        live_details["wickets"] += 1
        live_details["partnership"] = 0
        live_details["partnershipflag"] = 0
    # update progression
    progression.update_one(
        {"_id": ball_id},
        {"$set": progression_object}
    )
    # next ball
    ball_data = live_details["current_ball_id"]
    dismissal_code = ""
    runout = False
    runout0 = ["runoutbr0", "runoutkr0", "runoutb1", "runoutk1", "runoutbr2", "runoutkr2"]
    runout1 = ["runoutb0", "runoutk0", "runoutbr1", "runoutkr1", "runoutb2", "runoutk2"]
    if data.get("dismissal_code") is not None:
        dismissal_code = data["dismissal_code"]
        runout = bool(dismissal_code in runout0 or dismissal_code in runout1)
    if data["legal_delivery"]:
        ball_data[1] += 1
        ball_data[2] = 0
        if ball_data[1] == 7:
            ball_data[0] += 1
            ball_data[1] = 1
            ball_data[2] = 0
            if bool(
                (batter_runs % 2 == 0 and not runout and data["bye"] == 0 and data["leg_bye"] == 0)
                or (batter_runs == 0 and data["bye"] % 2 == 0 and data["leg_bye"] == 0)
                or (batter_runs == 0 and data["leg_bye"] % 2 == 0 and data["bye"] == 0)
                or dismissal_code in runout0
            ):
                b1 = live_details["batter"]
                b2 = live_details["nonstriker"]
                live_details["batter"] = b2
                live_details["nonstriker"] = b1
        else:
            if bool(
                (batter_runs % 2 == 1 and not runout and data["bye"] == 0 and data["leg_bye"] == 0)
                or (batter_runs == 0 and data["bye"] % 2 == 1 and data["leg_bye"] == 0)
                or (batter_runs == 0 and data["leg_bye"] % 2 == 1 and data["bye"] == 0)
                or dismissal_code in runout1
            ):
                b1 = live_details["batter"]
                b2 = live_details["nonstriker"]
                live_details["batter"] = b2
                live_details["nonstriker"] = b1
    else:
        ball_data[2] += 1
        if batter_runs % 2 == 1 or (data["wide"] > 0 and data["wide"] % 2 == 0):
            b1 = live_details["batter"]
            b2 = live_details["nonstriker"]
            live_details["batter"] = b2
            live_details["nonstriker"] = b1
    live_details["current_ball_id"] = ball_data
    live_details["previousPartnership"] = partnership_id
    # update everything
    bowler_stats.update_one(
        {"_id": current_bowler},
        {"$set": bowler_data}
    )
    live_match.update_one(
        {"_id": 1},
        {"$set": live_details}
    )
    live_details = live_match.find_one(1)
