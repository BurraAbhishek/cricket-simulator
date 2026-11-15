from django.shortcuts import render
from bin.models.team import Team, TeamCollection, AbstractPlayer
from modules.index.common import get_innings_ordinals
from modules.replay.display.summary import get_live_summary
from modules.replay.display.export_game import fetch_live_game


def get_replay_scorecard(request, innings):
    game = fetch_live_game()
    summary = get_live_summary(game)
    # ordinals
    ordinals = get_innings_ordinals(game)
    for i in range(len(ordinals)):
        ordinals[i] = (
            Team(game["innings"][i]["batting_team"]).get("name")
            + " "
            + ordinals[i]
        )
    # render
    if innings == -1:
        return render(
            request,
            "replay_scorecard.html",
            {
                "summary": summary,
                "c": list(range(len(game["innings"]))),
                "ordinals": ordinals,
                "innings": innings
            }
        )
    else:
        team = TeamCollection()
        try:
            innings_data = game["innings"][innings]
        except IndexError:
            last_inning = len(game["innings"]) - 1
            return get_replay_scorecard(request, last_inning)
        team1_collection = team.get(
            innings_data["batting_team"]
        )
        team2_collection = team.get(
            innings_data["bowling_team"]
        )
        batter_scorecard = get_batter_scorecard(
            team1_collection,
            innings_data["batter_stats"]
        )
        bowler_scorecard = get_bowler_scorecard(
            team2_collection,
            innings_data["bowler_stats"]
        )
        fow = get_fall_of_wickets(
            innings_data["data"]
        )
        yet_to_bat = get_yet_to_bat(
            team1_collection,
            innings_data["batter_stats"],
            game["nomination"][innings_data["batting_team"]]["default"]
        )
        extra_str = format_extra_string(innings_data["extras"])
        for i in batter_scorecard:
            if i["dismissed"]:
                for j in fow:
                    if i["batter_id"] == j["dismissed_id"]:
                        i["dismissal_comment"] = j["commentary"]
        return render(
            request,
            "replay_scorecard.html",
            {
                "summary": summary,
                "c": list(range(len(game["innings"]))),
                "ordinals": ordinals,
                "innings": innings,
                "batter_scorecard": batter_scorecard,
                "bowler_scorecard": bowler_scorecard,
                "score_string": get_score_string(
                    innings_data["score"],
                    innings_data["balls"],
                    innings_data["wickets"]
                ),
                "fow": fow,
                "ytb": yet_to_bat,
                "extra_str": extra_str
            }
        )


def get_batter_scorecard(collection, batter_stats: list):
    scorecard = []
    for i in batter_stats:
        stat = {}
        stat["batter_id"] = i["_id"]
        stat["batter_name"] = collection.find_one(i["_id"])["name"]
        stat["runs"] = i["runs"]
        stat["balls"] = i["balls"]
        stat["avatar"] = AbstractPlayer(i["_id"]).avatar()
        stat["player_title"] = AbstractPlayer(i["_id"]).rating_title()
        try:
            stat["fours"] = i["scoring"][4]
            stat["sixes"] = i["scoring"][6]
        except KeyError:
            stat["fours"] = i["fours"]
            stat["sixes"] = i["sixes"]
        stat["dismissed"] = i["dismissed"]
        stat["dismissal_comment"] = ""
        if i["balls"] == 0:
            stat["strike_rate"] = float(0)
        else: 
            stat["strike_rate"] = i["runs"] * 100 / i["balls"]
        if i["dismissed"]:
            stat["batter_status"] = get_fall_of_wicket_new(i["dismissal"])
        else:
            stat["batter_status"] = "not out"
        scorecard.append(stat)
    return scorecard


def get_bowler_scorecard(collection, bowler_stats: list):
    scorecard = []
    for i in bowler_stats:
        stat = {}
        stat["bowler_id"] = i["_id"]
        stat["bowler_name"] = collection.find_one(i["_id"])["name"]
        stat["balls"] = i["balls"]
        stat["runs"] = i["runs"]
        stat["wickets"] = i["wickets"]
        stat["maidens"] = i["maidens"]
        stat["avatar"] = AbstractPlayer(i["_id"]).avatar()
        stat["player_title"] = AbstractPlayer(i["_id"]).rating_title()
        if i["balls"] % 6 == 0:
            stat["overs"] = str(i["balls"] // 6)
        else:
            stat["overs"] = str(i["balls"] // 6) + "." + str(i["balls"] % 6)
        if i["balls"] == 0:
            stat["economy"] = float(0)
        else: 
            stat["economy"] = i["runs"] * 6 / i["balls"]
        scorecard.append(stat)
    return scorecard


def get_fall_of_wicket(fow: dict):
    bowler_name = TeamCollection().fetch_player_map(
        fow["bowler"]
        ).get("player_name")
    fielder_name = TeamCollection().fetch_player_map(
        fow["fielder"]
        ).get("player_name")
    if fow["mode"] == "b":
        return "b " + bowler_name
    elif fow["mode"] == "c":
        if fow["bowler"] == fow["fielder"]:
            return "c & b " + bowler_name
        else:
            return "c " + fielder_name + " b " + bowler_name
    elif fow["mode"] == "lbw":
        return "lbw b " + bowler_name
    elif fow["mode"] == "st":
        return "st " + fielder_name + " b " + bowler_name
    return "w " + bowler_name


def get_fall_of_wicket_new(fow: dict):
    bowler_name = TeamCollection().fetch_player_map(
        fow["bowler"]
        ).get("player_name")
    fielder_name = TeamCollection().fetch_player_map(
        fow["fielder"]
        ).get("player_name")
    if fow["mode"] == "b":
        return [
            {
                "key": "type",
                "value": "b"
            },
            {
                "key": "name",
                "value": bowler_name
            }
        ]
    elif fow["mode"] == "c":
        if fow["bowler"] == fow["fielder"]:
            return [
                {
                    "key": "type",
                    "value": "c & b"
                },
                {
                    "key": "name",
                    "value": bowler_name
                }
            ]
        else:
                return [
                {
                    "key": "type",
                    "value": "c"
                },
                {
                    "key": "name",
                    "value": fielder_name
                },
                {
                    "key": "type",
                    "value": "b"
                },
                {
                    "key": "name",
                    "value": bowler_name
                }
            ]
    elif fow["mode"] == "lbw":
        return [
                {
                    "key": "type",
                    "value": "lbw b"
                },
                {
                    "key": "name",
                    "value": bowler_name
                }
            ]
    elif fow["mode"] == "st":
            return [
                {
                    "key": "type",
                    "value": "st"
                },
                {
                    "key": "name",
                    "value": fielder_name
                },
                {
                    "key": "type",
                    "value": "b"
                },
                {
                    "key": "name",
                    "value": bowler_name
                }
            ]
    elif fow["mode"] == "hitwicket":
        return [
                {
                    "key": "type",
                    "value": "hit wicket b"
                },
                {
                    "key": "name",
                    "value": bowler_name
                }
            ]
    elif fow["mode"] == "runout":
        return [
                {
                    "key": "type",
                    "value": "run out "
                },
                {
                    "key": "name",
                    "value": "(" + str(fielder_name) + ")"
                }
            ]
    elif fow["mode"] == "timeout":
        return [
                {
                    "key": "type",
                    "value": "timed out"
                }
            ]
    elif fow["mode"] == "obstructing":
        return [
                {
                    "key": "type",
                    "value": "obstructing the field"
                }
            ]
    elif fow["mode"] == "retired":
        return [
                {
                    "key": "type",
                    "value": "retired out"
                }
            ]
    elif fow["mode"] == "hittheballtwice":
        return [
                {
                    "key": "type",
                    "value": "hit the ball twice"
                }
            ]
    return "w " + bowler_name


def get_score_string(score: int, balls: int, wickets: int) -> str:
    output = ""
    output += str(score)
    output += " ("
    if balls % 6 == 0:
        output += str(balls // 6)
    else:
        output += str(balls // 6) + "." + str(balls % 6)
    output += " over"
    if balls != 6:
        output += "s"
    output += ", "
    output += str(wickets)
    output += " wicket"
    if wickets != 1:
        output += "s"
    output += ")"
    return output


def get_yet_to_bat(bat_collection: Team, batter_stats: list, bat_lineup=None):
    batted = [i["_id"] for i in batter_stats]
    if bat_lineup is not None:
        ytb_full = list(bat_lineup)[:11]
    else:
        ytb_full = list(bat_collection.lineup())[:11]
    ytb = []
    for i in ytb_full:
        if i not in batted:
            ytb.append(
                {
                    "id": i,
                    "name": AbstractPlayer(i).name(),
                    "player_title": AbstractPlayer(i).rating_title()
                }
            )
    return ytb


def get_fall_of_wickets(innings):
    fow = []
    score = 0
    wicket = 1
    for i in innings:
        for j in i:
            score += j["score_int"]
            if (
                j["dismissed_batter"] is not None 
                and j["dismissed_batter"] != ""
            ):
                dismissed_batter = TeamCollection().fetch_player_map(
                    j["dismissed_batter"]
                    ).get("player_name")
                fow_element = {
                    "over": j["over"],
                    "ball": j["ball"],
                    "dismissed_id": j["dismissed_batter"],
                    "dismissed_batter": dismissed_batter,
                    "score": score,
                    "wicket": wicket,
                    "stage": format_fow_over_string(
                        int(6 * j["over"]) + j["ball"] - 6
                    ),
                    "commentary": str(
                        str(j["over"] - 1)
                        + "."
                        + str(j["ball"])
                        + ": "
                        + j["commentary"]
                    )
                }
                fow.append(fow_element)
                wicket += 1
    return fow


def format_fow_over_string(balls):
    output = ''
    if balls >= 6:
        output += str(balls // 6)
        output += " over"
        if (balls // 6) > 1:
            output += "s"
    if balls > 6 and balls % 6 > 0:
        output += "\n"
    if balls % 6 > 0:
        output += str(balls % 6)
        output += " ball"
        if (balls % 6 > 1):
            output += "s"
    if balls == 0:
        output = "0 balls"
    return output


def format_extra_string(extra: dict):
    if extra.get("total", 0) <= 0:
        return "0"
    s = str(extra.get("total"))
    s += " ("
    s0 = []
    for i in ["wide", "no_ball", "bye", "leg_bye", "penalty"]:
        if extra.get(i) > 0:
            if i == "penalty":
                s2 = "Penalty Run"
            else:
                s2 = " ".join(j.capitalize() for j in i.split("_"))
            s1 = str(extra.get(i))
            s1 += " "
            s1 += s2
            if extra.get(i) > 1:
                s1 += "s"
            s0.append(s1)
    for i, e in enumerate(s0):
        s += e
        if i < len(s0) - 1:
            s += ", "
    s += ")"
    return s
