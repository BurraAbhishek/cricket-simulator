from modules.index.match_toppers import get_inning_toppers_bat, get_inning_toppers_bowl


def get_potm(game):
    # limited overs
    cutoff_multiplier = 1.5
    nbInnings = len(game["innings"])
    if nbInnings < 2:
        # Forfeit the award if no change of innings
        return ""
    # if team batting first won
    if game["winner"] == game["team1"]:
        bat_score = game["innings"][0]["score"]
        bat_balls = game["innings"][0]["balls"]
        bat_toppers = get_inning_toppers_bat(game, 0)
        bowl_toppers = get_inning_toppers_bowl(game, 1)
        if nbInnings > 2:
            if game["follow_on"] is True:
                bowl_toppers += get_inning_toppers_bowl(game, 2)
                bowl_toppers.sort(key=lambda x: 1 if x["balls"] <= 0 else 0)
                bowl_toppers.sort(key=lambda x: x["runs"] / (1 + x["balls"]))
                bowl_toppers.sort(key=lambda x: x["runs"] if x["balls"] <= 0 else x["runs"] / x["balls"])
                bowl_toppers.sort(key=lambda x: x["wickets"], reverse=True)
            else:
                bat_toppers += get_inning_toppers_bat(game, 2)
                bat_toppers.sort(key=lambda x: x["balls"])
                bat_toppers.sort(key=lambda x: x["runs"], reverse=True)
        if nbInnings > 3:
            if game["follow_on"] is True:
                bat_toppers += get_inning_toppers_bat(game, 3)
                bat_toppers.sort(key=lambda x: x["balls"])
                bat_toppers.sort(key=lambda x: x["runs"], reverse=True)
            else:
                bowl_toppers += get_inning_toppers_bowl(game, 3)
                bowl_toppers.sort(key=lambda x: 1 if x["balls"] <= 0 else 0)
                bowl_toppers.sort(key=lambda x: x["runs"] / (1 + x["balls"]))
                bowl_toppers.sort(key=lambda x: x["runs"] if x["balls"] <= 0 else x["runs"] / x["balls"])
                bowl_toppers.sort(key=lambda x: x["wickets"], reverse=True)
        if bat_score >= bat_balls * cutoff_multiplier:
            return bat_toppers[0]["_id"]
        elif bowl_toppers[0]["wickets"] < 1 and bat_toppers[0]["runs"] >= 50:
            return bat_toppers[0]["_id"]
        else:
            return bowl_toppers[0]["_id"]
    elif game["winner"] == game["team2"]:
        bat_score = game["innings"][1]["score"]
        bat_balls = game["innings"][1]["balls"]
        bat_toppers = get_inning_toppers_bat(game, 1)
        bowl_toppers = get_inning_toppers_bowl(game, 0)
        if nbInnings > 2:
            if game["follow_on"] is True:
                bat_toppers += get_inning_toppers_bat(game, 2)
                bat_toppers.sort(key=lambda x: x["balls"])
                bat_toppers.sort(key=lambda x: x["runs"], reverse=True)
            else:
                bowl_toppers += get_inning_toppers_bowl(game, 2)
                bowl_toppers.sort(key=lambda x: 1 if x["balls"] <= 0 else 0)
                bowl_toppers.sort(key=lambda x: x["runs"] / (1 + x["balls"]))
                bowl_toppers.sort(key=lambda x: x["runs"] if x["balls"] <= 0 else x["runs"] / x["balls"])
                bowl_toppers.sort(key=lambda x: x["wickets"], reverse=True)
        if nbInnings > 3:
            if game["follow_on"] is True:
                bowl_toppers += get_inning_toppers_bowl(game, 3)
                bowl_toppers.sort(key=lambda x: 1 if x["balls"] <= 0 else 0)
                bowl_toppers.sort(key=lambda x: x["runs"] / (1 + x["balls"]))
                bowl_toppers.sort(key=lambda x: x["runs"] if x["balls"] <= 0 else x["runs"] / x["balls"])
                bowl_toppers.sort(key=lambda x: x["wickets"], reverse=True)
            else:
                bat_toppers += get_inning_toppers_bat(game, 3)
                bat_toppers.sort(key=lambda x: x["balls"])
                bat_toppers.sort(key=lambda x: x["runs"], reverse=True)
        if bat_score >= bat_balls * cutoff_multiplier:
            return bat_toppers[0]["_id"]
        elif bowl_toppers[0]["wickets"] < 1 and bat_toppers[0]["runs"] >= 50:
            return bat_toppers[0]["_id"]
        else:
            return bowl_toppers[0]["_id"]
    else:
        bat_toppers = get_inning_toppers_bat(game, 0)
        bowl_toppers = get_inning_toppers_bowl(game, 0)
        if nbInnings > 1:
            bat_toppers += get_inning_toppers_bat(game, 1)
            bowl_toppers += get_inning_toppers_bowl(game, 1)
            if nbInnings > 2:
                bat_toppers += get_inning_toppers_bat(game, 2)
                bowl_toppers += get_inning_toppers_bowl(game, 2)
                if nbInnings > 3:
                    bat_toppers += get_inning_toppers_bat(game, 3)
                    bowl_toppers += get_inning_toppers_bowl(game, 3)
            bat_toppers.sort(key=lambda x: x["balls"])
            bat_toppers.sort(key=lambda x: x["runs"], reverse=True)
            bowl_toppers.sort(key=lambda x: 1 if x["balls"] <= 0 else 0)
            bowl_toppers.sort(key=lambda x: x["runs"] / (1 + x["balls"]))
            bowl_toppers.sort(key=lambda x: x["runs"] if x["balls"] <= 0 else x["runs"] / x["balls"])
            bowl_toppers.sort(key=lambda x: x["wickets"], reverse=True)
            condition0 = bool(
                bat_toppers[0]["runs"] > 0 
                or bat_toppers[0]["balls"] > 0
                or bowl_toppers[0]["wickets"] > 0
                or bowl_toppers[0]["balls"] > 0
            )
            if not condition0:
                # Award forfeiture
                return ""
        for i in game["innings"]:
            cutoff_score = bool((int(i["score"]) - (int(i["balls"]) * cutoff_multiplier)) >= 0)
            if cutoff_score:
                return bat_toppers[0]["_id"]
        if bowl_toppers[0]["wickets"] < 1 and bat_toppers[0]["runs"] >= 50:
            return bat_toppers[0]["_id"]
        return bowl_toppers[0]["_id"]
