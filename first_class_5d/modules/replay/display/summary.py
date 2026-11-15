from bin.mongoinserts.load_teams import TeamCollection
from bin.mongoinserts.load_games import translate_ko_id
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS
from modules.index.summary import format_score


def get_live_summary(game):
    output = {}
    # team collection
    team_collection = TeamCollection()
    # to enable team flags or not
    output["show_flags"] = TOURNAMENT_SETTINGS.get("team_flag", False)
    # Name of the match
    if game["_id"][0] == "m":
        output["match_name"] = "Group Stage • Live"
    else:
        output["match_name"] = translate_ko_id(game["_id"]) + " • Live"
    # Teams
    team1 = team_collection.find_one(game["team1"])
    team2 = team_collection.find_one(game["team2"])
    output["team1_id"] = team1.get("_id")
    output["team2_id"] = team2.get("_id")
    output["team1_name"] = team1.get("name")
    output["team2_name"] = team2.get("name")
    output["team1_flag"] = team1.get("flag")
    output["team2_flag"] = team2.get("flag")
    output["team1_flagcolor"] = team1.get("color")
    output["team2_flagcolor"] = team2.get("color")
    nbInnings = len(game["innings"])
    # Decisions
    output["decision1"] = ""
    output["decision2"] = ""
    # Scores
    output["score1"] = format_score(
        game["innings"][0]["score"],
        game["innings"][0]["wickets"],
        game["innings"][0]["declared"]
    )
    if nbInnings > 1:
        output["score2"] = format_score(
            game["innings"][1]["score"],
            game["innings"][1]["wickets"],
            game["innings"][1]["declared"]
        )
    if nbInnings > 2:
        if game["follow_on"]:
            output["score4"] = format_score(
                game["innings"][2]["score"],
                game["innings"][2]["wickets"],
                game["innings"][2]["declared"]
            )
        else:
            output["score3"] = format_score(
                game["innings"][2]["score"],
                game["innings"][2]["wickets"],
                game["innings"][2]["declared"]
            )
    if nbInnings > 3:
        if game["follow_on"]:
            output["score3"] = format_score(
                game["innings"][3]["score"],
                game["innings"][3]["wickets"],
                game["innings"][3]["declared"]
            )
        else:
            output["score4"] = format_score(
                game["innings"][3]["score"],
                game["innings"][3]["wickets"],
                game["innings"][3]["declared"]
            )
    # Balls
    output["overs1"] = format_overs(
        game["innings"][0]["balls"]
    )
    if nbInnings > 1:
        output["overs2"] = format_overs(
            game["innings"][1]["balls"]
        )
    if nbInnings > 2:
        output["overs3"] = format_overs(
            game["innings"][2]["balls"]
        )
    if nbInnings > 3:
        output["overs4"] = format_overs(
            game["innings"][3]["balls"]
        )
    # Result
    try:
        winner_name = team_collection.find_one(game["winner"])["name"]
    except TypeError:
        winner_name = None
    output["win_string"] = format_winstring(winner_name, game["margin"])
    output["follow_on"] = game["follow_on"]
    return output


def format_overs(balls):
    if balls % 6 == 0:
        return str(balls // 6)
    else:
        return str(balls // 6) + "." + str(balls % 6)


def format_winstring(winner, margin):
    # Tie case
    if (winner is None or winner == ""):
        return margin
    else:
        return str(
            winner
            + " won by "
            + margin
        )
