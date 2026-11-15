from django.shortcuts import render
from bin.models.team import Team, AbstractPlayer
from bin.mongodb import mongoclient, mongoreplayclient
from bin.mongoinserts.load_games import translate_ko_id
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS
from modules.index.summary import format_score
from modules.replay.display.export_game import fetch_live_game
from modules.replay.display.scorecard import get_fall_of_wicket_new


def watchReplayGameOnTV(request):
    game = mongoclient.replay_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS
    )
    game_details = game.find_one(0)
    live_details = game.find_one(1)
    replay_details_2 = game.find_one(2)
    game_id = game_details.get("id")
    game_name = "Group Stage"
    if game_id is not None:
        if game_id[0] == "m":
            game_name = "Group Stage"
        else:
            game_name = translate_ko_id(game_id)
    game_result = "Live"
    result_class = "paper red-notification bat-style"
    flip_board = bool(live_details["innings"] > 1)
    tv_widgets = TOURNAMENT_SETTINGS.get("tv_widgets", False)
    team1_result = "½"
    team2_result = "½"
    if live_details["replay_stage"] == 0:
        game = fetch_live_game()
        winner = game["winner"]
        margin = game["margin"]
        if winner == "":
            game_result = str(margin)
        else:
            loser = ""
            if game["winner"] == game["team1"]:
                loser = game["team2"]
                result_class = "paper red-notification bowl-style"
                team1_result = 0
                team2_result = 1
            if game["winner"] == game["team2"]:
                loser = game["team1"]
                team1_result = 1
                team2_result = 0
            if game["winner"] == "" and game["margin"].lower() == "double forfeit":
                team1_result = 0
                team2_result = 0
            game_result = Team(winner).get("name")
            game_result += " beat "
            game_result += Team(loser).get("name")
            game_result += " by "
            game_result += game["margin"]
    i1 = replay_details_2["innings"][int(live_details["innings"]) - 1]["data"]
    opening_batter = i1[0][0]["batter"]
    opening_nonstriker = i1[0][0]["nonstriker"]
    opening_bowler = i1[0][0]["bowler"]
    bat_1 = None
    bat_2 = None
    bowler = None
    evaluation = live_details["evaluation"]
    try:
        team1 = AbstractPlayer(opening_batter).team()
        team1_object = {
            "id": team1.id(),
            "name": team1.name(),
            "light": team1.get("light_color"),
            "dark": team1.get("dark_color"),
            "theme": team1.get("color"),
            "flag": team1.get("flag"),
            "rating": team1.get_rating(),
            "scores": [],
            "result": team1_result
        }
    except TypeError:
        team1_object = {
            "id": None,
            "name": "",
            "light": "#FF5555",
            "dark": "#110000",
            "theme": "#FF0000",
            "flag": None,
            "rating": None,
            "scores": [],
            "result": team1_result
        }
    try:
        team2 = AbstractPlayer(opening_bowler).team()
        team2_object = {
            "id": team2.id(),
            "name": team2.name(),
            "light": team2.get("light_color"),
            "dark": team2.get("dark_color"),
            "theme": team2.get("color"),
            "flag": team2.get("flag"),
            "rating": team2.get_rating(),
            "scores": [],
            "result": team2_result
        }
    except TypeError:
        team2_object = {
            "id": None,
            "name": "",
            "light": "#FF5555",
            "dark": "#110000",
            "theme": "#FF0000",
            "flag": None,
            "rating": None,
            "scores": [],
            "result": team2_result
        }
    bat1 = {
        "id": None,
        "name": "",
        "avatar": "",
        "team_id": live_details["bat"],
        "team_name": team1.name(),
        "rating": None,
        "runs": 0,
        "balls": 0,
        "out": False,
        "dismissal": [],
        "scoring": [0, 0, 0, 0, 0, 0, 0],
        "strikerate": 0
    }
    bat2 = {
        "id": None,
        "name": "",
        "avatar": "",
        "team_id": live_details["bat"],
        "team_name": team1.name(),
        "rating": None,
        "runs": 0,
        "balls": 0,
        "out": False,
        "dismissal": [],
        "scoring": [0, 0, 0, 0, 0, 0, 0],
        "strikerate": 0
    }
    bowl = {
        "id": None,
        "name": "",
        "avatar": "",
        "team_id": live_details["bat"],
        "team_name": team1.name(),
        "rating": None,
        "wickets": 0,
        "runs": 0,
        "overs": format_overs(0),
        "economy": 0
    }
    if live_details["batter"] is not None and live_details["balls"] > 0:
        bat_1 = AbstractPlayer(live_details["batter"])
    elif live_details["balls"] == 0:
        bat_1 = AbstractPlayer(opening_batter) 
    if live_details["nonstriker"] is not None and live_details["balls"] > 0:
        bat_2 = AbstractPlayer(live_details["nonstriker"])
    elif live_details["balls"] == 0:
        bat_2 = AbstractPlayer(opening_nonstriker)
    if live_details["bowler"] is not None and live_details["balls"] > 0:
        bowler = AbstractPlayer(live_details["bowler"])
    elif live_details["balls"] == 0:
        bowler = AbstractPlayer(opening_bowler)
    # Fetch individual stats
    run_rate = 0
    required_rate = 0
    over_scores, over_total = OverScores().export()
    if live_details["balls"] > 0:
        run_rate = 6 * live_details["score"] / live_details["balls"]
    balls_remaining = live_details["total_balls"] - live_details["balls"]
    runs_remaining = live_details["target"] - live_details["score"]
    if balls_remaining > 0:
        required_rate = 6 * runs_remaining / balls_remaining
    else:
        required_rate = -1
    try:
        batter_stats = mongoreplayclient.get_batter_stat()
        bowler_stats = mongoreplayclient.get_bowler_stat()
    except TypeError:
        pass
    if bat_1 is not None:
        bat1["id"] = bat_1.id()
        bat1["name"] = bat_1.name()
        bat1["avatar"] = bat_1.avatar()
        bat1["player_title"] = bat_1.rating_title()
        bat1["rating"] = bat_1.get("rating_bat")
    if bat_2 is not None:
        bat2["id"] = bat_2.id()
        bat2["name"] = bat_2.name()
        bat2["avatar"] = bat_2.avatar()
        bat2["player_title"] = bat_2.rating_title()
        bat2["rating"] = bat_2.get("rating_bat")
    if bowler is not None:
        bowl["id"] = bowler.id()
        bowl["name"] = bowler.name()
        bowl["avatar"] = bowler.avatar()
        bowl["player_title"] = bowler.rating_title()
        bowl["rating"] = bowler.get("rating_bowl")
    try:
        bat_1_details = batter_stats.find_one(live_details["batter"])
        bat1["runs"] = bat_1_details["runs"]
        bat1["balls"] = bat_1_details["balls"]
        bat1["out"] = bat_1_details["dismissed"]
        bat1["scoring"] = bat_1_details["scoring"]
        if bat1["balls"] > 0:
            bat1["strikerate"] = bat1["runs"] * 100 / bat1["balls"]
        if "dismissal" in bat_1_details:
            bat1["dismissal"] = get_fall_of_wicket_new(bat_1_details["dismissal"])
    except TypeError:
        pass
    except KeyError:
        pass
    try:
        bat_2_details = batter_stats.find_one(live_details["nonstriker"])
        bat2["runs"] = bat_2_details["runs"]
        bat2["balls"] = bat_2_details["balls"]
        bat2["out"] = bat_2_details["dismissed"]
        bat2["scoring"] = bat_2_details["scoring"]
        if bat2["balls"] > 0:
            bat2["strikerate"] = bat2["runs"] * 100 / bat2["balls"]
        if "dismissal" in bat_2_details:
            bat2["dismissal"] = get_fall_of_wicket_new(bat_2_details["dismissal"])
    except TypeError:
        pass
    except KeyError:
        pass
    try:
        bowl_details = bowler_stats.find_one(live_details["bowler"])
        bowl["wickets"] = bowl_details["wickets"]
        bowl["runs"] = bowl_details["runs"]
        bowl["overs"] = format_overs(bowl_details["balls"])
        if bowl_details["balls"] > 0:
            bowl["economy"] = bowl["runs"] * 6 / bowl_details["balls"]
    except TypeError:
        pass
    # Format evaluation
    evaluation["components"] = [
        {
            "key": Team(game_details['team1']).name() + " victory",
            "value": evaluation["white"] * 100
        },
        {
            "key": Team(game_details['team2']).name() + " victory",
            "value": evaluation["black"] * 100
        },
    ]
    in_score = format_score(live_details["score"], live_details["wickets"])
    in_balls = format_over_string(live_details["balls"])
    team1_object["scores"].append({"score": in_score, "over": in_balls})
    if live_details["innings"] > 1:
        game = fetch_live_game()
        score1 = game["innings"][0]["score"]
        balls1 = game["innings"][0]["balls"]
        wickets1 = game["innings"][0]["wickets"]
        team2_object["scores"].append({
            "score": format_score(score1, wickets1),
            "over": format_over_string(balls1)
        })
    return render(
        request,
        "tv.html",
        {
            "team1": team1_object,
            "team2": team2_object,
            "bat1": bat1,
            "bat2": bat2,
            "bowl": bowl,
            "in_runs": live_details["score"],
            "in_wickets": live_details["wickets"],
            "in_overs": live_details["balls"] // 6,
            "in_balls": live_details["balls"] % 6,
            "in_score": in_score,
            "flip_board": flip_board,
            "over_scores": over_scores,
            "over_total": over_total,
            "run_rate": run_rate,
            "required_rate": required_rate,
            "chasing": (live_details["stage"] > 1),
            "target": live_details["target"],
            "runs_remaining": runs_remaining,
            "balls_remaining": balls_remaining,
            "game_over": (live_details["replay_stage"] == 0),
            "match_name": game_name,
            "game_result": game_result,
            "result_class": result_class,
            "engine_name": evaluation.get("name", "DefaultEngine"),
            "evaluation": evaluation,
            "tv_widgets": tv_widgets,
            "evalbar": {
                "white": str(evaluation["white"] * 90) + "vh",
                "black": str(evaluation["black"] * 90) + "vh"
            }
        }
    )


def format_overs(balls):
    if balls % 6 == 0:
        return str(balls // 6)
    else:
        return str(balls // 6) + "." + str(balls % 6)


def format_over_string(balls):
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


class OverScores():

    scores = []
    legal = []
    score = 0

    def __init__(self) -> None:
        self.scores = []
        self.legal = []
        self.score = 0
        over = []
        try:
            progression = mongoreplayclient.get_past_balls()
        except TypeError:
            progression = None
        if progression is not None:
            all_balls = [] + progression.find()
            if len(all_balls) > 0:
                all_balls.sort(key=lambda x: self.ball_sorter(x["_id"]))
                last_over = all_balls[-1]["over"]
                for i in reversed(all_balls):
                    if i["over"] < last_over:
                        break
                    over.append(i)
        if len(over) > 0:
            for i in reversed(over):
                self.legal.append(i.get("legal_delivery", True))
                self.scores.append({
                    "score": i["score"],
                    "wicket": bool(i["dismissed_batter"] != ""),
                    "six": bool(i.get("score_bat", "score_int") >= 6),
                    "four": bool(i.get("score_bat", "score_int") == 4),
                    "extra": bool(
                        i.get("wide", 0) > 0
                        or i.get("no_ball", 0) > 0
                        or i.get("bye", 0) > 0
                        or i.get("leg_bye", 0) > 0
                        or i.get("penalty", 0) > 0
                        )
                })
                self.score += i.get("score_int", 0)

    def ball_sorter(self, ball_id: str):
        split_ball = ball_id.split(".")
        return int(split_ball[0]), int(split_ball[1]), int(split_ball[2])

    def export(self):
        output = [None] * 6
        for i in range(len(self.scores)):
            if not self.legal[i]:
                output.append(None)
            output[i] = self.scores[i]
        return output, self.score
