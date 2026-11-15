from django.http import HttpResponseRedirect
from bin.mongodb import mongoclient, mongoreplayclient
from modules.replay.controllers.ball import process_ball
from modules.replay.controllers.game import nextGameStage


def nextDelivery():
    live_details_collection = mongoclient.replay_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS
    )
    live_details = live_details_collection.find_one(1)
    replay_data = mongoclient.replay_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS
    ).find_one(2)
    batter_stats = replay_data["innings"][live_details["innings"] - 1]["batter_stats"]
    innings_data = replay_data["innings"][live_details["innings"] - 1]["data"]
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
        mongoclient.CURRENT_MATCH_DETAILS
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
        nextGameStage()


def nextReplayDelivery(request):
    live_details_collection = mongoclient.replay_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS
    )
    replay_data = mongoclient.replay_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS
    ).find_one(2)
    live_details = live_details_collection.find_one(1)
    replay_stage = live_details["replay_stage"]
    if replay_stage > 0 and replay_stage % 3 == 2:
        nextReplayDeliveryN()
    elif replay_stage > 0 and replay_stage % 3 == 1:
        load_commentary(replay_stage // 3, "start")
        live_details_collection = mongoclient.replay_db_get_collection(
            mongoclient.CURRENT_MATCH_DETAILS
        )
        all_commentary = replay_data["innings"][replay_stage // 3]["commentary"]
        for i in all_commentary:
            comment_id = i["_id"][2:]
            if comment_id != "start" and comment_id != "end":
                load_commentary(replay_stage // 3, comment_id)
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
                    "previousPartnership": None
                }
            }
        )
        live_details_collection = mongoclient.replay_db_get_collection(
            mongoclient.CURRENT_MATCH_DETAILS
        )
        if (
            not live_details_collection.find_one(0)["isTest"]
            and replay_stage == 4
        ):
            target = live_details_collection.find_one(2)["innings"][0]["score"] + 1
            live_details_collection.update_one(
                {
                    "_id": 1
                },
                {
                    "$set": {
                        "target": target,
                    }
                }
            )   
    elif replay_stage > 0 and replay_stage % 3 == 0:
        load_commentary((replay_stage // 3) - 1, "end")
    live_details_collection = mongoclient.replay_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS
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
