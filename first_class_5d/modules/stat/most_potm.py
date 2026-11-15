from collections import defaultdict
from django.shortcuts import render
from bin.models.team import Team, AbstractPlayer
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS
from modules.stat.all_games import get_all_games


def get_all_potm():
    potm_dict = defaultdict(lambda: 0)
    game_dict = defaultdict(lambda: 0)
    potm_list = []
    # Search all matches
    games = get_all_games()
    for i in games:
        if i["margin"] not in ["Walkover", "Match Cancelled", "Disciplinary Forfeit"]:
            team1 = Team(i["team1"])
            team2 = Team(i["team2"])
            for j in team1.members():
                game_dict[j["_id"]] += 1
            for j in team2.members():
                game_dict[j["_id"]] += 1
            if i.get("player_of_the_match") is not None and i.get("player_of_the_match") != "":
                potm_dict[i["player_of_the_match"]] += 1
    for i in potm_dict.keys():
        player = AbstractPlayer(i)
        team = player.team()
        potm_list.append(
            {
                "id": i,
                "rank": 0,
                "name": player.name(),
                "team_id": team.id(),
                "team_name": team.name(),
                "team_color": team.get("color"),
                "team_flag": team.get("flag"),
                "potm": potm_dict[i],
                "matches": game_dict[i],
                "avatar": player.avatar(),
                "player_title": player.rating_title()
            }
        )
    del game_dict
    if len(potm_list) > 0:
        potm_list.sort(key=lambda x: x["matches"])
        potm_list.sort(key=lambda x: x["potm"], reverse=True)
        rank = 1
        potm_count = potm_list[0]["potm"]
        skip = 0
        for i in potm_list:
            if i["potm"] < potm_count:
                rank += skip
                skip = 1
            else:
                skip += 1
            i["rank"] = rank
            potm_count = i["potm"]
    return potm_list


def render_stat_potm(request):
    potm_list = get_all_potm()
    return render(
        request,
        "stat/most_awards.html",
        {
            "stat": potm_list,
            "settings": TOURNAMENT_SETTINGS
        }
    )
