def bot_wicket_threshold(rating: int):
    if rating >= 2900:
        w_thresholds = {
            2899: 1,
            2900: 0.5
        }
    elif rating >= 2650:
        w_thresholds = {
            rating - 25: 1,
            rating: 0.5,
            2900: 0
        }
    elif rating <= 1000:
        w_thresholds = {
            1000: 1,
            1025: 0.2,
            2000: 0.1,
            2900: 0
        }
    elif rating >= 2200:
        w_thresholds = {
            rating - 300: 1,
            rating: 0.5,
            2650: 0.1,
            2900: 0
        }
    else:
        w_thresholds = {
            1000: 1,
            rating: 0.5,
            2900: 0
        }
    return w_thresholds


def load_bot_team(rating: int):

    # Team Classification
    team_id = "BOT" + str(rating)

    team_name = "BOT" + str(rating)
    # team_name = player_name_prefix + "s"
    player_name_prefix = team_name[:-1]
    # team_name = team_name[:8] + " " + str(rating)

    team_members = []
    for j in range(1, 12):
        team_members.append(
            {
                "_id": team_id + "_" + str(j),
                "name": player_name_prefix + " " + str(j),
                "ai": True,
                "bat_style": "any",
                "bowl_style": "any",
                "rating_bat": rating,
                "rating_bowl": rating,
                "rating_field": rating,
                "avatar": "images/default/abstract/bot.svg",
                "avatar0": "images/default/abstract/bot.svg",
                "face": "images/default/abstract/bot.svg",
                "team": team_id,
                "flight": (rating >= 2200),
                "captain": (j == 1),
                "wicketkeeper": (j == 6 or rating >= 2400),
                "w_threshold": bot_wicket_threshold(rating),
            }
        )

    # Team details
    team = {
        "_id": team_id,
        "name": team_name,
        "ai": True,
        "color": "#FF0000",
        "rating": rating,
        "captain": team_members[0]["_id"],
        "kFactor": 10,
        "members": team_members,
        "dark_color": "#220000",
        "light_color": "#FF7070",
        "flag": "images/default/abstract/bot.svg",
        "player_prefix": team_id + "_",
        "batting_orders": [3, 4, 4],
        "rating_glicko2": {
            "rating": rating,
            "rd": 0,
            "vol": 0.001
        }
    }

    return team

