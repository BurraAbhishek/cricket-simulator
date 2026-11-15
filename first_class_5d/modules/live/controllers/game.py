from django.shortcuts import render
from django.http import HttpResponseRedirect
from bin.mongodb import mongoclient
from bin.models.team import Team, AbstractPlayer
from bin.mongoinserts.load_games import translate_ko_id
from modules.live.forms.game import Game
from modules.live.controllers.lineup import fetch_opening_bowler


def newGame(request):

    if request.method == "POST":
        form = Game(request.POST)
        if form.is_valid():
            game = {
                "_id": 0,
                "id": form.cleaned_data["match_ID"],
                "isTest": True,
                "isKnockout": False,
                "isFinal": False,
                "wickets": int(form.cleaned_data["wickets"]),
                "team1": form.cleaned_data["team_1"],
                "team2": form.cleaned_data["team_2"],
                "toss": int(form.cleaned_data["toss"]),
                "target": 0,
                "innings1": {
                    "batting_team": form.cleaned_data["team_1"],
                    "bowling_team": form.cleaned_data["team_2"],
                    "score": 0,
                    "balls": 0,
                    "wickets": 0
                },
                "innings2": {
                    "batting_team": form.cleaned_data["team_2"],
                    "bowling_team": form.cleaned_data["team_1"],
                    "score": 0,
                    "balls": 0,
                    "wickets": 0
                },
                "innings3": {
                    "batting_team": form.cleaned_data["team_1"],
                    "bowling_team": form.cleaned_data["team_2"],
                    "score": 0,
                    "balls": 0,
                    "wickets": 0
                },
                "innings4": {
                    "batting_team": form.cleaned_data["team_2"],
                    "bowling_team": form.cleaned_data["team_1"],
                    "score": 0,
                    "balls": 0,
                    "wickets": 0
                }
            }
            mongoclient.live_db_insert_one(
                mongoclient.CURRENT_MATCH_DETAILS,
                game
            )
            batting_team_list = list(Team(form.cleaned_data["team_1"]).find())
            bowling_team_list = list(Team(form.cleaned_data["team_2"]).find())
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
                "bat": form.cleaned_data["team_1"],
                "bowl": form.cleaned_data["team_2"],
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
                "first_batting_team": form.cleaned_data["team_1"],
                "net_score": 0,
                "over_score": 0,
                "over_wicket": 0,
                "over_sixes": 0,
                "over_score_bat": 0,
                "over_score_bowl": 0,
                "over_bowlers": [],
                "free_hit": False,
            }
            
            init_comments(
                state,
                str(form.cleaned_data["match_ID"]),
                int(form.cleaned_data["toss"])
                )
            mongoclient.live_db_insert_one(
                mongoclient.CURRENT_MATCH_DETAILS,
                state
            )
            return HttpResponseRedirect("/live/")
    else:
        return render(
            request,
            "live_new.html",
            {
                "title": "New Match",
                "form": Game(),
            }
        )


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
    opening_bowler = fetch_opening_bowler(state["bowl"])
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
