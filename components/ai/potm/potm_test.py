from time import time
from django.http import HttpResponseRedirect
from bin.mongoinserts.load_games import TOURNAMENT_GAMES
from bin.mongoinserts.cachebase import get_item, set_item
from modules.ai.potm import get_potm, get_potm_data


def test_ai_potm(_):
    results = {
        "checkpoint": 0,
        "data": {},
        "matching": 0,
        "not_matching": 0
    }
    games = TOURNAMENT_GAMES["groupstage"] + TOURNAMENT_GAMES["knockout"]
    current_time = time()
    for game in games:
        game_summary = get_potm_data(game)
        chosen_potm = get_potm(game_summary)
        #chosen_potm = game["player_of_the_match"]
        time_diff = time() - current_time
        current_time = time()
        matching = bool(game["player_of_the_match"] == chosen_potm)
        results["data"][game["_id"]] = {
            "summary": game_summary,
            "original_potm": game["player_of_the_match"],
            "new_potm": chosen_potm,
            "matching": matching,
            "time_taken": time_diff
        }
        results["checkpoint"] += 1
        if matching:
            results["matching"] += 1
        else:
            results["not_matching"] += 1
        print(game["_id"], game["player_of_the_match"], chosen_potm)
        set_item("test_ai_potm", results)
    return HttpResponseRedirect("/")