import random
from django.shortcuts import render
from django.http import HttpResponseRedirect
from bin.mongodb import mongoclient, mongolivematchclient
from bin.models.team import Team, AbstractPlayer
from modules.live.forms.innings import Innings
from modules.live.controllers.ball import process_ball
from modules.live.controllers.commentary_data_teamwise import fetch_commentary_data_teamwise
from modules.live.controllers.lineup import fetch_lineup, fetch_opening_bowler
from modules.live.controllers.scorer import fetch_scorer
from modules.live.controllers.dismissal import fetch_dismissal_type
from modules.live.controllers.declare_automate import can_declare
from modules.exportgame.paginator import get_innings_dataset, get_sessions_dataset
from modules.exportgame.export_game import export_live_game


balls_to_automate_one_call = 2700
automate_declaration = True


def is_it_out_threshold(threshold):
    multiplier = 3
    variate = 1
    for _ in range(multiplier):
        variate = variate * random.random()
    return variate > threshold


def is_it_extra(extra: dict, score_bat: int=0):
    multiplier = 3
    variate = 1
    for _ in range(multiplier):
        variate = variate * random.random()
    variate = 1 - variate
    # Limit extras to prevent endless matches
    u_limit = 0.5
    # Hold extras
    extras = []
    # Priority: No ball > wide > bye > leg bye > penalty
    # All teams bowl a mix.
    if variate < min(extra.get("no_ball", 0), u_limit):
        if score_bat >= 6:
            return "no_ball"
        extras.append("no_ball")
    # Only 6nb is allowed. No other extra with sixes
    if score_bat >= 6:
        return None
    # Wide
    if variate < min(extra.get("wide", 0), u_limit):
        extras.append("wide")
    # this is a batter thing.
    if bool(
        variate < min(extra.get("bye", 0), u_limit) 
        and score_bat in [1, 2, 3, 4]
    ):
        extras += ["bye", "leg_bye"]
    if variate < min(extra.get("penalty", 0), u_limit):
        extras.append("penalty")
    if len(extras) < 1:
        return None
    else:
        return random.choice(extras)


def nextDeliveryAutomated(request):
    live_match = mongoclient.live_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS
    )
    live_details = live_match.find_one(1)
    BAT_TEAM = live_details["bat"]
    BOWL_TEAM = live_details["bowl"]
    BATTING_ORDER, _, _, _ = fetch_lineup(
        BAT_TEAM, BOWL_TEAM
    )
    if request.method == 'POST':
        if live_details["batter"] is None:
            live_match.update_one(
                {
                    "_id": 1
                },
                {
                    "$set": {
                        "batter": BATTING_ORDER[0],
                        "nonstriker": BATTING_ORDER[1]
                    }
                }
            )
        return nextDeliveryAutomatedSequence(request)
    else:
        return render(
            request,
            "live_inning.html",
            {
                "title": "New Match",
                "form": Innings(),
                "current_over": live_details["current_ball_id"][0],
                "current_ball": live_details["current_ball_id"][1],
                "next_inning": live_details["nextInningFlag"]
            }
        )


def nextDeliveryAutomatedSequence(request):
    for _ in range(balls_to_automate_one_call):
        live_match = mongoclient.live_db_get_collection(
            mongoclient.CURRENT_MATCH_DETAILS
        )
        live_details = live_match.find_one(1)
        bat_team = live_details["bat"]
        bowl_team = live_details["bowl"]
        BATTING_ORDER, BOWLING_ORDER, FIELDING_ORDER, WICKETKEEPER = fetch_lineup(
            bat_team, bowl_team
        )
        cleaned_data = {}
        if int(live_details["current_ball_id"][1]) < 2 and int(live_details["current_ball_id"][2]) == 0:
            live_match.update_one(
                {
                    "_id": 1
                },
                {
                    "$set": {
                        "over_sixes": 0,
                        "over_score": 0,
                        "over_score_bat": 0,
                        "over_score_bowl": 0,
                        "over_bowlers": []
                    }
                }
            )
        nb_bowlers = len(BOWLING_ORDER)
        current_bowler = BOWLING_ORDER[int(live_details["current_ball_id"][0]) % nb_bowlers]
        # What if the keeper is bowling
        if current_bowler == WICKETKEEPER:
            potential_keepers = []
            for i in Team(bowl_team).members():
                if i["wicketkeeper"] is True and i["_id"] != current_bowler:
                    potential_keepers.append(i["_id"])
            if len(potential_keepers) > 0:
                WICKETKEEPER = random.choice(potential_keepers)
            else:
                WICKETKEEPER = random.choice([i for i in FIELDING_ORDER if i != current_bowler])
        # end
        bat_parent = AbstractPlayer(live_details["batter"]).parent_team_name()
        bowl_parent = AbstractPlayer(current_bowler).parent_team_name()
        batter_score_options, b_w_threshold, extra = (
            fetch_scorer(
                live_details["batter"], 
                live_details["nonstriker"],
                current_bowler,
                live_details["current_ball_id"][0]
            )
        )
        score_bat = random.choice(batter_score_options)
        extra_processed = is_it_extra(extra, score_bat)
        wide = 0
        no_ball = 0
        bye = 0
        leg_bye = 0
        penalty = 0
        score = str(score_bat)
        # Wicket
        is_the_batter_out = is_it_out_threshold(b_w_threshold)
        if is_the_batter_out:
            wicket_type = random.choice(
                fetch_dismissal_type(
                    live_details["bat"],
                    live_details["bowl"],
                    live_details["batter"],
                    current_bowler,
                    live_details["nonstriker"],
                    AbstractPlayer(live_details["batter"]).get("rating_bat", 1800),
                    AbstractPlayer(current_bowler).get("rating_bowl", 1800)
                )
            )
            if wicket_type == "timeout" and live_details["current_ball_id"] != "0.1.0":
                # Only valid for first ball.
                # If not, let the batter be out bowled
                batter_stats = mongolivematchclient.get_batter_stat()
                if batter_stats.find_one(live_details["batter"]) is not None:
                    # Can't time them out now!
                    wicket_type = "b"
            dismissal_code = wicket_type
            if dismissal_code == "cw" or dismissal_code == "cb":
                wicket_type = "c"
            if dismissal_code in ["runoutb0", "runoutk0", "runoutb1", "runoutk1", "runoutb2", "runoutk2"]:
                wicket_type = "runout"
            if dismissal_code in ["runoutbr0", "runoutkr0", "runoutbr1", "runoutkr1", "runoutbr2", "runoutkr2"]:
                wicket_type = "runout"
            if live_details["free_hit"] is True:
                if wicket_type not in ["runout", "obstructing", "hittheballtwice"]:
                    is_the_batter_out = False
            if not is_the_batter_out:
                del wicket_type
                del dismissal_code
        # Extras
        if extra_processed is not None:
            if extra_processed == "no_ball":
                if live_details["free_hit"] is True:
                    # For safety, no consecutive no-balls
                    no_ball = 0
                    extra_processed = None
                else:
                    no_ball = 1
                    score += "nb"
                    live_match.update_one(
                        {
                            "_id": 1
                        },
                        {
                            "$set": {
                                "free_hit": True
                            }
                        }
                    )
                    live_details = live_match.find_one(1)
            elif extra_processed == "wide":
                wide = min(1 + score_bat, 5)
                if wide < 5 and not extra.get("run_in_wide", True):
                    wide = 1
                score_bat = 0
                score = str(wide - 1) + "wd"
            elif extra_processed == "bye":
                bye = min(score_bat, 4)
                score_bat = 0
                score = str(bye) + "b"
            elif extra_processed == "leg_bye":
                leg_bye = min(score_bat, 4)
                score_bat = 0
                score = str(leg_bye) + "lb"
            elif extra_processed == "penalty":
                # batting side awarded 5 penalty runs
                penalty = 5
                score_bat = 0
                score = "pen"
            if is_the_batter_out:
                is_the_batter_out = False
                del wicket_type
                del dismissal_code
        score_bowler = score_bat + wide + no_ball
        score_int = score_bowler + bye + leg_bye + penalty
        legal_ball = True
        if wide > 0 or no_ball > 0 or penalty > 0:
            legal_ball = False
        if legal_ball and live_details["free_hit"] is True:
            live_match.update_one(
                {
                    "_id": 1
                },
                {
                    "$set": {
                        "free_hit": False
                    }
                }
            )
        if is_the_batter_out:
            # Except if run out.
            score_bat = 0
            score_int = 0
            if dismissal_code in ["runoutb1", "runoutk1", "runoutbr1", "runoutkr1"]:
                score_bat = 1
                score_int = 1
            if dismissal_code in ["runoutb2", "runoutk2", "runoutbr2", "runoutkr2"]:
                score_bat = 2
                score_int = 2
            if wicket_type in ["timeout", "retired"]:
                legal_ball = False
        # is the game already completed?
        chasing = bool(live_details["innings"] > 3)
        if chasing:
            to_win = live_details["target"] - live_details["score"]
            if to_win < 3 and to_win > 0:
                if to_win == 1:
                    if no_ball > 0:
                        no_ball = 1
                        score_bat = 0
                        score_int = 0
                        score = "0nb"
                    elif wide > 0 and wide < 5:
                        wide = 1
                        score = "0wd"
                    elif bye == 2 or bye == 3:
                        bye = 1
                        score = "1b"
                    elif leg_bye == 2 or leg_bye == 3:
                        leg_bye = 1
                        score = "1lb"
                    elif score_bat == 1 or score_bat == 2 or score_bat == 3:
                        score_bat = 1
                        score = "1"
                        if is_the_batter_out:
                            is_the_batter_out = False
                            del wicket_type
                            del dismissal_code
                if to_win == 2:
                    if no_ball > 0:
                        no_ball = 1
                        if score_bat == 2 or score_bat == 3:
                            score_bat = 1
                        score = str(score_bat) + "nb"
                    elif wide > 1 and wide < 5:
                        wide = 2
                        score = "1wd"
                    elif bye == 3:
                        bye = 2
                        score = "2b"
                    elif leg_bye == 3:
                        leg_bye = 2
                        score = "2lb"
                    elif score_bat == 2 or score_bat == 3:
                        score_bat = 2
                        score = "2"
                        if is_the_batter_out:
                            is_the_batter_out = False
                            del wicket_type
                            del dismissal_code        
                score_bowler = score_bat + wide + no_ball
                score_int = score_bowler + bye + leg_bye + penalty
        # continue
        cleaned_data = {
            "legal_delivery": legal_ball,
            "bowler": current_bowler,
            "batter": live_details["batter"],
            "nonstriker": live_details["nonstriker"],
            "score_bat": score_bat,
            "score_int": score_int,
            "is_batter_out": False,
            "dismissed_batter": "",
            "dismissal": "",
            "fielder": "",
            "dismissal_code": str(dismissal_code if is_the_batter_out else ""),
            "wide": wide,
            "no_ball": no_ball,
            "bye": bye,
            "leg_bye": leg_bye,
            "penalty": penalty,
            "commentary": ""
        }
        ball_id = str(
            str(live_details["current_ball_id"][0])
            + "."
            + str(live_details["current_ball_id"][1])
            + "."
            + str(live_details["current_ball_id"][2])
        )
        live_details = live_match.find_one(1)
        if int(live_details["wickets"]) >= 10:
            return decision_next_steps(request)
        if int(live_details["innings"]) > 3:
            if int(live_details["score"]) >= int(live_details["target"]):
                return decision_next_steps(request)
        if (
            (
                int(live_details["all_session_balls"]) 
                + int(live_details["balls"]) 
                >= int(live_details["total_balls"])
            ) and (
                int(live_details["current_ball_id"][1]) == 1
            )
        ):
            game_timeout = True
            inning_dataset = get_innings_dataset(live_details["innings"])
            session_dataset = get_sessions_dataset(inning_dataset)
            ds2 = 0
            ds0 = 0
            if session_dataset[-1][3] < 14:
                game_timeout = False
            else:
                for ds1 in reversed(session_dataset):
                    if ds1[8]:
                        ds0 += 1
                    if ds1[3] < 14:
                        if ds0 < 180:
                            ds2 = 180 - ds0
                            game_timeout = False
                        break
            ds0 = 0
            for ds1 in reversed(session_dataset):
                if ds1[8]:
                    ds0 += 1
                if ds1[3] < 12:
                    if ds0 < 540:
                        ds2 = max(0, max(540 - ds0, ds2) - ((14 - int(session_dataset[-1][3])) * 180))
                        game_timeout = False
                    break        
            if game_timeout:
                # Only 1 inning - forfeit
                if int(live_details["innings"]) == 1:
                    return export_live_game(request, force_end=-1)
                # Game Over
                return export_live_game(request, force_end=1)
            else:
                live_details["total_balls"] += int(
                    (14 - int(session_dataset[-1][3])) * 180
                    + ds2
                )
        # Declaration flag
        try:
            ref_score = max(live_details["all_scores"])
            batter_stats = mongolivematchclient.get_batter_stat()
            if automate_declaration is True:
                declaration_flag = can_declare(
                    live_details["bat"],
                    live_details["bowl"],
                    live_details["first_batting_team"],
                    live_details["score"],
                    live_details["balls"],
                    live_details["wickets"],
                    batter_stats.find_one(live_details["batter"])["runs"],
                    batter_stats.find_one(live_details["nonstriker"])["runs"],
                    False,
                    live_details["net_score"],
                    ref_score,
                    Team(live_details["bat"]).aggression_rating(),
                    AbstractPlayer(current_bowler).get("rating_bowl", 1800)
                )
            else:
                declaration_flag = False
            if declaration_flag:
                i1 = int(live_details["innings"]) - 1
                declaration_status = live_details["declaration"]
                declaration_status[i1] = True
                live_match.update_one(
                    {
                        "_id": 1
                    },
                    {
                        "$set": {
                            "declaration": declaration_status
                        }
                    }
                )
        except TypeError:
            pass
        # continue
        i1 = int(live_details["innings"]) - 1
        declaration_status = live_details["declaration"]
        if declaration_status[i1] is True:
            return decision_next_steps(request)
        current_batter = live_details["batter"]
        current_nonstriker = live_details["nonstriker"]
        bowler_name = AbstractPlayer(current_bowler).abstract_name()
        batter_name = AbstractPlayer(current_batter).abstract_name()
        # out
        if is_the_batter_out:
            score = "W"
            if score_int > 0:
                score = str(score_int) + "+W"
            if dismissal_code in ["b", "cb", "lbw", "hitwicket", "hittheballtwice"]:
                cleaned_data["fielder"] = current_bowler
            elif dismissal_code == "st" or dismissal_code == "cw":
                cleaned_data["fielder"] = WICKETKEEPER
            elif wicket_type == "timeout" or wicket_type == "retired":
                cleaned_data["fielder"] = Team(bowl_team).get("captain")
            else:
                cleaned_data["fielder"] = random.choice(
                    [i for i in FIELDING_ORDER if i != current_bowler and i != WICKETKEEPER]
                )
            cleaned_data["is_batter_out"] = True
            cleaned_data["dismissed_batter"] = current_batter
            if wicket_type == "runout":
                if dismissal_code in ["runoutk0", "runoutb1", "runoutk2"]:
                    cleaned_data["dismissed_batter"] = current_nonstriker
            cleaned_data["dismissal"] = wicket_type
        # over score
        live_match.update_one(
            {
                "_id": 1
            },
            {
                "$inc": {
                    "over_score": cleaned_data["score_int"],
                    "over_score_bat": cleaned_data["score_bat"],
                    "over_score_bowl": cleaned_data["score_bat"] + wide + no_ball,
                    "over_sixes": int(1 if cleaned_data["score_bat"] >= 6 else 0)
                }
            }
        )
        # commentary
        commentary = ""
        commentary += bowler_name
        commentary += " to "
        commentary += batter_name
        hattrick_comment = ""
        if is_the_batter_out and cleaned_data["dismissal"] in ["b", "c", "lbw", "st", "hitwicket"]:
            live_details["hattrick_flag"][current_bowler] += 1
        else:
            live_details["hattrick_flag"][current_bowler] = 0
        live_match.update_one(
            {"_id": 1}, 
            {"$set": {"hattrick_flag": live_details["hattrick_flag"]}}
        )
        if live_details["hattrick_flag"][current_bowler] == 3:
            hattrick_comment = "HAT-TRICK! "
        if live_details["hattrick_flag"][current_bowler] == 6:
            hattrick_comment = "BACK-TO-BACK HAT-TRICKS! "
        if is_the_batter_out:
            if cleaned_data["dismissal"] == "lbw":
                commentary += ", OUT LBW! " + hattrick_comment + fetch_commentary_data_teamwise(
                        "lbw",
                        current_batter,
                        current_bowler
                    )
            elif cleaned_data["dismissal"] == "b":
                # Full speed crash
                commentary += ", OUT! BOWLED! " + hattrick_comment + fetch_commentary_data_teamwise(
                        "b",
                        current_batter,
                        current_bowler,
                        WICKETKEEPER
                    )
            elif cleaned_data["dismissal"] == "st":
                commentary += ", OUT! Stumped! " + hattrick_comment + fetch_commentary_data_teamwise(
                        "st",
                        current_batter,
                        current_bowler,
                        WICKETKEEPER
                    )
            elif cleaned_data["dismissal"] == "c":
                if cleaned_data["fielder"] == current_bowler:
                    commentary += ", OUT! CAUGHT AND BOWLED! " + hattrick_comment + fetch_commentary_data_teamwise(
                            "cb",
                            current_batter,
                            current_bowler
                        )
                elif cleaned_data["fielder"] == WICKETKEEPER:
                    commentary += ", OUT! CAUGHT BEHIND! " + hattrick_comment + fetch_commentary_data_teamwise(
                            "cw",
                            current_batter,
                            current_bowler,
                            WICKETKEEPER
                        )
                else:
                    commentary += ", OUT! TAKEN! " + hattrick_comment + fetch_commentary_data_teamwise(
                            "c",
                            current_batter,
                            current_bowler,
                            cleaned_data["fielder"]
                        )
            elif cleaned_data["dismissal"] == "hitwicket":
                commentary += ", OUT! HIT WICKET! " + hattrick_comment + fetch_commentary_data_teamwise(
                        "hitwicket",
                        current_batter,
                        current_bowler
                    )
            elif cleaned_data["dismissal"] == "runout":
                commentary += ", OUT! RUN OUT! " + fetch_commentary_data_teamwise(
                        dismissal_code,
                        cleaned_data["dismissed_batter"],
                        current_bowler,
                        cleaned_data["fielder"]
                    )
            elif cleaned_data["dismissal"] in ["hittheballtwice", "obstructing"]:
                commentary += ", OUT! " + fetch_commentary_data_teamwise(
                        dismissal_code,
                        current_batter,
                        current_bowler
                    )
            elif cleaned_data["dismissal"] == "retired":
                commentary = str(
                    batter_name 
                    + " is retired out! "
                    + " The batter leaves the playing field"
                    + " without authorization. Subsequently,"
                    + " the batter is dismissed."
                )
            elif cleaned_data["dismissal"] == "timeout":
                commentary = str(
                    batter_name 
                    + " is timed out! "
                    + " The batter is not ready to face the ball"
                    + " within the duration permitted under the"
                    + " tournament playing conditions. Subsequently, the"
                    + " fielding captain appeals for timed out and"
                    + " the batter is dismissed."
                )
            else:
                commentary += ", OUT! " + cleaned_data["dismissal"] + " " + cleaned_data["fielder"]
        elif score == "0" or score == "0nb":
            commentary += ", NO RUN. "
        elif score == "1" or score == "1nb":
            commentary += ", ONE RUN. "
        elif score == "2" or score == "2nb":
            commentary += ", TWO RUNS. "
        elif score == "3" or score == "3nb":
            commentary += ", THREE RUNS. "
        elif score == "4" or score == "4nb":
            commentary += ", FOUR! "
        elif score == "5" or score == "5nb":
            commentary += ", FIVE RUNS! "
        elif score == "6" or score == "6nb":
            commentary += ", SIX! "
        else:
            commentary += ", "
        over_bowlers = live_details["over_bowlers"]
        over_bowlers.append(current_bowler)
        live_match.update_one(
                {
                    "_id": 1
                },
                {
                    "$set": {
                        "over_bowlers": over_bowlers
                    }
                }
            )
        live_details = live_match.find_one(1)
        over_sixes = live_details["over_sixes"]
        if over_sixes == 6:
            commentary += "SIX SIXES IN THIS OVER"
            if int(live_details["current_ball_id"][1]) > 5:
                commentary += "! "
            else:
                commentary += " ALREADY! "
        if int(live_details["current_ball_id"][1]) > 5:
            over_score_bowl = live_details["over_score_bowl"]
            if over_bowlers is None:
                over_bowlers = []
            one_bowler = bool(len(set(over_bowlers)) < 2)
            if over_score_bowl < 1 and legal_ball and one_bowler:
                if score == "W":
                    commentary += " "
                commentary += "A maiden over for the bowler. "
                bowler_stats = mongolivematchclient.get_bowler_stat()
                bowler_stats.update_one(
                    {"_id": current_bowler},
                    {"$inc": {
                        "maidens": 1
                    }}
                )
        batter_stats = mongolivematchclient.get_batter_stat()
        current_batter_collection = batter_stats.find_one(current_batter)
        if current_batter_collection is not None:
            current_batter_runs = current_batter_collection["runs"]
            current_batter_runs += int(score_bat)
            current_bat1_flag = live_details["bat50flag"][current_batter]
            batter50flag = bool(
                current_batter_runs % 50 < 6 
                and (current_batter_runs // 50) > current_bat1_flag
            )
            batter50 = 50 * (current_batter_runs // 50)
        current_total = live_details["score"] + int(score_int)
        current_total_flag = live_details["team50flag"]
        team50flag = bool(
            current_total % 50 < 6 
            and (current_total // 50) > current_total_flag
        )
        team50 = 50 * (current_total // 50)
        if current_batter_collection is not None:
            if batter50flag:
                commentary += str(batter50) + " comes up for " + batter_name
                if team50flag:
                    commentary += " and "
                else:
                    commentary += "! "
        if team50flag:
            batting_team = live_details["bat"]
            batting_team1 = Team(batting_team).abstract_name()
            commentary += str(team50) + " comes up for " + batting_team1 + "! "
        if score == "pen":
            batting_team1 = Team(live_details["bat"]).abstract_name()
            commentary = "Oh, dear! " + batting_team1 + " have been awarded 5 penalty runs!"
            if team50flag:
                commentary += " As a result, " + str(team50) + " comes up for " + batting_team1 + "! "
        if cleaned_data["commentary"] == "" and not is_the_batter_out:
            commentary += fetch_commentary_data_teamwise(
                    score,
                    current_batter,
                    current_bowler
                )
        else:
            commentary += cleaned_data["commentary"]
        ball = {
            "_id": ball_id,
            "over": live_details["current_ball_id"][0] + 1,
            "ball": live_details["current_ball_id"][1],
            "legal_delivery": legal_ball,
            "bowler": current_bowler,
            "batter": current_batter,
            "nonstriker": current_nonstriker,
            "score_int": int(score_int),
            "score_bat": int(score_bat),
            "score": score,
            "dismissed_batter": cleaned_data["dismissed_batter"],
            "commentary": commentary,
            "wide": wide,
            "no_ball": no_ball,
            "bye": bye,
            "leg_bye": leg_bye,
            "penalty": penalty,
            "batting_team_50_milestone": 0,
            "batting_stand_50_milestone": 0,
            "batter_50_milestone": 0,
            "bowler_wicket_milestone": 0
        }
        progression = mongolivematchclient.get_past_balls()
        progression.insert_one(ball)
        process_ball(cleaned_data)
        live_match.create()
        live_details = live_match.find_one(1)
        if is_the_batter_out:
            if int(live_details["wickets"]) >= 10:
                return decision_next_steps(request)
            next_batter = BATTING_ORDER[int(live_details["wickets"]) + 1]
            batter_stats = mongolivematchclient.get_batter_stat()
            if batter_stats.find_one(live_details["batter"])["dismissed"]:
                live_match.update_one(
                    {
                        "_id": 1
                    },
                    {
                        "$set": {
                            "batter": next_batter
                        }
                    }
                )
            elif batter_stats.find_one(live_details["nonstriker"])["dismissed"]:
                live_match.update_one(
                    {
                        "_id": 1
                    },
                    {
                        "$set": {
                            "nonstriker": next_batter
                        }
                    }
                )
            live_details = live_match.find_one(1)
    return HttpResponseRedirect("/live/")


def decision_next_steps(request):
    live_match = mongoclient.live_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS
    )
    live_details = live_match.find_one(1)
    if live_details["innings"] < 4:
        return live_next_innings(request)
    else:
        return export_live_game(request)  


def live_next_innings(request):
    live_match = mongoclient.live_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS
    )
    live_details = live_match.find_one(1)
    curr_inning = live_details["innings"]
    curr_lead = live_details["net_score"]
    follow_on = bool(curr_lead >= 200)
    live_match.update_one(
        {
            "_id": 1
        }, 
        {
            '$inc': {
                'all_session_balls': live_details["balls"]
            }
        }
    )
    if True:
        if curr_inning == 2:
            bat50flags = live_details["bat50flag"]
            for i in bat50flags.keys():
                bat50flags[i] = 0
            hattrick_flags = live_details["hattrick_flag"]
            for i in hattrick_flags.keys():
                hattrick_flags[i] = 0
            live_match.update_one(
                {
                    "_id": 1
                }, 
                {
                    '$set': {
                        'bat50flag': bat50flags,
                        'hattrick_flag': hattrick_flags
                    }
                }
            )
        if curr_inning == 2 and follow_on is True:
            next_batting_team = live_details["bat"]
            next_bowling_team = live_details["bowl"]
            live_match.update_one(
                {
                    "_id": 1
                }, 
                {
                    '$set': {
                        'follow_on_enabled': True
                    }
                }
            )
        else:
            next_batting_team = live_details["bowl"]
            next_bowling_team = live_details["bat"]
        if curr_inning == 3:
            if next_batting_team == live_details["first_batting_team"]:
                target = 1 - live_details["net_score"]
            else:
                target = 1 + live_details["net_score"]
            if target < 1:
                # Innings win
                return export_live_game(request)
        else:
            target = None
        batting_order, bowling_order, _, _ = fetch_lineup(
            next_batting_team,
            next_bowling_team
        )
        next_batter1 = batting_order[0]
        next_batter2 = batting_order[1]
        next_bowler = bowling_order[0]
        all_scores = live_details["all_scores"]
        all_scores[curr_inning - 1] = live_details["score"]
        live_match.update_one(
            {
                "_id": 1
            }, 
            {
                '$set': {
                    'stage': int(curr_inning) + 1,
                    'innings': int(curr_inning) + 1,
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
                    'all_scores': all_scores,
                    'previousPartnership': None,
                    'target': target,
                    'nextInningFlag': False
                }
            }
        )
    next_innings_chase_commentary(curr_inning + 1)
    return nextDeliveryAutomatedSequence(request)


def next_innings_chase_commentary(curr_inning):
    # for test matches
    state = mongoclient.live_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS
    ).find_one(1)
    bat_team = Team(state["bat"])
    bowl_team = Team(state["bowl"])
    bat_name = bat_team.abstract_name()
    bowl_name = bowl_team.abstract_name()
    opening_bowler = fetch_opening_bowler(state["bowl"])
    bowl_1_name = AbstractPlayer(opening_bowler).abstract_name()
    run_chase_str = "... THE RUN CHASE ..."
    if curr_inning < 3:
        run_chase_str = "... " + bat_name.upper() + " FIRST INNINGS ..."
    else:
        run_chase_str = "... " + bat_name.upper() + " SECOND INNINGS ..."
    start_comment_data = {
        "_id": str(curr_inning) + ".start",
        "comments": [
            {
                "key": "Text",
                "value": run_chase_str
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
    if curr_inning == 2:
        comment_collection = mongoclient.live_db_get_collection(
                mongoclient.CURRENT_INNINGS2_COMMENTARY
            )
        comment_collection.insert_one(start_comment_data)
    elif curr_inning == 3:
        comment_collection = mongoclient.live_db_get_collection(
                mongoclient.CURRENT_INNINGS3_COMMENTARY
            )
        comment_collection.insert_one(start_comment_data)
    elif curr_inning == 4:
        comment_collection = mongoclient.live_db_get_collection(
                mongoclient.CURRENT_INNINGS4_COMMENTARY
            )
        comment_collection.insert_one(start_comment_data)
    pass
