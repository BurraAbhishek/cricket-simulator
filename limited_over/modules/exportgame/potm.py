from modules.index.match_toppers import get_inning_toppers_bat, get_inning_toppers_bowl


def get_potm(game: dict):
    # limited overs
    # Edge cases: 3 all out, 4/0. Bowler should get
    # Edge case: Econ. rate vs. strike rate in above case.
    cutoff_multiplier = 1.5
    # if team batting first won
    if game["winner"] == game["team1"]:
        bat_score = game["innings"][0]["score"]
        bat_balls = game["innings"][0]["balls"]
        bat_toppers = get_inning_toppers_bat(game, 0)
        bowl_toppers = get_inning_toppers_bowl(game, 1)
        if bat_score >= bat_balls * cutoff_multiplier:
            return bat_toppers[0]["_id"]
        elif bowl_toppers[0]["wickets"] < 1 and bat_toppers[0]["runs"] >= 50:
            return bat_toppers[0]["_id"]
        else:
            return bowl_toppers[0]["_id"]
    elif game["winner"] == game["team2"]:
        bat_score = game["innings"][1]["score"]
        bat_balls = game["innings"][1]["balls"]
        total_overs = game.get("overs", bat_balls)
        expected_bat_score = game["target"]
        bat_toppers = get_inning_toppers_bat(game, 1)
        bowl_toppers = get_inning_toppers_bowl(game, 0)
        condition1 = bool(expected_bat_score >= bat_balls * cutoff_multiplier)
        condition2 = bool(bat_score >= 6 * total_overs)
        condition3 = bool(bowl_toppers[0].economy() > 6 * cutoff_multiplier)
        if condition1 and (condition2 or condition3):
            return bat_toppers[0]["_id"]
        elif bowl_toppers[0]["wickets"] < 1 and bat_toppers[0]["runs"] >= 50:
            return bat_toppers[0]["_id"]
        else:
            return bowl_toppers[0]["_id"]
    elif game["winner"] == "" and game["margin"] == "Match Tied":
        bat_score = game["innings"][0]["score"]
        bat_toppers = []
        bat_toppers += get_inning_toppers_bat(game, 0)
        bat_toppers += get_inning_toppers_bat(game, 1)
        bat_toppers.sort(key=lambda x: 0 if not x.dismissed else 1)
        bat_toppers.sort(key=lambda x: x.balls)
        bat_toppers.sort(key=lambda x: x.runs, reverse=True)
        bat_shortlist = bat_toppers[0]
        bowl_toppers = []
        bowl_toppers += get_inning_toppers_bowl(game, 0)
        bowl_toppers += get_inning_toppers_bowl(game, 1)
        bowl_toppers.sort(key=lambda x: 0 if x.balls > 0 else 1)
        bowl_toppers.sort(key=lambda x: x.runs / (1 + x.balls))
        bowl_toppers.sort(key=lambda x: x.economy())
        bowl_toppers.sort(key=lambda x: x.wickets, reverse=True)
        bowl_shortlist = bowl_toppers[0]
        if bat_shortlist.team().id() == game["team1"]:
            bat_balls = game["innings"][0]["balls"]
        elif bat_shortlist.team().id() == game["team2"]:
            bat_balls = game["innings"][1]["balls"]
        else:
            # Default
            bat_balls = 20
        total_overs = game.get("overs", bat_balls)
        condition0 = bool(
            bat_shortlist.runs > 0 
            or bat_shortlist.balls > 0
            or bowl_shortlist.wickets > 0
            or bowl_shortlist.balls > 0
        )
        if not condition0:
            # Award forfeiture
            return ""
        condition1 = bool(bat_shortlist.strike_rate() > 100 * cutoff_multiplier)
        condition2 = bool(bat_score >= 6 * total_overs)
        condition3 = bool(bowl_shortlist.economy() > 6 * cutoff_multiplier)
        if condition1 and (condition2 or condition3):
            return bat_shortlist["_id"]
        elif bowl_shortlist.wickets < 1 and bat_shortlist.runs >= 50:
            return bat_shortlist["_id"]
        else:
            return bowl_shortlist["_id"]
    return ""
