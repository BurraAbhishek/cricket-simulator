from django.http import HttpResponseRedirect
from bin.mongodb import mongoclient, mongoreplayclient
from modules.replay.controllers.ball import process_ball
from modules.replay.controllers.game import nextGameStage


def nextDelivery():
    live_details_collection = mongoclient.replay_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS1
    )
    live_details = live_details_collection.find_one(1)
    replay_data = mongoclient.replay_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS2
    ).find_one(2)
    innings_index = live_details["innings"] - 1
    batter_stats = replay_data["innings"][innings_index]["batter_stats"]
    innings_data = replay_data["innings"][innings_index]["data"]
    ball_over = live_details["current_ball_id"][0]
    ball_id = str(
        str(live_details["current_ball_id"][0])
        + "."
        + str(live_details["current_ball_id"][1])
        + "."
        + str(live_details["current_ball_id"][2])
    )
    ball = None
    try:
        for i in innings_data[ball_over]:
            if i["_id"] == ball_id:
                ball = i
    except IndexError:
        pass
    if ball is None:
        # Innings completed
        nextGameStage()
    else:
        ball["post_comment"] = []
        session_data = replay_data.get("session_data", [])
        if len(session_data) > 0:
            if ball_id in session_data[innings_index].keys():
                ball["post_comment"] = session_data[innings_index][ball_id]
        try:
            live_details_collection.update_one(
                    {
                        "_id": 1
                    },
                    {
                        "$set": {
                            "evaluation": ball["evaluation"]
                        }
                    }
                )
        except:
            pass
        progression = mongoreplayclient.get_past_balls()
        progression.insert_one(ball)
        process_ball(ball, batter_stats)


def nextReplayDeliveryN(n=1):
    for _ in range(n):
        nextDelivery()


def load_commentary(inning: int, position: str):
    comments = mongoreplayclient.get_mid_commentary(inning + 1)
    replay_data = mongoclient.replay_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS2
    ).find_one(2)
    replay_comments = replay_data["innings"][inning]["commentary"]
    for i in replay_comments:
        i_id = i["_id"][2:]
        if i_id == position:
            comments.insert_one(i)
    # next stage
    if position == "start":
        nextGameStage()
    elif position == "end":
        pass
        # nextGameStage()


def nextReplayDelivery(request):
    live_details_collection = mongoclient.replay_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS1
    )
    replay_details_collection = mongoclient.replay_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS2
    )
    live_details = live_details_collection.find_one(1)
    replay_stage = live_details["replay_stage"]
    if replay_stage > 0 and replay_stage % 3 == 2:
        # nextReplayDeliveryN()
        nextDelivery()
    elif replay_stage > 0 and replay_stage % 3 == 1:
        if replay_stage == 7:
            follow_on = replay_details_collection.find_one(2)["follow_on"]
            live_details_collection = mongoclient.replay_db_get_collection(
                mongoclient.CURRENT_MATCH_DETAILS0
            )
            live_details_collection.update_one(
                {
                    "_id": 0
                },
                {
                    "$set": {
                        "follow_on": bool(follow_on)
                    }
                }
            )
            live_details_collection = mongoclient.replay_db_get_collection(
                mongoclient.CURRENT_MATCH_DETAILS1
            )
            live_details_collection.update_one(
                {
                    "_id": 1
                },
                {
                    "$set": {
                        "follow_on_enabled": bool(follow_on)
                    }
                }
            )
        load_commentary(replay_stage // 3, "start")
        load_inning_data = replay_details_collection.find_one(2)["innings"]
        batting_team = load_inning_data[replay_stage // 3]["batting_team"]
        bowling_team = load_inning_data[replay_stage // 3]["bowling_team"]
        all_commentary = load_inning_data[replay_stage // 3]["commentary"]
        for i in all_commentary:
            comment_id = i["_id"][2:]
            if comment_id != "start" and comment_id != "end":
                load_commentary(replay_stage // 3, comment_id)
        live_details_collection = mongoclient.replay_db_get_collection(
            mongoclient.CURRENT_MATCH_DETAILS1
        )
        live_details_collection.update_one(
            {
                "_id": 1
            },
            {
                "$set": {
                    "current_ball_id": [0, 1, 0],
                    "score": 0,
                    "wickets": 0,
                    "balls": 0,
                    "over_score_bowl": 0,
                    "over_bowlers": [],
                    "bat": batting_team,
                    "bowl": bowling_team,
                    "previousPartnership": None
                }
            }
        )
    elif replay_stage > 0 and replay_stage % 3 == 0:
        live_details_collection = mongoclient.replay_db_get_collection(
            mongoclient.CURRENT_MATCH_DETAILS1
        )
        inning_number = ((replay_stage + 2) // 3)
        load_commentary((replay_stage // 3) - 1, "end")
        declaration = live_details["declaration"]
        replay_details_collection = mongoclient.replay_db_get_collection(
            mongoclient.CURRENT_MATCH_DETAILS2
        )
        inning_data = replay_details_collection.find_one(2)["innings"]
        for i in inning_data:
            declaration[inning_number - 1] = inning_data[inning_number - 1]["declared"]
        live_details_collection.update_one(
            {
                "_id": 1
            },
            {
                "$set": {
                    "declaration": declaration
                }
            }
        )
        nextGameStage()
    live_details_collection = mongoclient.replay_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS1
    )
    if replay_stage > 0:
        inning_number = ((replay_stage + 2) // 3)
        live_details_collection.update_one(
            {
                "_id": 1
            },
            {
                "$set": {
                    "innings": inning_number,
                    "stage": inning_number
                }
            }
        )
    return HttpResponseRedirect("/replay/")
