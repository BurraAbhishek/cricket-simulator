from django.shortcuts import render
from django.http import HttpResponseRedirect
from bin.mongodb import mongoclient, mongolivematchclient
from bin.models.team import Team, AbstractPlayer
from modules.live.forms.innings import Innings
from modules.live.controllers.ball import process_ball
from modules.live_automated.controllers.commentary_data_teamwise import fetch_commentary_data_teamwise


def nextDelivery(request):
    live_details = mongoclient.live_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS
    ).find_one(1)
    if request.method == "POST":
        form = Innings(request.POST)
        if form.is_valid():
            ball_id = str(
                str(live_details["current_ball_id"][0])
                + "."
                + str(live_details["current_ball_id"][1])
                + "."
                + str(live_details["current_ball_id"][2])
            )
            # Fetch data
            score_bat = int(form.cleaned_data["score"])
            wide = int(form.cleaned_data.get("wide", 0))
            no_ball = int(form.cleaned_data.get("no_ball", 0))
            bye = int(form.cleaned_data.get("bye", 0))
            leg_bye = int(form.cleaned_data.get("leg_bye", 0))
            penalty = int(form.cleaned_data.get("penalty", 0))
            legal_ball = True
            score = str(score_bat)
            if not form.cleaned_data.get("legal_delivery", True):
                legal_ball = False
            if form.cleaned_data.get("legal_delivery", True) == "False":
                legal_ball = False
            # Extra runs
            if no_ball > 0:
                wide = 0
                bye = 0
                leg_bye = 0
                legal_ball = False
                score = str(score_bat) + "nb"
            elif wide > 0:
                no_ball = 0
                bye = 0
                leg_bye = 0
                legal_ball = False
                score = str(wide - 1) + "wd"
            elif bye > 0:
                score_bat = 0
                score = str(bye) + "b"
            elif leg_bye > 0:
                score_bat = 0
                score = str(leg_bye) + "lb"
            if penalty > 0:
                legal_ball = False
                score = "pen"
            # Total score
            score_int = int(
                score_bat
                + wide
                + no_ball
                + bye
                + leg_bye
                + penalty
            )
            # The players
            if form.cleaned_data["batter"] is None or form.cleaned_data["batter"] == "":
                current_batter = live_details["batter"]
            else:
                current_batter = form.cleaned_data["batter"]
            if form.cleaned_data["bowler"] is None or form.cleaned_data["bowler"] == "":
                current_bowler = live_details["bowler"]
            else:
                current_bowler = form.cleaned_data["bowler"]
            if form.cleaned_data["nonstriker"] is None or form.cleaned_data["nonstriker"] == "":
                current_nonstriker = live_details["nonstriker"]
            else:
                current_nonstriker = form.cleaned_data["nonstriker"]
            # The keeper
            wicketkeeper = None
            for i in Team(live_details["bowl"]).members():
                if i["_id"] != current_bowler and i["wicketkeeper"] is True:
                    wicketkeeper = i["_id"]
            # Dismissal
            is_the_batter_out = False
            if (
                form.cleaned_data["dismissed_batter"] != ""
            ):
                is_the_batter_out = True
                score = "W"
                dismissal_code = form.cleaned_data["dismissal"]
                if dismissal_code == "runout":
                    if score_bat == 0 and form.cleaned_data["dismissed_batter"] == current_batter:
                        dismissal_code = "runoutb0"
                    if score_bat == 0 and form.cleaned_data["dismissed_batter"] == current_nonstriker:
                        dismissal_code = "runoutk0"
                    if score_bat == 1 and form.cleaned_data["dismissed_batter"] == current_batter:
                        dismissal_code = "runoutk1"
                        score = "1+W"
                    if score_bat == 1 and form.cleaned_data["dismissed_batter"] == current_nonstriker:
                        dismissal_code = "runoutb1"
                        score = "1+W"
                    if score_bat == 2 and form.cleaned_data["dismissed_batter"] == current_batter:
                        dismissal_code = "runoutb2"
                        score = "2+W"
                    if score_bat == 2 and form.cleaned_data["dismissed_batter"] == current_nonstriker:
                        dismissal_code = "runoutk2"
                        score = "2+W"
            # Write back to form
            form.cleaned_data["is_batter_out"] = is_the_batter_out
            form.cleaned_data["legal_delivery"] = legal_ball
            form.cleaned_data["score_bat"] = score_bat
            form.cleaned_data["score_int"] = score_int
            form.cleaned_data["wide"] = wide
            form.cleaned_data["no_ball"] = no_ball
            form.cleaned_data["bye"] = bye
            form.cleaned_data["leg_bye"] = leg_bye
            form.cleaned_data["penalty"] = penalty
            if is_the_batter_out:
                form.cleaned_data["dismissal_code"] = dismissal_code
            else:
                form.cleaned_data["dismissal_code"] = ""
            # Commentary
            bowler_name = AbstractPlayer(current_bowler).abstract_name()
            batter_name = AbstractPlayer(current_batter).abstract_name()
            commentary = ""
            commentary += bowler_name
            commentary += " to "
            commentary += batter_name
            if is_the_batter_out:
                if form.cleaned_data["dismissal"] == "lbw":
                    commentary += ", OUT LBW! " + fetch_commentary_data_teamwise(
                            "lbw",
                            current_batter,
                            current_bowler
                        )
                elif form.cleaned_data["dismissal"] == "b":
                    commentary += ", OUT! BOWLED! " + fetch_commentary_data_teamwise(
                            "b",
                            current_batter,
                            current_bowler
                        )
                elif form.cleaned_data["dismissal"] == "st":
                    commentary += ", OUT! Stumped! " + fetch_commentary_data_teamwise(
                            "st",
                            current_batter,
                            current_bowler
                        )
                elif form.cleaned_data["dismissal"] == "c":
                    if form.cleaned_data["fielder"] == current_bowler:
                        commentary += ", OUT! CAUGHT AND BOWLED! " + fetch_commentary_data_teamwise(
                                "cb",
                                current_batter,
                                current_bowler
                            )
                    elif form.cleaned_data["fielder"] == wicketkeeper:
                        commentary += ", OUT! CAUGHT BEHIND! " + fetch_commentary_data_teamwise(
                                "cw",
                                current_batter,
                                current_bowler
                            )
                    else:
                        commentary += ", OUT! TAKEN! " + fetch_commentary_data_teamwise(
                                "c",
                                current_batter,
                                current_bowler
                            )
                elif form.cleaned_data["dismissal"] == "hitwicket":
                    commentary += ", OUT! HIT WICKET! " + fetch_commentary_data_teamwise(
                            "hitwicket",
                            current_batter,
                            current_bowler
                        )
                elif form.cleaned_data["dismissal"] == "runout":
                    commentary += ", OUT! RUN OUT! " + fetch_commentary_data_teamwise(
                            dismissal_code,
                            current_batter,
                            current_bowler
                        )
                elif form.cleaned_data["dismissal"] in ["hittheballtwice", "obstructing"]:
                    commentary += ", OUT! " + fetch_commentary_data_teamwise(
                            dismissal_code,
                            current_batter,
                            current_bowler
                        )
                elif form.cleaned_data["dismissal"] == "retired":
                    commentary = str(
                        batter_name 
                        + " is retired out! "
                        + " The batter leaves the playing field"
                        + " without authorization. Subsequently,"
                        + " the batter is dismissed."
                    )
                elif form.cleaned_data["dismissal"] == "timeout":
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
                    commentary += ", OUT! " + form.cleaned_data["dismissal"] + " " + form.cleaned_data["fielder"]
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
            if live_details["balls"] > 1:
                batter_stats = mongolivematchclient.get_batter_stat()
                current_batter_collection = batter_stats.find_one(current_batter)
                if current_batter_collection is not None:
                    current_batter_runs = current_batter_collection["runs"]
                    current_batter_runs += int(score_int)
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
                    batting_team = Team(live_details["bat"]).abstract_name()
                    commentary += str(team50) + " comes up for " + batting_team + "! "
            if score == "pen":
                batting_team1 = Team(live_details["bat"]).abstract_name()
                commentary = "Oh, dear! " + batting_team1 + " have been awarded 5 penalty runs!"
            if form.cleaned_data["commentary"] == "":
                commentary += fetch_commentary_data_teamwise(
                    score,
                    current_batter,
                    current_bowler
                )
            else:
                commentary += form.cleaned_data["commentary"]
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
                "dismissed_batter": form.cleaned_data["dismissed_batter"],
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
            process_ball(form.cleaned_data)
            return HttpResponseRedirect("/live/")
        else:
            return render(
                request,
                "live_inning.html",
                {
                    "title": "First Innings",
                    "form": Innings(),
                    "current_over": live_details["current_ball_id"][0],
                    "current_ball": live_details["current_ball_id"][1],
                    "next_inning": live_details["nextInningFlag"]
                }
            )
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