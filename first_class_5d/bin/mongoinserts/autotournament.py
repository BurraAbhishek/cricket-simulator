import os
import shutil
import json
import random
from copy import deepcopy
from urllib.parse import urlencode
from django.contrib.staticfiles import finders
from django.http import HttpResponseRedirect, HttpRequest
from django.shortcuts import render
from bin.models.team import Team
from bin.mongoinserts.load_games import get_knockout_matches, load_ongoing_matches
from bin.mongoinserts.pairing import get_test_pairings
from bin.mongoinserts.groupstage import get_knockout_bracket
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS
from modules.live.controllers.game_automate import newGame
from modules.exportgame.export_game_automated import EXPORT_LOCATION


def play_from_match(request, m_id):
    return play_match(request, m_id)


def play_only_match(request, m_id):
    if request.GET:
        return play_match(request, m_id, only=True, params=request.GET)
    else:
        return play_match(request, m_id, only=True)


def play_match(request, m_id, only=False, params=None):
    pairings = get_pairings()
    try:
        i = pairings[m_id]
    except IndexError:
        # Play knockout
        # return HttpResponseRedirect("/")
        return play_knockout(request, None, 0)
    newGame(request, i)
    base = str(finders.searched_locations[0])
    match_location = base + "/" + EXPORT_LOCATION + "/" + i["match_id"] + ".json"
    try:
        f = open(match_location)
        f.close()
    except FileNotFoundError:
        return play_match(request, m_id - 1)
    reset_match()
    if only is True:
        if params:
            return HttpResponseRedirect("/play?" + urlencode(params))
        return HttpResponseRedirect("/play")
    return render(
        request,
        "automated_matches.html",
        {
            "current_match_number": m_id + 1,
            "total_matches": len(pairings)
        }
    )


def play_bronze_playoff(request, teams, finalists, position):
    pairing = {
        "match_id": "thirdplace",
        "team1": teams[0],
        "team2": teams[1],
        "nom1": Team(teams[0]).nominations(),
        "nom2": Team(teams[1]).nominations(),
        "toss": random.randint(1, 2)
    }
    newGame(request, pairing)
    base = str(finders.searched_locations[0])
    match_location = base + "/" + EXPORT_LOCATION + "/thirdplace.json"
    reset_match()
    f = open(match_location, "r")
    m = json.load(f)
    f.close()
    print("Game played: " + m[0]["_id"])
    return play_knockout(request, finalists, position + 1)


def play_knockout(request, initial_bracket=None, position=None):
    if initial_bracket is None:
        initial_bracket = get_knockout_bracket()
        reset_ko_pairings()
    if position is None:
        position = 0
    if len(initial_bracket) < 2:
        return HttpResponseRedirect("/")
    teams = deepcopy(initial_bracket)
    pairing0 = get_ko_pairings()
    pairing = pairing0["games"]
    k = len(teams) // 2
    bracket = []
    losers = []
    for i in range(0, k):
        bracket_element = [teams[i], teams[2 * k - i - 1]]
        random.shuffle(bracket_element)
        bracket.append(bracket_element)
    for i0, i in enumerate(bracket):
        toss = random.randint(1, 2)
        pairing[position + i0]["team1"] = i[0]["team"]
        pairing[position + i0]["team2"] = i[1]["team"]
        pairing[position + i0]["nom1"] = Team(i[0]["team"]).nominations()
        pairing[position + i0]["nom2"] = Team(i[1]["team"]).nominations()
        pairing[position + i0]["toss"] = toss
        newGame(request, pairing[position + i0])
        base = str(finders.searched_locations[0])
        match_location = base + "/" + EXPORT_LOCATION + "/" + pairing[position + i0]["match_id"] + ".json"
        reset_match()
        f = open(match_location, "r")
        m = json.load(f)
        f.close()
        print("Game played: " + m[0]["_id"])
        winner = m[0]["winner"]
        while winner == "":
            newGame(request, pairing[position + i0])
            f = open(match_location, "r")
            m = json.load(f)
            f.close()
            reset_match()
            print("Game played: " + m[0]["_id"])
            winner = m[0]["winner"]
        pairing[position + i0]["winner"] = winner
        pairing[position + i0]["player_of_the_match"] = m[0]["player_of_the_match"]
        pairing0["games"] = pairing
        if m[0]["_id"] == "sf1":
            if winner == i[0]["team"]:
                pairing0["sf"][0]["winner"] = i[0]["team"]
                pairing0["sf"][0]["loser"] = i[1]["team"]
            elif winner == i[1]["team"]:
                pairing0["sf"][0]["winner"] = i[1]["team"]
                pairing0["sf"][0]["loser"] = i[0]["team"]
        if m[0]["_id"] == "sf2":
            if winner == i[0]["team"]:
                pairing0["sf"][1]["winner"] = i[0]["team"]
                pairing0["sf"][1]["loser"] = i[1]["team"]
            elif winner == i[1]["team"]:
                pairing0["sf"][1]["winner"] = i[1]["team"]
                pairing0["sf"][1]["loser"] = i[0]["team"]
        update_ko_pairings(pairing0)
        if winner == i[0]["team"]:
            teams = [e for e in teams if e["team"] != i[1]["team"]]
            losers.append(i[1]["team"])
        elif winner == i[1]["team"]:
            teams = [e for e in teams if e["team"] != i[0]["team"]]
            losers.append(i[0]["team"])
        print(m[0]["_id"].upper() + " Completed")
    if len(teams) < 2:
        return HttpResponseRedirect("/")
    else:
        if len(losers) == 2 and TOURNAMENT_SETTINGS.get("thirdplace", False):
            return play_bronze_playoff(request, losers, teams, position + len(bracket))
        else:
            return play_knockout(request, teams, position + len(bracket))


def reset_match():
    base = str(finders.searched_locations[0])
    location = base + "/temp/"
    shutil.rmtree(location + "live")
    os.mkdir(location + "live")
    new_location = location + "live/match_details.json"
    f = open(new_location, "w+")
    f.write('{}')
    f.close()


def reset_pairings():
    base = str(finders.searched_locations[0])
    location = base + "/temp/"
    new_location = location + "pairings.json"
    f = open(new_location, "w+")
    f.write('{}')
    f.close()
    pairings = get_test_pairings()
    with open(new_location, "w+") as f:
        json.dump(pairings, f, indent=4)


def reset_ko_pairings():
    base = str(finders.searched_locations[0])
    location = base + "/temp/"
    new_location = location + "knockout_pairings.json"
    f = open(new_location, "w+")
    f.write('{}')
    f.close()
    pairings = reset_knockout_pairings()
    with open(new_location, "w+") as f:
        json.dump(pairings, f, indent=4)


def get_pairings():
    base = str(finders.searched_locations[0])
    location = base + "/temp/"
    new_location = location + "pairings.json"
    try:
        f = open(new_location)
        f.close()
    except FileNotFoundError:
        reset_pairings()
    f = open(new_location, "r")
    x = json.load(f)
    f.close()
    return x


def get_ko_pairings():
    base = str(finders.searched_locations[0])
    location = base + "/temp/"
    new_location = location + "knockout_pairings.json"
    try:
        f = open(new_location)
        f.close()
    except FileNotFoundError:
        reset_ko_pairings()
    f = open(new_location, "r")
    x = json.load(f)
    f.close()
    return x


def update_pairings(updated_pairing):
    base = str(finders.searched_locations[0])
    location = base + "/temp/"
    new_location = location + "pairings.json"
    try:
        f = open(new_location)
        f.close()
    except FileNotFoundError:
        reset_pairings()
    with open(new_location, "w+") as f:
        json.dump(updated_pairing, f, indent=4)


def update_ko_pairings(updated_pairing):
    base = str(finders.searched_locations[0])
    location = base + "/temp/"
    new_location = location + "knockout_pairings.json"
    try:
        f = open(new_location)
        f.close()
    except FileNotFoundError:
        reset_ko_pairings()
    with open(new_location, "w+") as f:
        json.dump(updated_pairing, f, indent=4)


def reset_knockout_pairings():
    ongoing_games = load_ongoing_matches()
    ko_ids = get_knockout_matches()
    pairings = {
        "teams": get_knockout_bracket(),
        "survivors": [],
        "ids": ko_ids,
        "games": [],
        "potm": {}
    }
    if TOURNAMENT_SETTINGS.get("knockout", 1) > 1:
        pairings["sf"] = [
            {
                "winner": "",
                "loser": ""
            },
            {
                "winner": "",
                "loser": ""
            }
        ]
    for i in ongoing_games:
        if i["player_of_the_match"] != "":
            if i["player_of_the_match"] in pairings["potm"].keys():
                pairings["potm"][i["player_of_the_match"]] += 1
            else:
                pairings["potm"][i["player_of_the_match"]] = 1
    for i in ko_ids:
        pairings["games"].append(
            {
                "id": i,
                "match_id": i,
                "round_matches": len(ko_ids),
                "team1": "",
                "team2": "",
                "nom1": None,
                "nom2": None,
                "toss": 0,
                "winner": "",
                "player_of_the_match": ""
            }
        )
    return pairings


def render_autotournament_ui(request: HttpRequest):
    pairings = get_pairings()
    num_games = len(pairings)
    for i0, i in enumerate(pairings):
        id_parts = i["match_id"].split("_")
        team1 = Team(i["team1"])
        team2 = Team(i["team2"])
        i["index"] = i0
        i["team1_name"] = team1.name()
        i["team2_name"] = team2.name()
        i["team1_flag"] = team1.get("flag")
        i["team2_flag"] = team2.get("flag")
        i["team1_color"] = team1.get("color")
        i["team2_color"] = team2.get("color")
        i["id_formatted"] = str(
            str(int(id_parts[1]))
            + " • "
            + str(int(id_parts[2]))
        )
    params = None
    if request is not None:
        team1 = request.GET.get("team1")
        team2 = request.GET.get("team2")
        # Test
        if team1 is not None:
            if team2 is None:
                pairings = [i for i in pairings if i["team1"] == team1 or i["team2"] == team1]
            else:
                pairings = [
                    i for i in pairings 
                    if (i["team1"] == team1 and i["team2"] == team2)
                    or (i["team1"] == team2 and i["team2"] == team1)
                ]
            params = urlencode(request.GET)
    return render(
        request,
        "automate_tournament.html",
        {
            "pairings": pairings,
            "groupstage_count": num_games,
            "settings": TOURNAMENT_SETTINGS,
            "params": params
        }
    )
