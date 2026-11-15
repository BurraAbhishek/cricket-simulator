import math
from bin.models.team import Team, AbstractPlayer
from bin.mongoinserts.load_games import translate_ko_id
from modules.exportgame.export_innings import export_live_innings


def ball_string(ball: int, end_flag: bool) -> str:
    if ball == 1:
        return "start"
    elif end_flag:
        return "end"
    b0 = ball // 6
    b1 = ball % 6
    if b1 == 0:
        b0 -= 1
        b1 = 6
    return str(str(b0) + "." + str(b1) + ".0")


def get_innings_dataset(nbInnings):
    innings = []
    if nbInnings > 0:
        innings1 = export_live_innings(1)
        innings.append(innings1)
    if nbInnings > 1:
        innings2 = export_live_innings(2)
        innings.append(innings2)
    if nbInnings > 2:
        innings3 = export_live_innings(3)
        innings.append(innings3)
    if nbInnings > 3:
        innings4 = export_live_innings(4)
        innings.append(innings4)
    return innings


def get_sessions_dataset(innings):
    bowled_balls = 0
    remaining_balls = 180
    session_balls = 0
    session = 0
    ds = []
    relative_score = 0
    curr_batting_team = None
    clause117 = False
    previous_session_extended = 0
    if len(innings) > 0:
        curr_batting_team = innings[0]["batting_team"]
    for k1, i in enumerate(innings):
        if curr_batting_team != i["batting_team"]:
            relative_score = 0 - relative_score
            curr_batting_team = i["batting_team"]
        i_balls = 0
        score = 0
        wicket = 0
        for j in i["data"]:
            for k in j:
                if k["legal_delivery"] is True:
                    bowled_balls += 1
                    i_balls += 1
                    session_balls += 1
                score += k["score_int"]
                relative_score += k["score_int"]
                wicket += int(0 if k["dismissed_batter"] == "" else 1)
                ds.append([
                        k1,
                        bowled_balls,
                        k["_id"],
                        session,
                        k["bowler"],
                        score,
                        wicket,
                        relative_score,
                        k["legal_delivery"]
                    ])
                if k["legal_delivery"] is True:
                    remaining_balls -= 1
                if remaining_balls == 0:
                    if wicket == 9 and not clause117 and i["balls"] - i_balls > 0:
                        clause117 = True
                        if i["balls"] - i_balls > 48 and i["balls"] - i_balls < 78:
                            remaining_balls = i["balls"] - i_balls
                        else:
                            remaining_balls += 48
                    elif i["balls"] - i_balls > 0 and i["balls"] - i_balls < 30:
                        remaining_balls = i["balls"] - i_balls
                    else:
                        if session < 14:
                            session += 1
                        if session % 3 == 0:
                            session_balls = 0
                        if not clause117:
                            remaining_balls = 180
                        elif session % 3 == 0:
                            remaining_balls = 180
                            clause117 = False
                        else:
                            remaining_balls = 132
                            clause117 = False
        if remaining_balls == 0 and session < 14 and not clause117:
            session += 1
        elif clause117 and remaining_balls < 48:
            if remaining_balls > 0 and session < 14:
                session += 1
            previous_session_extended += 48 - remaining_balls
            remaining_balls = 132 + remaining_balls
            if session % 3 == 0:
                remaining_balls += 48
            clause117 = False
        elif previous_session_extended > 0 and bowled_balls > 102 and remaining_balls < 30:
            if session < 14:
                session += 1
            remaining_balls = 180 + remaining_balls
        elif bowled_balls > 150 - previous_session_extended and remaining_balls < 30:
            if session < 14:
                session += 1
            remaining_balls = 180 + remaining_balls
        remaining_balls = min(6 * math.ceil(remaining_balls / 6), 180)
        if session % 3 == 2:
            if session_balls < 360:
                session_remaining_balls = 6 * math.ceil((360 - session_balls) / 6)
                session_remaining_balls = min(session_remaining_balls, 48)
                remaining_balls += session_remaining_balls
        if session % 3 == 0:
            previous_session_extended = 0
            session_balls = 0
        clause117 = False
    return ds


def get_raw_sessions(innings1, game_id="final", game_wickets=10):
    # innings - list of all innings
    # go by overs.
    innings = [] + innings1
    total_balls = 0
    for i in innings:
        total_balls += i["balls"]
    if total_balls < 180:
        return {
            "innings": innings,
            "sessions": [
                {
                    "start_inning": 0,
                    "start_ball": "start",
                    "end_inning": len(innings) - 1,
                    "end_ball": "end",
                    "capture_end": True
                }
            ]
        }
    ds = get_sessions_dataset(innings)
    # ds (data structure ;) is our prime variable now
    # identifying stop gaps
    start_data = [ds[0]]
    end_data = []
    change_inning = []
    lead_moments = []
    for i in range(0, len(ds) - 1):
        # Yes, hit a six in the first ball and declare straightaway!
        if ds[i + 1][3] - ds[i][3] == 1:
            end_data.append(ds[i])
            start_data.append(ds[i + 1])
            if ds[i + 1][0] - ds[i][0] == 1 or i == len(ds) - 1:
                change_inning.append(True)
            else:
                change_inning.append(False)
        if ds[i + 1][0] > 0:
            if innings[ds[i][0]]["batting_team"] == innings[ds[i + 1][0]]["batting_team"]:
                if ds[i][7] < 0 and ds[i + 1][7] == 0:
                    lead_moments.append({
                        "inning": ds[i + 1][0],
                        "ball": ds[i + 1][2],
                        "type": 0
                    })
                if ds[i][7] <= 0 and ds[i + 1][7] > 0 and ds[i + 1][0] < 3:
                    lead_moments.append({
                        "inning": ds[i + 1][0],
                        "ball": ds[i + 1][2],
                        "type": 1
                    })
            else:
                if ds[i][7] > 0 and ds[i + 1][7] == 0:
                    lead_moments.append({
                        "inning": ds[i + 1][0],
                        "ball": ds[i + 1][2],
                        "type": 0
                    })
                if ds[i][7] >= 0 and ds[i + 1][7] > 0 and ds[i + 1][0] < 3:
                    lead_moments.append({
                        "inning": ds[i + 1][0],
                        "ball": ds[i + 1][2],
                        "type": 1
                    })
    end_data.append(ds[-1])
    change_inning.append(True)
    # Create the dataset
    sessions = []
    for i in range(0, len(change_inning)):
        x = {
            "start_inning": start_data[i][0],
            "start_ball": str("start" if start_data[i][2] == "0.1.0" else start_data[i][2]),
            "end_inning": end_data[i][0],
            "end_ball": str("end" if change_inning[i] is True else end_data[i][2]),
            "capture_end": change_inning[i]
        }
        if x["capture_end"] is False:
            x["end_comments"] = []
        sessions.append(x)
    # Now do the honors.
    for i1 in range(len(end_data) - 1):
        if change_inning[i1] is False and i1 < len(end_data) - 1:
            i = end_data[i1]
            i2 = start_data[i1 + 1]
            session_end = i[3] + 1
            end_over = int(i[2].split(".")[0]) + 1
            break_type = ""
            bat_team = innings[i[0]]["batting_team"]
            bowl_team = innings[i[0]]["bowling_team"]
            bat_team_name = Team(bat_team).abstract_name()
            bowl_team_name = Team(bowl_team).abstract_name()
            next_session_init = ""
            next_day = False
            session_day = 1 + ((session_end - 1) // 3)
            if session_end % 3 == 1:
                break_type = "Lunch"
                next_session_init = "... SESSION 2, DAY " + str(session_day) + " ..."
                endcomment21 = "We will be back soon for the second session of the day..."
            elif session_end % 3 == 2:
                break_type = "Tea"
                next_session_init = "... SESSION 3, DAY " + str(session_day) + " ..."
                endcomment21 = "We will be back soon for the third and final session of the day..."
            else:
                break_type = "Stumps"
                next_session_init = "... SESSION 1, DAY " + str(session_day + 1) + " ..."
                endcomment21 = str(
                    "That's all for today. Action continues tomorrow when "
                    + bat_team_name
                    + " come out to bat again on Day "
                    + str(session_day + 1)
                    + ". Do join us then, take care and goodbye!"
                )
                next_day = True
            endcomment = " "
            endcomment1 = "The score is " + str(i[5])
            if i[6] == 0:
                endcomment1 += " without loss"
            else:
                endcomment1 += "/" + str(i[6])
            endcomment1 += " after " + str(end_over) + " overs"
            endcomment += endcomment1
            endcomment += " and that will be "
            endcomment += break_type
            endcomment += " on Day "
            endcomment += str(session_day) + "."
            over = int(i[2].split(".")[0])
            for b in innings[i[0]]["data"][over]:
                if b["_id"] == i[2]:
                    b["commentary"] += endcomment
            endcomment3 = ""
            if game_id == "final":
                endcomment3 += "Welcome back to the Final! "
            elif game_id[0] == "m":
                endcomment3 += "Welcome back to Match "
                endcomment3 += str(int(game_id.split("_")[2]))
                endcomment3 += ", Week "
                endcomment3 += str(int(game_id.split("_")[1]))
                endcomment3 += ". "
            else:
                endcomment3 += "Welcome back to "
                endcomment3 += translate_ko_id(game_id)
                endcomment3 += ". "
            endcomment3 += endcomment1
            endcomment3 += " and "
            endcomment3 += bat_team_name
            endcomment3 += " will pick up from where they left off." 
            endcomment4 = next_session_resume_commentary(bat_team, bowl_team, i2[4])
            startcomments = [
                {
                "key": "Text",
                "value": next_session_init
                }
            ]
            if next_day:
                startcomments.append({
                    "key": "Text",
                    "value": endcomment3
                })
            startcomments.append({
                "key": "Text",
                "value": endcomment4
            })
            endcomment2 = str(
                "End of Session "
                + str(1 + int((session_end - 1) % 3))
                + ", Day "
                + str(session_day)
                + ". That will be "
                + break_type
                + " on Day "
                + str(session_day)
                + ". "
                + endcomment1
                + "."
            )
            if i[0] > 0:
                if i[7] == 1:
                    endcomment2 += " " + bat_team_name + " lead by 1 run."
                elif i[7] < -1 and i[0] > 2:
                    wickets_to_win = int(game_wickets) - int(i[6])
                    endcomment2 += str(
                        " " 
                        + bat_team_name 
                        + " need " 
                        + str(1 - i[7]) 
                        + " runs to win, with "
                        + bowl_team_name
                        + " needing "
                        + str(wickets_to_win)
                        + " wicket"
                        + str("." if wickets_to_win == 1 else "s.")
                    )
                elif i[7] == -1 and i[0] > 2:
                    wickets_to_win = int(game_wickets) - int(i[6])
                    endcomment2 += str(
                        " " 
                        + bat_team_name 
                        + " need 1 run to win, with "
                        + bowl_team_name
                        + " needing "
                        + str(wickets_to_win)
                        + " wicket"
                        + str("" if wickets_to_win == 1 else "s")
                        + " for a tie."
                    )
                elif i[7] == -1:
                    endcomment2 += " " + bat_team_name + " trail by 1 run."
                elif i[7] > 0:
                    endcomment2 += " " + bat_team_name + " lead by " + str(i[7]) + " runs."
                elif i[7] < 0:
                    endcomment2 += " " + bat_team_name + " trail by " + str(0 - i[7]) + " runs."
                else:
                    endcomment2 += " The scores are level."
            end_comments = [
                {
                    "key": "Text",
                    "value": endcomment2
                },
                {
                    "key": "Text",
                    "value": endcomment21
                }
            ]
            sessions[i1]["end_comments"] = end_comments
            start_comments = {
                "_id": str(int(i2[0]) + 1) + "." + i2[2],
                "comments": startcomments
            }
            innings[int(i2[0])]["commentary"].append(start_comments)
    # Mentioning the lead if applicable
    if len(sessions) > 1:
        for i in lead_moments:
            batting_side = Team(innings[i["inning"]]["batting_team"]).abstract_name()
            if i["inning"] == 1 and i["type"] == 0:
                lead_indicator_comment = "The scores are level."
            if i["inning"] == 2 and i["type"] == 0:
                lead_indicator_comment = "The scores are level."
            if i["inning"] == 3 and i["type"] == 0:
                lead_indicator_comment = str(
                    "The scores are level and "
                    + batting_side
                    + " need 1 run to win."
                )
            if i["inning"] == 1 and i["type"] == 1:
                lead_indicator_comment = str(
                    batting_side.upper()
                    + " TAKE THE LEAD!"
                )
            if i["inning"] == 2 and i["type"] == 1:
                lead_indicator_comment = str(
                    batting_side.upper()
                    + " RETAKE THE LEAD!"
                )
            lead_indicator_over = int(i["ball"].split(".")[0])
            for j in innings[i["inning"]]["data"][lead_indicator_over]:
                if j["_id"] == i["ball"]:
                    j["commentary"] += " " + lead_indicator_comment
    # And we should be good.
    result = {
        "innings": innings,
        "sessions": sessions
    }
    return result


def next_session_resume_commentary(bat, bowl, next_bowler):
    bat_name = Team(bat).abstract_name()
    bowl_name = Team(bowl).abstract_name()
    bowl_1_name = AbstractPlayer(next_bowler).abstract_name()
    x = str(
        bowl_name
        + " players are seen having a chit chat near the ropes. "
        + "They will get into a huddle before they disperse "
        + "and are followed by the two "
        + bat_name
        + " batters. "
        + bowl_1_name
        + " will resume the proceedings with the ball for "
        + bowl_name
        + ". Let's play..."
    )
    return x
