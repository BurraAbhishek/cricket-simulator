import json
from django.contrib.staticfiles import finders
from bin.mongodb import mongoclient
from bin.models.team import Team, AbstractPlayer
from bin.mongoinserts.load_games import count_games_per_team
from bin.mongoinserts.groupstage import get_knockout_bracket
from bin.mongoinserts.eligibility import QUALIFIED
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS
from modules.exportgame.export_innings import export_live_innings
from modules.exportgame.potm import get_potm
from modules.exportgame.paginator import get_raw_sessions


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


def commentary_sorter(a):
    a1 = a["_id"].split(".")[1]
    if a1 == "start":
        a2 = 0
    elif a1 == "end":
        a2 = 5000
    else:
        a2 = int(a1)
    return a2


def export_live_game_automated(request, force_end=0):
    # Match
    temp_match_collection = mongoclient.live_db_get_collection(
        mongoclient.CURRENT_MATCH_DETAILS
    )
    temp_match = temp_match_collection.find_one(0)
    temp_details = temp_match_collection.find_one(1)
    nbInnings = temp_details["stage"]
    # fetch innings
    innings = []
    innings1 = export_live_innings(1)
    innings.append(innings1)
    if nbInnings > 1:
        innings2 = export_live_innings(2)
        innings.append(innings2)
    if nbInnings > 2:
        innings3 = export_live_innings(3)
        innings.append(innings3)
    if nbInnings > 3:
        innings4 = export_live_innings(4)
        innings.append(innings4)
    game_id = temp_match["id"]
    # fetch sessions
    game_sessions_update = get_raw_sessions(innings, game_id, int(temp_match["wickets"]))
    innings = game_sessions_update["innings"]
    game_sessions = game_sessions_update["sessions"]
    # game
    follow_on = bool(temp_details["follow_on_enabled"])
    game = {
        "_id": temp_match["id"],
        "isTest": temp_match["isTest"],
        "follow_on_threshold": 200,
        "follow_on": follow_on,
        "wickets": temp_match["wickets"],
        "team1": temp_match["team1"],
        "team2": temp_match["team2"],
        "toss": int(temp_match["toss"]),
        "nomination": temp_match["nominations"],
        "innings": innings,
        "sessions": game_sessions,
        "target": temp_details["target"],
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
            "result": [0.5, 0.5],
            "result_valid": True,
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
    if nbInnings > 2:
        if temp_details["net_score"] > 0:
            if nbInnings == 3:
                game["margin"] = "an innings and "
            else:
                game["margin"] = ""
            game["winner"] = temp_match["team1"]
            game["margin"] += str(temp_details["net_score"]) + " run"
            if temp_details["net_score"] != 1:
                game["margin"] += "s"
            if follow_on and nbInnings == 4:
                game["margin"] = str(temp_match["wickets"] - innings4["wickets"]) + " wicket"
                if temp_match["wickets"] - innings4["wickets"] != 1:
                    game["margin"] += "s"
            game["assessment"]["result"] = [1, 0]
        elif temp_details["net_score"] < 0:
            game["winner"] = temp_match["team2"]
            if nbInnings == 3:
                game["margin"] = "an innings and "
                game["margin"] += str(0 - temp_details["net_score"]) + " run"
                if temp_details["net_score"] != -1:
                    game["margin"] += "s"
            else:
                game["margin"] = str(temp_match["wickets"] - innings4["wickets"]) + " wicket"
                if temp_match["wickets"] - innings4["wickets"] != 1:
                    game["margin"] += "s"
            if follow_on and nbInnings == 4:
                game["margin"] = str(0 - temp_details["net_score"]) + " run"
                if temp_details["net_score"] != -1:
                    game["margin"] += "s"
            game["assessment"]["result"] = [0, 1]
        else:
            game["margin"] = "Match Tied"
    else:
        game["margin"] = "Draw"
    # Force draw if any
    if force_end == 1:
        # Draw
        game["margin"] = "Draw"
        game["winner"] = ""
    # Player of the match
    potm = get_potm(game)
    game["player_of_the_match"] = potm
    # Player of the tournament
    if game["_id"] == "final":
        # Change later if required
        pott = player_of_the_tournament(game["player_of_the_match"])
        if pott is None:
            if game["winner"] != "":
                pott = Team(game["winner"]).captain()
        game["player_of_the_tournament"] = pott
    # Force double forfeit if any
    if force_end == -1:
        game["margin"] = "Double Forfeit"
        game["winner"] = ""
        game["player_of_the_match"] = ""
        game["assessment"]["result"] = [0, 0]
        game["assessment"]["result_valid"] = False
        game["assessment"]["integrity"] = 0.1
        game["assessment"]["fixing"].append(
            "Not more than one innings was played. Therefore, neither side"
            + " has put in sufficient efforts to win."
        )
        game["assessment"]["executive"] = str(
            "Both sides played out only one innings and improperly influenced"
            + " the result of the match. Both sides forfeit the match."
        )
    # End commentaries
    session_ends = [-1, -1, -1, -1]
    for i, e in enumerate(game["sessions"]):
        if e.get("end_ball", "") == "end":
            j = int(e["end_inning"])
            if i % 3 == 2:
                session_ends[j] = i // 3
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
        if i == len(game["innings"]):
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
                potm_alias = AbstractPlayer(potm).abstract_name()
                e["commentary"][-1]["comments"].append({
                    "key": "Text",
                    "value": str(
                            potm_alias
                            + " will receive Player of the Match award."
                        )
                    })
            bot = False
            team1_o = Team(game["team1"])
            team2_o = Team(game["team2"])
            if team1_o.ai() or team2_o.ai():
                bot = True
            if game["_id"][0] == "m":
                match_week = int(game["_id"].split("_")[1])
                max_games, _ = count_games_per_team()
                if match_week >= max_games:
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
                        defending_champions_name = Team(defending_champions).abstract_name()
                        challengers_name = Team(challengers).abstract_name()
                        e["commentary"][-1]["comments"].append(
                            {
                            "key": "Text",
                            "value": str(
                                "That's all from this match. "
                                + defending_champions_name
                                + " will face " 
                                + challengers_name
                                + " in the Final later this week. Do join us then, take care and goodbye!"
                            )
                            })
                    else:
                        e["commentary"][-1]["comments"].append(
                            {
                            "key": "Text",
                            "value": "That's all from this match and it is time for the knockouts. Do join us then, take care and goodbye!"
                            })
                else:
                    e["commentary"][-1]["comments"].append({
                        "key": "Text",
                        "value": "That's all from this match. The next set of matches begins next week. Do join us then, take care and goodbye!"
                    })
            elif game["_id"] == "final" and game["winner"] != "":
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
            elif game["_id"] == "sf2":
                ko_bracket = get_knockout_pairings()
                team1 = ko_bracket["sf"][0]["winner"]
                team2 = game["winner"]
                defending_champions = team1
                challengers = team2
                defending_champions_name = Team(defending_champions).abstract_name()
                challengers_name = Team(challengers).abstract_name()
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
                e["commentary"][-1]["comments"].append({
                    "key": "Text",
                    "value": comment
                })
            elif game["_id"] == "sf1":
                winner = game["winner"]
                winner_name = Team(winner).abstract_name()
                comment = str(
                    winner_name
                    + " have qualified for the final and will await the result of Semi-Final 2"
                    + " which will begin shortly. Do join us then, take care and goodbye!"
                )
                e["commentary"][-1]["comments"].append({
                    "key": "Text",
                    "value": comment
                })
            elif game["_id"] == "thirdplace":
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
                    e["commentary"][-1]["comments"].append({
                        "key": "Text",
                        "value": comment
                    })
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
                if temp_match["id"] in [str("r8_" + str(k)) for k in range(1, 9)]:
                    nextstage = "quarter-finals"
                elif temp_match["id"] in ["qf1", "qf2", "qf3", "qf4"]:
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
                e["commentary"][-1]["comments"].append({
                    "key": "Text",
                    "value": comment
                })
        else:
            team_name1 = Team(e["batting_team"]).abstract_name()
            team_name2 = Team(e["bowling_team"]).abstract_name()
            if e["declared"] is True:
                e["data"][-1][-1]["commentary"] += str(
                    " "
                    + team_name1
                    + " declare with "
                    + str(e["score"])
                    + " runs"
                )
                if e["wickets"] == 0:
                    e["data"][-1][-1]["commentary"] += " and no loss of wicket"
                elif e["wickets"] == 1:
                    e["data"][-1][-1]["commentary"] += " for the loss of 1 wicket"
                else:
                    e["data"][-1][-1]["commentary"] += str(
                        " for the loss of " 
                        + str(e["wickets"]) 
                        + " wickets"
                        )
                if e["balls"] == 0 or e["balls"] == 1:
                    e["data"][-1][-1]["commentary"] += "!"
                elif e["balls"] < 6:
                    e["data"][-1][-1]["commentary"] += str(
                        " after "
                        + str(e["balls"])
                        + " balls!"
                    )
                elif e["balls"] == 6:
                    e["data"][-1][-1]["commentary"] += str(
                        " after 1 over!"
                    )
                else:
                    e["data"][-1][-1]["commentary"] += str(
                        " after "
                        + str(len(e["data"]))
                        + " overs!"
                    )
            else:
                if e["score"] == 0:
                    e["data"][-1][-1]["commentary"] += str(
                        " "
                        + team_name1.upper()
                        + " ARE ALL OUT FOR NOUGHT!"
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
                        + " in "
                        + str(e["balls"])
                        + " balls."
                        )
            if i == 1:
                if session_ends[0] > -1:
                    e["commentary"][-1]["comments"].append({
                        "key": "Text",
                        "value": str(
                            team_name2
                            + " will bat next."
                        )
                    })
                    e["commentary"][-1]["comments"].append({
                        "key": "Text",
                        "value": str(
                            "That's all for today. Action continues tomorrow when "
                            + team_name2
                            + " come out to bat in the next innings on Day "
                            + str(session_ends[0] + 2)
                            + ". Do join us then, take care and goodbye!"
                        )
                    })
                else:
                    e["commentary"][-1]["comments"].append({
                        "key": "Text",
                        "value": str(
                            "Now, it's "
                            + team_name2
                            + " to bat next. Back in a bit for the next innings..."
                        )
                    })
            if i == 2:
                if follow_on:
                    e["commentary"][-1]["comments"].append({
                        "key": "Text",
                        "value": str(
                            team_name2
                            + " have the option of enforcing follow-on since they lead by "
                            + str(abs(game["innings"][0]["score"] - game["innings"][1]["score"]))
                            + " runs. THEY WILL ENFORCE FOLLOW-ON! This means that "
                            + team_name1
                            + " must bat again."
                        )
                    })
                elif game["innings"][0]["score"] == game["innings"][1]["score"]:
                    e["commentary"][-1]["comments"].append({
                        "key": "Text",
                        "value": str(
                            team_name2
                            + " must bat next since the scores are level."
                        )
                    })
                elif game["innings"][0]["score"] >= 200 + game["innings"][1]["score"]:
                    e["commentary"][-1]["comments"].append({
                        "key": "Text",
                        "value": str(
                            team_name2
                            + " have the option of enforcing follow-on since they lead by "
                            + str(abs(game["innings"][0]["score"] - game["innings"][1]["score"]))
                            + " runs. THEY HAVE OPTED TO NOT ENFORCE FOLLOW-ON! This means that "
                            + team_name2
                            + " will bat next."
                        )
                    })
                elif game["innings"][0]["score"] > game["innings"][1]["score"]:
                    lead_value = abs(game["innings"][0]["score"] - game["innings"][1]["score"])
                    e["commentary"][-1]["comments"].append({
                        "key": "Text",
                        "value": str(
                            team_name2
                            + " lead by "
                            + str(lead_value)
                            + " run"
                            + str("" if lead_value == 1 else "s")
                            + ". The minimum lead required to enforce follow-on is "
                            + str(game["follow_on_threshold"])
                            + " runs. This means that "
                            + team_name2
                            + " must bat next."
                        )
                    })
                else:
                    lead_value = abs(game["innings"][1]["score"] - game["innings"][0]["score"])
                    e["commentary"][-1]["comments"].append({
                        "key": "Text",
                        "value": str(
                            team_name2
                            + " must bat next since they trail by "
                            + str(lead_value)
                            + " run"
                            + str("." if lead_value == 1 else "s.")
                        )
                    })
                if session_ends[1] > -1:
                    e["commentary"][-1]["comments"].append({
                        "key": "Text",
                        "value": str(
                            "That's all for today. Action continues tomorrow when "
                            + str(team_name1 if follow_on else team_name2)
                            + " come out to bat in the next innings on Day "
                            + str(session_ends[1] + 2)
                            + ". Do join us then, take care and goodbye!"
                        )
                    })
                else:
                    e["commentary"][-1]["comments"][-1]["value"] += " Back in a bit for the next innings..."
            if i == 3:
                # There is a 4th innings and a corresponding target.
                if follow_on:
                    target = 1 + abs(
                        game["innings"][0]["score"]
                        - game["innings"][1]["score"]
                        - game["innings"][2]["score"]
                    )
                else:
                    target = 1 + abs(
                        game["innings"][1]["score"]
                        - game["innings"][0]["score"]
                        - game["innings"][2]["score"]
                    )
                e["commentary"][-1]["comments"].append({
                    "key": "Text",
                    "value": str(
                        "The equations have come out. "
                        + team_name2
                        + " need "
                        + str(target)
                        + " run"
                        + str("" if target == 1 else "s")
                        + " to win while "
                        + team_name1
                        + " need 10 wickets to win."
                    )
                })
                if session_ends[2] > -1:
                    e["commentary"][-1]["comments"][-1]["value"] += " We will be back tomorrow for the run chase..."
                else:
                    e["commentary"][-1]["comments"][-1]["value"] += " We will be back shortly for the run chase..."
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
