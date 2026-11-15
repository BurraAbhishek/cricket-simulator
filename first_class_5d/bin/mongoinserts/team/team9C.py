# Reverse-Lineup Bots

def carl_w_threshold(one_index, rating=2000):
    revl_mean14 = 0.008
    revl_mean24 = 0.006
    revl_sd_level = 2
    b_w_threshold14 = revl_mean14 * (one_index ** revl_sd_level)
    b_w_threshold25 = revl_mean24 * (one_index ** revl_sd_level)
    b_w_threshold27 = min(0.1, b_w_threshold25)
    if rating >= 2850:
        return {
            1000: 1,
            2650: b_w_threshold14,
            rating: b_w_threshold27,
            rating + 50: 0
        }
    if rating >= 2650:
        return {
            1000: 1,
            2400: b_w_threshold14,
            2650: 0.5,
            rating + 50: b_w_threshold27,
            2900: 0
        }
    if rating >= 2400:
        return {
            1000: 1,
            2400: b_w_threshold14,
            rating: b_w_threshold25,
            2650: b_w_threshold27,
            2900: 0
        }
    if rating <= 1025:
        return {
            1000: 1,
            1025: b_w_threshold14,
            1050: b_w_threshold27,
            2900: 0
        }
    return {
        1000: 1,
        1025: b_w_threshold14,
        rating: b_w_threshold27,
        2900: 0
    }


team_prefix = "CARLBOT_"
team_id = "CARLBOT"
team_name = "Reversed Lineup Bots"
team_name_prefix = "Reverse-Lineup Bot "

bat_ratings = [950, 1100, 1550, 1800, 2000, 2100, 2250, 2450, 2550, 2600, 2650]
bowl_ratings = [1025, 1100, 1550, 1800, 2000, 2100, 2250, 2450, 2550, 2600, 2625]
field_ratings = [875, 1100, 1550, 1800, 2000, 2100, 2250, 2450, 2550, 2600, 2675]
team_rating = 2550


# List of team members
team_members = [
    {
        "_id": team_prefix + str(i),
        "name": team_name_prefix + str(i),
        "bat_style": "any",
        "bowl_style": "any",
        "rating_bat": bat_ratings[i - 1],
        "rating_bowl": bowl_ratings[i - 1],
        "rating_field": field_ratings[i - 1],
        "avatar": "images/default/abstract/bot.svg",
        "avatar0": "images/default/abstract/bot.svg",
        "face": "images/default/abstract/bot.svg",
        "team": team_id,
        "bowl": True,
        "field": field_ratings[i - 1] >= 2000,
        "flight": bat_ratings[i - 1] >= 2500,
        "captain": i == 1,
        "wicketkeeper": i >= 6,
        "w_threshold": carl_w_threshold(i, bat_ratings[i - 1]),
    } for i in range(1, 12)
]

# Team details
team = {
    "_id": team_id,
    "name": team_name,
    "ai": True,
    "color": "#FF0000",
    "rating": team_rating,
    "captain": team_prefix + "1",
    "kFactor": 40,
    "members": team_members,
    "dark_color": "#220000",
    "light_color": "#FF4444",
    "flag": "images/default/abstract/bot.svg",
    "player_prefix": team_prefix,
    "batting_orders": [4, 4, 3],
    "bowling_orders": {
        "selection": "waveform",
        "bowlers": []
    },
    "rating_glicko2": {
        "rating": team_rating,
        "rd": 80,
        "vol": 0.05
    }
}


def fetch_carl():
    return team
