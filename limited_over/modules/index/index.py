from django.shortcuts import render
from bin.models.team import Team, TeamCollection, AbstractPlayer
from bin.models.role import Batter, Bowler
from bin.mongoinserts.load_teams import TOURNAMENT_TEAMS
from bin.mongoinserts.load_games import TOURNAMENT_GAMES
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS
from bin.mongoinserts.groupstage import update_gs, final_standing
from bin.mongoinserts.eligibility import QUALIFIED, ELIMINATED
from bin.mongoinserts.team.hostteam import HOST_DICT
from modules.index import match_toppers
from modules.index.summary import format_score
from modules.stat.most_runs import get_all_batters, run_object
from modules.stat.most_wickets import get_all_bowlers, wicket_object


def index(request):
    # Team-rating mapping
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
    # Toss Choices
    toss_choices = []
    for i in TOURNAMENT_TEAMS.keys():
        if not Team(i).ai():
            if TOURNAMENT_SETTINGS["decision"] == 1:
                toss = 1
            else:
                toss = 2
            toss_choices.append(
                {
                    "id": i,
                    "name": TOURNAMENT_TEAMS[i]["name"],
                    "flag": TOURNAMENT_TEAMS[i]["flag"],
                    "color": TOURNAMENT_TEAMS[i]["color"],
                    "rating": TOURNAMENT_TEAMS[i]["rating"],
                    "toss": toss
                }
            )
    # Get Final
    knockout = TOURNAMENT_GAMES["knockout"]
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
        i["rating"] = TOURNAMENT_TEAMS[i["_id"]]["rating_glicko2"]['rating']
        i["rd"] = TOURNAMENT_TEAMS[i["_id"]]["rating_glicko2"]['rd']
    # Final standings
    nb_team = 0
    nb_bot_team = 0
    for i in TOURNAMENT_TEAMS.keys():
        if Team(i).ai():
            nb_bot_team += 1
        else:
            nb_team += 1
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
            },
            {
                "id": loser,
                "name": TOURNAMENT_TEAMS.get(loser).get("name"),
                "flag": TOURNAMENT_TEAMS.get(loser).get("flag"),
                "bgcolor": TOURNAMENT_TEAMS.get(loser).get("color"),
                "groupstage": 2,
                "position": 2,
            }
        ]
    else:
        final_standings = final_standing(groupstage_table)
    # Get groupstage matches
    groupstage_matches_raw = TOURNAMENT_GAMES["groupstage"]
    groupstage_matches = []
    knockout_matches = []
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
        pott1 = {
            "id": None,
            "name": "No Award",
            "team": None,
            "player_title": {"id": "None", "name": ""}
        }
    else:
        pott_map = TeamCollection().fetch_player_map(pott)
        pott_name = pott_map["player_name"]
        pott_team_id = pott_map["team_id"]
        pott_team = pott_map["team_name"]
        pott1 = {
            "id": pott,
            "name": pott_name,
            "team": pott_team,
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
    nb_team_string = str(len(final_standings))
    if nb_team > 0 and nb_bot_team > 0:
        nb_team_string += " (" + str(nb_team) + " + " + str(nb_bot_team) + " bot teams)"
    elif nb_bot_team > 0:
        nb_team_string += " (" + str(nb_bot_team) + " bot teams)"
    nb_team_string = str(nb_team + nb_bot_team)
    # most runs
    batters_list = [] + get_all_batters()
    if len(batters_list) > 0:
        batters_list.sort(key=lambda x: x["balls"])
        batters_list.sort(key=lambda x: x["runs"], reverse=True)
        bat_topper = batters_list[0]
    else:
        bat_topper = run_object(
            pott,
            pott_name,
            pott_team_id,
            Team(pott_map["team_id"]).get("name"),
            Team(pott_map["team_id"]).get("flag"),
            Team(pott_map["team_id"]).get("color")
        )
    most_runs_id = bat_topper["id"]
    most_runs_name = bat_topper["name"]
    most_runs_team = bat_topper["team_name"]
    most_runs_value = bat_topper["runs"]
    # most wickets
    bowlers_list = [] + get_all_bowlers()
    if len(bowlers_list) > 0:
        bowlers_list.sort(key=lambda x: x["runs"])
        bowlers_list.sort(key=lambda x: x["wickets"], reverse=True)
        bowl_topper = bowlers_list[0]
    else:
        bowl_topper = wicket_object(
            pott,
            pott_name,
            pott_team_id,
            Team(pott_map["team_id"]).get("name"),
            Team(pott_map["team_id"]).get("flag"),
            Team(pott_map["team_id"]).get("color")
        )
    most_wickets_id = bowl_topper["id"]
    most_wickets_name = bowl_topper["name"]
    most_wickets_team = bowl_topper["team_name"]
    most_wickets_value = bowl_topper["wickets"]
    if TOURNAMENT_SETTINGS["knockout"] == 1:
        ko = "final"
    elif TOURNAMENT_SETTINGS["knockout"] == 2:
        ko = "semi-finals"
    elif TOURNAMENT_SETTINGS["knockout"] == 3:
        ko = "quarter-finals"
    else:
        ko = "knockout"
    num_slots = 2 ** TOURNAMENT_SETTINGS["knockout"]
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
        most_runs_team_object = Team(bat_topper["team_id"])
        most_wickets_team_object = Team(bowl_topper["team_id"])
        pott1 = {
            "id": pott,
            "name": pott_name,
            "flag": pott_team.get("flag"),
            "bgcolor": pott_team.get("color"),
            "player_title": AbstractPlayer(pott).rating_title()
        }
        most_runs_team = {
            "name": most_runs_team_object.get("name"),
            "flag": most_runs_team_object.get("flag"),
            "bgcolor": most_runs_team_object.get("color")
        }
        most_wickets_team = {
            "name": most_wickets_team_object.get("name"),
            "flag": most_wickets_team_object.get("flag"),
            "bgcolor": most_wickets_team_object.get("color")
        }
    # Render
    return render(
        request,
        "index.html",
        {
            "groupstage_table": groupstage_table,
            "groupstage_matches": groupstage_matches,
            "final_standings": final_standings,
            "final": final,
            "knockout": knockout_matches,
            "champions": champions,
            "winning_captain": winning_captain,
            "runners_up": runners_up,
            "rating_map": rating_map,
            "toss_choices": toss_choices,
            "pott": pott1,
            "nb_matches": len(groupstage_matches) + len(knockout_matches),
            "nb_participants": nb_team_string,
            "one_winner": show_runner_up,
            "most_runs_id": most_runs_id,
            "most_runs_name": most_runs_name,
            "most_runs_team": most_runs_team,
            "most_runs_value": format_thousands(most_runs_value),
            "most_runs_title": AbstractPlayer(bat_topper["id"]).rating_title(),
            "most_wickets_id": most_wickets_id,
            "most_wickets_name": most_wickets_name,
            "most_wickets_team": most_wickets_team,
            "most_wickets_value": format_thousands(most_wickets_value),
            "most_wickets_title": AbstractPlayer(bowl_topper["id"]).rating_title(),
            "settings": TOURNAMENT_SETTINGS,
            "all_qualified": all_qualified,
            "num_slots": num_slots,
            "ko": ko,
            "ko_start": len(groupstage_matches),
            "group_teams": grouping,
            "hosts": HOST_DICT
        }
    )


def process_groupstagematch_data(data):
    output = {}
    output["id"] = data["_id"]
    output["qualified"] = []
    output["eliminated"] = []
    output["enable_notes"] = False
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
    output["score1"] = format_score(
        data["innings"][0]["score"],
        data["innings"][0]["wickets"]
    )
    output["score2"] = format_score(
        data["innings"][1]["score"],
        data["innings"][1]["wickets"]
    )
    output["balls1"] = format_over_string(
        data["innings"][0]["balls"]
    )
    output["balls2"] = format_over_string(
        data["innings"][1]["balls"]
    )
    try:
        winner_name = team_collection.find_one(data["winner"])["name"]
    except TypeError:
        winner_name = None
    output["win_string"] = format_winstring(winner_name, data["margin"])
    # Toppers
    batter1 = match_toppers.get_inning_toppers_bat(data, 0)[0]
    batter2 = match_toppers.get_inning_toppers_bat(data, 1)[0]
    bowler1 = match_toppers.get_inning_toppers_bowl(data, 0)[0]
    bowler2 = match_toppers.get_inning_toppers_bowl(data, 1)[0]
    # what we can show
    bat1flag = True
    bat2flag = True
    bowl1flag = True
    bowl2flag = True
    output["show_1"] = True
    output["show_2"] = True
    if batter1.runs < 1:
        bat1flag = False
    if batter2.runs < 1:
        bat2flag = False
    if bowler1.wickets < 1:
        bowl1flag = False
    if bowler2.wickets < 1:
        bowl2flag = False
    # Placeholders
    p1up = None
    p2up = None
    p1dn = None
    p2dn = None
    # nbsp
    output["p1upnbsp"] = False
    output["p2upnbsp"] = False
    output["p1nbsp"] = False
    output["p2nbsp"] = False
    # Now check
    if (not bat1flag) and (not bowl1flag) and (not bat2flag) and (not bowl2flag):
        output["show_1"] = False
        output["show_2"] = False
    elif (bat1flag) and (not bowl1flag) and (not bat2flag) and (not bowl2flag):
        p1up = format_bat_topper_string(batter1)
        output["p2upnbsp"] = True
        output["show_2"] = False
    elif (not bat1flag) and (bowl1flag) and (not bat2flag) and (not bowl2flag):
        p1up = format_bowl_topper_string(bowler1)
        output["p2upnbsp"] = True
        output["show_2"] = False
    elif (not bat1flag) and (not bowl1flag) and (bat2flag) and (not bowl2flag):
        p2up = format_bat_topper_string(batter2)
        output["p1upnbsp"] = True
        output["show_2"] = False
    elif (not bat1flag) and (not bowl1flag) and (not bat2flag) and (bowl2flag):
        p2up = format_bowl_topper_string(bowler2)
        output["p1upnbsp"] = True
        output["show_2"] = False
    elif (not bowl1flag) and (not bowl2flag):
        if bat1flag:
            p1up = format_bat_topper_string(batter1)
        if bat2flag:
            p2up = format_bat_topper_string(batter2)
        output["show_2"] = False
    elif (not bat1flag) and (not bat2flag):
        if bowl1flag:
            p1up = format_bowl_topper_string(bowler1)
        if bowl2flag:
            p2up = format_bowl_topper_string(bowler2)
        output["show_2"] = False
    elif (not bat1flag) and (not bowl2flag):
        if bowl1flag:
            p1up = format_bowl_topper_string(bowler1)
        if bat2flag:
            p2up = format_bat_topper_string(batter2)
        output["show_2"] = False
    elif (not bowl1flag) and (not bat2flag):
        if bat1flag:
            p1up = format_bat_topper_string(batter1)
        if bowl2flag:
            p2up = format_bowl_topper_string(bowler2)
        output["show_2"] = False
    else:
        if bat1flag:
            p1up = format_bat_topper_string(batter1)
        else:
            p1up = ""
            output["p1upnbsp"] = True
        if bat2flag:
            p2up = format_bat_topper_string(batter2)
        else:
            p2up = ""
            output["p2upnbsp"] = True
        if bowl1flag:
            p1dn = format_bowl_topper_string(bowler1)
        else:
            p1dn = ""
            output["p1nbsp"] = True
        if bowl2flag:
            p2dn = format_bowl_topper_string(bowler2)
        else:
            p2dn = ""
            output["p2nbsp"] = True
    output["p1up"] = p1up
    output["p2up"] = p2up
    output["p1dn"] = p1dn
    output["p2dn"] = p2dn
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
    # Qualified and eliminated
    if len(QUALIFIED) > 0:
        output["enable_notes"] = True
        for i in QUALIFIED:
            if i["match"] == output["id"]:
                output["qualified"].append(
                    team_collection.find_one(i["team"])["name"]
                )
    if len(ELIMINATED) > 0:
        output["enable_notes"] = True
        for i in ELIMINATED:
            if i["match"] == output["id"]:
                output["eliminated"].append(
                    team_collection.find_one(i["team"])["name"]
                )
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


def format_bat_topper_string(batter: Batter):
    new_output = {
        "id": batter.id(),
        "type": "batter",
        "name": batter.name(),
        "color": batter.color(),
        "runs": batter.runs,
        "balls": batter.balls,
        "out": batter.dismissed,
        "player_title": batter.rating_title()
    }
    return new_output


def format_bowl_topper_string(bowler: Bowler):
    new_output = {
        "id": bowler.id(),
        "type": "bowler",
        "name": bowler.name(),
        "color": bowler.color(),
        "wickets": bowler.wickets,
        "runs": bowler.runs,
        "balls": format_over_string(bowler.balls),
        "player_title": bowler.rating_title()
    }
    return new_output


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


def format_thousands(nb: int) -> str:
    if nb >= 1000000:
        return str(nb)[:-6] + "," + str(nb)[-6:-3] + "," + str(nb)[-3:]
    if nb >= 1000:
        return str(nb)[:-3] + "," + str(nb)[-3:]
    return str(nb) 
