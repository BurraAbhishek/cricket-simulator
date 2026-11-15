from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from bin.mongoinserts.load_games import fetch_game
from bin.models.team import TeamCollection, AbstractPlayer
from modules.index.summary import get_summary, format_score
from modules.index.common import get_innings_ordinals
from modules.index import match_toppers


def match_summary(request, clas, id):
    game = fetch_game(clas, id)
    if game is None:
        raise PermissionDenied
    # Now the actual stuff
    output = {
        "potm_forfeit": False,
        "is_final": False
    }
    
    team = TeamCollection()
    try:
        if game["player_of_the_tournament"] is not None:
            output["is_final"] = True
            pott_data = team.fetch_player_map(game["player_of_the_tournament"])
            output["pott_id"] = game["player_of_the_tournament"]
            output["pott_name"] = str(
                pott_data.get("player_name")
                + " (" 
                + pott_data.get("team_name")
                + ")"
            )
            output["pott_player_title"] = AbstractPlayer(game["player_of_the_tournament"]).rating_title()
            pott_team = team.get(pott_data.get("team_id"))
            output["pott_avatar"] = pott_team.fetch_one(
                game["player_of_the_tournament"],
                "avatar"
            )
            output["pott_color"] = pott_team.get("light_color")
            output["pott_bgcolor"] = pott_team.get("dark_color")
    except KeyError:
        pass
    try:
        if game["player_of_the_match"] is None:
            output["potm_forfeit"] = True
        # player of the match
        potm_data = team.fetch_player_map(game["player_of_the_match"])
        potm_team = team.get(potm_data.get("team_id"))
        output["potm_id"] = game["player_of_the_match"]
        output["potm_name"] = str(
            potm_data.get("player_name")
            + " (" 
            + potm_data.get("team_name")
            + ")"
        )
        output["potm_player_title"] = AbstractPlayer(game["player_of_the_match"]).rating_title()
        output["potm_avatar"] = potm_team.fetch_one(
            game["player_of_the_match"],
            "avatar"
        )
        output["potm_color"] = potm_team.get("light_color")
        output["potm_bgcolor"] = potm_team.get("dark_color")
    except KeyError:
        output["potm_forfeit"] = True
    except TypeError:
        output["potm_forfeit"] = True
    except AttributeError:
        output["potm_forfeit"] = True
    # QA
    summary = get_summary(game)
    innings_data = []
    for i in range(len(game["innings"])):
        innings_data.append(get_stats(game, i))
    # Innings
        output["innings"] = innings_data
    # inning number
    inning_ordinal = get_innings_ordinals(game)
    for i in range(len(game["innings"])):
        output["innings"][i]["ordinal"] = inning_ordinal[i]
    # Toss
    if game["toss"] == 1:
        toss_string = "Toss: " + output["innings"][0]["batting_team"] + " chose to bat"
    elif game["toss"] == 2:
        toss_string = "Toss: " + output["innings"][1]["batting_team"] + " chose to bowl"
    else:
        toss_string = "Toss: Fixed"
    # render
    return render(
        request,
        "matchsummary.html",
        {
            "data": output,
            "summary": summary,
            "toss_string": toss_string
        }
    )


def get_stats(game, innings):
    team = TeamCollection()
    stat = {
        "batting_team": "",
        "bowling_team": "",
        "score_string": "",
        "rows": 3,
        "bat1": {
            "active": True,
            "id": "",
            "name": "",
            "avatar": "",
            "runs": 0,
            "balls": 0,
            "dismissed": False
        },
        "bat2": {
            "active": True,
            "id": "",
            "name": "",
            "avatar": "",
            "runs": 0,
            "balls": 0,
            "dismissed": False
        },
        "bat3": {
            "active": True,
            "id": "",
            "name": "",
            "avatar": "",
            "runs": 0,
            "balls": 0,
            "dismissed": False
        },
        "bowl1": {
            "active": True,
            "id": "",
            "name": "",
            "avatar": "",
            "wickets": 0,
            "runs": 0,
            "balls": 0
        },
        "bowl2": {
            "active": True,
            "id": "",
            "name": "",
            "avatar": "",
            "wickets": 0,
            "runs": 0,
            "balls": 0
        },
        "bowl3": {
            "active": True,
            "id": "",
            "name": "",
            "avatar": "",
            "wickets": 0,
            "runs": 0,
            "balls": 0
        },
    }
    batters1 = match_toppers.get_inning_toppers_bat(game, innings)
    bowlers1 = match_toppers.get_inning_toppers_bowl(game, innings)
    bat_collection = team.get(
        game["innings"][innings]["batting_team"]
    )
    bowl_collection = team.get(
        game["innings"][innings]["bowling_team"]
    )
    stat["bat1"] = {
        "active": True,
        "id": batters1[0]["_id"],
        "name": bat_collection.find_one(batters1[0]["_id"])["name"],
        "avatar": bat_collection.fetch_one(batters1[0]["_id"], "avatar"),
        "runs": batters1[0]["runs"],
        "balls": batters1[0]["balls"],
        "dismissed": batters1[0]["dismissed"],
        "player_title": AbstractPlayer(batters1[0]["_id"]).rating_title()
    }
    if len(batters1) > 1:
        stat["bat2"] = {
            "active": True,
            "id": batters1[1]["_id"],
            "name": bat_collection.find_one(batters1[1]["_id"])["name"],
            "avatar": bat_collection.fetch_one(batters1[1]["_id"], "avatar"),
            "runs": batters1[1]["runs"],
            "balls": batters1[1]["balls"],
            "dismissed": batters1[1]["dismissed"],
            "player_title": AbstractPlayer(batters1[1]["_id"]).rating_title()
        }
        if len(batters1) > 2:
            stat["bat3"] = {
                "active": True,
                "id": batters1[2]["_id"],
                "name": bat_collection.find_one(batters1[2]["_id"])["name"],
                "avatar": bat_collection.fetch_one(batters1[2]["_id"], "avatar"),
                "runs": batters1[2]["runs"],
                "balls": batters1[2]["balls"],
                "dismissed": batters1[2]["dismissed"],
                "player_title": AbstractPlayer(batters1[2]["_id"]).rating_title()
            }
        else:
            stat["bat3"]["active"] = False
    else:
        stat["bat2"]["active"] = False
        stat["bat3"]["active"] = False
    stat["bowl1"] = {
        "active": True,
        "id": bowlers1[0]["_id"],
        "name": bowl_collection.find_one(bowlers1[0]["_id"])["name"],
        "avatar": bowl_collection.fetch_one(bowlers1[0]["_id"], "avatar"),
        "wickets": bowlers1[0]["wickets"],
        "runs": bowlers1[0]["runs"],
        "overs": format_overs(bowlers1[0]["balls"]),
        "player_title": AbstractPlayer(bowlers1[0]["_id"]).rating_title()
    }
    if len(bowlers1) > 1:
        stat["bowl2"] = {
            "active": True,
            "id": bowlers1[1]["_id"],
            "name": bowl_collection.find_one(bowlers1[1]["_id"])["name"],
            "avatar": bowl_collection.fetch_one(bowlers1[1]["_id"], "avatar"),
            "wickets": bowlers1[1]["wickets"],
            "runs": bowlers1[1]["runs"],
            "overs": format_overs(bowlers1[1]["balls"]),
            "player_title": AbstractPlayer(bowlers1[1]["_id"]).rating_title()
        }
        if len(bowlers1) > 2:
            stat["bowl3"] = {
                "active": True,
                "id": bowlers1[2]["_id"],
                "name": bowl_collection.find_one(bowlers1[2]["_id"])["name"],
                "avatar": bowl_collection.fetch_one(bowlers1[2]["_id"], "avatar"),
                "wickets": bowlers1[2]["wickets"],
                "runs": bowlers1[2]["runs"],
                "overs": format_overs(bowlers1[2]["balls"]),
                "player_title": AbstractPlayer(bowlers1[2]["_id"]).rating_title()
            }
        else:
            stat["bowl3"]["active"] = False
    else:
        stat["bowl2"]["active"] = False
        stat["bowl3"]["active"] = False
    stat["batting_team"] = team.find_one(game["innings"][innings]["batting_team"])["name"]
    stat["bowling_team"] = team.find_one(game["innings"][innings]["bowling_team"])["name"]
    stat["score_string"] = str(
        format_score(
            game["innings"][innings]["score"],
            game["innings"][innings]["wickets"],
            game["innings"][innings]["declared"]
        )
        + " ("
        + format_overs(game["innings"][innings]["balls"])
        + ")"
    )
    if (not stat["bat3"]["active"]) and (not stat["bowl3"]["active"]):
        stat["rows"] = 2
    return stat


def format_overs(balls):
    if balls % 6 == 0:
        return str(balls // 6)
    else:
        return str(balls // 6) + "." + str(balls % 6)
