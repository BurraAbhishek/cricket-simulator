import json
from django.contrib.staticfiles import finders
from bin.mongodb import mongoclient
from bin.models.team import Team, AbstractPlayer
from bin.mongoinserts.eligibility import QUALIFIED
from bin.mongoinserts.load_games import max_groupstage_games
from bin.mongoinserts.groupstage import get_knockout_bracket
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS
from modules.exportgame.export_innings import export_live_innings
from modules.exportgame.potm import get_potm


EXPORT_LOCATION = "matches_json_automated"


def get_pairings():
    base = str(finders.searched_locations[0])
    location = base + "/temp/"
    new_location = location + "pairings.json"
    try:
        f = open(new_location)
        f.close()
    except FileNotFoundError:
        return None
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
        pass
    try:
        with open(new_location, "w+") as f:
            json.dump(updated_pairing, f, indent=4)
    except FileNotFoundError:
        pass


def get_knockout_pairings():
    base = str(finders.searched_locations[0])
    location = base + "/temp/"
    new_location = location + "knockout_pairings.json"
    try:
        f = open(new_location)
        f.close()
    except FileNotFoundError:
        return None
    f = open(new_location, "r")
    x = json.load(f)
    f.close()
    return x


def update_knockout_pairings(updated_pairing):
    base = str(finders.searched_locations[0])
    location = base + "/temp/"
    new_location = location + "knockout_pairings.json"
    try:
        f = open(new_location)
        f.close()
    except FileNotFoundError:
        pass
    try:
        with open(new_location, "w+") as f:
            json.dump(updated_pairing, f, indent=4)
    except FileNotFoundError:
        pass


def player_of_the_tournament(final_potm=None):
    ko_pairings = get_knockout_pairings()
    if ko_pairings is None:
        return None
    for i in ko_pairings["games"]:
        if i["player_of_the_match"] != "":
            if i["player_of_the_match"] in ko_pairings["potm"].keys():
                ko_pairings["potm"][i["player_of_the_match"]] += 1
            else:
                ko_pairings["potm"][i["player_of_the_match"]] = 1
    if final_potm is not None and final_potm != "":
        if final_potm in ko_pairings["potm"].keys():
            ko_pairings["potm"][final_potm] += 1
        else:
            ko_pairings["potm"][final_potm] = 1
    potms = []
    for i in ko_pairings["potm"].keys():
        potms.append([i, ko_pairings["potm"][i]])
    potms.sort(key=lambda x: x[1], reverse=True)
    return potms[0][0]


def closing_comment(game):
    i = game["_id"]
    pairing = get_pairings()
    t1 = Team(pairing[0]["team1"])
    t2 = Team(pairing[0]["team2"])
    if pairing is None:
        return None
    bot = False
    if t1.ai() or t2.ai():
        bot = True
    comment = None
    if i[0] == "m":
        match_number = int(i[1:])
        max_round = 2 * TOURNAMENT_SETTINGS["series_games"]
        if match_number >= max_groupstage_games():
            if TOURNAMENT_SETTINGS["knockout"] == 1:
                try:
                    defending_champions = QUALIFIED[0]["team"]
                    challengers = QUALIFIED[1]["team"]
                except IndexError:
                    o = {
                        "team1": game["team1"],
                        "team2": game["team2"],
                        "team1_score": game["innings"][0]["score"],
                        "team1_balls": game["innings"][0]["balls"],
                        "team1_wickets": game["innings"][0]["wickets"],
                        "team2_score": game["innings"][1]["score"],
                        "team2_balls": game["innings"][1]["balls"],
                        "team2_wickets": game["innings"][1]["wickets"],
                        "winner": game["winner"]
                    }
                    ko = get_knockout_bracket(o)
                    defending_champions = ko[0]["team"]
                    challengers = ko[1]["team"]
                final1 = Team(defending_champions)
                final2 = Team(challengers)
                defending_champions_name = final1.abstract_name()
                challengers_name = final2.abstract_name()
                if not final1.ai():
                    defending_champions_name = final1.abstract_name()
                if not final2.ai():
                    challengers_name = final2.abstract_name()
                comment = str(
                    "Round "
                    + str(max_round)
                    + " is officially completed and it is time for the big moment. "
                    + defending_champions_name
                    + " will face " 
                    + challengers_name
                    + " in the Final. Do join us then, take care and goodbye!"
                )
            else:
                comment = str(
                    "Round "
                    + str(max_round)
                    + " is officially completed and it is time for the knockouts. Do join us then, take care and goodbye!"
                )
        else:
            curr_pairing = pairing[match_number - 1]
            next_pairing = pairing[match_number]
            team1 = next_pairing["team1"]
            team2 = next_pairing["team2"]
            team1_t = Team(team1)
            team2_t = Team(team2)
            if team1_t.ai() and not team2_t.ai():
                team1 = next_pairing["team2"]
                team2 = next_pairing["team1"]
            else:
                team1 = next_pairing["team1"]
                team2 = next_pairing["team2"]
            team1_t = Team(team1)
            team2_t = Team(team2)
            team1_name = team1_t.abstract_name()
            team2_name = team2_t.abstract_name()
            if next_pairing["curr_round"] > curr_pairing["curr_round"]:
                comment = "Round "
                comment += str(curr_pairing["curr_round"])
                comment += " is officially completed. Next, in Round "
                comment += str(next_pairing["curr_round"])
                comment += ", "
                if bot and TOURNAMENT_SETTINGS.get("bot_group", True):
                    comment += "the Group 1 teams must "
                    if team1_t.ai():
                        comment += "bowl"
                    else:
                        comment += "bat"
                    comment += " first. The first match will feature "
                    comment += team1_name
                    comment += " facing "
                    comment += team2_name
                else:
                    comment += "the toss will be flipped. The first match will feature "
                    comment += team1_name
                    comment += " facing "
                    comment += team2_name
            else:
                comment = "Next, "
                comment += team1_name
                comment += " will face "
                comment += team2_name
            comment += ". Do join us then, take care and goodbye!"
    else:
        # knockout
        if i == "final":
            return None
        elif i == "sf2":
            ko_bracket = get_knockout_pairings()
            team1 = ko_bracket["sf"][0]["winner"]
            team2 = game["winner"]
            defending_champions = team1
            challengers = team2
            final1 = Team(defending_champions)
            final2 = Team(challengers)
            defending_champions_name = final1.abstract_name()
            challengers_name = final2.abstract_name()
            comment = str(
                "It is time for the big moment. "
                + defending_champions_name
                + " will face " 
                + challengers_name
                + " in the final. Do join us then, take care and goodbye!"
            )
            if TOURNAMENT_SETTINGS.get("knockout", 1) > 1 and TOURNAMENT_SETTINGS.get("thirdplace", False):
                loser = None
                if game["winner"] == game["team1"]:
                    loser = game["team2"]
                elif game["winner"] == game["team2"]:
                    loser = game["team1"]
                if loser is None:
                    loser_str = "the losing side"
                else:
                    loser_str = Team(loser).abstract_name()
                comment = str(
                    defending_champions_name
                    + " will face " 
                    + challengers_name
                    + " in the Final. Before that, "
                    + loser_str
                    + " will face "
                    + Team(ko_bracket["sf"][0]["loser"]).abstract_name()
                    + " in the battle for third place."
                    + " Do join us then, take care and goodbye!"
                )
        elif i == "sf1":
            winner = game["winner"]
            winner_name = Team(winner).abstract_name()
            comment = str(
                winner_name
                + " have qualified for the Final and will await the result of Semi-Final 2"
                + " which will begin shortly. Do join us then, take care and goodbye!"
            )
        elif i == "thirdplace":
            try:
                ko_bracket = get_knockout_pairings()
                final1 = Team(ko_bracket["sf"][0]["winner"])
                final2 = Team(ko_bracket["sf"][1]["winner"])
                defending_champions_name = final1.abstract_name()
                challengers_name = final2.abstract_name()
                comment = str(
                    "It is time for the big moment. "
                    + defending_champions_name
                    + " will face " 
                    + challengers_name
                    + " in the Final. Do join us then, take care and goodbye!"
                )
            except Exception:
                pass
        else:
            winner = game["winner"]
            loser = ""
            if game["winner"] == game["team1"]:
                loser = game["team2"]
            elif game["winner"] == game["team2"]:
                loser = game["team1"]
            if loser == "":
                return None
            winner_name = Team(winner).abstract_name()
            loser_name = Team(loser).abstract_name()
            if i in [str("r8_" + str(k)) for k in range(1, 9)]:
                nextstage = "quarter-finals"
            elif i in ["qf1", "qf2", "qf3", "qf4"]:
                nextstage = "semi-finals"
            else:
                nextstage = "next stage of the knockout"
            comment = str(
                winner_name
                + " advance to the "
                + nextstage
                + " while "
                + loser_name
                + " are out of the competition. The next knockout match will begin shortly. Do join us then, take care and goodbye!"
            )
    return comment


def export_live_game_automated(request):
    # fetch innings
    innings = []
    innings1 = export_live_innings(1)
    innings2 = export_live_innings(2)
    innings.append(innings1)
    innings.append(innings2)
    # Match
    temp_match = mongoclient.live_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS
    ).find_one(0)
    game = {
        "_id": temp_match["id"],
        "isTest": temp_match["isTest"],
        "overs": temp_match["overs"],
        "wickets": temp_match["wickets"],
        "team1": temp_match["team1"],
        "team2": temp_match["team2"],
        "toss": int(temp_match["toss"]),
        "nomination": temp_match["nominations"],
        "innings": innings,
        "target": innings1["score"] + 1,
        "winner": "",
        "margin": "",
        "player_of_the_match": "",
        "assessment": {
            "nomination": {
                temp_match["team1"]: {
                    "integrity_clearance": True,
                    "roster_clearance": True
                },
                temp_match["team2"]: {
                    "integrity_clearance": True,
                    "roster_clearance": True
                }
            },
            "integrity": 1,
            "result": [],
            "result_valid": True,
            "pitch": 1,
            "outfield": 1,
            "violations": {
                "summary": [],
                "behavior": [],
                "stop_clock": [],
                "ball": [],
                "park": [],
                "cheat": [],
                "fixing": []
            },
            "executive": "The match reached its natural conclusion based solely on player merit. No breaches detected.",
            "remarks": []
        }
    }
    if innings1["score"] > innings2["score"]:
        game["winner"] = temp_match["team1"]
        game["assessment"]["result"] = [1, 0]
        game["margin"] = str(innings1["score"] - innings2["score"]) + " run"
        if innings1["score"] - innings2["score"] != 1:
            game["margin"] += "s"
    elif innings1["score"] < innings2["score"]:
        game["winner"] = temp_match["team2"]
        game["assessment"]["result"] = [0, 1]
        game["margin"] = str(temp_match["wickets"] - innings2["wickets"]) + " wicket"
        if temp_match["wickets"] - innings2["wickets"] != 1:
            game["margin"] += "s"
    else:
        game["assessment"]["result"] = [0.5, 0.5]
        game["margin"] = "Match Tied"
    # Player of the Match
    potm = get_potm(game)
    game["player_of_the_match"] = potm
    # Player of the Tournament
    if game["_id"] == "final":
        # Change later if required
        pott = player_of_the_tournament(game["player_of_the_match"])
        if pott is None:
            if game["winner"] != "":
                pott = Team(game["winner"]).captain()
        game["player_of_the_tournament"] = pott
    # End commentaries
    for i, e in enumerate(game["innings"], start=1):
        has_end = False
        for j in e["commentary"]:
            if j["_id"] == str(i) + ".end":
                has_end = True
        if not has_end:
            e["commentary"].append({
                "_id": str(i) + ".end",
                "comments": []
            })
        if i == 2:
            if game["winner"] is not None and game["winner"] != "":
                game_winner_name = Team(game["winner"]).abstract_name()
                win_string = str(
                    " "
                    + game_winner_name
                    + " win by "
                    + game["margin"]
                    + "!"
                )
                if game["_id"] == "final":
                    win_string = str(
                        " "
                        + game_winner_name
                        + " win the final by "
                        + game["margin"]
                        + "!"
                    )
                if game["_id"] == "sf1":
                    win_string = str(
                        " "
                        + game_winner_name
                        + " win the semi-final by "
                        + game["margin"]
                        + "!"
                    )
                if game["_id"] == "sf2":
                    ko_bracket = get_knockout_pairings()
                    team1 = ko_bracket["sf"][0]["winner"]
                    opponent = Team(team1).abstract_name()
                    win_string = str(
                        " "
                        + game_winner_name
                        + " win by "
                        + game["margin"]
                        + " and will face "
                        + opponent
                        + " in the final."
                    )
                if game["_id"] in ["qf1", "qf2", "qf3", "qf4"]:
                    win_string = str(
                        " "
                        + game_winner_name
                        + " win the quarter-final by "
                        + game["margin"]
                        + "!"
                    )
                e["data"][-1][-1]["commentary"] += win_string
            if potm is not None and potm != "":
                potm_alias = Team(potm).abstract_name()
                e["commentary"][-1]["comments"].append({
                    "key": "Text",
                    "value": str(
                            potm_alias
                            + " will receive Player of the Match award."
                        )
                    })
            closing_comment0 = closing_comment(game)
            if closing_comment0 is not None:
                e["commentary"][-1]["comments"].append({
                    "key": "Text",
                    "value": closing_comment0
                })
            if game["_id"] == "final" and game["winner"] != "":
                if pott is not None and pott != "":
                    pott_alias = Team(pott).abstract_name()
                    e["commentary"][-1]["comments"].append({
                        "key": "Text",
                        "value": str(
                                pott_alias
                                + " will receive Player of the Tournament award."
                            )
                        })
                if game["winner"] == game["team1"]:
                    loser = game["team2"]
                else:
                    loser = game["team1"]
                e["commentary"][-1]["comments"].append({
                        "key": "Text",
                        "value": str(
                                "Next up, the players of the runners-up team, "
                                + Team(loser).abstract_name()
                                + ", are called up one-by-one to collect"
                                + " their medals."
                            )
                        })
                e["commentary"][-1]["comments"].append({
                        "key": "Text",
                        "value": str(
                                "It is now time for the players of the winning team, "
                                + Team(game["winner"]).abstract_name()
                                + ", to be called up on stage to collect"
                                + " their medals."
                            )
                        })
                winning_captain = Team(game["winner"]).captain()
                e["commentary"][-1]["comments"].append({
                        "key": "Text",
                        "value": str(
                                "It's time for the final moment. Victorious captain "
                                + AbstractPlayer(winning_captain).abstract_name()
                                + " collects the trophy and holds it aloft."
                                + " The celebrations will continue for a long, long"
                                + " time to come. Until next time, take care"
                                + " and goodbye!"
                            )
                        })
        else:
            team_name1 = Team(e["batting_team"]).abstract_name()
            team_name2 = Team(e["bowling_team"]).abstract_name()
            if e["wickets"] < 10:
                if e["score"] == 0:
                    e["data"][-1][-1]["commentary"] += str(
                        " "
                        + team_name1
                        + " finish with nought"
                    )
                elif e["score"] == 1:
                    e["data"][-1][-1]["commentary"] += str(
                        " "
                        + team_name1
                        + " finish with 1 run"
                    )
                else:
                    e["data"][-1][-1]["commentary"] += str(
                        " "
                        + team_name1
                        + " finish with "
                        + str(e["score"])
                        + " runs"
                    )
                if e["wickets"] == 0:
                    e["data"][-1][-1]["commentary"] += " and no loss of wicket"
                    if e["score"] >= 360:
                        e["data"][-1][-1]["commentary"] += "!"
                    else:
                        e["data"][-1][-1]["commentary"] += "."
                elif e["wickets"] == 1:
                    e["data"][-1][-1]["commentary"] += " for the loss of 1 wicket."
                else:
                    e["data"][-1][-1]["commentary"] += str(
                        " for the loss of " 
                        + str(e["wickets"]) 
                        + " wickets."
                        )
            else:
                if e["score"] == 0:
                    e["data"][-1][-1]["commentary"] += str(
                    " "
                    + team_name1.upper()
                    + " ARE BOWLED OUT FOR NOUGHT!"
                )
                elif e["score"] == 1:
                    e["data"][-1][-1]["commentary"] += str(
                    " "
                    + team_name1
                    + " are bowled out for a mere 1 run!"
                )
                else:
                    e["data"][-1][-1]["commentary"] += str(
                        " "
                        + team_name1
                        + " are bowled out for "
                        + str(e["score"])
                        + "."
                    )
            e["commentary"][-1]["comments"].append({
                "key": "Text",
                "value": str(
                    team_name2
                    + " need "
                    + str(e["score"] + 1)
                    + " run"
                    + str("" if e["score"] == 0 else "s")
                    + " to win in "
                    + str(6 * game["overs"])
                    + " balls. Back in a bit for the chase..."
                )
            })
    # Commentary clean up
    for i in game["innings"]:
        for i0 in i["data"]:
            for j in i0:
                s = str(j["commentary"])
                s = s.strip()
                s = " ".join([k for k in s.split(" ") if k != ""])
                j["commentary"] = s
    # Export
    match_path_str = EXPORT_LOCATION + "/" + temp_match["id"] + ".json"
    match_path = finders.find(match_path_str)
    if match_path is None:
        mp = str(finders.searched_locations[0])
        f = open(mp + "/" + match_path_str, "w")
        f.write('{}')
        f.close()
    match_path = finders.find(match_path_str)
    f = open(match_path, "w+")
    json.dump([game], f, indent=2)
    f.close()
    # Save result only for groupstage
    if temp_match["id"][0] == "m":
        pairing = get_pairings()
        if pairing is not None:
            for i in pairing:
                if i["match_id"] == temp_match["id"]:
                    i["winner"] = game["winner"]
            update_pairings(pairing)
