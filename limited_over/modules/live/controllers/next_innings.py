from django.http import HttpResponseRedirect
from bin.mongodb import mongoclient
from bin.models.team import Team, AbstractPlayer
from modules.exportgame.export_game import export_live_game
from modules.live_automated.controllers.lineup import fetch_lineup


def decision_next_steps(request):
    live_match = mongoclient.live_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS
    )
    live_details = live_match.find_one(1)
    if live_details["innings"] == 1:
        return live_next_innings(request)
    else:
        return export_live_game(request)  


def live_next_innings(request):
    live_match = mongoclient.live_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS
    )
    live_details = live_match.find_one(1)
    if request.method == "POST" or request.method == "GET":
        next_batting_team = live_details["bowl"]
        next_bowling_team = live_details["bat"]
        target = live_details["score"] + 1
        batting_order, bowling_order, _, _ = fetch_lineup(
            next_batting_team,
            next_bowling_team
        )
        next_batter1 = batting_order[0]
        next_batter2 = batting_order[1]
        next_bowler = bowling_order[0]
        if isinstance(next_bowler, list):
            next_bowler = str(next_bowler[0])
        live_match.update_one(
            {
                "_id": 1
            }, 
            {
                '$set': {
                    'stage': 2,
                    'innings': 2,
                    'bat': next_batting_team,
                    'bowl': next_bowling_team,
                    'batter': next_batter1,
                    'nonstriker': next_batter2,
                    'bowler': next_bowler,
                    'score': 0,
                    'wickets': 0,
                    'balls': 0,
                    'partnership': 0,
                    'partnershipflag': 0,
                    'team50flag': 0,
                    'current_ball_id': [0, 1, 0],
                    'previousPartnership': None,
                    'target': target,
                    'nextInningFlag': False
                }
            }
        )
    next_innings_chase_commentary()
    return HttpResponseRedirect("/live/")


def next_innings_chase_commentary():
    # only if it is limited overs run chase
    state = mongoclient.live_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS
    ).find_one(1)
    bat_team = Team(state["bat"])
    bowl_team = Team(state["bowl"])
    bat_name = bat_team.abstract_name()
    bowl_name = bowl_team.abstract_name()
    '''
    _, bowling_order, _, _ = fetch_lineup(
        state["bat"],
        state["bowl"]
    )
    '''
    bowl_1_name = AbstractPlayer(state["bowler"]).abstract_name()
    start_comment_data = {
        "_id": "2.start",
        "comments": [
            {
                "key": "Text",
                "value": "... THE RUN CHASE ..."
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
                    + ". Let's play..."
                )
            },
        ]
    }
    comment_collection = mongoclient.live_db_get_collection(
            mongoclient.CURRENT_INNINGS2_COMMENTARY
        )
    comment_collection.insert_one(start_comment_data)
    pass