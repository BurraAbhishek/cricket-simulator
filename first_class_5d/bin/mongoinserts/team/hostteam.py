from bin.mongoinserts.team.team9C import fetch_carl
from bin.mongoinserts.team.bots import load_bot_team

'''
Placeholder to put teams in index.html.
'''

HOST_TEAMS = {
    "CARLBOT": fetch_carl(),
    "BOT1000": load_bot_team(1000),
    "BOT1400": load_bot_team(1400),
    "BOT1500": load_bot_team(1500),
    "BOT1800": load_bot_team(1800),
    "BOT2000": load_bot_team(2000),
    "BOT2200": load_bot_team(2200),
    "BOT2300": load_bot_team(2300),
    "BOT2400": load_bot_team(2400),
    "BOT2500": load_bot_team(2500),
    "BOT2800": load_bot_team(2800)
}

def get_replacer_dict(teams):
    final_dict = {}
    for i in teams.keys():
        final_dict[i] = teams[i]["name"]
        members = HOST_TEAMS[i]["members"]
        for j in members:
            final_dict[j.get("_id")] = j.get("name")
    return final_dict

HOST_DICT = get_replacer_dict(HOST_TEAMS)

