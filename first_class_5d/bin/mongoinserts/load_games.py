import math
import time
import json
from django.contrib.staticfiles import finders
from bin.models.team import Team
from bin.mongoinserts.player_dict import get_replacer_dict
from bin.mongoinserts.load_teams import TOURNAMENT_TEAMS
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS
from bin.mongoinserts.cachebase import set_item, get_item
from modules.rating.decision.outcome import rate_game
from modules.engine.evaluation import BaseRFTestCricketEngine


def get_match_ids(
        i: int,
        max_games: int | None=None,
        venue: str | int | None=None,
        max_venues: int | None=None
        ) -> str:
    computed_max_games, computed_max_venues = count_games_per_team()
    if max_games is None:
        max_games = computed_max_games
    if max_venues is None:
        max_venues = computed_max_venues
    prefix = "m"
    if max_games <= 0 or max_venues <= 0:
        return prefix + str(i)
    # format: m_{week}_{board}. Board 1 is the top board
    prefix += "_"
    # week
    num_zero = int(math.log10(max_games))
    if max_games >= 1 and max_games <= 9:
        num_zero = 1
    formatting = "{:"
    if num_zero < 10:
        formatting += "0"
    formatting += str(num_zero + 1)
    formatting += "d}"
    s1 = prefix + formatting.format(i)
    # board
    num_zero = int(math.log10(max_venues))
    if max_venues >= 1 and max_venues <= 9:
        num_zero = 1
    formatting = "{:"
    if num_zero < 10:
        formatting += "0"
    formatting += str(num_zero + 1)
    formatting += "d}"
    s1 += "_" + formatting.format(venue)
    return s1


def count_games_per_team():
    nb_bots = 0
    nb_team = 0
    for i in TOURNAMENT_TEAMS.keys():
        if Team(i).ai():
            nb_bots += 1
        else:
            nb_team += 1
    if nb_bots > 0 and TOURNAMENT_SETTINGS.get("bot_group", True):
        max_weeks = min(nb_bots, nb_team)
        max_venue = min(nb_bots, nb_team)
    else:
        nb_teams = nb_team + nb_bots
        max_weeks = nb_teams - 1
        max_venue = nb_teams // 2
    if TOURNAMENT_SETTINGS.get("series_games", 1) > 1:
        max_weeks = max_weeks * TOURNAMENT_SETTINGS["series_games"]
    return max_weeks, max_venue


def max_groupstage_games():
    if TOURNAMENT_SETTINGS["groupstage"] is False:
        return 0
    if TOURNAMENT_SETTINGS["series_games"] < 1:
        return 0
    max_weeks, max_venue = count_games_per_team()
    return max_weeks * max_venue


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
    if i == "thirdplace":
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


def load_matches_from_scratch():
    print("Cache invalidated, reloading...")
    matches = {
        "groupstage": [],
        "knockout": []
    }
    max_weeks, max_venue = count_games_per_team()
    weeks = list(range(1, max_weeks + 1))
    venues = list(range(1, max_venue + 1))
    x0 = 0
    x1 = 0
    x2 = 0
    x3 = 0
    for i in weeks:
        a = []
        for j in venues:
            try:
                match_id = get_match_ids(i, max_weeks, j, max_venue)
                t0 = time.perf_counter()
                match_path = finders.find('matches_json/weeks/' + match_id + '.json')
                match_data_serialized = open(match_path)
                x = match_data_serialized.read()
                d = get_replacer_dict()
                for k in d.keys():
                    x = x.replace(k, d[k])
                match_data = json.loads(x)
                match_raw = match_data[0]
                t1 = time.perf_counter()
                x1 += t1 - t0
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
                t2 = time.perf_counter()
                x2 += t2 - t1
                match_evaluation = BaseRFTestCricketEngine(match_raw)
                match_raw["prediction"] = match_evaluation.evaluate_json_standard()
                for i2, i1 in enumerate(match_raw["innings"]):
                    match_evaluation.curr_inning = i2
                    for j1 in i1["data"]:
                        for k1 in j1:
                            match_evaluation.record_event(k1)
                            k1["evaluation"] = match_evaluation.evaluate_json_standard()
                t3 = time.perf_counter()
                x3 += t3 - t2
                a.append(match_raw)
            except TypeError:
                pass
        matches["groupstage"].append(a)
        print("Loaded component " + str(i) + " of " + str(max_weeks))
    print("Load time: " + str(x1))
    print("Rate time: " + str(x2))
    print("Eval time: " + str(x3))
    # final
    knockout_games = get_knockout_matches()
    for i0 in knockout_games:
        try:
            match_path = finders.find('matches_json/final/' + str(i0) + '.json')
            match_data_serialized = open(match_path)
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
            match_evaluation = BaseRFTestCricketEngine(match_raw)
            match_raw["prediction"] = match_evaluation.evaluate_json_standard()
            for i2, i1 in enumerate(match_raw["innings"]):
                match_evaluation.curr_inning = i2
                for j1 in i1["data"]:
                    for k1 in j1:
                        match_evaluation.record_event(k1)
                        k1["evaluation"] = match_evaluation.evaluate_json_standard()
            matches["knockout"].append(match_raw)
        except TypeError:
            pass
    t0 = time.perf_counter()
    set_item("games", matches, indent=0)
    t1 = time.perf_counter()
    print("Time to save to JSON: " + str(t1 - t0))
    print("Time to load JSON using old and slow: " + str(t1 - t0))
    # set_item("teams", TOURNAMENT_TEAMS, indent=0)
    return matches


def load_matches():
    x = get_item("games")
    if x is not None:
        return x
    return load_matches_from_scratch()


TOURNAMENT_GAMES = load_matches()


def fetch_game(clas, id):
    db = TOURNAMENT_GAMES.get(clas)
    if db is None:
        return None
    if clas == "knockout":
        for i in db:
            if i["_id"] == id:
                return i
    if clas == "groupstage":
        week = int(id.split("_")[1]) - 1
        for i in db[week]:
            if i["_id"] == id:
                return i
    return None


class Tournament():

    def __init__(self) -> None:
        self.__games = TOURNAMENT_GAMES

    def knockout(self):
        return self.__games.get("knockout")

    def final(self):
        return self.__games.get("knockout")[-1]

    def week(self, w: int):
        return self.__games.get("groupstage")[w - 1]

    def find(self):
        games = []
        for i in self.__games.get("groupstage"):
            games = games + i
        return games
        
    def find_one(self, id):
        db = self.__games.get("groupstage")
        week = int(id.split("_")[1]) - 1
        for i in db[week]:
            if i["_id"] == id:
                return i
        return None


def load_ongoing_matches():
    games = []
    max_weeks, max_venues = count_games_per_team()
    for i in range(1, max_weeks + 1):
        for j in range(1, max_venues + 1):
            match_id = get_match_ids(i, venue=j)
            match_path1 = finders.find('matches_json/weeks/' + match_id + '.json')
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
                    "id": x["_id"],
                    "team1": x["team1"],
                    "team2": x["team2"],
                    "innings": [],
                    "winner": x["winner"],
                    "margin": x["margin"],
                    "player_of_the_match": x["player_of_the_match"]
                }
                for k in x["innings"]:
                    o1 = {
                        "batting_team": k["batting_team"],
                        "bowling_team": k["bowling_team"],
                        "score": k["score"],
                        "balls": k["balls"],
                        "wickets": k["wickets"]
                    }
                    o["innings"].append(o1)
                games.append(o)
    return games
