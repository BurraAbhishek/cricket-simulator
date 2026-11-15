from bin.mongoinserts.load_games import TOURNAMENT_GAMES, translate_ko_id
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS


def get_all_games():
    games = []
    games += TOURNAMENT_GAMES.get("knockout")
    games += TOURNAMENT_GAMES.get("groupstage")
    return games


def max_groupstage():
    return len(TOURNAMENT_GAMES.get("groupstage"))


def get_match_name(match_id: str):
    if match_id[0] == "m":
        num_rounds = int(TOURNAMENT_SETTINGS.get("series_games", 0.5) * 2)
        num_games = max_groupstage()
        k1 = int(match_id[1:])
        k = num_games // num_rounds
        round_number = str(((k1 - 1) // k) + 1)
        match_number = str(1 + ((k1 - 1) % k))
        return "Group Stage, Round " + round_number + ", Match " + match_number
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
    if inning == 1:
        return "1st Innings"
    if inning == 2:
        return "2nd Innings"
    return ""
