from django.shortcuts import render
from bin.models.team import Team, TeamCollection
from modules.live.display.summary import get_live_summary
from modules.live.display.export_game import fetch_live_game


def get_live_scorecard(request, innings):
    game = fetch_live_game()
    summary = get_live_summary(game)
    # render
    if innings == -1:
        return render(
            request,
            "live_scorecard.html",
            {
                "summary": summary,
                "c": list(range(len(game["innings"]))),
                "innings": innings
            }
        )
    else:
        team1_collection = Team(
            game["innings"][innings]["batting_team"]
        )
        team2_collection = Team(
            game["innings"][innings]["bowling_team"]
        )
        batter_scorecard = get_batter_scorecard(
            team1_collection,
            game["innings"][innings]["batter_stats"]
        )
        bowler_scorecard = get_bowler_scorecard(
            team2_collection,
            game["innings"][innings]["bowler_stats"]
        )
        fow = get_fall_of_wickets(
            game["innings"][innings]["data"],
            game["innings"][innings]["batting_team"]
        )
        yet_to_bat = get_yet_to_bat(
            team1_collection,
            game["innings"][innings]["batter_stats"]
        )
        return render(
            request,
            "live_scorecard.html",
            {
                "summary": summary,
                "c": list(range(1, len(game["innings"]) + 1)),
                "innings": innings,
                "batter_scorecard": batter_scorecard,
                "bowler_scorecard": bowler_scorecard,
                "score_string": get_score_string(
                    game["innings"][innings]["score"],
                    game["innings"][innings]["balls"],
                    game["innings"][innings]["wickets"]
                ),
                "fow": fow,
                "ytb": yet_to_bat
            }
        )



def get_batter_scorecard(collection, batter_stats: list):
    scorecard = []
    for i in batter_stats:
        stat = {}
        stat["batter_name"] = collection.find_one(i["_id"])["name"]
        stat["runs"] = i["runs"]
        stat["balls"] = i["balls"]
        stat["fours"] = i["fours"]
        stat["sixes"] = i["sixes"]
        if i["balls"] == 0:
            stat["strike_rate"] = float(0)
        else: 
            stat["strike_rate"] = i["runs"] * 100 / i["balls"]
        if i["dismissed"]:
            stat["batter_status"] = get_fall_of_wicket(i["dismissal"])
        else:
            stat["batter_status"] = "not out"
        scorecard.append(stat)
    return scorecard


def get_bowler_scorecard(collection, bowler_stats: list):
    scorecard = []
    for i in bowler_stats:
        stat = {}
        stat["bowler_name"] = collection.find_one(i["_id"])["name"]
        stat["runs"] = i["runs"]
        stat["wickets"] = i["wickets"]
        stat["maidens"] = i["maidens"]
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
    bowler_name = TeamCollection().fetch_player_map(fow["bowler"])["player_name"]
    fielder_name = TeamCollection().fetch_player_map(fow["fielder"])["player_name"]
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
    elif fow["mode"] == "hit wicket":
        return "hit wicket b " + bowler_name
    elif fow["mode"] == "run out":
        return "run out (" + fielder_name + ")"
    elif fow["mode"] == "retired":
        return "retired out"
    else:
        return fow["mode"]


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


def get_yet_to_bat(bat_collection, batter_stats: list):
    batted = [i["_id"] for i in batter_stats]
    ytb_full = list(bat_collection.find())
    ytb = [i["name"] for i in ytb_full if i["_id"] not in batted]
    return ytb


def get_fall_of_wickets(innings, batting_team):
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
                    "dismissed_batter": dismissed_batter,
                    "score": score,
                    "wicket": wicket,
                    "stage": format_fow_over_string(
                        int(6 * j["over"]) + j["ball"] - 6
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
        output += " "
    if balls % 6 > 0:
        output += str(balls % 6)
        output += " ball"
        if (balls % 6 > 1):
            output += "s"
    return output
