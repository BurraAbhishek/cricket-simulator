from collections import defaultdict
from django.shortcuts import render
from bin.models.team import Team
from bin.mongoinserts.load_games import TOURNAMENT_GAMES, translate_ko_id
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS


WIN = "Victory"
LOSS = "Defeat"
TIE = "Draw"


def fetch_team_name(id: str):
    return Team(id).get("name")


def get_team_progression(request, id: str):
    d = defaultdict(int)
    groupstage_matches = []
    groupstage_team_collection_raw = TOURNAMENT_GAMES.get("groupstage")
    groupstage_team_collection = []
    for i in groupstage_team_collection_raw:
        if i["team1"] == id or i["team2"] == id:
            key = ''.join(sorted([i["team1"], i["team2"]]))
            d[key] += 1
            groupstage_team_collection.append(i)
    num_games = len(groupstage_team_collection_raw)
    try:
        num_rounds = max(d.values())
    except ValueError:
        num_rounds = 1
    for i in list(groupstage_team_collection):
        j = {
            "match_number": 0,
            "round": 0,
            "match": 0,
            "opponent": "",
            "opponent_name": "",
            "result": "",
            "margin": "",
            "display_class": "",
            "link": "/#groupstagematch-" + i["_id"]
        }
        try:
            k1 = int(i["_id"][1:])
            k = num_games // num_rounds
            j["match_number"] = k1
            j["round"] = ((k1 - 1) // k) + 1
            j["match"] = 1 + ((k1 - 1) % k)
        except TypeError:
            pass
        if i["team1"] == id:
            j["opponent"] = i["team2"]
            j["opponent_name"] = fetch_team_name(i["team2"])
        elif i["team2"] == id:
            j["opponent"] = i["team1"]
            j["opponent_name"] = fetch_team_name(i["team1"])
        if id == i["winner"]:
            j["result"] = WIN
            j["margin"] = i["margin"]
            j["display_class"] = "win"
        elif i["winner"] ==  j["opponent"]:
            j["result"] = LOSS
            j["margin"] = i["margin"]
            j["display_class"] = "loss"
        elif i["winner"] == "" and i["margin"] == "Double Forfeit":
            j["result"] = i["margin"]
            j["margin"] = ""
            j["display_class"] = "loss"
        else:
            j["result"] = TIE
            j["display_class"] = "tie"
        groupstage_matches.append(j)
    knockout_raw = TOURNAMENT_GAMES.get("knockout")
    if TOURNAMENT_SETTINGS["knockout"] == 1 and len(knockout_raw) > 0:
        final = {
            "eligible": False,
            "opponent": "",
            "opponent_name": "",
            "result": "",
            "margin": "",
            "display_class": ""
        }
        # FINAL
        final_raw = knockout_raw[-1]
        if final_raw["team1"] == id or final_raw["team2"] == id:
            final["eligible"] = True
            if final_raw["team1"] == id:
                final["opponent"] = final_raw["team2"]
                final["opponent_name"] = fetch_team_name(final_raw["team2"])
            elif final_raw["team2"] == id:
                final["opponent"] = final_raw["team1"]
                final["opponent_name"] = fetch_team_name(final_raw["team1"])
            if id == final_raw["winner"]:
                final["result"] = WIN
                final["margin"] = final_raw["margin"]
                final["display_class"] = "win"
            elif final_raw["winner"] == final["opponent"]:
                final["result"] = LOSS
                final["margin"] = final_raw["margin"]
                final["display_class"] = "loss"
            else:
                final["result"] = TIE
                final["display_class"] = "tie"
        return groupstage_matches, final
    else:
        final = []
        for i in knockout_raw:
            if i["team1"] == id or i["team2"] == id:
                match_id = translate_ko_id(i["_id"])
                if i["_id"][0] == "r":
                    match_id = match_id[9:]
                o = {
                    "match": match_id,
                    "opponent": "",
                    "opponent_name": "",
                    "result": "",
                    "margin": "",
                    "display_class": "",
                    "link": "/#knockoutmatch-" + i["_id"]
                }
                if i["team1"] == id:
                    o["opponent"] = i["team2"]
                    o["opponent_name"] = fetch_team_name(i["team2"])
                elif i["team2"] == id:
                    o["opponent"] = i["team1"]
                    o["opponent_name"] = fetch_team_name(i["team1"])
                if id == i["winner"]:
                    o["result"] = WIN
                    o["margin"] = i["margin"]
                    o["display_class"] = "win"
                elif i["winner"] == o["opponent"]:
                    o["result"] = LOSS
                    o["margin"] = i["margin"]
                    o["display_class"] = "loss"
                else:
                    o["result"] = TIE
                    o["display_class"] = "tie"
                final.append(o)
        return groupstage_matches, final


def fetch_team_progression(request, id: str):
    # current team
    team_name = fetch_team_name(id)
    groupstage_matches, final = get_team_progression(request, id)
    # Render
    return render(
        request,
        "teamprogression.html",
        {
            "team_name": team_name,
            "groupstage_matches": groupstage_matches,
            "final": final,
            "settings": TOURNAMENT_SETTINGS
        }
    )
