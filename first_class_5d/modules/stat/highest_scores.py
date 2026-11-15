from django.shortcuts import render
from bin.models.team import Team, AbstractPlayer
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS
from modules.stat.all_games import get_all_games, get_match_name, get_match_link, innings_verbose


def get_all_scores():
    batters_list = []
    # Search all matches
    games = get_all_games()
    for i in games:
        for k0, i0 in enumerate(i["innings"], start=1):
            result_class = ""
            if i["winner"] == i0["batting_team"]:
                result = 1
                result_class = "win"
            elif i["winner"] == i0["bowling_team"]:
                result = -1
                result_class = "loss"
            elif i["winner"] == "" and i["margin"] == "Match Tied":
                result = 0
                result_class = "draw"
            elif i["margin"].lower() == "double forfeit":
                result = -2
            else:
                result = 0
            for j in i0["batter_stats"]:
                bat_player = AbstractPlayer(j["_id"])
                bat_strike_rate = 0
                if j["balls"] > 0:
                    bat_strike_rate = 100 * j["runs"] / j["balls"]
                inning_name = innings_verbose(k0)
                team = Team(i0["batting_team"])
                opposition = Team(i0["bowling_team"])
                bat_object = {
                    "match": i["_id"],
                    "id": j["_id"],
                    "match_name": get_match_name(i["_id"]),
                    "match_link": get_match_link(i["_id"]),
                    "name": bat_player.name(),
                    "team_id": team.id(),
                    "team_name": team.name(),
                    "team_color": bat_player.color(),
                    "team_flag": bat_player.flag(),
                    "runs": j["runs"],
                    "balls": j["balls"],
                    "dismissed": j["dismissed"],
                    "strike_rate": bat_strike_rate,
                    "opposition": opposition.id(),
                    "opposition_name": opposition.name(),
                    "opposition_color": opposition.get("color"),
                    "opposition_flag": opposition.get("flag"),
                    "opposition_rating": opposition.get_rating(),
                    "innings_position": inning_name,
                    "result": result,
                    "result_class": result_class,
                    "player_title": bat_player.rating_title(),
                    "margin": i["margin"]
                }
                batters_list.append(bat_object)
    return [] + batters_list


def render_highest_score(request):
    batters_list = get_all_scores()
    if len(batters_list) > 0:
        batters_list.sort(key=lambda x: x["result"], reverse=True)
        batters_list.sort(key=lambda x: x["opposition_rating"], reverse=True)
        batters_list.sort(key=lambda x: 1 if x["dismissed"] else 0)
        batters_list.sort(key=lambda x: x["balls"])
        batters_list.sort(key=lambda x: x["runs"], reverse=True)
        rank = 1
        skip = 0
        runs = batters_list[0]["runs"]
        for i in batters_list:
            if i["runs"] < runs:
                rank += 1
                skip = 1
            else:
                skip += 1
            i["rank"] = rank
            runs = i["runs"]
    return render(
        request,
        "stat/max_scores.html",
        {
            "stat": batters_list,
            "settings": TOURNAMENT_SETTINGS
        }
    )
