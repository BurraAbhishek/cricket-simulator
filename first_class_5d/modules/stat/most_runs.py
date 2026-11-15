from django.shortcuts import render
from bin.mongoinserts.load_teams import TOURNAMENT_TEAMS
from bin.models.team import AbstractPlayer
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS
from modules.stat.all_games import get_all_games


def run_object(id, name, t_id, t_name, t_color, t_flag):
    return {
        "id": id,
        "name": name,
        "team_id": t_id,
        "team_name": t_name,
        "team_color": t_color,
        "team_flag": t_flag,
        "rank": 0,
        "50": 0,
        "100": 0,
        "200": 0,
        "runs": 0,
        "balls": 0,
        "fours": 0,
        "sixes": 0,
        "wickets": 0,
        "matches": 0,
        "avatar": AbstractPlayer(id).avatar(),
        "rating": AbstractPlayer(id).get("rating_bat"),
        "player_title": AbstractPlayer(id).rating_title(),
        "disqualified": AbstractPlayer(id).disqualified()
    }


def get_all_batters():
    team_list = TOURNAMENT_TEAMS.keys()
    batters_dict = {}
    batters_list = []
    for i in team_list:
        j1 = TOURNAMENT_TEAMS[i]["members"]
        j2 = TOURNAMENT_TEAMS[i]["name"]
        j3 = TOURNAMENT_TEAMS[i].get("color")
        j4 = TOURNAMENT_TEAMS[i].get("flag")
        for k in j1:
            batters_dict[k["_id"]] = run_object(
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
            for j in i0["batter_stats"]:
                batters_dict[j["_id"]]["runs"] += j["runs"]
                batters_dict[j["_id"]]["balls"] += j["balls"]
                try:
                    batters_dict[j["_id"]]["fours"] += j["scoring"][4]
                    batters_dict[j["_id"]]["sixes"] += j["scoring"][6]
                except KeyError:
                    batters_dict[j["_id"]]["fours"] += j["fours"]
                    batters_dict[j["_id"]]["sixes"] += j["sixes"]
                if j["runs"] >= 50:
                    batters_dict[j["_id"]]["50"] += 1
                if j["runs"] >= 100:
                    batters_dict[j["_id"]]["100"] += 1
                if j["runs"] >= 200:
                    batters_dict[j["_id"]]["200"] += 1
                if j["dismissed"]:
                    batters_dict[j["_id"]]["wickets"] += 1
                if j["balls"] > 0 or j["dismissed"]:
                    batters_dict[j["_id"]]["matches"] += 1
    for i in batters_dict.keys():
        if batters_dict[i]["balls"] > 0 and not batters_dict[i]["disqualified"]:
            batters_list.append(batters_dict[i])
    return [] + batters_list


def render_most_runs(request):
    batters_list = get_all_batters()
    batters_list.sort(key=lambda x: x["balls"])
    batters_list.sort(key=lambda x: x["runs"], reverse=True)
    if len(batters_list) > 0:
        rank = 1
        skip = 0
        runs = batters_list[0]["runs"]
        for i in batters_list:
            if i["runs"] < runs:
                rank += skip
                skip = 1
            else:
                skip += 1
            i["rank"] = rank
            runs = i["runs"]
    return render(
        request,
        "stat/most_runs.html",
        {
            "stat": batters_list,
            "criterion": "Runs",
            "settings": TOURNAMENT_SETTINGS
        }
    )


def render_most_fours(request):
    batters_list = get_all_batters()
    batters_list.sort(key=lambda x: x["balls"])
    batters_list.sort(key=lambda x: x["runs"], reverse=True)
    batters_list.sort(key=lambda x: x["fours"], reverse=True)
    if len(batters_list) > 0:
        rank = 1
        skip = 0
        fours = batters_list[0]["fours"]
        for i in batters_list:
            if i["fours"] < fours:
                rank += skip
                skip = 1
            else:
                skip += 1
            i["rank"] = rank
            fours = i["fours"]
    return render(
        request,
        "stat/most_runs.html",
        {
            "stat": batters_list,
            "criterion": "Fours",
            "settings": TOURNAMENT_SETTINGS
        }
    )


def render_most_sixes(request):
    batters_list = get_all_batters()
    batters_list.sort(key=lambda x: x["balls"])
    batters_list.sort(key=lambda x: x["runs"], reverse=True)
    batters_list.sort(key=lambda x: x["sixes"], reverse=True)
    if len(batters_list) > 0:
        rank = 1
        skip = 0
        sixes = batters_list[0]["sixes"]
        for i in batters_list:
            if i["sixes"] < sixes:
                rank += skip
                skip = 1
            else:
                skip += 1
            i["rank"] = rank
            sixes = i["sixes"]
    return render(
        request,
        "stat/most_runs.html",
        {
            "stat": batters_list,
            "criterion": "Sixes",
            "settings": TOURNAMENT_SETTINGS
        }
    )


def render_most_boundaries(request):
    batters_list = get_all_batters()
    for i in batters_list:
        i["boundaries"] = i["sixes"] + i["fours"]
    batters_list.sort(key=lambda x: x["balls"])
    batters_list.sort(key=lambda x: x["runs"], reverse=True)
    batters_list.sort(key=lambda x: x["sixes"], reverse=True)
    batters_list.sort(key=lambda x: x["boundaries"], reverse=True)
    if len(batters_list) > 0:
        rank = 1
        skip = 0
        boundaries = batters_list[0]["boundaries"]
        for i in batters_list:
            if i["boundaries"] < boundaries:
                rank += skip
                skip = 1
            else:
                skip += 1
            i["rank"] = rank
            boundaries = i["boundaries"]
    return render(
        request,
        "stat/most_runs.html",
        {
            "stat": batters_list,
            "criterion": "Boundaries",
            "settings": TOURNAMENT_SETTINGS
        }
    )


def render_most_50s(request):
    cutoff = 50
    batters_list_raw = get_all_batters()
    batters_list = []
    for i in batters_list_raw:
        if i[str(cutoff)] > 0:
            batters_list.append(i)
    batters_list.sort(key=lambda x: x["balls"])
    batters_list.sort(key=lambda x: x["runs"], reverse=True)
    batters_list.sort(key=lambda x: x[str(cutoff)], reverse=True)
    if len(batters_list) > 0:
        rank = 1
        skip = 0
        n = batters_list[0][str(cutoff)]
        for i in batters_list:
            if i[str(cutoff)] < n:
                rank += skip
                skip = 1
            else:
                skip += 1
            i["rank"] = rank
            n = i[str(cutoff)]
    return render(
        request,
        "stat/most_runs.html",
        {
            "stat": batters_list,
            "criterion": "Half centuries",
            "settings": TOURNAMENT_SETTINGS
        }
    )


def render_most_100s(request):
    cutoff = 100
    batters_list_raw = get_all_batters()
    batters_list = []
    for i in batters_list_raw:
        if i[str(cutoff)] > 0:
            batters_list.append(i)
    batters_list.sort(key=lambda x: x["balls"])
    batters_list.sort(key=lambda x: x["runs"], reverse=True)
    batters_list.sort(key=lambda x: x[str(cutoff)], reverse=True)
    if len(batters_list) > 0:
        rank = 1
        skip = 0
        n = batters_list[0][str(cutoff)]
        for i in batters_list:
            if i[str(cutoff)] < n:
                rank += skip
                skip = 1
            else:
                skip += 1
            i["rank"] = rank
            n = i[str(cutoff)]
    return render(
        request,
        "stat/most_runs.html",
        {
            "stat": batters_list,
            "criterion": "Centuries",
            "settings": TOURNAMENT_SETTINGS
        }
    )


def render_most_200s(request):
    cutoff = 200
    batters_list_raw = get_all_batters()
    batters_list = []
    for i in batters_list_raw:
        if i[str(cutoff)] > 0:
            batters_list.append(i)
    batters_list.sort(key=lambda x: x["balls"])
    batters_list.sort(key=lambda x: x["runs"], reverse=True)
    batters_list.sort(key=lambda x: x[str(cutoff)], reverse=True)
    if len(batters_list) > 0:
        rank = 1
        skip = 0
        n = batters_list[0][str(cutoff)]
        for i in batters_list:
            if i[str(cutoff)] < n:
                rank += skip
                skip = 1
            else:
                skip += 1
            i["rank"] = rank
            n = i[str(cutoff)]
    return render(
        request,
        "stat/most_runs.html",
        {
            "stat": batters_list,
            "criterion": "Double hundreds",
            "settings": TOURNAMENT_SETTINGS
        }
    )


def render_max_batting_average(request):
    batters_list = get_all_batters()
    for i in batters_list:
        if i["wickets"] < 1:
            i["batting_average"] = i["runs"]
        else:
            i["batting_average"] = i["runs"] / i["wickets"]
    batters_list.sort(key=lambda x: x["balls"])
    batters_list.sort(key=lambda x: x["runs"] / (1 + x["balls"]), reverse=True)
    batters_list.sort(key=lambda x: x["wickets"])
    batters_list.sort(key=lambda x: x["runs"], reverse=True)
    batters_list.sort(key=lambda x: x["runs"] / (1 + x["wickets"]), reverse=True)
    batters_list.sort(key=lambda x: x["batting_average"], reverse=True)
    batters_list.sort(key=lambda x: 1 if x["wickets"] <= 0 else 0, reverse=True)
    if len(batters_list) > 0:
        rank = 1
        skip = 0
        zero_wicket = True
        n = batters_list[0]["batting_average"]
        for i in batters_list:
            if zero_wicket:
                if i["wickets"] > 0:
                    rank += skip
                    skip = 1
                    zero_wicket = False
                else:
                    skip += 1
            elif i["batting_average"] < n and i["wickets"] > 0:
                rank += skip
                skip = 1
            else:
                skip += 1
            if i["wickets"] == 0:
                i["rank"] = 1
            else:
                i["rank"] = rank
            i["rank"] = rank
            n = i["batting_average"]
    return render(
        request,
        "stat/max_batting_average.html",
        {
            "stat": batters_list,
            "settings": TOURNAMENT_SETTINGS
        }
    )


def render_max_strike_rate(request):
    batters_list = get_all_batters()
    for i in batters_list:
        i["strike_rate"] = 100 * i["runs"] / i["balls"]
    batters_list.sort(key=lambda x: x["balls"])
    batters_list.sort(key=lambda x: x["runs"], reverse=True)
    batters_list.sort(key=lambda x: x["runs"] / x["balls"], reverse=True)
    if len(batters_list) > 0:
        rank = 1
        skip = 0
        n = batters_list[0]["strike_rate"]
        for i in batters_list:
            if i["strike_rate"] < n:
                rank += skip
                skip = 1
            else:
                skip += 1
            i["rank"] = rank
            n = i["strike_rate"]
    return render(
        request,
        "stat/max_strike_rate.html",
        {
            "stat": batters_list,
            "settings": TOURNAMENT_SETTINGS
        }
    )
