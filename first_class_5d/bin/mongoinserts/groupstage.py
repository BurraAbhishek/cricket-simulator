from copy import deepcopy
from bin.models.team import Team
from bin.mongoinserts.load_teams import TOURNAMENT_TEAMS
from bin.mongoinserts.load_games import TOURNAMENT_GAMES, Tournament
from bin.mongoinserts.load_games import load_ongoing_matches, count_games_per_team
from bin.mongoinserts.load_games import get_knockout_bracket as get_knockout_teams
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS


def make_team_stat(team_id, team_name, position=0, rating=0):
    return {
        "_id": team_id,
        "id": team_id,
        "name": team_name,
        "bgcolor": Team(team_id).get("color"),
        "flag": Team(team_id).get("flag"),
        "position": position,
        "status": 0,
        "rating": rating,
        "played": 0,
        "win": 0,
        "loss": 0,
        "tie": 0,
        "total_points": 0,
        "games": [],
        "results": [],
        "opponents": [],
        "tb_scores": [],
        "tie_break": 0,
        "innings_win": 0,
        "disqualified": Team(team_id).disqualified()
    }


def make_initial_gs(request):
    # Fetch teams
    team_data = []
    for i in TOURNAMENT_TEAMS.keys():
        team_data.append(TOURNAMENT_TEAMS.get(i))
    team_data.sort(key=lambda x: x["rating"], reverse=True)
    # Each team
    groupstage_table = []
    max_games, _ = count_games_per_team()
    for i, e in enumerate(team_data):
        team_stat = make_team_stat(
            e["_id"],
            e["name"],
            i + 1,
            e["rating"]
        )
        result = []
        for _ in range(max_games):
            result.append(None)
        team_stat["temp_results"] = result
        groupstage_table.append(team_stat)
    return groupstage_table


def update_gs(request):
    # Fetch groupstage
    groupstage_table = make_initial_gs(request)
    gs_document = {}
    tournament = Tournament()
    # Fetch groupstage matches
    groupstage_matches = tournament.find()
    if len(groupstage_matches) > 0:
        max_week = int(groupstage_matches[-1]["_id"].split("_")[1])
    else:
        max_week = 0
    for i in groupstage_table:
        gs_document[i["_id"]] = i
    for i in groupstage_matches:
        gs_document[i["team1"]]["played"] += 1
        gs_document[i["team2"]]["played"] += 1
        if i["winner"] == i["team1"]:
            gs_document[i["team1"]]["win"] += 1
            gs_document[i["team1"]]["results"].append(1)
            gs_document[i["team2"]]["loss"] += 1
            gs_document[i["team2"]]["results"].append(0)
        elif i["winner"] == i["team2"]:
            gs_document[i["team2"]]["win"] += 1
            gs_document[i["team2"]]["results"].append(1)
            gs_document[i["team1"]]["loss"] += 1
            gs_document[i["team1"]]["results"].append(0)
        elif i["winner"] == "" and i["margin"] == "Double Forfeit":
            gs_document[i["team1"]]["loss"] += 1
            gs_document[i["team1"]]["results"].append(0)
            gs_document[i["team2"]]["loss"] += 1
            gs_document[i["team2"]]["results"].append(0)
        elif i["winner"] == "" and i["margin"] == "Match Cancelled":
            gs_document[i["team1"]]["loss"] += 1
            gs_document[i["team1"]]["results"].append(0)
            gs_document[i["team2"]]["loss"] += 1
            gs_document[i["team2"]]["results"].append(0)
        else:
            gs_document[i["team1"]]["tie"] += 1
            gs_document[i["team2"]]["tie"] += 1
            gs_document[i["team1"]]["results"].append(0.5)
            gs_document[i["team2"]]["results"].append(0.5)
        gs_document[i["team1"]]["games"].append(i["_id"])
        gs_document[i["team2"]]["games"].append(i["_id"])
        gs_document[i["team1"]]["opponents"].append(i["team2"])
        gs_document[i["team2"]]["opponents"].append(i["team1"])
        # Disqualification
        if i.get("disqualifications") is not None:
            for t1 in i["disqualifications"]:
                gs_document[t1]["status"] = -2
        # innings win or its equivalent
        if bool(
            'innings' in i["margin"]
            or i["margin"].lower() == 'walkover'
            or i["margin"].lower() == 'forfeit'
            or i["margin"].lower() == 'disciplinary forfeit'
        ):
            gs_document[i["winner"]]["innings_win"] += 1
        # tie breaks
        gs_sub_document = {
            i["team1"]: {
                "t_runs": 0,
                "t_balls": 0,
                "t_wickets": 0,
                "o_runs": 0,
                "o_balls": 0,
                "o_wickets": 0
            },
            i["team2"]: {
                "t_runs": 0,
                "t_balls": 0,
                "t_wickets": 0,
                "o_runs": 0,
                "o_balls": 0,
                "o_wickets": 0
            }
        }
        for j in i["innings"]:
            gs_sub_document[j["batting_team"]]["t_runs"] += j["score"]
            gs_sub_document[j["batting_team"]]["t_balls"] += j["balls"]
            gs_sub_document[j["batting_team"]]["t_wickets"] += j["wickets"]
            gs_sub_document[j["bowling_team"]]["o_runs"] -= j["score"]
            gs_sub_document[j["bowling_team"]]["o_balls"] -= j["balls"]
            gs_sub_document[j["bowling_team"]]["o_wickets"] -= j["wickets"]
        if gs_sub_document[i["team1"]]["t_runs"] >= gs_sub_document[i["team2"]]["t_runs"]:
            k = gs_sub_document[i["team1"]]
        else:
            k = gs_sub_document[i["team2"]]
        if k["t_balls"] == 0 and k["o_balls"] == 0:
            if k["t_runs"] > 0 and k["o_runs"] <= 0:
                tb = 36 / (1 + k["t_wickets"])
            elif k["t_runs"] <= 0 and k["o_runs"] > 0:
                tb = -36 / (1 + k["o_wickets"])
            else:
                tb = 0
        elif k["o_balls"] == 0:
            tb = 6 * k["t_runs"] / (k["t_balls"] * (k["t_wickets"] + 1))
        elif k["t_balls"] == 0:
            tb = 6 * k["o_runs"] / (k["o_balls"] * (k["o_wickets"] - 1))
        else:
            tb = (
                6 * k["t_runs"] / (k["t_balls"] * (k["t_wickets"] + 1))
            ) + (
                6 * k["o_runs"] / (k["o_balls"] * (k["o_wickets"] - 1))
            )
        if bool(
            i["margin"].lower() == 'walkover'
            or i["margin"].lower() == 'match cancelled'
            or i["margin"].lower() == 'disciplinary forfeit'
        ) and bool(
            k["o_balls"] == 0
            and k["o_runs"] == 0
            and k["t_balls"] == 0
            and k["t_runs"] == 0
        ):
            tb = None
            gs_document[i["team1"]]["tb_scores"].append(tb)
            gs_document[i["team2"]]["tb_scores"].append(tb)
        else:
            if gs_sub_document[i["team1"]]["t_runs"] >= gs_sub_document[i["team2"]]["t_runs"]:
                gs_document[i["team1"]]["tb_scores"].append(tb)
                gs_document[i["team1"]]["tie_break"] += tb
                gs_document[i["team2"]]["tb_scores"].append(0 - tb)
                gs_document[i["team2"]]["tie_break"] -= tb
            else:
                gs_document[i["team1"]]["tb_scores"].append(0 - tb)
                gs_document[i["team1"]]["tie_break"] -= tb
                gs_document[i["team2"]]["tb_scores"].append(tb)
                gs_document[i["team2"]]["tie_break"] += tb
    # QUALIFIED AND ELIMINATED
    '''
    for i in QUALIFIED:
        if i["week"] <= max_week:
            gs_document[i["team"]]["status"] = 1
    for i in ELIMINATED:
        if i["week"] <= max_week:
            gs_document[i["team"]]["status"] = -1
    '''
    # END OF QE
    for i in range(len(groupstage_table)):
        groupstage_table[i] = gs_document[groupstage_table[i]["_id"]]
    for i in groupstage_table:
        i["total_points"] = i["win"] + 0.5 * i["tie"]
        really_played = len([j for j in i["tb_scores"] if j is not None])
        if i["played"] > 0 and really_played > 0:
            i["tie_break"] = i["tie_break"] / really_played
        for j, k in enumerate(i["results"]):
            i["temp_results"][j] = {
                "match": i["games"][j],
                "result": i["results"][j],
                "opponent": i["opponents"][j],
                "weight": i["tie_break"] if i["tb_scores"][j] is None else i["tb_scores"][j]
            }
    groupstage_table.sort(key=lambda x: x["tie_break"], reverse=True)
    groupstage_table.sort(key=lambda x: x["innings_win"], reverse=True)
    groupstage_table.sort(key=lambda x: x["win"], reverse=True)
    groupstage_table.sort(key=lambda x: x["total_points"], reverse=True)
    slots = 2 ** TOURNAMENT_SETTINGS.get("knockout", 1)
    for i, e in enumerate(groupstage_table):
        if e["played"] >= max_week and groupstage_table[i]["status"] > -2:
            if i < slots:
                groupstage_table[i]["status"] = 1
            else:
                groupstage_table[i]["status"] = -1
    return groupstage_table



def get_knockout_bracket(ongoing_match=None):
    games = load_ongoing_matches()
    if ongoing_match is not None:
        games.append(ongoing_match)
    d = {}
    for i in games:
        d1 = {}
        if i["team1"] not in d.keys():
            d[i["team1"]] = {
                "team": i["team1"],
                "points": 0,
                "t_runs": 0,
                "o_runs": 0,
                "t_balls": 0,
                "o_balls": 0,
                "t_wickets": 0,
                "o_wickets": 0,
                "win": 0,
                "innings_win": 0,
                "n": 0
            }
        if i["team2"] not in d.keys():
            d[i["team2"]] = {
                "team": i["team2"],
                "points": 0,
                "t_runs": 0,
                "o_runs": 0,
                "t_balls": 0,
                "o_balls": 0,
                "t_wickets": 0,
                "o_wickets": 0,
                "win": 0,
                "innings_win": 0,
                "n": 0
            }
        d1[i["team1"]] = {
            "team": i["team1"],
            "points": 0,
            "t_runs": 0,
            "o_runs": 0,
            "t_balls": 0,
            "o_balls": 0,
            "t_wickets": 0,
            "o_wickets": 0,
            "n": 0
        }
        d1[i["team2"]] = {
            "team": i["team1"],
            "points": 0,
            "t_runs": 0,
            "o_runs": 0,
            "t_balls": 0,
            "o_balls": 0,
            "t_wickets": 0,
            "o_wickets": 0,
            "n": 0
        }
        # innings win
        if i["winner"] is not None and i["winner"] != "":
            d[i["winner"]]["win"] += 1
            if 'innings' in i["margin"]:
                d[i["winner"]]["innings_win"] += 1
        for j in i["innings"]:
            d[j["batting_team"]]["t_runs"] += j["score"]
            d[j["bowling_team"]]["o_runs"] -= j["score"]
            d[j["batting_team"]]["t_balls"] += j["balls"]
            d[j["bowling_team"]]["o_balls"] -= j["balls"]
            d[j["batting_team"]]["t_wickets"] += j["wickets"]
            d[j["bowling_team"]]["o_wickets"] -= j["wickets"]
            d1[j["batting_team"]]["t_runs"] += j["score"]
            d1[j["bowling_team"]]["o_runs"] -= j["score"]
            d1[j["batting_team"]]["t_balls"] += j["balls"]
            d1[j["bowling_team"]]["o_balls"] -= j["balls"]
            d1[j["batting_team"]]["t_wickets"] += j["wickets"]
            d1[j["bowling_team"]]["o_wickets"] -= j["wickets"]
        if d1[i["team1"]]["t_runs"] >= d1[i["team2"]]["t_runs"]:
            k = d1[i["team1"]]
        else:
            k = d1[i["team2"]]
        if k["t_balls"] == 0 and k["o_balls"] == 0:
            if k["t_runs"] > 0 and k["o_runs"] <= 0:
                tb = 36 / (1 + k["t_wickets"])
            elif k["t_runs"] <= 0 and k["o_runs"] > 0:
                tb = -36 / (1 + k["o_wickets"])
            else:
                tb = 0
        elif k["o_balls"] == 0:
            tb = 6 * k["t_runs"] / (k["t_balls"] * (k["t_wickets"] + 1))
        elif k["t_balls"] == 0:
            tb = 6 * k["o_runs"] / (k["o_balls"] * (k["o_wickets"] - 1))
        else:
            tb = (
                6 * k["t_runs"] / (k["t_balls"] * (k["t_wickets"] + 1))
            ) + (
                6 * k["o_runs"] / (k["o_balls"] * (k["o_wickets"] - 1))
            )
        if d1[i["team1"]]["t_runs"] >= d1[i["team2"]]["t_runs"]:
            d[i["team1"]]["n"] += tb
            d[i["team2"]]["n"] -= tb
        else:
            d[i["team2"]]["n"] += tb
            d[i["team1"]]["n"] -= tb
        if i["winner"] == i["team1"]:
            d[i["team1"]]["points"] += 2
        elif i["winner"] == i["team2"]:
            d[i["team2"]]["points"] += 2
        else:
            d[i["team1"]]["points"] += 1
            d[i["team2"]]["points"] += 1
    l = list(d.values())
    slots = 2 ** TOURNAMENT_SETTINGS["knockout"]
    l.sort(key=lambda x: x["n"], reverse=True)
    l.sort(key=lambda x: x["innings_win"], reverse=True)
    l.sort(key=lambda x: x["win"], reverse=True)
    l.sort(key=lambda x: x["points"], reverse=True)
    return l[:slots]


def final_standing(groupstage):
    fs0 = []
    fs = []
    for i, e in enumerate(groupstage, start=1):
        fs0.append(
            {
                "id": e["_id"],
                "name": e["name"],
                "flag": e["flag"],
                "bgcolor": e["bgcolor"],
                "groupstage": i,
                "position": i,
                "disqualified": bool(e["status"] <= -2 or e["disqualified"])
            }
        )
    n0 = 2 ** TOURNAMENT_SETTINGS["knockout"]
    ko = {}
    for i in TOURNAMENT_GAMES["knockout"]:
        ko_object = {
            "id": i["_id"],
            "t": [i["team1"], i["team2"]],
            "w": -1
        }
        if i["winner"] == i["team1"]:
            ko_object["w"] = 0
        elif i["winner"] == i["team2"]:
            ko_object["w"] = 1
        ko[i["_id"]] = ko_object
    if len(fs0) > n0:
        fs = fs0[n0:] + fs
        survivors = deepcopy(fs0[:n0])
    else:
        survivors = deepcopy(fs0)
    survivor_ids = [i["id"] for i in survivors]
    ko_bracket = get_knockout_teams()
    for i in ko_bracket:
        losers = []
        for j in i:
            game = ko[j]
            if game["w"] >= 0:
                loser = game["t"][(game["w"] + 1) % 2]
                survivor_ids.remove(loser)
        for t in survivors:
            if t["id"] not in survivor_ids:
                losers.append(t)
        survivors = [t for t in survivors if t["id"] in survivor_ids]
        fs = losers + fs
    fs = survivors + fs
    if TOURNAMENT_SETTINGS.get("thirdplace", False) and len(fs) >= 4:
        t1 = fs[2]
        t2 = fs[3]
        if ko["thirdplace"]["w"] == list(ko["thirdplace"]["t"]).index(t2["id"]):
            fs[2] = t2
            fs[3] = t1
    for i, e in enumerate(fs, start=1):
        e["position"] = i
    if ko["final"]["w"] == -1:
        fs[1]["position"] = 1
    return fs
