team_prefix = "ADAMBOT_"
team_id = "ADAMBOT"
team_name = "Adaptive Scorers"
player_name_prefix = "Adaptive Scorer Bot "

team_rating = 1600

# Team Designations
team_designations = [
    team_name,
    "President of the " + team_name,
    "Vice President of the " + team_name,
    team_name + " Secretary of State",
    team_name + " Secretary of the Treasury",
    team_name + " Secretary of Defense",
    "Goalkeeper of the " + team_name,
    "Attorney-General of the " + team_name,
    team_name + " Secretary of Home Affairs",
    team_name + " Press Secretary",
    team_name + " Secretary of Operations",
    team_name + " Secretary of Training"
]

# List of team members
team_members = [
    {
        "_id": team_prefix + str(i),
        "name": player_name_prefix + str(i),
        "bat_style": "any",
        "bowl_style": "any",
        "rating_bat": team_rating,
        "rating_bowl": team_rating,
        "rating_field": team_rating,
        "avatar": "images/bot/full/botadam.png",
        "avatar0": "images/bot/full/botadam.png",
        "face": "images/bot/face/botadam.png",
        "team": team_id,
        "flight": False,
        "captain": i == 1,
        "wicketkeeper": i == 6,
        "description": team_designations[i]
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
    "flag": "images/bot/flag/botadam.png",
    "player_prefix": team_prefix,
    "batting_orders": [3, 4, 4],
    "rating_glicko2": {
        "rating": team_rating,
        "rd": 350,
        "vol": 0.05
    }
}


def fetch_adam():
    return team
