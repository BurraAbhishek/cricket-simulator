from django.shortcuts import render
from bin.models.team import Team, TeamCollection, AbstractPlayer
from bin.mongoinserts.load_teams import TOURNAMENT_TEAMS
from bin.mongoinserts.load_games import Tournament
from bin.mongoinserts.groupstage import final_standing
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS
from bin.mongoinserts.groupstage import update_gs
from bin.mongoinserts.team.hostteam import HOST_DICT
from modules.index.summary import format_score


def index(request):
    # Team-rating mapping
    team_collection = TeamCollection()
    group1 = []
    group2 = []
    grouping = []
    rating_map = []
    for i in TOURNAMENT_TEAMS.keys():
        rating_map.append(
            {
                "id": TOURNAMENT_TEAMS[i]["_id"],
                "name": TOURNAMENT_TEAMS[i]["name"],
                "flag": TOURNAMENT_TEAMS[i]["flag"],
                "bgcolor": TOURNAMENT_TEAMS[i]["color"],
                "rating": TOURNAMENT_TEAMS[i]["rating"],
                "components": TOURNAMENT_TEAMS[i].get("components")
            }
        )
    rating_map.sort(key=lambda x: x["rating"], reverse=True)
    for i in rating_map:
        if Team(i["id"]).ai():
            group2.append(i)
        else:
            group1.append(i)
    for i in range(min(len(group1), len(group2))):
        grouping.append([group1[i], group2[i]])
    # Get groupstage table
    tournament = Tournament()
    groupstage_table = []
    final_standings = []
    groupstage_table = update_gs(request)
    nb_team, nb_bot_team = team_collection.count_groups()
    nb_games = nb_team
    if nb_bot_team <= 0:
        nb_games -= 1
    elif nb_bot_team > 0 and not TOURNAMENT_SETTINGS.get("bot_group", True):
        nb_games += nb_bot_team - 1
    # Get Final
    knockout = tournament.knockout()
    if len(knockout) > 0:
        final_raw = knockout[-1]
    else:
        final_raw = {
            "team1": rating_map[0]["id"],
            "team2": rating_map[1]["id"],
            "winner": rating_map[0]["id"],
            "player_of_the_tournament": Team(rating_map[0]["id"]).find_one(0).get("_id")
        }
    # Get groupstage table
    groupstage_table = update_gs(request)
    for i in groupstage_table:
        if i["status"] == 1:
            i["statusclass"] = "game-won"
        elif i["status"] == -1:
            i["statusclass"] = "game-lost"
        else:
            i["statusclass"] = "game-draw"
        i["rating"] = Team(i["_id"]).get_rating()
        i["rd"] = Team(i["_id"]).get("rating_glicko2").get("rd")
    # Final standings
    if TOURNAMENT_SETTINGS["debug"] is True:
        loser = ""
        if final_raw["winner"] == final_raw["team2"]:
            loser = final_raw["team1"]
        else:
            loser = final_raw["team2"]
        final_standings = [
            {
                "id": final_raw["winner"],
                "name": TOURNAMENT_TEAMS.get(final_raw["winner"]).get("name"),
                "flag": TOURNAMENT_TEAMS.get(final_raw["winner"]).get("flag"),
                "bgcolor": TOURNAMENT_TEAMS.get(final_raw["winner"]).get("color"),
                "groupstage": 1,
                "position": 1,
                "disqualified": False,
                "hanged": False
            },
            {
                "id": loser,
                "name": TOURNAMENT_TEAMS.get(loser).get("name"),
                "flag": TOURNAMENT_TEAMS.get(loser).get("flag"),
                "bgcolor": TOURNAMENT_TEAMS.get(loser).get("color"),
                "groupstage": 2,
                "position": 2,
                "disqualified": False,
                "hanged": False
            }
        ]
    else:
        final_standings = final_standing(groupstage_table)
    # Get groupstage matches
    groupstage_matches_raw = tournament.find()
    groupstage_matches = []
    knockout_matches = []
    final = []
    for game in groupstage_matches_raw:
        groupstage_matches.append(process_groupstagematch_data(game))
    for game in knockout:
        knockout_matches.append(process_groupstagematch_data(game))
    if len(knockout) > 0:
        final = process_groupstagematch_data(final_raw)
    else:
        final = None
    # Player of the Tournament
    pott = final_raw["player_of_the_tournament"]
    if pott == "":
        pott1 = "No Award"
    else:
        pott_map = team_collection.fetch_player_map(pott)
        pott_name = pott_map["player_name"]
        pott_team = pott_map["team_name"]
        pott1 = {
            "id": pott,
            "name": pott_name + " (" + pott_team + ")",
            "player_title": AbstractPlayer(pott).rating_title()
        }
    # Champions
    show_runner_up = True
    champions_id = final_raw["winner"]
    if champions_id == "":
        champions = final_standings[0]["name"] + ", " + final_standings[1]["name"]
        winning_captain = ""
        show_runner_up = False
    else:
        champions_map = TOURNAMENT_TEAMS.get(champions_id)
        champions = champions_map["name"]
        winning_captain = champions_map["members"][0]["name"]
    # runner up
    runners_up = final_standings[1]["name"]
    # nb teams
    nb_team_string = str(nb_team + nb_bot_team)
    # if nb_bot_team > 0:
    #    nb_team_string += " (" + str(nb_team) + " + " + str(nb_bot_team) + " bot teams)"
    num_slots = 2 ** TOURNAMENT_SETTINGS.get("knockout")
    if num_slots >= nb_bot_team + nb_team:
        all_qualified = True
    else:
        all_qualified = False
    # If team flags are on
    if show_runner_up:
        champions = {
            "id": champions_map.get("_id"),
            "name": champions_map.get("name"),
            "flag": champions_map.get("flag"),
            "bgcolor": champions_map.get("color")
        }
        runner_up_team = Team(final_standings[1]["id"])
        runners_up = {
            "id": runner_up_team.get("_id"),
            "name": runner_up_team.get("name"),
            "flag": runner_up_team.get("flag"),
            "bgcolor": runner_up_team.get("color")
        }
    if TOURNAMENT_SETTINGS["team_flag"] is True:
        pott_team = Team(pott_map["team_id"])
        pott1 = {
            "id": pott,
            "name": pott_name,
            "flag": pott_team.get("flag"),
            "bgcolor": pott_team.get("color"),
            "player_title": AbstractPlayer(pott).rating_title()
        }
    # Render
    return render(
        request,
        "index.html",
        {
            "gs_index": [str(i) for i in range(1, nb_games + 1)],
            "groupstage_table": groupstage_table,
            "groupstage_matches": groupstage_matches,
            "final_standings": final_standings,
            "final": final,
            "knockout": knockout_matches,
            "champions": champions,
            "winning_captain": winning_captain,
            "runners_up": runners_up,
            "rating_map": rating_map,
            "pott": pott1,
            "nb_matches": len(groupstage_matches) + len(knockout_matches),
            "nb_groupstage": len(groupstage_matches),
            "nb_participants": nb_team_string,
            "one_winner": show_runner_up,
            "all_qualified": all_qualified,
            "num_slots": num_slots,
            "group_teams": grouping,
            "nb_per_group": range(len(group1)),
            "settings": TOURNAMENT_SETTINGS,
            "hosts": HOST_DICT
        }
    )


def process_groupstagematch_data(data):
    output = {}
    output["id"] = data["_id"]
    output["qualified"] = []
    output["eliminated"] = []
    output["disqualified"] = []
    output["enable_notes"] = False
    output["enable_potm"] = True
    if data["_id"][0] == "m":
        split_match_id = data["_id"].split("_")
        output["week"] = str(int(split_match_id[1]))
        output["match_code"] = str(int(split_match_id[2]))
    else:
        output["match_code"] = str(data["_id"])
        output["week"] = ""
    team_collection = TeamCollection()
    team1 = team_collection.find_one(data["team1"])
    team2 = team_collection.find_one(data["team2"])
    output["team1"] = data["team1"]
    output["team2"] = data["team2"]
    output["team1_name"] = team1["name"]
    output["team2_name"] = team2["name"]
    output["team1_rating"] = round(data["rating_initial"][data["team1"]]["rating"])
    output["team2_rating"] = round(data["rating_initial"][data["team2"]]["rating"])
    output["team1_rdiff"] = data["rc1"]
    output["team2_rdiff"] = data["rc2"]
    output["team1_flag"] = team1.get("flag")
    output["team2_flag"] = team2.get("flag")
    output["team1_flagcolor"] = team1.get("color")
    output["team2_flagcolor"] = team2.get("color")
    if data.get("played", True):
        output["score1"] = format_score(
            data["innings"][0]["score"],
            data["innings"][0]["wickets"],
            data["innings"][0]["declared"]
        )
        output["balls1"] = format_over_string(
            data["innings"][0]["balls"]
        )
    else:
        output["score1"] = ""
        output["balls1"] = ""
    output["score2"] = ""
    output["balls2"] = ""
    output["score3"] = ""
    output["balls3"] = ""
    output["score4"] = ""
    output["balls4"] = ""
    output["second_innings"] = False
    if len(data["innings"]) > 1:
        output["score2"] = format_score(
            data["innings"][1]["score"],
            data["innings"][1]["wickets"],
            data["innings"][1]["declared"]
        )
        output["balls2"] = format_over_string(
            data["innings"][1]["balls"]
        )
    elif data.get("played", True):
        output["score2"] = "Did Not Bat"
        output["balls2"] = "-"
    if len(data["innings"]) > 2:
        output["second_innings"] = True
        if data["follow_on"]:
            output["score4"] = format_score(
                data["innings"][2]["score"],
                data["innings"][2]["wickets"],
                data["innings"][2]["declared"]
            )
            output["balls4"] = format_over_string(
                data["innings"][2]["balls"]
            )
        else:
            output["score3"] = format_score(
                data["innings"][2]["score"],
                data["innings"][2]["wickets"],
                data["innings"][2]["declared"]
            )
            output["balls3"] = format_over_string(
                data["innings"][2]["balls"]
            )
    if len(data["innings"]) > 3:
        if data["follow_on"]:
            output["score3"] = format_score(
                data["innings"][3]["score"],
                data["innings"][3]["wickets"],
                data["innings"][3]["declared"]
            )
            output["balls3"] = format_over_string(
                data["innings"][3]["balls"]
            )
        else:
            output["score4"] = format_score(
                data["innings"][3]["score"],
                data["innings"][3]["wickets"],
                data["innings"][3]["declared"]
            )
            output["balls4"] = format_over_string(
                data["innings"][3]["balls"]
            )
    else:
        if data["follow_on"]:
            output["score3"] = "_"
            output["balls3"] = "_"
        else:
            output["score4"] = "_"
            output["balls4"] = "_"
    try:
        winner_name = team_collection.find_one(data["winner"])["name"]
    except TypeError:
        winner_name = None
    output["win_string"] = format_winstring(winner_name, data["margin"])
    try:
        potm = data["player_of_the_match"]
        potm_team_map = team_collection.fetch_player_map(potm)
        potm_team = potm_team_map["team_name"]
        potm_name = potm_team_map["player_name"]
        output["potm"] = potm_name + " (" + potm_team + ")"
        output["potm_id"] = potm
        output["potm_player_title"] = AbstractPlayer(potm).rating_title()
    except KeyError:
        output["potm"] = "Award forfeited"
    except TypeError:
        output["potm"] = "Award forfeited"
    except AttributeError:
        output["potm"] = "Award forfeited"
    if str(data.get("margin", "")).lower() in ["walkover", "match cancelled", "disciplinary forfeit"]:
        output["potm"] = ""
        output["enable_potm"] = False
    if data.get("disqualifications") is not None:
        output["enable_notes"] = True
        for i in data["disqualifications"]:
            output["disqualified"].append(team_collection.find_one(i)["name"])
    return output


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


def format_bat_topper_string(batter):
    playermap = TeamCollection()
    batter_team_map = playermap.fetch_player_map(batter["_id"])
    batter_collection = playermap.get(batter_team_map["team_id"])
    color = batter_collection.get("color")
    data = batter_collection.find_one(batter["_id"])
    output = data["name"]
    output += " "
    output += str(batter["runs"])
    if not batter["dismissed"]:
        output += "*"
    output += " ("
    output += str(batter["balls"])
    output += ")"
    return output


def format_bowl_topper_string(bowler):
    playermap = TeamCollection()
    batter_team_map = playermap.fetch_player_map(bowler["_id"])
    batter_collection = playermap.get(batter_team_map["team_id"])
    color = batter_collection.get("color")
    data = batter_collection.find_one(bowler["_id"])
    output = data["name"]
    output += " "
    output += str(bowler["wickets"])
    output += "/"
    output += str(bowler["runs"])
    output += " ("
    output += format_over_string(bowler["balls"])
    output += ")"
    return output


def format_over_string(balls):
    output = ''
    if balls >= 6:
        output += str(balls // 6)
        output += " Over"
        if (balls // 6) > 1:
            output += "s"
    if balls > 6 and balls % 6 > 0:
        output += " "
    if balls % 6 > 0:
        output += str(balls % 6)
        output += " Ball"
        if (balls % 6 > 1):
            output += "s"
    if balls == 0:
        output = "0 Balls"
    return output
