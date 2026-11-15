from django.http import HttpResponseRedirect
from bin.mongodb import mongoclient
from bin.mongoinserts.load_teams import TeamCollection


def live_next_innings(request):
    live_match = mongoclient.live_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS
    )
    live_details = live_match.find_one(1)
    if request.method == "POST" or request.method == "GET":
        next_batting_team = live_details["bowl"]
        next_bowling_team = live_details["bat"]
        if live_details["innings"] == 2 and live_details["follow_on_enabled"] is True:
            next_batting_team = live_details["bat"]
            next_bowling_team = live_details["bowl"]
            live_match.insert_one(
                {
                    "_id": 2,
                    "follow_on": True
                }
            )
        batter = ""
        nonstriker = ""
        bowler = ""
        if "BOT" in str(next_batting_team):
            batter = next_batting_team + "_1"
            nonstriker = next_batting_team + "_2"
        else:
            batter = next_batting_team[-1] + "1"
            nonstriker = next_batting_team[-1] + "2"
        if "BOT" in str(next_bowling_team):
            bowler: str = str(next_bowling_team) + "_1",
        else:
            bowler: str = str(str(next_bowling_team[-1]) + "1"),
        # target = live_details["score"] + 1
        live_match.update_one(
            {
                "_id": 1
            }, 
            {
                '$inc': {
                    'stage': 1,
                    'innings': 1,
                },
                '$set': {
                    'bat': next_batting_team,
                    'bowl': next_bowling_team,
                    'batter': batter,
                    'nonstriker': nonstriker,
                    'bowler': bowler[0], # just the bowler id
                    'score': 0,
                    'wickets': 0,
                    'balls': 0,
                    'partnership': 0,
                    'partnershipflag': 0,
                    'team50flag': 0,
                    'current_ball_id': [0, 1, 0],
                    'previousPartnership': None,
                    # 'target': target,
                    'nextInningFlag': False
                }
            }
        )
    next_innings_chase_commentary()
    return HttpResponseRedirect("/live/")


def next_innings_chase_commentary():
    # for test match
    team_collection = TeamCollection()
    state = mongoclient.live_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS
    ).find_one(1)
    inning_number = state["innings"]
    bat_name = team_collection.find_one(state["bat"])["name"]
    bowl_name = team_collection.find_one(state["bowl"])["name"]
    bowl_1_name = team_collection.find_one(state["bowl"])["members"][0]["name"]
    inning_text_1 = "... "
    inning_text_1 += str(bat_name).upper()
    if inning_number < 3:
        inning_text_1 += " FIRST "
    else:
        inning_text_1 += " SECOND "
    inning_text_1 += "INNINGS ..."
    start_comment_data = {
        "_id": str(inning_number) + ".start",
        "comments": [
            {
                "key": "Text",
                "value": inning_text_1
            },
            {
                "key": "Text",
                "value": str(
                    bowl_name
                    + " players are seen having a chit chat near the ropes. "
                    + "They will get into a huddle before they disperse "
                    + "and are followed by the two "
                    + bat_name
                    + " openers. "
                    + bowl_1_name
                    + " will start the proceedings with the new ball for "
                    + bowl_name
                    + ". Let's play... "
                )
            },
        ]
    }
    if inning_number == 2:
        comment_collection = mongoclient.live_db_get_collection(
                mongoclient.CURRENT_INNINGS2_COMMENTARY
            )
        comment_collection.insert_one(start_comment_data)
    elif inning_number == 3:
        comment_collection = mongoclient.live_db_get_collection(
                mongoclient.CURRENT_INNINGS3_COMMENTARY
            )
        comment_collection.insert_one(start_comment_data)
    elif inning_number == 4:
        comment_collection = mongoclient.live_db_get_collection(
                mongoclient.CURRENT_INNINGS4_COMMENTARY
            )
        comment_collection.insert_one(start_comment_data)
    pass


def test_next_inning_commentary():
    pass