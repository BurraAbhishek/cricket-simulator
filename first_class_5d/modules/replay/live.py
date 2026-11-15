from django.shortcuts import render
from bin.mongodb import mongoclient
from bin.models.team import Team
from bin.mongoinserts.load_games import Tournament
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS


def replayGame(request, clas="", id=""):
    if mongoclient.replay_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS2
    ).find_one(2) is not None:
        return replayGameUserInterface(request)
    tournament = Tournament()
    game = None
    if clas == "knockout":
        games = tournament.knockout()
        for i in games:
            if i["_id"] == id:
                game = i
                break
    elif clas == "groupstage":
        game = tournament.find_one(id)
    if game is None:
        return None
    loadGame(clas, game)
    return replayGameUserInterface(request)


def replayGameUserInterface(request):
    play_option_caption = str(
        "Play next ball immediately"
    )
    replay_stage = mongoclient.replay_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS1
    ).find_one(1)["replay_stage"]
    if replay_stage == 1 or replay_stage == 3:
        play_option_caption = str(
            "Load first innings commentary"
        )
    elif replay_stage == 4 or replay_stage == 6:
        play_option_caption = str(
            "Load second innings commentary"
        )
    elif replay_stage == 7 or replay_stage == 9:
        play_option_caption = str(
            "Load third innings commentary"
        )
    elif replay_stage == 10 or replay_stage == 12:
        play_option_caption = str(
            "Load fourth innings commentary"
        )
    elif replay_stage == 0:
        play_option_caption = str(
            "Replay completed"
        )
    try:
        replay_interval = int(TOURNAMENT_SETTINGS.get("replay_interval", 0))
    except ValueError:
        replay_interval = 0
    replay_automate = bool(
        replay_stage > 0
        and replay_interval > 0
    )
    return render(
        request,
        "replay_index.html",
        {
            "title": "Match Replay",
            "play_caption": play_option_caption,
            "replay_stage": replay_stage,
            "replay_interval": replay_interval,
            "replay_automate": replay_automate
        }
    )


def loadGame(clas, game):
    # Load data
    try:
        _ = game["player_of_the_tournament"]
        is_final = True
    except KeyError:
        is_final = False
    game1 = {
        "_id": 0,
        "id": game["_id"],
        "isTest": game["isTest"],
        "isKnockout": (clas == "knockout"),
        "isFinal": is_final,
        "wickets": game["wickets"],
        "team1": game["team1"],
        "team2": game["team2"],
        "toss": game["toss"],
        "target": 0,
        "nomination": game.get("nomination", {
            game["team1"]: Team(game["team1"]).nominations(),
            game["team2"]: Team(game["team2"]).nominations()
        }),
        "innings1": {
            "batting_team": game["innings"][0]["batting_team"],
            "bowling_team": game["innings"][0]["bowling_team"],
            "score": 0,
            "balls": 0,
            "wickets": 0
        },
        "innings2": {
            "batting_team": game["innings"][0]["bowling_team"],
            "bowling_team": game["innings"][0]["batting_team"],
            "score": 0,
            "balls": 0,
            "wickets": 0
        }
    }
    mongoclient.replay_db_insert_one(
        mongoclient.CURRENT_MATCH_DETAILS0,
        game1
    )
    target = 1
    if game["target"] is not None:
        target = int(game["target"])
    state = {
        "_id": 1,
        "stage": 1,
        "innings": 1,
        "bat": game["team1"],
        "bowl": game["team2"],
        "batter": None,
        "nonstriker": None,
        "bowler": None,
        "previousBowler": None,
        "previousPartnership": None,
        "score": 0,
        "wickets": 0,
        "balls": 0,
        "target": target,
        "total_balls": 6 * 450,
        "current_ball_id": [0, 1, 0],
        "replay_stage": 1,
        "declaration": [False, False, False, False],
        "follow_on_enabled": False,
        "first_batting_team": game["team1"],
        "net_score": 0,
        "over_score_bowl": 0,
        "over_bowlers": []
    }
    try:
        state["evaluation"] = game["prediction"]
    except KeyError:
        state["evaluation"] = {"white": 0.498, "draw": 0.004, "black": 0.498, "eval_verbose": "0.0"}
    mongoclient.replay_db_insert_one(
        mongoclient.CURRENT_MATCH_DETAILS1,
        state
    )
    replay = {
        "_id": 2,
        "nbInnings": 0,
        "follow_on": game["follow_on"],
        "winner": game["winner"],
        "margin": game["margin"],
        "session_data": [],
        "innings": []
    }
    for i in game["innings"]:
        replay["innings"].append(i)
        replay["nbInnings"] += 1
        replay["session_data"].append({})
    for i in game.get("sessions", []):
        if not i.get("capture_end", True):
            replay["session_data"][i["end_inning"]][i["end_ball"]] = i.get("end_comments", [])
    mongoclient.replay_db_insert_one(
        mongoclient.CURRENT_MATCH_DETAILS2,
        replay
    )
