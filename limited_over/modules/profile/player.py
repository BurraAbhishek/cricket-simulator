from django.shortcuts import render
from django.http import HttpResponseNotFound
from bin.models.team import Team, TeamCollection
from bin.mongoinserts.load_games import TOURNAMENT_GAMES, translate_ko_id
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS


def get_member(request, id: str):
    team_collection = TeamCollection()
    playermap = team_collection.fetch_player_map(id)
    if playermap is None:
        return HttpResponseNotFound("Team Member unavailable")
    team_id: str = playermap.get("team_id")
    team: Team = team_collection.get(team_id)
    if team is None:
        return HttpResponseNotFound("Team Member unavailable")
    member = team.find_one(id)
    bat_stat, bowl_stat = get_stat(team_id, member.as_dict())
    return render(
        request,
        "member.html",
        {
            "player_id": member.id(),
            "player_name": member.name(),
            "player_avatar": member.avatar(),
            "player_team": team.get("name"),
            "player_team_id": team_id,
            "batting_rating": member.get("rating_bat"),
            "bowling_rating": member.get("rating_bowl"),
            "fielding_rating": member.get("rating_field"),
            "player_title": member.rating_title(),
            "player_description": member.get("description"),
            "extended_player_description": member.get("extended_description"),
            "bat": bat_stat,
            "bowl": bowl_stat
        }
    )


def get_stat(team, player):
    groupstage_matches_raw = [] + TOURNAMENT_GAMES["groupstage"]
    groupstage_matches_raw += TOURNAMENT_GAMES["knockout"]
    bat_stat = []
    bowl_stat = []
    for game in groupstage_matches_raw:
        if game["team1"] == team or game["team2"] == team:
            for i1, i2 in enumerate(game["innings"], start=1):
                if i1 == 1:
                    innings_position = "1st Innings"
                elif i1 == 2:
                    innings_position = "2nd Innings"
                else:
                    innings_position = ""
                if i2["batting_team"] == team:
                    bat_summary = {
                        "id": player["_id"],
                        "name": player["name"],
                        "opponent": i2["bowling_team"],
                        "opponent_name": Team(i2["bowling_team"]).get("name"),
                        "match": game["_id"],
                        "match_name": get_match_id(game["_id"]),
                        "match_link": get_match_link(game["_id"]),
                        "innings": i1,
                        "innings_position": innings_position,
                        "result_class": "",
                        "runs": 0,
                        "balls": 0,
                        "fours": 0,
                        "sixes": 0,
                        "strike_rate": 0,
                        "dismissed": False,
                        "batted": False
                    }
                    if game["winner"] == team:
                        bat_summary["result_class"] = "win"
                    elif game["winner"] == i2["bowling_team"]:
                        bat_summary["result_class"] = "loss"
                    elif game["winner"] == "" and game["margin"] == "Match Tied":
                        bat_summary["result_class"] = "tie"
                    elif game["margin"].lower() == "double forfeit":
                        bat_summary["result_class"] = "loss"
                    for batter in i2["batter_stats"]:
                        if batter["_id"] == player["_id"]:
                            strike_rate = 0
                            if batter["balls"] > 0:
                                strike_rate = 100 * batter["runs"] / batter["balls"]
                            bat_summary["runs"] = batter["runs"]
                            bat_summary["balls"] = batter["balls"]
                            try:
                                bat_summary["fours"] = batter["fours"]
                                bat_summary["sixes"] = batter["sixes"]
                            except KeyError:
                                bat_summary["fours"] = batter["scoring"][4]
                                bat_summary["sixes"] = batter["scoring"][6]
                            bat_summary["dismissed"] = batter["dismissed"]
                            bat_summary["strike_rate"] = strike_rate
                            bat_summary["batted"] = True
                    bat_stat.append(bat_summary)
                if i2["bowling_team"] == team:
                    bowl_summary = {
                        "id": player["_id"],
                        "name": player["name"],
                        "opponent": i2["batting_team"],
                        "opponent_name": Team(i2["batting_team"]).get("name"),
                        "match": game["_id"],
                        "match_name": get_match_id(game["_id"]),
                        "match_link": get_match_link(game["_id"]),
                        "innings": i1,
                        "innings_position": innings_position,
                        "result_class": "",
                        "overs": 0,
                        "balls": 0,
                        "dots": 0,
                        "maidens": 0,
                        "runs": 0,
                        "wickets": 0,
                        "economy": 0,
                        "bowled": False
                    }
                    if game["winner"] == team:
                        bowl_summary["result_class"] = "win"
                    elif game["winner"] == i2["batting_team"]:
                        bowl_summary["result_class"] = "loss"
                    elif game["winner"] == "" and game["margin"] == "Match Tied":
                        bowl_summary["result_class"] = "tie"
                    elif game["margin"].lower() == "double forfeit":
                        bowl_summary["result_class"] = "loss"
                    for bowler in i2["bowler_stats"]:
                        if bowler["_id"] == player["_id"]:
                            economy = 0
                            if bowler["balls"] > 0:
                                economy = 6 * bowler["runs"] / bowler["balls"]
                            bowl_summary["balls"] = bowler["balls"]
                            bowl_summary["overs"] = format_overs(bowler["balls"])
                            bowl_summary["dots"] = bowler["dots"]
                            bowl_summary["maidens"] = bowler["maidens"]
                            bowl_summary["runs"] = bowler["runs"]
                            bowl_summary["wickets"] = bowler["wickets"]
                            bowl_summary["economy"] = economy
                            bowl_summary["bowled"] = True
                    bowl_stat.append(bowl_summary)
    return bat_stat, bowl_stat


def get_match_id(match_id: str):
    if match_id[0] == "m":
        num_rounds = int(TOURNAMENT_SETTINGS.get("series_games", 0.5) * 2)
        num_games = len(TOURNAMENT_GAMES["groupstage"])
        k1 = int(match_id[1:])
        k = num_games // num_rounds
        round_number = str(((k1 - 1) // k) + 1)
        match_number = str(1 + ((k1 - 1) % k))
        return "Group Stage, Round " + round_number + ", Match " + match_number
    elif match_id[0] == "r":
        match_id_parts = match_id.split("_")
        match_number = match_id_parts[0][1:]
        return "Round of " + match_number
    else:
        return translate_ko_id(match_id)


def get_match_link(match_id: str):
    if match_id[0] == "m":
        return "/#groupstagematch-" + match_id
    if match_id == "final":
        if TOURNAMENT_SETTINGS.get("knockout") == 1:
            return "/#final-match"
        else:
            return "/#knockoutmatch-final"
    return "/#knockoutmatch-" + match_id


def format_overs(balls):
    if balls % 6 == 0:
        return str(balls // 6)
    else:
        return str(balls // 6) + "." + str(balls % 6)
