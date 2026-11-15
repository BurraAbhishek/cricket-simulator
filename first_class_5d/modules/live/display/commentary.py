from math import ceil
from django.shortcuts import render
from bin.models.team import Team, TeamCollection, AbstractPlayer
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS
from modules.live.display.summary import get_live_summary
from modules.live.display.export_game import fetch_live_game
from modules.index.scorecard import get_fall_of_wicket_new


def get_live_commentary(request, match_session=1):
    game = fetch_live_game()
    commentary = []
    for i, e in enumerate(game["innings"]):
        commentary += get_innings_commentary(
            e,
            False,
            game["target"],
            120
        )
    summary = get_live_summary(game)
    commentary_types = {
        "text": "Text",
        "image": "Image",
        "over": "Over",
        "ball": "Ball"
    }
    # render
    return render(
        request,
        "commentary.html",
        {
            "commentary": reversed(commentary),
            "summary": summary,
            "ctx": commentary_types
        }
    )


def get_innings_commentary(
        data, 
        chasing=False, 
        target=0, 
        balls_remaining=120
    ):
    score = 0
    wicket = 0
    ball = 0
    commentary = []
    inning_comment = {}
    bat_runs = {}
    bat_balls = {}
    bat_dismissed = {}
    bowl_wickets = {}
    bowl_runs = {}
    bowl_balls = {}
    bowl_names = {}
    teams = TeamCollection()
    batting_team = Team(data["batting_team"])
    bowling_team = Team(data["bowling_team"])
    bat_fall_of_wicket = {}
    bat_wicket_method = {}
    for i in data["batter_stats"]:
        if i.get("dismissed", False) is True:
            bat_fall_of_wicket[i.get("_id")] = get_fall_of_wicket_new(
                i["dismissal"]
            )
            bat_wicket_method[i.get("_id")] = i["dismissal"]["mode"]
    for i in list(batting_team.find()):
        bat_runs[i["_id"]] = 0
        bat_balls[i["_id"]] = 0
        bat_dismissed[i["_id"]] = False
    for i in list(bowling_team.find()):
        bowl_runs[i["_id"]] = 0
        bowl_balls[i["_id"]] = 0
        bowl_wickets[i["_id"]] = 0
        bowl_names[i["_id"]] = i["name"]
    for i in data["commentary"]:
        ball_id = i["_id"][2:]
        inning_comment[ball_id] = i["comments"]
    try:
        for j in inning_comment["start"]:
            commentary.append(j)
    except KeyError:
        pass
    milestone_decision = TOURNAMENT_SETTINGS.get("milestone", False)
    for i, j in enumerate(data["data"]):
        over_total = 0
        over_scores = ""
        bowler = ""
        for k in j:
            try:
                for l in inning_comment[k["_id"]]:
                    commentary.append(l)
            except KeyError:
                pass
            comment = {
                "key": "Ball",
                "value": str(
                    str(k["over"] - 1)
                    + "."
                    + str(k["ball"])
                    + ": "
                    + k["commentary"]
                ),
                "score": k["score"],
                "score_int": k["score_int"],
                "wicket": False,
                "four": False,
                "six": False,
                "extra": False,
                "milestones": []
            }
            bat_score = k["score_int"] - int(
                k["wide"]
                + k["no_ball"]
                + k["bye"]
                + k["leg_bye"]
                + k["penalty"]
            )
            bowl_score = k["score_int"] - int(
                k["bye"]
                + k["leg_bye"]
                + k["penalty"]
            )
            extra = bool(
                k["wide"] > 0
                or k["no_ball"] > 0
                or k["bye"] > 0
                or k["leg_bye"] > 0
                or k["penalty"] > 0
            )
            score += k["score_int"]
            over_total += k["score_int"]
            over_scores += k["score"] + " "
            bat_runs[k["batter"]] += bat_score
            bowl_runs[k["bowler"]] += bowl_score
            if k["legal_delivery"]:
                ball += 1
                bat_balls[k["batter"]] += 1
                bowl_balls[k["bowler"]] += 1
                balls_remaining -= 1
            elif k["no_ball"] > 0:
                # No run chase in perfect Test
                bat_balls[k["batter"]] += 1
            if (
                k["dismissed_batter"] is not None 
                and k["dismissed_batter"] != ""
            ):
                comment["wicket"] = True
                bat_dismissed[k["dismissed_batter"]] = True
                wicket += 1
                if (
                    bat_wicket_method[k["dismissed_batter"]] in [
                        "b",
                        "c",
                        "lbw",
                        "st",
                        "hitwicket"
                    ]
                ):
                    bowl_wickets[k["bowler"]] += 1
                if (
                    bat_wicket_method[k["dismissed_batter"]] in [
                        "timeout",
                        "retired"
                    ]
                ):
                    comment["value"] = k["commentary"]
            if k["penalty"] > 0:
                comment["value"] = k["commentary"]
            if "score_bat" not in k.keys():
                k["score_bat"] = k["score_int"]
            if k["score_bat"] == 4 and not extra and not comment["wicket"]:
                comment["four"] = True
            if k["score_bat"] >= 6 and not extra and not comment["wicket"]:
                comment["six"] = True
            if comment["wicket"] is False and extra is True:
                comment["extra"] = True
            if milestone_decision is True:
                if k["batting_team_50_milestone"] > 0:
                    milestone_object = {
                        "type": "team",
                        "team": batting_team.name(),
                        "color": batting_team.get("dark_color"),
                        "flag_color": batting_team.get("color"),
                        "flag": batting_team.get("flag"),
                        "title": str(
                            str(50 * k["batting_team_50_milestone"])
                            + " runs for the team"
                        ),
                        "score": str(str(score) + "/" + str(wicket))
                    }
                    comment["milestones"].append(milestone_object)
                if k["batting_stand_50_milestone"] > 0:
                    batter = AbstractPlayer(k["batter"])
                    nonstriker = AbstractPlayer(k["nonstriker"])
                    milestone_object = {
                        "type": "stand",
                        "p1": batter.name(),
                        "p2": nonstriker.name(),
                        "p1_runs": str(
                            str(bat_runs[k["batter"]])
                            + "* ("
                            + str(bat_balls[k["batter"]])
                            + ")"
                        ),
                        "p2_runs": str(
                            str(bat_runs[k["nonstriker"]])
                            + "* ("
                            + str(bat_balls[k["nonstriker"]])
                            + ")"
                        ),
                        "p1_avatar": batter.avatar(),
                        "p2_avatar": nonstriker.avatar(),
                        "color": batting_team.get("dark_color"),
                        "title": str(
                            str(50 * k["batting_stand_50_milestone"])
                            + " runs partnership"
                        )
                    }
                    comment["milestones"].append(milestone_object)
                if k["batter_50_milestone"] > 0:
                    batter = AbstractPlayer(k["batter"])
                    title = str(50 * k["batter_50_milestone"]) + " runs"
                    if k["batter_50_milestone"] == 1:
                        title = "Half century"
                    if k["batter_50_milestone"] == 2:
                        title = "Century"
                    if k["batter_50_milestone"] == 4:
                        title = "Double hundred"
                    if k["batter_50_milestone"] == 10:
                        title = "Half millennium"
                    if k["batter_50_milestone"] == 20:
                        title = "Millennium"
                    milestone_object = {
                        "type": "batter",
                        "title": title,
                        "name": batter.name(),
                        "score": str(
                            str(bat_runs[k["batter"]])
                            + "* ("
                            + str(bat_balls[k["batter"]])
                            + ")"
                        ),
                        "avatar": batter.avatar(),
                        "color": batting_team.get("dark_color"),
                    }
                    comment["milestones"].append(milestone_object)
                if k["bowler_wicket_milestone"] > 2:
                    bowler = AbstractPlayer(k["bowler"])
                    title = str(k["bowler_wicket_milestone"]) + " wicket haul"
                    milestone_object = {
                        "type": "bowler",
                        "title": title,
                        "name": bowler.name(),
                        "subtitle": str(
                            str(bowl_wickets[k["bowler"]])
                            + "/"
                            + str(bowl_runs[k["bowler"]])
                            + " ("
                            + format_overs(bowl_balls[k["bowler"]])
                            + ")"
                        ),
                        "avatar": bowler.avatar(),
                        "color": bowling_team.get("dark_color"),
                    }
                    comment["milestones"].append(milestone_object)
                if k["dismissed_batter"] != "":
                    batter = AbstractPlayer(k["dismissed_batter"])
                    milestone_object = {
                        "type": "wicket",
                        "title": "Fall of wicket",
                        "batter": batter.name(),
                        "batter_score": str(
                            str(bat_runs[k["dismissed_batter"]])
                            + " ("
                            + str(bat_balls[k["dismissed_batter"]])
                            + ")"
                        ),
                        "avatar": batter.avatar(),
                        "dismissal": bat_fall_of_wicket[k["dismissed_batter"]],
                        "color": batting_team.get("dark_color"),
                    }
                    comment["milestones"].append(milestone_object)
            commentary.append(comment)
            bowler = k["bowler"]
            b1, b2 = get_over_batters(
                k["batter"],
                k["nonstriker"],
                teams.get(data["batting_team"]),
                bat_runs,
                bat_balls,
                bat_dismissed
            )
        requiredrate = "-"
        if chasing:
            if balls_remaining > 0:
                rrr = ceil(
                        float(
                            int(target - score) * 6 / int(balls_remaining)
                        ) * 100
                    ) / 100
                if rrr <= 0:
                    requiredrate = "-"
                else:
                    requiredrate = str(rrr)
            else:
                requiredrate = "-"
        if bowler != "":
            batting_team_name = Team(data["batting_team"]).get("name")
            comment = {
                "key": "Over",
                "over": i + 1,
                "batting_team": batting_team_name,
                "score": score,
                "wicket": wicket,
                "ball": ball,
                "runrate": 0,
                "over_total": str(over_total) + " run",
                "over_scores": over_scores,
                "bowler_name": bowl_names[bowler],
                "bowler_runs": bowl_runs[bowler],
                "bowler_overs": format_overs(bowl_balls[bowler]),
                "bowler_wickets": bowl_wickets[bowler],
                "batter1": b1,
                "batter2_enabled": (b2 is not None),
                "batter2": b2,
                "chasing": chasing,
                "requiredrate": requiredrate
            }
            if ball > 0:
                comment["runrate"] = score * 6 / ball
            if over_total != 1:
                comment["over_total"] += "s"
            commentary.append(comment)
    try:
        for j in inning_comment["end"]:
            commentary.append(j)
    except KeyError:
        pass
    return commentary


def get_over_batters(
        b1_id,
        b2_id,
        team: Team,
        bat_runs,
        bat_balls,
        bat_dismissed
    ):
    b1 = None
    b2 = None
    if (
        not bat_dismissed[b1_id]
        and not bat_dismissed[b2_id]
    ):
        b1_name = team.find_one(b1_id)["name"]
        b2_name = team.find_one(b2_id)["name"]
        b1 = {
            "name": b1_name,
            "runs": bat_runs[b1_id],
            "balls": bat_balls[b1_id],
        }
        b2 = {
            "name": b2_name,
            "runs": bat_runs[b2_id],
            "balls": bat_balls[b2_id],
        }
    elif bat_dismissed[b1_id]:
        b2_name = team.find_one(b2_id)["name"]
        b1 = {
            "name": b2_name,
            "runs": bat_runs[b2_id],
            "balls": bat_balls[b2_id],
        }
    elif bat_dismissed[b2_id]:
        b1_name = team.find_one(b1_id)["name"]
        b1 = {
            "name": b1_name,
            "runs": bat_runs[b1_id],
            "balls": bat_balls[b1_id],
        }
    return b1, b2


def format_overs(balls):
    if balls % 6 == 0:
        return str(balls // 6)
    else:
        return str(balls // 6) + "." + str(balls % 6)


def get_session_commentary(game, session_index: int):
    live_phase = game["sessions"][session_index]
    start_ball = live_phase["start_ball"]
    end_ball = live_phase["end_ball"]
    start_inning = int(live_phase["start_inning"])
    end_inning = int(live_phase["end_inning"])
    use_end_inning = bool(live_phase["capture_end"])
    end_phase_comments = None
    if not use_end_inning:
        end_phase_comments = live_phase["end_comments"]
    commentary = []
    for i in range(start_inning, end_inning + 1):
        commentary += get_innings_session_commentary(
            game["innings"][i],
            i == 3,
            game["target"],
            3600,
            i,
            False,
            (start_inning, start_ball),
            (end_inning, end_ball),
            use_end_inning,
            end_phase_comments
        )
    return commentary


def get_innings_session_commentary(
        data, 
        chasing=False, 
        target=0, 
        balls_remaining=120,
        innings_index=0,
        use_session_data=False,
        start_ball_pack=None,
        end_ball_pack=None,
        use_end_inning=True,
        end_phase_comments=None
    ):
    score = 0
    wicket = 0
    ball = 0
    commentary = []
    inning_comment = {}
    session_comment = {}
    bat_runs = {}
    bat_balls = {}
    bat_dismissed = {}
    bowl_wickets = {}
    bowl_runs = {}
    bowl_balls = {}
    bowl_names = {}
    start_inning = None
    start_ball = None
    end_inning = None
    end_ball = None
    teams = TeamCollection()
    batting_team = Team(data["batting_team"])
    bowling_team = Team(data["bowling_team"])
    bat_fall_of_wicket = {}
    bat_wicket_method = {}
    for i in data["batter_stats"]:
        if i.get("dismissed", False) is True:
            bat_fall_of_wicket[i.get("_id")] = get_fall_of_wicket_new(
                i["dismissal"]
            )
            bat_wicket_method[i.get("_id")] = i["dismissal"]["mode"]
    milestone_decision = TOURNAMENT_SETTINGS.get("milestone", False)
    if start_ball_pack is not None:
        start_inning, start_ball = start_ball_pack
    if end_ball_pack is not None:
        end_inning, end_ball = end_ball_pack
    for i in list(teams.get(data["batting_team"]).find()):
        bat_runs[i["_id"]] = 0
        bat_balls[i["_id"]] = 0
        bat_dismissed[i["_id"]] = False
    for i in list(teams.get(data["bowling_team"]).find()):
        bowl_runs[i["_id"]] = 0
        bowl_balls[i["_id"]] = 0
        bowl_wickets[i["_id"]] = 0
        bowl_names[i["_id"]] = i["name"]
    # start and end commentary
    for i in data["commentary"]:
        ball_id = i["_id"][2:]
        inning_comment[ball_id] = i["comments"]
    # is there a start and end
        use_data = True
        if start_ball is not None and start_inning == innings_index:
            use_data = False
    if start_ball is not None:
        if start_ball == "0.1.0" or start_ball == "start":
            use_data = True
    if use_data:
        try:
            for j in inning_comment["start"]:
                commentary.append(j)
        except KeyError:
            pass
    for i, j in enumerate(data["data"]):
        over_total = 0
        over_scores = ""
        bowler = ""
        for k in j:
            if not use_data:
                if k["_id"] == start_ball:
                    use_data = True
            try:
                for l in inning_comment[k["_id"]]:
                    if use_data:
                        commentary.append(l)
            except KeyError:
                pass
            comment = {
                "key": "Ball",
                "value": str(
                    str(k["over"] - 1)
                    + "."
                    + str(k["ball"])
                    + ": "
                    + k["commentary"]
                ),
                "score": k["score"],
                "score_int": k["score_int"],
                "wicket": False,
                "four": False,
                "six": False,
                "extra": False,
                "milestones": []
            }
            bat_score = k["score_int"] - int(
                k["wide"]
                + k["no_ball"]
                + k["bye"]
                + k["leg_bye"]
                + k["penalty"]
            )
            bowl_score = k["score_int"] - int(
                k["bye"]
                + k["leg_bye"]
                + k["penalty"]
            )
            extra = bool(
                k["wide"] > 0
                or k["no_ball"] > 0
                or k["bye"] > 0
                or k["leg_bye"] > 0
                or k["penalty"] > 0
            )
            score += k["score_int"]
            over_total += k["score_int"]
            over_scores += k["score"] + " "
            bat_runs[k["batter"]] += bat_score
            bowl_runs[k["bowler"]] += bowl_score
            if k["legal_delivery"]:
                ball += 1
                bat_balls[k["batter"]] += 1
                bowl_balls[k["bowler"]] += 1
                balls_remaining -= 1
            elif k["no_ball"] > 0:
                # No run chase in perfect Test
                bat_balls[k["batter"]] += 1
            if (
                k["dismissed_batter"] is not None 
                and k["dismissed_batter"] != ""
            ):
                comment["wicket"] = True
                bat_dismissed[k["dismissed_batter"]] = True
                wicket += 1
                if (
                    bat_wicket_method[k["dismissed_batter"]] in [
                        "b",
                        "c",
                        "lbw",
                        "st",
                        "hitwicket"
                    ]
                ):
                    bowl_wickets[k["bowler"]] += 1
                if (
                    bat_wicket_method[k["dismissed_batter"]] in [
                        "timeout",
                        "retired"
                    ]
                ):
                    comment["value"] = k["commentary"]
            if k["penalty"] > 0:
                comment["value"] = k["commentary"]
            if "score_bat" not in k.keys():
                k["score_bat"] = k["score_int"]
            if use_data:
                if k["score_bat"] == 4 and not extra and not comment["wicket"]:
                    comment["four"] = True
                if k["score_bat"] >= 6 and not extra and not comment["wicket"]:
                    comment["six"] = True
                if comment["wicket"] is False and extra is True:
                    comment["extra"] = True
                if milestone_decision is True:
                    if k["batting_team_50_milestone"] > 0:
                        milestone_object = {
                            "type": "team",
                            "team": batting_team.name(),
                            "color": batting_team.get("dark_color"),
                            "flag_color": batting_team.get("color"),
                            "flag": batting_team.get("flag"),
                            "title": str(
                                str(50 * k["batting_team_50_milestone"])
                                + " runs for the team"
                            ),
                            "score": str(str(score) + "/" + str(wicket))
                        }
                        comment["milestones"].append(milestone_object)
                    if k["batting_stand_50_milestone"] > 0:
                        batter = AbstractPlayer(k["batter"])
                        nonstriker = AbstractPlayer(k["nonstriker"])
                        milestone_object = {
                            "type": "stand",
                            "p1": batter.name(),
                            "p2": nonstriker.name(),
                            "p1_runs": str(
                                str(bat_runs[k["batter"]])
                                + "* ("
                                + str(bat_balls[k["batter"]])
                                + ")"
                            ),
                            "p2_runs": str(
                                str(bat_runs[k["nonstriker"]])
                                + "* ("
                                + str(bat_balls[k["nonstriker"]])
                                + ")"
                            ),
                            "p1_avatar": batter.avatar(),
                            "p2_avatar": nonstriker.avatar(),
                            "color": batting_team.get("dark_color"),
                            "title": str(
                                str(50 * k["batting_stand_50_milestone"])
                                + " runs partnership"
                            )
                        }
                        comment["milestones"].append(milestone_object)
                    if k["batter_50_milestone"] > 0:
                        batter = AbstractPlayer(k["batter"])
                        title = str(50 * k["batter_50_milestone"]) + " runs"
                        if k["batter_50_milestone"] == 1:
                            title = "Half century"
                        if k["batter_50_milestone"] == 2:
                            title = "Century"
                        if k["batter_50_milestone"] == 4:
                            title = "Double hundred"
                        if k["batter_50_milestone"] == 10:
                            title = "Half millennium"
                        if k["batter_50_milestone"] == 20:
                            title = "Millennium"
                        milestone_object = {
                            "type": "batter",
                            "title": title,
                            "name": batter.name(),
                            "score": str(
                                str(bat_runs[k["batter"]])
                                + "* ("
                                + str(bat_balls[k["batter"]])
                                + ")"
                            ),
                            "avatar": batter.avatar(),
                            "color": batting_team.get("dark_color"),
                        }
                        comment["milestones"].append(milestone_object)
                    if k["bowler_wicket_milestone"] > 2:
                        bowler = AbstractPlayer(k["bowler"])
                        title = str(k["bowler_wicket_milestone"]) + " wicket haul"
                        milestone_object = {
                            "type": "bowler",
                            "title": title,
                            "name": bowler.name(),
                            "subtitle": str(
                                str(bowl_wickets[k["bowler"]])
                                + "/"
                                + str(bowl_runs[k["bowler"]])
                                + " ("
                                + format_overs(bowl_balls[k["bowler"]])
                                + ")"
                            ),
                            "avatar": bowler.avatar(),
                            "color": bowling_team.get("dark_color"),
                        }
                        comment["milestones"].append(milestone_object)
                    if k["dismissed_batter"] != "":
                        batter = AbstractPlayer(k["dismissed_batter"])
                        milestone_object = {
                            "type": "wicket",
                            "title": "Fall of wicket",
                            "batter": batter.name(),
                            "batter_score": str(
                                str(bat_runs[k["dismissed_batter"]])
                                + " ("
                                + str(bat_balls[k["dismissed_batter"]])
                                + ")"
                            ),
                            "avatar": batter.avatar(),
                            "dismissal": bat_fall_of_wicket[k["dismissed_batter"]],
                            "color": batting_team.get("dark_color"),
                        }
                        comment["milestones"].append(milestone_object)
                commentary.append(comment)
                bowler = k["bowler"]
                b1, b2 = get_over_batters(
                    k["batter"],
                    k["nonstriker"],
                    teams.get(data["batting_team"]),
                    bat_runs,
                    bat_balls,
                    bat_dismissed
                )
        requiredrate = "-"
        if chasing:
            if balls_remaining > 0:
                rrr = ceil(
                        float(
                            int(target - score) * 6 / int(balls_remaining)
                        ) * 100
                    ) / 100
                if rrr <= 0:
                    requiredrate = "-"
                else:
                    requiredrate = str(rrr)
            else:
                requiredrate = "-"
        if bowler != "":
            batting_team_name = Team(data["batting_team"]).get("name")
            if use_data:
                comment = {
                    "key": "Over",
                    "over": i + 1,
                    "batting_team": batting_team_name,
                    "score": score,
                    "wicket": wicket,
                    "ball": ball,
                    "runrate": 0,
                    "over_total": str(over_total) + " run",
                    "over_scores": over_scores,
                    "bowler_name": bowl_names[bowler],
                    "bowler_runs": bowl_runs[bowler],
                    "bowler_overs": format_overs(bowl_balls[bowler]),
                    "bowler_wickets": bowl_wickets[bowler],
                    "batter1": b1,
                    "batter2_enabled": (b2 is not None),
                    "batter2": b2,
                    "chasing": chasing,
                    "requiredrate": requiredrate
                }
                if ball > 0:
                    comment["runrate"] = score * 6 / ball
                if over_total != 1:
                    comment["over_total"] += "s"
                commentary.append(comment)
        try:
            for j in session_comment[k["_id"]]:
                if use_data:
                    commentary.append(j)
        except KeyError:
            pass
        if not use_end_inning:
            if k["_id"] == end_ball and innings_index == end_inning:
                use_data = False
                break
    if innings_index == end_inning and not use_end_inning:
        try:
            for j in end_phase_comments:
                commentary.append(j)
        except KeyError:
            pass
    try:
        for j in inning_comment["end"]:
            if use_data:
                commentary.append(j)
    except KeyError:
        pass
    return commentary
