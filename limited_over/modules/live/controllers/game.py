from math import ceil
from django.shortcuts import render
from django.http import HttpResponseRedirect
from bin.mongodb import mongoclient
from bin.models.team import Team, AbstractPlayer
from bin.mongoinserts.load_games import translate_ko_id, max_groupstage_games
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS
from modules.live_automated.controllers.lineup import fetch_lineup
from modules.live.forms.game import Game


def newGame(request):

    if request.method == "POST":
        form = Game(request.POST)
        if form.is_valid():
            game = {
                "_id": 0,
                "id": form.cleaned_data["match_id"],
                # "isTest": bool(form.cleaned_data["is_test"]),
                # "isKnockout": bool(form.cleaned_data["is_knockout"]),
                # "isFinal": bool(form.cleaned_data["is_final"]),
                "isTest": False,
                "isKnockout": False,
                "isFinal": False,
                "overs": form.cleaned_data["overs"],
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
                "over_score": 0,
                "over_score_bat": 0,
                "over_score_bowl": 0,
                "over_bowlers": [],
                "free_hit": False,
                "partnership": 0,
                "previousPartnership": None,
                "bat50flag": bat_team_state,
                "hattrick_flag": bowl_team_flag,
                "partnershipflag": 0,
                "team50flag": 0,
                "target": 1,
                "total_balls": 6 * int(form.cleaned_data["overs"]),
                "current_ball_id": [0, 1, 0],
                "nextInningFlag": False
            }
            init_comments1(form.cleaned_data)
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


def init_comments1(pairing):
    match_id = pairing["match_id"]
    pairing["team1"] = pairing["team_1"]
    pairing["team2"] = pairing["team_2"]
    pairing["toss"] = int(pairing["toss"])
    try:
        if match_id[0] == "r":
            m = "Match " + match_id.split("_")[1] + ", "
            m += translate_ko_id(match_id)
        else:
            pairing["round_matches"] = max_groupstage_games() // 2
            pairing["curr_round"] = ceil(int(match_id[1:]) / pairing["round_matches"])
            m = str(
                    int(match_id[1:]) - int(
                        (pairing["curr_round"] - 1) * pairing["round_matches"]
                    )
                )
    except ValueError:
        m = translate_ko_id(match_id)
    bat = Team(pairing["team1"])
    bowl = Team(pairing["team2"])
    bat_name = bat.abstract_name()
    bowl_name = bowl.abstract_name()
    _, bowl_lineup, _, _ = fetch_lineup(pairing["team1"], pairing["team2"])
    bowl_1_name = AbstractPlayer(bowl_lineup[0]).abstract_name()
    if match_id[0] == "m":
        startcomment1 = str(
            "Welcome to Match " 
            + str(m) 
            + " of "
            + str(pairing["round_matches"])
            + " round "
            + str(pairing["curr_round"])
            + " group stage matches in this tournament."
        )
    elif match_id == "final":
        startcomment1 = str(
            "Finally, we are down to the two finalists of this tournament."
        )
    else:
        startcomment1 = str(
            "Welcome to " 
            + str(m) 
            + "."
        )
    if pairing["toss"] > 0:
        startcomment2 = str(
            "We have "
            + bat_name 
            + " facing " 
            + bowl_name 
            + "." 
        )
        if pairing["toss"] == 1:
            tosscomment = str(
                bat_name
                + " won the toss and elected to bat first."
            )
        elif pairing["toss"] == 2:
            tosscomment = str(
                bowl_name
                + " won the toss and elected to bowl first."
            )
        else:
            tosscomment = ""
        start_comment_data = {
            "_id": "1.start",
            "comments": [
                {
                    "key": "Text",
                    "value": startcomment1
                },
                {
                    "key": "Text",
                    "value": startcomment2
                },
                {
                    "key": "Text",
                    "value": "... TOSS ..."
                },
                {
                    "key": "Text",
                    "value": tosscomment
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
                        + ". Let's play..."
                    )
                },
            ]
        }
    else:
        if match_id[0] == "m" and TOURNAMENT_SETTINGS.get("bot_group", True):
            if bowl.ai() and not bat.ai():
                startcomment2 = str(
                        "We have " 
                        + bat_name
                        + " facing " 
                        + bowl_name
                        + ". As per the rules, " 
                        + bat_name
                        + " will bat first in this entire round."
                    )
            elif bat.ai() and not bowl.ai():
                startcomment2 = str(
                        "We have " 
                        + bat_name 
                        + " facing " 
                        + bowl_name 
                        + ". As per the rules, " 
                        + bowl_name 
                        + " will bowl first in this entire round."
                    )
            else:
                startcomment2 = str(
                    "We have " 
                    + bat_name 
                    + " facing " 
                    + bowl_name 
                    + ". As per the rules, " 
                    + bat_name
                    + " will bat first and "
                    + bowl_name 
                    + " will bowl first."
                )
        else:
            startcomment2 = str(
                    "We have " 
                    + bat_name 
                    + " facing " 
                    + bowl_name 
                    + ". As per the rules, " 
                    + bat_name
                    + " will bat first and "
                    + bowl_name 
                    + " will bowl first."
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
                    "value": startcomment2
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
                        + ". Let's play..."
                    )
                },
            ]
        }
    comment_collection = mongoclient.live_db_get_collection(
            mongoclient.CURRENT_INNINGS1_COMMENTARY
        )
    comment_collection.insert_one(start_comment_data)
