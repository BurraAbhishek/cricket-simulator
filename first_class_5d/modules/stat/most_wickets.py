from django.shortcuts import render
from bin.mongoinserts.load_teams import TOURNAMENT_TEAMS
from bin.models.team import AbstractPlayer
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS
from modules.stat.all_games import get_all_games


def wicket_object(id, name, t_id, t_name, t_color, t_flag):
    return {
        "id": id,
        "name": name,
        "team_id": t_id,
        "team_name": t_name,
        "team_color": t_color,
        "team_flag": t_flag,
        "balls": 0,
        "dots": 0,
        "maidens": 0,
        "runs": 0,
        "wickets": 0,
        "matches": 0,
        "avatar": AbstractPlayer(id).avatar(),
        "rating": AbstractPlayer(id).get("rating_bowl"),
        "player_title": AbstractPlayer(id).rating_title(),
        "disqualified": AbstractPlayer(id).disqualified()
    }


def get_all_bowlers():
    team_list = TOURNAMENT_TEAMS.keys()
    bowlers_dict = {}
    bowlers_list = []
    for i in team_list:
        j1 = TOURNAMENT_TEAMS[i]["members"]
        j2 = TOURNAMENT_TEAMS[i]["name"]
        j3 = TOURNAMENT_TEAMS[i].get("color")
        j4 = TOURNAMENT_TEAMS[i].get("flag")
        for k in j1:
            bowlers_dict[k["_id"]] = wicket_object(
                k["_id"],
                k["name"],
                i,
                j2,
                j3,
                j4
            )
    # Search all matches
    games = get_all_games()
    for i in games:
        for i0 in i["innings"]:
            for j in i0["bowler_stats"]:
                bowlers_dict[j["_id"]]["runs"] += j["runs"]
                bowlers_dict[j["_id"]]["dots"] += j["dots"]
                bowlers_dict[j["_id"]]["maidens"] += j["maidens"]
                bowlers_dict[j["_id"]]["balls"] += j["balls"]
                bowlers_dict[j["_id"]]["wickets"] += j["wickets"]
                if j["balls"] > 0:
                    bowlers_dict[j["_id"]]["matches"] += 1
    for i in bowlers_dict.keys():
        if bowlers_dict[i]["balls"] > 0 and not bowlers_dict[i]["disqualified"]:
            bowlers_list.append(bowlers_dict[i])
    return bowlers_list


def render_most_wickets(request):
    bowlers_list = get_all_bowlers()
    bowlers_list.sort(key=lambda x: x["runs"])
    bowlers_list.sort(key=lambda x: x["wickets"], reverse=True)
    if len(bowlers_list) > 0:
        rank = 1
        skip = 0
        wickets = bowlers_list[0]["wickets"]
        for i in bowlers_list:
            if i["wickets"] < wickets:
                rank += skip
                skip = 1
            else:
                skip += 1
            i["rank"] = rank
            wickets = i["wickets"]
    return render(
        request,
        "stat/most_wickets.html",
        {
            "stat": bowlers_list,
            "settings": TOURNAMENT_SETTINGS
        }
    )


def render_best_economy(request):
    bowlers_list = get_all_bowlers()
    for i in bowlers_list:
        if i["balls"] <= 0:
            i["economy"] = 36
        else:
            i["economy"] = 6 * i["runs"] / i["balls"]
    bowlers_list.sort(key=lambda x: x["runs"])
    bowlers_list.sort(key=lambda x: x["wickets"], reverse=True)
    bowlers_list.sort(key=lambda x: x["runs"] / (1 + x["balls"]))
    bowlers_list.sort(key=lambda x: x["economy"])
    bowlers_list.sort(key=lambda x: 1 if x["balls"] <= 0 else 0)
    if len(bowlers_list) > 0:
        rank = 1
        skip = 0
        n = bowlers_list[0]["economy"]
        for i in bowlers_list:
            if i["economy"] > n:
                rank += skip
                skip = 1
            else:
                skip += 1
            i["rank"] = rank
            n = i["economy"]
    return render(
        request,
        "stat/best_economy.html",
        {
            "stat": bowlers_list,
            "settings": TOURNAMENT_SETTINGS,
            "title": "economy"
        }
    )


def render_best_bowling_average(request):
    bowlers_list = get_all_bowlers()
    for i in bowlers_list:
        if i["wickets"] <= 0:
            i["bowling_average"] = i["runs"]
        else:
            i["bowling_average"] = i["runs"] / i["wickets"]
    bowlers_list.sort(key=lambda x: x["runs"])
    bowlers_list.sort(key=lambda x: x["wickets"], reverse=True)
    bowlers_list.sort(key=lambda x: x["runs"] / (1 + x["wickets"]))
    bowlers_list.sort(key=lambda x: x["bowling_average"])
    bowlers_list.sort(key=lambda x: 1 if x["wickets"] <= 0 else 0)
    if len(bowlers_list) > 0:
        rank = 1
        skip = 0
        n = bowlers_list[0]["bowling_average"]
        for i in bowlers_list:
            if i["bowling_average"] > n and i["wickets"] > 0:
                rank += skip
                skip = 1
            else:
                skip += 1
            if i["wickets"] == 0:
                i["rank"] = rank + 1
            else:
                i["rank"] = rank
            n = i["bowling_average"]
    return render(
        request,
        "stat/best_economy.html",
        {
            "stat": bowlers_list,
            "settings": TOURNAMENT_SETTINGS,
            "title": "average"
        }
    )
