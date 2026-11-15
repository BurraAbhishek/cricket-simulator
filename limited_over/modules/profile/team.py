from django.shortcuts import render
from django.http import HttpResponseNotFound, HttpResponseRedirect
from bin.models.team import Team, TeamCollection, AbstractPlayer
from bin.mongoinserts.team.hostteam import HOST_TEAMS
from bin.mongoinserts.load_games import TOURNAMENT_GAMES
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS
from bin.mongoinserts.groupstage import update_gs, final_standing
from modules.index.index import process_groupstagematch_data
from modules.index.team_progression import get_team_progression


def get_lineup(request, id: str):
    try:
        team = TeamCollection().find_one(id)
        if team is None:
            return HttpResponseNotFound("Team unavailable")
    except TypeError:
        return HttpResponseNotFound("Team unavailable")
    members = team["members"]
    for i in members:
        i["id"] = i["_id"]
        i["approved_avatar"] = AbstractPlayer(i["_id"]).avatar()
        i["player_title"] = AbstractPlayer(i["_id"]).rating_title()
        i["selected_rating"] = int((i["rating_bat"] + i["rating_bowl"] + i["rating_field"]) / 3)
    # Top, middle, lower order
    try:
        batting_orders = team["batting_orders"]
    except KeyError:
        batting_orders = [4, 4, 3]
    if TOURNAMENT_SETTINGS.get("batting_order_render", False):
        t1 = batting_orders[0]
        t2 = batting_orders[0] + batting_orders[1]
        batting_order = [
            members[:t1], # Top order
            members[t1:t2], # Middle order
            members[t2:11], # Lower order / Tail Fortress
            members[11:] # Substitutes
        ]
    else:
        split_index = 5
        if batting_orders[0] + batting_orders[1] == 6:
            split_index = 6
        elif batting_orders[0] == 4 and batting_orders[1] == 4:
            split_index = 6
        elif batting_orders[0] == 3 and batting_orders[1] == 5:
            split_index = 6
        batting_order = [members[:split_index], members[split_index:11], members[11:]]
    return render(
        request,
        "lineup.html",
        {
            "team": team,
            "batting_orders": batting_order
        }
    )


def get_team(request, id: str):
    try:
        team = TeamCollection().find_one(id)
        if team is None:
            return HttpResponseNotFound("Team unavailable")
    except TypeError:
        return HttpResponseNotFound("Team unavailable")
    team["id"] = team["_id"]
    team_member_list = []
    flag = {}
    if TOURNAMENT_SETTINGS.get("team_flag", False) is True:
        flag = {
            "bgcolor": team.get("color"),
            "flag": team.get("flag")
        }
    for i in team["members"]:
        name = i["name"]
        if (
            i["captain"] is True 
            or i["wicketkeeper"] is True
        ):
            name += " "
            if i["captain"] is True and i["wicketkeeper"] is True:
                name += "(c) (wk)"
            elif i["captain"] is True:
                name += "(c)"
            elif i["wicketkeeper"] is True:
                name += "(wk)"
        team_member_list.append({
            "name": name,
            "id": i["_id"],
            "player_title": AbstractPlayer(i["_id"]).rating_title()
        })
    knockout_raw = TOURNAMENT_GAMES["knockout"]
    groupstage_matches_raw = TOURNAMENT_GAMES["groupstage"]
    campaign = False
    if len(knockout_raw) > 0 or len(groupstage_matches_raw) > 0:
        campaign = True
    groupstage_table = update_gs(request)
    if len(knockout_raw) > 0:
        final_table = final_standing(groupstage_table)
    else:
        final_table = []
        for i, e in enumerate(groupstage_table, start=1):
            final_table.append(
                {
                    "id": e["_id"],
                    "name": e["name"],
                    "flag": e["flag"],
                    "bgcolor": e["bgcolor"],
                    "groupstage": i,
                    "position": i,
                }
            )
    for i, e in enumerate(groupstage_table, start=1):
        if e["_id"] == id:
            groupstage_result = i
            break
    for i, e in enumerate(final_table, start=1):
        if e["id"] == id:
            final_result = i
            break
    groupstage_campaign, final_campaign = get_team_progression(request, id)
    # Get groupstage matches
    num_groupstage = 0
    for i in groupstage_matches_raw:
        num_groupstage += len(i)
    groupstage_matches = []
    ratings = [Team(id).init_rating()]
    rating_labels = ["Initial Rating"]
    match_number = 1
    round_number = 1
    for game in groupstage_matches_raw:
        game_result = process_groupstagematch_data(game)
        game_result["result_class"] = "match-summary-default"
        game_result["match_number"] = match_number
        if game["winner"] == id:
            game_result["result_class"] = "match-summary-win"
        elif game["winner"] == game["team1"] and id == game["team2"]:
            game_result["result_class"] = "match-summary-loss"
        elif game["winner"] == game["team2"] and id == game["team1"]:
            game_result["result_class"] = "match-summary-loss"
        elif game["winner"] == "" and game["margin"] == "Double Forfeit":
            game_result["result_class"] = "match-summary-loss"
        if game["team1"] == id or game["team2"] == id:
            groupstage_matches.append(game_result)
            ratings.append(game["rating_final"][id]["rating"])
            rating_labels.append("Round " + str(round_number))
            round_number += 1
        match_number += 1
    # Get Final
    if TOURNAMENT_SETTINGS["knockout"] == 1:
        if len(knockout_raw) > 0:
            final_raw = TOURNAMENT_GAMES["knockout"][-1]
            final = process_groupstagematch_data(final_raw)
            final["result_class"] = "match-summary-default"
            final["match_number"] = match_number
            if final_raw["winner"] == id:
                final["result_class"] = "match-summary-win"
            elif final_raw["winner"] == final_raw["team1"] and id == final_raw["team2"]:
                final["result_class"] = "match-summary-loss"
            elif final_raw["winner"] == final_raw["team2"] and id == final_raw["team1"]:
                final["result_class"] = "match-summary-loss"
            if final_raw["team1"] == id or final_raw["team2"] == id:
                ratings.append(final_raw["rating_final"][id]["rating"])
                rating_labels.append("Final")
        else:
            final = None
        return render(
            request,
            "team.html",
            {
                "team": team,
                "members": team_member_list,
                "groupstage_position": groupstage_result,
                "placement": final_result,
                "groupstage_campaign": groupstage_campaign,
                "final_campaign": final_campaign,
                "groupstage_matches": groupstage_matches,
                "final": final,
                "ko": "final",
                "settings": TOURNAMENT_SETTINGS,
                "flag": flag,
                "show_games": campaign,
                "ratings": ratings,
                "rating_labels": rating_labels,
                "tournament_games": len(groupstage_matches_raw) + 1,
                "show_rating_chart": TOURNAMENT_SETTINGS.get("show_rating_chart", True)
            }
        )
    else:
        ko_games = []
        for game in knockout_raw:
            game_result = process_groupstagematch_data(game)
            game_result["result_class"] = "match-summary-default"
            game_result["match_number"] = match_number
            if game["winner"] == id:
                game_result["result_class"] = "match-summary-win"
            elif game["winner"] == game["team1"] and id == game["team2"]:
                game_result["result_class"] = "match-summary-loss"
            elif game["winner"] == game["team2"] and id == game["team1"]:
                game_result["result_class"] = "match-summary-loss"
            if game["team1"] == id or game["team2"] == id:
                ko_games.append(game_result)
                ratings.append(game["rating_final"][id]["rating"])
                if game["_id"] == "final":
                    rating_labels.append("Final")
                elif game["_id"] == "thirdplace":
                    rating_labels.append("Third Place Playoff")
                elif game["_id"] in ["sf1", "sf2"]:
                    rating_labels.append("Semi-Final")
                elif game["_id"] in ["qf1", "qf2", "qf3", "qf4"]:
                    rating_labels.append("Quarter-Final")
                else:
                    game_id = game["_id"].split("_")[0][1:]
                    rating_labels.append("Round of " + game_id)
            match_number += 1
        return render(
            request,
            "team.html",
            {
                "team": team,
                "members": team_member_list,
                "groupstage_position": groupstage_result,
                "placement": final_result,
                "groupstage_campaign": groupstage_campaign,
                "final_campaign": final_campaign,
                "groupstage_matches": groupstage_matches,
                "final": ko_games,
                "ko": "final",
                "settings": TOURNAMENT_SETTINGS,
                "flag": flag,
                "show_games": campaign,
                "ratings": ratings,
                "rating_labels": rating_labels,
                "tournament_games": len(groupstage_matches_raw) + len(knockout_raw),
                "show_rating_chart": TOURNAMENT_SETTINGS.get("show_rating_chart", True)
            }
        )


def get_result(request, id: str):
    team_data = Team(id).as_dict()
    try:
        return render(
            request,
            "result/" + id + "/index.html",
            {
                "team": team_data,
                "teams": HOST_TEAMS
            }
        )
    except Exception as _:
        return HttpResponseRedirect("/team/" + id)


def get_result_page(request, id: str, page: str):
    team_data = Team(id).as_dict()
    try:
        return render(
            request,
            "result/" + id + "/" + page + ".html",
            {
                "team": team_data,
                "teams": HOST_TEAMS
            }
        )
    except Exception as _:
        return HttpResponseRedirect("/team/" + id + "/result")
