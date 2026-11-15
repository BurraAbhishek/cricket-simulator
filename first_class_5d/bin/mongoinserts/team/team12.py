import random


team_prefix = "Y"
team_id = "Team_" + team_prefix
team_name = "Team " + team_prefix

team_rating = 1840

def gen_name(l, threshold=2, mode=0):
    vowel = "aeiou"
    consonant = "bcdfghjklmnpqrstvwxyz"
    all_alphabet = vowel + consonant
    if mode == 1:
        initial = random.choice(all_alphabet).upper()
    elif mode == 2:
        initial = gen_name(random.randint(4, 12), threshold)
    hard_next_choices = {}
    for i in all_alphabet:
        if i in vowel:
            hard_next_choices[i] = consonant
        else:
            hard_next_choices[i] = vowel
    next_choices = {
        "a": all_alphabet,
        "e": all_alphabet,
        "i": "abcdefghjklmnopqrstvwxyz",
        "o": all_alphabet,
        "u": "abcdefghijklmnopqrstvwxyz",
        "b": "aehiouy",
        "c": "aehiou",
        "d": "aeiouy",
        "f": "aeiou",
        "g": "aehiou",
        "h": "aeiouy",
        "j": "aeiou",
        "k": "aeiouy",
        "l": "adehiopstuy",
        "m": "aeiouy",
        "n": "abcdefiosuvy",
        "p": "aehiouy",
        "q": "aeiou",
        "r": "aehiou",
        "s": "aehilotuy",
        "t": "aehiou",
        "v": "aeiou",
        "w": "aeiou",
        "x": "aeiou",
        "y": "abcdeilortu",
        "z": "aeiou"
    }
    name = random.choice(all_alphabet)
    vowel_flag = 0
    consonant_flag = 0
    if name in vowel:
        vowel_flag += 1
    else:
        consonant_flag += 1
    if threshold < 1:
        threshold = 1
    for i in range(l - 1):
        if vowel_flag >= threshold or consonant_flag >= threshold:
            chosen_alphabet = random.choice(hard_next_choices[name[-1]])
            vowel_flag = 0
            consonant_flag = 0
        else:
            chosen_alphabet = random.choice(next_choices[name[-1]])
        if chosen_alphabet in vowel:
            vowel_flag += 1
        else:
            consonant_flag += 1
        name += chosen_alphabet
    if mode == 1:
        output = initial + ". " + name.capitalize()
    elif mode == 2:
        output = initial + " " + name.capitalize()
    else:
        output = name.capitalize()
    return output


# A name in franchise tournament. E.g. Titled <Suffix> for <Thene> <Suffix>
# team_name = gen_name(random.randint(6, 8)) + " Strikers"

# List of team members
team_members = [
    {
        "_id": team_prefix + str(i),
        "name": gen_name(random.randint(4, 12), mode=2),
        "bat_style": "any",
        "bowl_style": "any",
        "rating_bat": team_rating,
        "rating_bowl": team_rating,
        "rating_field": team_rating,
        "avatar": "images/misc/standard/Y1.png",
        "avatar0": "images/misc/standard/Y1.png",
        "face": "images/misc/standard/Y3.png",
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
    "color": "#AABBCC",
    "rating": team_rating,
    "captain": team_prefix + "1",
    "kFactor": 40,
    "members": team_members,
    "dark_color": "#2F4F4F",
    "light_color": "#AABBCC",
    "flag": "images/misc/standard/Y2.png",
    "player_prefix": team_prefix,
    "rating_glicko2": {
        "rating": team_rating,
        "rd": 80,
        "vol": 0.05
    }
}


def fetch_team_Y():
    return team
