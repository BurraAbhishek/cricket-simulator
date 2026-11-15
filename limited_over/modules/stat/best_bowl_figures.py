from django.shortcuts import render
from bin.models.team import Team, TOURNAMENT_TEAMS, AbstractPlayer
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS
from modules.stat.all_games import get_all_games, get_match_name, get_match_link, innings_verbose



def format_overs(balls):
    if balls % 6 == 0:
        return str(balls // 6)
    else:
        return str(balls // 6) + "." + str(balls % 6)


def bowl_figures(b, m, r, w):
    result = ""
    result += format_overs(b)
    result += " - "
    result += str(m)
    result += " - "
    result += str(r)
    result += " - "
    result += str(w)
    return result


def get_all_bowlers():
    bowlers_dict = {}
    bowlers_list = []
    for i in TOURNAMENT_TEAMS.keys():
        j1 = Team(i).find()
        j2 = TOURNAMENT_TEAMS.get(i)
        for k in j1:
            bowlers_dict[k["_id"]] = {
                "name": k["name"],
                "team_id": j2["_id"],
                "team_name": j2["name"],
                "team_color": j2.get("color"),
                "team_flag": j2.get("flag")
            }
    # Search all matches
    games = get_all_games()
    for i in games:
        for i0, j0 in enumerate(i["innings"], start=1):
            result = "draw"
            if i["winner"] == j0["batting_team"]:
                result = "loss"
            if i["winner"] == j0["bowling_team"]:
                result = "win"
            if i["winner"] == "" and i["margin"] == "Match Tied":
                result = "tie"
            opposition = Team(j0["batting_team"])
            for j in j0["bowler_stats"]:
                if j["balls"] > 0:
                    inning_name = innings_verbose(i0)
                    figures = {
                        "rank": 0,
                        "match_id": i["_id"],
                        "id": j["_id"],
                        "match_name": get_match_name(i["_id"]),
                        "match_link": get_match_link(i["_id"]),
                        "bowler_name": bowlers_dict[j["_id"]]["name"],
                        "player_title": AbstractPlayer(j["_id"]).rating_title(),
                        "team_id": bowlers_dict[j["_id"]]["team_id"],
                        "team_name": bowlers_dict[j["_id"]]["team_name"],
                        "team_color": bowlers_dict[j["_id"]]["team_color"],
                        "team_flag": bowlers_dict[j["_id"]]["team_flag"],
                        "balls": j["balls"],
                        "dots": j["dots"],
                        "maidens": j["maidens"],
                        "runs": j["runs"],
                        "wickets": j["wickets"],
                        "bowl_figures": bowl_figures(
                            j["balls"],
                            j["maidens"],
                            j["runs"],
                            j["wickets"]
                        ),
                        "overs": format_overs(j["balls"]),
                        "opposition": j0["batting_team"],
                        "opposition_name": opposition.get("name"),
                        "opposition_color": opposition.get("color"),
                        "opposition_flag": opposition.get("flag"),
                        "opposition_rating": opposition.get("rating_glicko2").get("rating"),
                        "innings_position": inning_name,
                        "result_class": result
                    }
                    bowlers_list.append(figures)
    return bowlers_list


def render_best_bowl_figures(request):
    bowlers_list = get_all_bowlers()
    if len(bowlers_list) > 0:
        bowlers_list.sort(key=lambda x: x["opposition_rating"], reverse=True)
        bowlers_list.sort(key=lambda x: x["dots"], reverse=True)
        bowlers_list.sort(key=lambda x: x["maidens"], reverse=True)
        bowlers_list.sort(key=lambda x: x["balls"])
        bowlers_list.sort(key=lambda x: x["runs"] / (1 + x["balls"]))
        bowlers_list.sort(key=lambda x: x["runs"] if x["balls"] == 0 else x["runs"] / x["balls"])
        bowlers_list.sort(key=lambda x: x["runs"])
        bowlers_list.sort(key=lambda x: x["wickets"], reverse=True)
        rank = 1
        wickets = bowlers_list[0]["wickets"]
        runs = bowlers_list[0]["runs"]
        balls = bowlers_list[0]["balls"]
        maidens = bowlers_list[0]["maidens"]
        for i in bowlers_list:
            if i["wickets"] < wickets:
                rank += 1
            elif i["runs"] > runs:
                rank += 1
            elif i["runs"] * balls > runs * i["balls"]:
                rank += 1
            elif i["balls"] > balls:
                rank += 1
            elif i["maidens"] < maidens:
                rank += 1
            i["rank"] = rank
            wickets = i["wickets"]
            runs = i["runs"]
            balls = i["balls"]
            maidens = i["maidens"]
    return render(
        request,
        "stat/best_bowling_figures.html",
        {
            "stat": bowlers_list,
            "settings": TOURNAMENT_SETTINGS
        }
    )
