def load_bye_team(order):
    team_id = "BYE" + str(order)
    team_name = "Bye " + str(order)
    rating = int(order)
    # Team details
    team = {
        "_id": team_id,
        "name": team_name,
        "ai": True,
        "bye": True,
        "color": "#FF0000",
        "rating": rating,
        "captain": None,
        "kFactor": 0,
        "members": [],
        "dark_color": "#220000",
        "light_color": "#FF7070",
        "flag": "images/default/byes/bye.svg",
        "player_prefix": team_id + "_",
        "rating_glicko2": {
            "rating": rating,
            "rd": 0,
            "vol": 0.001
        }
    }
    return team
