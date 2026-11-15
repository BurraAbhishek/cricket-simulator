from copy import deepcopy
from bin.models.team import Team, TeamCollection
from bin.mongoinserts.load_games import TOURNAMENT_GAMES, load_ongoing_matches
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
        "net_run_rate": 0,
        "runs_scored": 0,
        "balls_scored": 0,
        "runs_given": 0,
        "balls_given": 0,
        "decision_match": "",
        "games": [],
        "results": []
    }


def make_initial_gs(request):
    # Fetch teams
    team_data: list[Team] = []
    team_collection = TeamCollection()
    for i in team_collection.find():
        team_data.append(Team(i))
    team_data.sort(key=lambda x: x.init_rating(), reverse=True)
    # Each team
    groupstage_table = []
    for i, e in enumerate(team_data):
        team_stat = make_team_stat(
            e.id(),
            e.name(),
            i + 1,
            e.init_rating()
        )
        groupstage_table.append(team_stat)
    return groupstage_table


def update_gs(request):
    # Fetch groupstage
    groupstage_table = make_initial_gs(request)
    gs_document = {}
    # Fetch groupstage matches
    groupstage_matches = TOURNAMENT_GAMES.get("groupstage")
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
        else:
            gs_document[i["team1"]]["tie"] += 1
            gs_document[i["team2"]]["tie"] += 1
            gs_document[i["team1"]]["results"].append(0.5)
            gs_document[i["team2"]]["results"].append(0.5)
        gs_document[i["team1"]]["games"].append(i["_id"])
        gs_document[i["team2"]]["games"].append(i["_id"])
        gs_document[i["team1"]]["runs_scored"] += i["innings"][0]["score"]
        gs_document[i["team2"]]["runs_scored"] += i["innings"][1]["score"]
        gs_document[i["team1"]]["runs_given"] += i["innings"][1]["score"]
        gs_document[i["team2"]]["runs_given"] += i["innings"][0]["score"]
        if i["innings"][0]["wickets"] >= i["wickets"]:
            gs_document[i["team1"]]["balls_scored"] += 6 * i["overs"]
            gs_document[i["team2"]]["balls_given"] += 6 * i["overs"]
        else:
            gs_document[i["team1"]]["balls_scored"] += i["innings"][0]["balls"]
            gs_document[i["team2"]]["balls_given"] += i["innings"][0]["balls"]
        if i["innings"][1]["wickets"] >= i["wickets"]:
            gs_document[i["team2"]]["balls_scored"] += 6 * i["overs"]
            gs_document[i["team1"]]["balls_given"] += 6 * i["overs"]
        else:
            gs_document[i["team2"]]["balls_scored"] += i["innings"][1]["balls"]
            gs_document[i["team1"]]["balls_given"] += i["innings"][1]["balls"]
        k1 = []
        for k in gs_document.keys():
            k1.append({
                "team": k,
                "curr_match": i["_id"],
                "played": gs_document[k]["played"],
                "points": 2 * gs_document[k]["win"] + gs_document[k]["tie"],
                "status": gs_document[k]["status"],
                "runs_scored": gs_document[k]["runs_scored"],
                "runs_given": gs_document[k]["runs_given"],
                "balls_scored": gs_document[k]["balls_scored"],
                "balls_given": gs_document[k]["balls_given"],
            })
        qualified, eliminated = elimination(k1)
        for j in qualified:
            if j["match"] == i["_id"]:
                gs_document[j["team"]]["status"] = 1
                if 2 ** TOURNAMENT_SETTINGS["knockout"] < len(gs_document.keys()):
                    gs_document[j["team"]]["decision_match"] = i["_id"]
        for j in eliminated:
            if j["match"] == i["_id"]:
                gs_document[j["team"]]["status"] = -1
                if 2 ** TOURNAMENT_SETTINGS["knockout"] < len(gs_document.keys()):
                    gs_document[j["team"]]["decision_match"] = i["_id"]
    for i in range(len(groupstage_table)):
        groupstage_table[i] = gs_document[groupstage_table[i]["_id"]]
    for i in groupstage_table:
        i["total_points"] = 2 * i["win"] + i["tie"]
        try:
            i["net_run_rate"] = float(
                float(6 * i["runs_scored"] / i["balls_scored"])
                - float(6 * i["runs_given"] / i["balls_given"])
            )
        except ZeroDivisionError:
            i["net_run_rate"] = 36
        if i["played"] == 0:
            i["net_run_rate"] = 0
    groupstage_table.sort(key=lambda x: x["net_run_rate"], reverse=True)
    groupstage_table.sort(key=lambda x: x["win"], reverse=True)
    groupstage_table.sort(key=lambda x: x["total_points"], reverse=True)
    return groupstage_table


def elimination(groupstage, rounds=0, slots=0):
    all_teams = TeamCollection()
    if rounds < 2:
        rounds = 2 * TOURNAMENT_SETTINGS["series_games"]
    if slots < 2:
        slots = 2 ** TOURNAMENT_SETTINGS["knockout"]
    if len(groupstage) <= slots:
        qualified = []
        for i in groupstage:
            qualified.append({"match": "", "team": i["team"]})
        return qualified, []
    qualified = []
    eliminated = []
    max_teams = all_teams.count()
    max_possible_scores = []
    bot_group = all_teams.group_split()
    max_games = rounds * max_teams
    if bot_group:
        max_games = int(max_games / 2)
    else:
        max_games -= rounds
    for i in groupstage:
        i["remaining"] = max_games - i["played"]
        i["max_possible_score"] = i["points"] + 2 * i["remaining"]
        try:
            i["net_run_rate"] = float(
                float(6 * i["runs_scored"] / i["balls_scored"])
                - float(6 * i["runs_given"] / i["balls_given"])
            )
        except ZeroDivisionError:
            i["net_run_rate"] = 36
        if i["played"] == 0:
            i["net_run_rate"] = 0
        max_possible_scores.append(i["max_possible_score"])
    max_possible_scores.sort(reverse=True)
    # sort
    groupstage.sort(key=lambda x: x["net_run_rate"], reverse=True)
    groupstage.sort(key=lambda x: x["remaining"], reverse=True)
    groupstage.sort(key=lambda x: x["points"], reverse=True)
    groupstage.sort(key=lambda x: x["max_possible_score"], reverse=True)
    # end sort
    promotion = max_possible_scores[slots]
    termination = groupstage[slots - 1]["points"]
    for i in groupstage:
        if i["points"] > promotion and i["status"] != 1:
            qualified.append({"match": i["curr_match"], "team": i["team"]})
            i["status"] = 1
        if (i["points"] + 2 * i["remaining"]) < termination and i["status"] != -1:
            eliminated.append({"match": i["curr_match"], "team": i["team"]})
            i["status"] = -1
    # edge cases
    if groupstage[slots]["remaining"] == 0:
        for i in groupstage[:slots]:
            if i["status"] != 1:
                qualified.append({"match": i["curr_match"], "team": i["team"]})
                i["status"] = 1
        for i in groupstage[slots:]:
            if i["status"] != -1:
                eliminated.append({"match": i["curr_match"], "team": i["team"]})
                i["status"] = -1
    # if all teams already qualified or eliminated
    qualifier_slots = slots
    elimination_slots = max_teams - slots
    for i in groupstage:
        if i["status"] == 1:
            qualifier_slots -= 1
        if i["status"] == -1:
            elimination_slots -= 1
    if elimination_slots <= 0 and qualifier_slots > 0:
        for i in groupstage:
            if i["status"] != -1 and i["status"] != 1:
                qualified.append({"match": i["curr_match"], "team": i["team"]})
                i["status"] = 1
    if qualifier_slots <= 0:
        for i in groupstage:
            if i["status"] != 1 and i["status"] != -1:
                eliminated.append({"match": i["curr_match"], "team": i["team"]})
                i["status"] = -1
    return qualified, eliminated


def get_knockout_bracket(ongoing_match=None):
    games = load_ongoing_matches()
    if ongoing_match is not None:
        games.append(ongoing_match)
    d = {}
    max_balls = 6 * TOURNAMENT_SETTINGS["overs"]
    for i in games:
        if i["team1"] not in d.keys():
            d[i["team1"]] = {
                "team": i["team1"],
                "points": 0,
                "r": 0,
                "-r": 0,
                "b": 0,
                "-b": 0,
                "n": 0
            }
        if i["team2"] not in d.keys():
            d[i["team2"]] = {
                "team": i["team2"],
                "points": 0,
                "r": 0,
                "-r": 0,
                "b": 0,
                "-b": 0,
                "n": 0
            }
        d[i["team1"]]["r"] += i["team1_score"]
        d[i["team1"]]["-r"] += i["team2_score"]
        d[i["team2"]]["r"] += i["team2_score"]
        d[i["team2"]]["-r"] += i["team1_score"]
        if i["team1_wickets"] >= 10:
            d[i["team1"]]["b"] += max_balls
            d[i["team2"]]["-b"] += max_balls
        else:
            d[i["team1"]]["b"] += i["team1_balls"]
            d[i["team2"]]["-b"] += i["team1_balls"]
        if i["team2_wickets"] >= 10:
            d[i["team2"]]["b"] += max_balls
            d[i["team1"]]["-b"] += max_balls
        else:
            d[i["team2"]]["b"] += i["team2_balls"]
            d[i["team1"]]["-b"] += i["team2_balls"]
        if i["winner"] == i["team1"]:
            d[i["team1"]]["points"] += 2
        elif i["winner"] == i["team2"]:
            d[i["team2"]]["points"] += 2
        else:
            d[i["team1"]]["points"] += 1
            d[i["team2"]]["points"] += 1
    l = list(d.values())
    for i in l:
        try:
            i["n"] = float(
                float(6 * i["r"] / i["b"]) - float(6 * i["-r"] / i["-b"])
            )
        except ZeroDivisionError:
            i["n"] = 36
    slots = 2 ** TOURNAMENT_SETTINGS["knockout"]
    l.sort(key=lambda x: x["n"], reverse=True)
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
