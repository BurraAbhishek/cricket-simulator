from bin.mongodb import mongoclient
from bin.models.team import Team, AbstractPlayer
from bin.mongoinserts.load_games import translate_ko_id
from modules.live.controllers.innings_automate_game import nextDeliveryAutomated
from modules.live.controllers.lineup import fetch_opening_bowler


def newGame(request, pairing):
    game = {
        "_id": 0,
        "id": pairing["match_id"],
        "isTest": True,
        "isKnockout": False,
        "isFinal": False,
        "wickets": 10,
        "team1": pairing["team1"],
        "team2": pairing["team2"],
        "toss": int(pairing["toss"]),
        "target": 0,
        "innings1": {
            "batting_team": pairing["team1"],
            "bowling_team": pairing["team2"],
            "score": 0,
            "balls": 0,
            "wickets": 0
        },
        "innings2": {
            "batting_team": pairing["team2"],
            "bowling_team": pairing["team1"],
            "score": 0,
            "balls": 0,
            "wickets": 0
        },
        "innings3": {
            "batting_team": pairing["team1"],
            "bowling_team": pairing["team2"],
            "score": 0,
            "balls": 0,
            "wickets": 0
        },
        "innings4": {
            "batting_team": pairing["team2"],
            "bowling_team": pairing["team1"],
            "score": 0,
            "balls": 0,
            "wickets": 0
        },
        "nominations": {
            pairing["team1"]: pairing["nom1"],
            pairing["team2"]: pairing["nom2"]
        }
    }
    mongoclient.live_db_insert_one(
        mongoclient.CURRENT_MATCH_DETAILS,
        game
    )
    batting_team_list = list(Team(pairing["team1"]).find())
    bowling_team_list = list(Team(pairing["team2"]).find())
    bat_team_state = {}
    bowl_team_flag = {}
    for i in batting_team_list:
        bat_team_state[i["_id"]] = 0
        bowl_team_flag[i["_id"]] = 0
    for i in bowling_team_list:
        bat_team_state[i["_id"]] = 0
        bowl_team_flag[i["_id"]] = 0
    state = {
        "_id": 1,
        "stage": 1,
        "innings": 1,
        "bat": pairing["team1"],
        "bowl": pairing["team2"],
        "batter": None,
        "nonstriker": None,
        "bowler": None,
        "previousBowler": None,
        "score": 0,
        "wickets": 0,
        "balls": 0,
        "net_score": 0,
        "partnership": 0,
        "previousPartnership": None,
        "bat50flag": bat_team_state,
        "hattrick_flag": bowl_team_flag,
        "partnershipflag": 0,
        "team50flag": 0,
        "target": 1,
        "total_balls": 2700,
        "all_session_balls": 0,
        "current_session": 1,
        "current_ball_id": [0, 1, 0],
        "all_scores": [0, 0, 0, 0],
        "declaration": [False, False, False, False],
        "follow_on_enabled": False,
        "nextInningFlag": False,
        "first_batting_team": pairing["team1"],
        "net_score": 0,
        "over_score": 0,
        "over_wicket": 0,
        "over_sixes": 0,
        "over_score_bat": 0,
        "over_score_bowl": 0,
        "over_bowlers": [],
        "free_hit": False
    }
    
    init_comments(
        state,
        str(pairing["match_id"]),
        int(pairing["toss"])
        )
    mongoclient.live_db_insert_one(
        mongoclient.CURRENT_MATCH_DETAILS,
        state
    )
    return nextDeliveryAutomated(request)


def init_comments(state, match_id, toss):
    if match_id[0] == "r":
        m = "Match " + match_id.split("_")[1] + ", "
        m += translate_ko_id(match_id)
    elif match_id[0] == "m":
        match_id_parts = match_id.split("_")
        m = str(
            "Match "
            + str(int(match_id_parts[2]))
            + " of Week "
            + str(int(match_id_parts[1]))
            + " Group Stage matches in this tournament"
        )
    else:
        m = translate_ko_id(match_id)
    bat = Team(state["bat"])
    bowl = Team(state["bowl"])
    bat_name = bat.abstract_name()
    bowl_name = bowl.abstract_name()
    opening_bowler = fetch_opening_bowler(state["bowl"], state["bat"])
    bowl_1_name = AbstractPlayer(opening_bowler).abstract_name()
    toss_string = ""
    if toss == 1:
        toss_string = bat_name + " won the toss and elected to bat first."
    elif toss == 2:
        toss_string = bowl_name + " won the toss and elected to bowl first."
    else:
        toss_string = str(
            "As per the rules, "
            + bat_name
            + " must bat first and "
            + bowl_name
            + " must bowl first."
        )
    if match_id == "final":
        startcomment1 = str(
            "Finally, we are down to the two finalists of this tournament."
        )
    else:
        startcomment1 = str(
            "Welcome to " 
            + str(m) 
            + "."
        )
    start_comment_data = {
        "_id": "1.start",
        "comments": [
            {
                "key": "Text",
                "value": startcomment1
            },
            {
                "key": "Text",
                "value": str(
                    "We have " 
                    + bat_name 
                    + " facing " 
                    + bowl_name
                    + "."
                )
            },
            {
                "key": "Text",
                "value": "... TOSS ..."
            },
            {
                "key": "Text",
                "value": toss_string
            },
            {
                "key": "Text",
                "value": "... MATCH ..."
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
    comment_collection = mongoclient.live_db_get_collection(
            mongoclient.CURRENT_INNINGS1_COMMENTARY
        )
    comment_collection.insert_one(start_comment_data)
