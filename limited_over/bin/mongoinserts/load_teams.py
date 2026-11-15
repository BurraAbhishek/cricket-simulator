from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS
from bin.mongoinserts.cachebase import get_item
from bin.mongoinserts.team.bots import load_bot_team
from bin.mongoinserts.team.team9C import fetch_carl


def load_teams_from_scratch():
    teams = {
        "CARLBOT": fetch_carl(),
        "BOT2800": load_bot_team(2800),
    }
    return teams


def load_teams():
    x = get_item("teams")
    if x is not None:
        return x
    return load_teams_from_scratch()


TOURNAMENT_TEAMS = load_teams()
