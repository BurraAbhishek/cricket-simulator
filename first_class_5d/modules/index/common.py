from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS


def get_innings_ordinals(game):
    names = []
    orders = {
        game["innings"][0]["batting_team"]: 0,
        game["innings"][0]["bowling_team"]: 0
    }
    for inning in game["innings"]:
        orders[inning["batting_team"]] += 1
        batting_team_inning_order = orders[inning["batting_team"]]
        if batting_team_inning_order == 1:
            names.append("1st Innings")
        elif batting_team_inning_order == 2:
            names.append("2nd Innings")
    return names


def render_score(score, wickets, declared=False, max_wickets=10):
    settings = {
        "format": TOURNAMENT_SETTINGS["scoring"].get(
            "format",
            "{score}/{wickets}{declaration}"
        ),
        "declaration": TOURNAMENT_SETTINGS["scoring"].get(
            "declaration",
            " dec"
        ),
        "show_last_wicket": TOURNAMENT_SETTINGS["scoring"].get(
            "show_last_wicket",
            ""
        )
    }
    if wickets >= max_wickets:
        settings["format"] = settings["format"].replace(
            "{wickets}",
            settings["show_last_wicket"]
        )
        settings["format"] = settings["format"].replace("/", "")
        settings["format"] = settings["format"].replace("-", "")
    declaration = ""
    if declared:
        declaration = settings["declaration"]
    return str(settings["format"]).format(
        score=score,
        wickets=wickets,
        declaration=declaration
        )
