import random


team_prefix = "X"
team_id = "Team_" + team_prefix
team_name = "Team " + team_prefix

team_rating = 1840

def gen_name(l):
    vowel = "aeiou"
    consonant = "bcdfghjklmnpqrstvwxyz"
    all_alphabet = vowel + consonant
    initial = random.choice(all_alphabet).upper()
    name = ""
    vowel_flag = random.choice([0, 1])
    for i in range(l):
        if i % 2 == vowel_flag:
            name += random.choice(vowel)
        else:
            name += random.choice(consonant)
    output = initial + ". " + name.capitalize()
    return output


# List of team members
team_members = [
    {
        "_id": team_prefix + str(i),
        "name": gen_name(12),
        "bat_style": "any",
        "bowl_style": "any",
        "rating_bat": team_rating,
        "rating_bowl": team_rating,
        "rating_field": team_rating,
        "avatar": "images/misc/standard/X1.png",
        "avatar0": "images/misc/standard/X1.png",
        "face": "images/misc/standard/X3.png",
        "team": team_id,
        "captain": i == 1,
        "wicketkeeper": i == 6
    } for i in range(1, 12)
]

# Team details
team = {
    "_id": team_id,
    "name": team_name,
    "ai": False,
    "color": "#8EAB67",
    "rating": team_rating,
    "captain": team_prefix + "1",
    "kFactor": 40,
    "members": team_members,
    "dark_color": "#223311",
    "light_color": "#8EAB67",
    "flag": "images/misc/standard/X2.png",
    "player_prefix": team_prefix,
    "rating_glicko2": {
        "rating": team_rating,
        "rd": 80,
        "vol": 0.05
    }
}


def fetch_team_X():
    return team
