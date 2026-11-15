from bin.models.team import TeamCollection
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
        output["match_name"] = "Group Stage • Replay"
    else:
        output["match_name"] = translate_ko_id(game["_id"]) + " • Replay"
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
    # Scores
    output["score1"] = format_score(
        game["innings"][0]["score"],
        game["innings"][0]["wickets"]
    )
    try:
        output["score2"] = format_score(
            game["innings"][1]["score"],
            game["innings"][1]["wickets"]
        )
    except IndexError:
        output["score2"] = ""
    # Balls
    output["overs1"] = format_overs(
        game["innings"][0]["balls"]
    )
    try:
        output["overs2"] = format_overs(
            game["innings"][1]["balls"]
        )
    except IndexError:
        output["overs2"] = ""
    # Result
    try:
        winner_name = team_collection.find_one(game["winner"])["name"]
    except TypeError:
        winner_name = None
    if winner_name is not None:
        output["win_string"] = format_winstring(winner_name, game["margin"])
    else:
        output["win_string"] = ""
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
