from bin.mongoinserts.load_games import TOURNAMENT_GAMES, translate_ko_id
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS


def get_all_games():
    # Only fetch completed games
    games = []
    games += TOURNAMENT_GAMES.get("knockout")
    for i in TOURNAMENT_GAMES.get("groupstage"):
        games += i
    return games


def max_groupstage():
    return len(TOURNAMENT_GAMES.get("groupstage")) * len(TOURNAMENT_GAMES.get("groupstage")[0])


def get_match_name(match_id: str):
    if match_id[0] == "m":
        match_id_components = match_id.split("_")
        round_number = str(int(match_id_components[1]))
        match_number = str(int(match_id_components[2]))
        return "Group Stage, Week " + round_number + ", Match " + match_number
    elif match_id[0] == "r":
        match_id_parts = match_id.split("_")
        match_number = match_id_parts[0][1:]
        return "Round of " + match_number
    else:
        return translate_ko_id(match_id)


def get_match_link(match_id: str):
    if match_id[0] == "m":
        return "/#groupstagematch-" + match_id
    if match_id == "final":
        if TOURNAMENT_SETTINGS.get("knockout") == 1:
            return "/#final-match"
        else:
            return "/#knockoutmatch-final"
    return "/#knockoutmatch-" + match_id


def innings_verbose(inning: int):
    if inning == 1 or inning == 2:
        return "1st Innings"
    if inning == 3 or inning == 4:
        return "2nd Innings"
    return ""
