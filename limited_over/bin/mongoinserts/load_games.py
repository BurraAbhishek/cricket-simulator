import math
import json
from django.contrib.staticfiles import finders
from bin.models.team import Team, TeamCollection
from bin.mongoinserts.load_teams import TOURNAMENT_TEAMS
from bin.mongoinserts.player_dict import get_replacer_dict
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS
from bin.mongoinserts.cachebase import set_item, get_item
from modules.rating.decision.outcome import rate_game
from modules.engine.evaluation import BaseLimitedOverCricketEngine



def get_match_ids(i: int, max_games: int | None=None) -> str:
    if max_games is None:
        max_games = max_groupstage_games()
    prefix = "m"
    suffix = ""
    if max_games <= 0:
        return prefix + str(i) + suffix
    num_zero = int(math.log10(max_games))
    if num_zero <= 0:
        return prefix + str(i) + suffix
    formatting = "{:"
    if num_zero < 10:
        formatting += "0"
    formatting += str(num_zero + 1)
    formatting += "d}"
    s1 = prefix + formatting.format(i) + suffix
    return s1


def get_knockout_matches():
    if TOURNAMENT_SETTINGS["knockout"] < 1:
        return []
    if TOURNAMENT_SETTINGS.get("thirdplace", False) and len(TOURNAMENT_TEAMS) >= 4:
        final = ["thirdplace", "final"]
    else:
        final = ["final"]
    if TOURNAMENT_SETTINGS["knockout"] == 1:
        return final
    elif TOURNAMENT_SETTINGS["knockout"] == 2:
        return ["sf1", "sf2"] + final
    elif TOURNAMENT_SETTINGS["knockout"] == 3:
        return ["qf1", "qf2", "qf3", "qf4", "sf1", "sf2"] + final
    else:
        ko = []
        ko3 = ["qf1", "qf2", "qf3", "qf4", "sf1", "sf2"] + final
        for i in range(TOURNAMENT_SETTINGS["knockout"], 3, -1):
            round_slots: int = 2 ** (i - 1)
            for j in range(1, 1 + round_slots):
                match_id = "r" + str(round_slots * 2) + "_" + str(j)
                ko.append(match_id)
        ko += ko3
        return ko


def get_knockout_bracket():
    bracket = []
    if TOURNAMENT_SETTINGS["knockout"] < 1:
        return bracket
    if TOURNAMENT_SETTINGS["knockout"] >= 1:
        bracket.append(["final"])
    if TOURNAMENT_SETTINGS["knockout"] >= 2:
        bracket.append(["sf1", "sf2"])
    if TOURNAMENT_SETTINGS["knockout"] >= 3:
        bracket.append(["qf1", "qf2", "qf3", "qf4"])
    if TOURNAMENT_SETTINGS["knockout"] > 3:
        for i in range(3, TOURNAMENT_SETTINGS["knockout"]):
            round_slots: int = 2 ** i
            ko = []
            for j in range(1, 1 + round_slots):
                match_id = "r" + str(round_slots * 2) + "_" + str(j)
                ko.append(match_id)
            bracket.append(ko)
    bracket.reverse()
    return bracket


def translate_ko_id(i: str) -> str:
    if i == "final":
        return "Final"
    elif i == "thirdplace":
        return "3rd Place Playoff"
    elif i == "sf1":
        return "Semi-Final 1"
    elif i == "sf2":
        return "Semi-Final 2"
    elif i == "qf1":
        return "Quarter-Final 1"
    elif i == "qf2":
        return "Quarter-Final 2"
    elif i == "qf3":
        return "Quarter-Final 3"
    elif i == "qf4":
        return "Quarter-Final 4"
    elif i[0] == "r":
        game_id_split = i.split("_")
        game_name = "Knockout Round of "
        game_name += game_id_split[0][1:]
        return game_name
    else:
        return i


def max_groupstage_games():
    if TOURNAMENT_SETTINGS["groupstage"] is False:
        return 0
    if TOURNAMENT_SETTINGS["series_games"] < 1:
        return 0
    team_collection = TeamCollection()
    grouping = team_collection.group_split()
    num_teams = team_collection.count()
    if grouping:
        total_games = int(num_teams * num_teams / 2)
    else:
        total_games = num_teams * (num_teams - 1)
    return total_games * int(TOURNAMENT_SETTINGS["series_games"])
    

def load_matches_from_scratch():
    print("Cache invalidated, reloading...")
    matches = {
        "groupstage": [],
        "knockout": []
    }
    # number of games
    if TOURNAMENT_SETTINGS["debug"] is True:
        total_games = 0
    else:
        total_games = max_groupstage_games()
    weeks = list(range(1, total_games + 1))
    # collection = mongoclient.tournament_db_get_collection(mongoclient.TOURNAMENT_GROUPSTAGE)
    for i in weeks:
        match_id = get_match_ids(i)
        match_path = finders.find('matches_json/' + match_id + '.json')
        match_data_serialized = open(match_path, "r")
        x = match_data_serialized.read()
        d = get_replacer_dict()
        for i in d.keys():
            x = x.replace(i, d[i])
        match_data = json.loads(x)
        match_raw = match_data[0]
        match_raw["rating_initial"] = {
            match_raw["team1"]: Team(match_raw["team1"]).get("rating_glicko2"),
            match_raw["team2"]: Team(match_raw["team2"]).get("rating_glicko2"),
        }
        rate_game(
            TOURNAMENT_TEAMS[match_raw["team1"]],
            TOURNAMENT_TEAMS[match_raw["team2"]], 
            match_raw["winner"],
            match_raw["margin"]
        )
        match_raw["rating_final"] = {
            match_raw["team1"]: Team(match_raw["team1"]).get("rating_glicko2"),
            match_raw["team2"]: Team(match_raw["team2"]).get("rating_glicko2"),
        }
        rc1 = round(match_raw["rating_final"][match_raw["team1"]]["rating"]) - round(match_raw["rating_initial"][match_raw["team1"]]["rating"])
        rc2 = round(match_raw["rating_final"][match_raw["team2"]]["rating"]) - round(match_raw["rating_initial"][match_raw["team2"]]["rating"])
        match_raw["rc1"] = rc1
        match_raw["rc2"] = rc2
        match_evaluation = BaseLimitedOverCricketEngine(match_raw)
        match_raw["prediction"] = match_evaluation.evaluate_json_standard()
        for i2, i1 in enumerate(match_raw["innings"]):
            match_evaluation.curr_inning = i2
            for j1 in i1["data"]:
                for k1 in j1:
                    match_evaluation.record_event(k1)
                    k1["evaluation"] = match_evaluation.evaluate_json_standard()
            match_evaluation.increment_inning()
        matches["groupstage"].append(match_raw)
        match_data_serialized.close()
    # knockout
    # collection = mongoclient.tournament_db_get_collection(mongoclient.TOURNAMENT_KNOCKOUT)
    if TOURNAMENT_SETTINGS["debug"] is True:
        knockout_games = []
    else:
        knockout_games = get_knockout_matches()
    for i0 in knockout_games:
        match_path = finders.find('matches_json/' + str(i0) + '.json')
        match_data_serialized = open(match_path, "r")
        x = match_data_serialized.read()
        d = get_replacer_dict()
        for i in d.keys():
            x = x.replace(i, d[i])
        match_data = json.loads(x)
        match_raw = match_data[0]
        match_raw["rating_initial"] = {
            match_raw["team1"]: Team(match_raw["team1"]).get("rating_glicko2"),
            match_raw["team2"]: Team(match_raw["team2"]).get("rating_glicko2"),
        }
        rate_game(
            TOURNAMENT_TEAMS[match_raw["team1"]],
            TOURNAMENT_TEAMS[match_raw["team2"]], 
            match_raw["winner"],
            match_raw["margin"]
        )
        match_raw["rating_final"] = {
            match_raw["team1"]: Team(match_raw["team1"]).get("rating_glicko2"),
            match_raw["team2"]: Team(match_raw["team2"]).get("rating_glicko2"),
        }
        rc1 = round(match_raw["rating_final"][match_raw["team1"]]["rating"]) - round(match_raw["rating_initial"][match_raw["team1"]]["rating"])
        rc2 = round(match_raw["rating_final"][match_raw["team2"]]["rating"]) - round(match_raw["rating_initial"][match_raw["team2"]]["rating"])
        match_raw["rc1"] = rc1
        match_raw["rc2"] = rc2
        match_evaluation = BaseLimitedOverCricketEngine(match_raw)
        match_raw["prediction"] = match_evaluation.evaluate_json_standard()
        for i2, i1 in enumerate(match_raw["innings"]):
            match_evaluation.curr_inning = i2
            for j1 in i1["data"]:
                for k1 in j1:
                    match_evaluation.record_event(k1)
                    k1["evaluation"] = match_evaluation.evaluate_json_standard()
            match_evaluation.increment_inning()
        matches["knockout"].append(match_raw)
        match_data_serialized.close()
    set_item("games", matches, indent=0)
    return matches


def load_matches():
    #x = get_item("games")
    #if x is not None:
    #    return x
    return load_matches_from_scratch()


TOURNAMENT_GAMES = load_matches()


def fetch_game(clas, id):
    db = TOURNAMENT_GAMES.get(clas)
    if db is None:
        return None
    for i in db:
        if i["_id"] == id:
            return i
    return None


def load_ongoing_matches():
    games = []
    num_games = max_groupstage_games()
    for i in range(1, num_games + 1):
        match_id = get_match_ids(i)
        match_path1 = finders.find('matches_json/' + match_id + '.json')
        match_path2 = finders.find('matches_json_automated/' + match_id + '.json')
        if match_path2 is None:
            match_path2 = match_path1
        elif match_path1 is None:
            match_path1 = match_path2
        if match_path1 is not None or match_path2 is not None:
            try:
                match_data_serialized = open(match_path2, "r")
            except FileNotFoundError:
                match_data_serialized = open(match_path1, "r")
            # Then we are good
            x0 = json.load(match_data_serialized)
            x = x0[0]
            match_data_serialized.close()
            o = {
                "team1": x["team1"],
                "team2": x["team2"],
                "team1_score": x["innings"][0]["score"],
                "team1_balls": x["innings"][0]["balls"],
                "team1_wickets": x["innings"][0]["wickets"],
                "team2_score": x["innings"][1]["score"],
                "team2_balls": x["innings"][1]["balls"],
                "team2_wickets": x["innings"][1]["wickets"],
                "winner": x["winner"],
                "player_of_the_match": x["player_of_the_match"]
            }
            games.append(o)
    return games
