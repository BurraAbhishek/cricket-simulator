import random
from copy import deepcopy
from bin.models.team import Team
from bin.mongoinserts.load_games import max_groupstage_games, get_match_ids
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS
from bin.mongoinserts.load_teams import TOURNAMENT_TEAMS


TEST = False
BOT = True


TEAMS_ROSTER = list(TOURNAMENT_TEAMS.keys())
TEAMS_ROSTER.sort(key=lambda x: Team(x).init_rating(), reverse=True)
TEAMS = [i for i in TEAMS_ROSTER if not Team(i).ai()]
BOTS = [i for i in TEAMS_ROSTER if Team(i).ai()]


def next_pairing_iteration(pairings, start_index=2, max_games=0, toss_fixed=True):
    if max_games == 0:
        max_games = 2 * len(pairings)
    for i, e in enumerate(pairings, start=1):
        e["curr_round"] += start_index
        e["match_id"] = get_match_ids(i + int(len(pairings) * start_index / 2), max_games)
        if toss_fixed:
            e["toss"] = 0
    return pairings


def get_limited_over_pairings():
    pairings = []
    if TEST:
        return pairings
    n3 = max_groupstage_games()
    if BOT and TOURNAMENT_SETTINGS.get("bot_group", True):
        n1 = len(TEAMS)
        n2 = 2 * n1 * n1
        teams = list(TEAMS)
        bots = list(BOTS)
        match_ids = []
        for i in range(1, n2 + 1):
            match_ids.append(get_match_ids(i, n3))
        i = 0
        if len(teams) != len(bots):
            return pairings
        for _ in range(n1):
            for j in range(n1):
                winner = ""
                potm = ""
                if TOURNAMENT_SETTINGS["decision"] == 1:
                    pairings.append(
                        {
                            "curr_round": 1,
                            "round_matches": n1 * n1,
                            "match_id": match_ids[i],
                            "team1": teams[j],
                            "team2": bots[j],
                            "nom1": Team(teams[j]).nominations(),
                            "nom2": Team(bots[j]).nominations(),
                            "overs": TOURNAMENT_SETTINGS["overs"],
                            "toss": 0,
                            "winner": winner,
                            "potm": potm
                        }
                    )
                else:
                    pairings.append(
                        {
                            "curr_round": 1,
                            "round_matches": n1 * n1,
                            "match_id": match_ids[i],
                            "team1": bots[j],
                            "team2": teams[j],
                            "nom1": Team(bots[j]).nominations(),
                            "nom2": Team(teams[j]).nominations(),
                            "overs": TOURNAMENT_SETTINGS["overs"],
                            "toss": 0,
                            "winner": winner,
                            "potm": potm
                        }
                    )
                i += 1
            if TOURNAMENT_SETTINGS["bot_order"] == 1:
                team = teams.pop(0)
                teams = teams + [team]
            else:
                bot = bots.pop(0)
                bots = bots + [bot]
        for _ in range(n1):
            for j in range(n1):
                winner = ""
                potm = ""
                if TOURNAMENT_SETTINGS["decision"] == 2:
                    pairings.append(
                        {
                            "curr_round": 2,
                            "round_matches": n1 * n1,
                            "match_id": match_ids[i],
                            "team1": teams[j],
                            "team2": bots[j],
                            "nom1": Team(teams[j]).nominations(),
                            "nom2": Team(bots[j]).nominations(),
                            "overs": TOURNAMENT_SETTINGS["overs"],
                            "toss": 0,
                            "winner": winner,
                            "potm": potm
                        }
                    )
                else:
                    pairings.append(
                        {
                            "curr_round": 2,
                            "round_matches": n1 * n1,
                            "match_id": match_ids[i],
                            "team1": bots[j],
                            "team2": teams[j],
                            "nom1": Team(bots[j]).nominations(),
                            "nom2": Team(teams[j]).nominations(),
                            "overs": TOURNAMENT_SETTINGS["overs"],
                            "toss": 0,
                            "winner": winner,
                            "potm": potm
                        }
                    )
                i += 1
            if TOURNAMENT_SETTINGS["bot_order"] == 1:
                team = teams.pop(0)
                teams = teams + [team]
            else:
                bot = bots.pop(0)
                bots = bots + [bot]
    elif BOT:
        n1 = len(TEAMS) + len(BOTS)
        if n1 % 2 == 1:
            return pairings
        n2 = n1 * (n1 - 1)
        if TOURNAMENT_SETTINGS.get("bot_order") == 1:
            teams = list(TEAMS) + list(BOTS)
        else:
            bot_teams = [] + BOTS
            bot_teams.reverse()
            teams = list(TEAMS) + list(bot_teams)
        match_ids = []
        for i in range(1, n2 + 1):
            match_ids.append(get_match_ids(i, n3))
        op_pairing = []
        for _ in range(n1 - 1):
            for j in range(int(n1 / 2)):
                x = random.choice([1, 2])
                if x == 2:
                    op_pairing.append([teams[n1 - 1 - j], teams[j]])
                else:
                    op_pairing.append([teams[j], teams[n1 - 1 - j]])
            team2 = teams.pop()
            team1 = teams.pop(0)
            teams = [team1] + [team2] + teams
        for i, e in enumerate(op_pairing):
            toss = random.choice([1, 2])
            winner = ""
            potm = ""
            pairings.append(
                {
                    "curr_round": 1,
                    "round_matches": len(op_pairing),
                    "match_id": match_ids[i],
                    "team1": e[0],
                    "team2": e[1],
                    "nom1": Team(e[0]).nominations(),
                    "nom2": Team(e[1]).nominations(),
                    "overs": TOURNAMENT_SETTINGS["overs"],
                    "toss": toss,
                    "winner": winner,
                    "potm": potm
                }
            )
        for i, e in enumerate(op_pairing):
            winner = ""
            potm = ""
            pairings.append(
                {
                    "curr_round": 2,
                    "round_matches": len(op_pairing),
                    "match_id": match_ids[i + int(n2 / 2)],
                    "team1": e[1],
                    "team2": e[0],
                    "nom1": Team(e[1]).nominations(),
                    "nom2": Team(e[0]).nominations(),
                    "overs": TOURNAMENT_SETTINGS["overs"],
                    "toss": 0,
                    "winner": winner,
                    "potm": potm
                }
            )
    else:
        n1 = len(TEAMS)
        if n1 % 2 == 1:
            return pairings
        n2 = n1 * (n1 - 1)
        teams = list(TEAMS)
        match_ids = []
        for i in range(1, n2 + 1):
            match_ids.append(get_match_ids(i, n3))
        op_pairing = []
        for _ in range(n1 - 1):
            for j in range(int(n1 / 2)):
                x = random.choice([1, 2])
                if x == 2:
                    op_pairing.append([teams[n1 - 1 - j], teams[j]])
                else:
                    op_pairing.append([teams[j], teams[n1 - 1 - j]])
            team2 = teams.pop()
            team1 = teams.pop(0)
            teams = [team1] + [team2] + teams
        for i, e in enumerate(op_pairing):
            toss = random.choice([1, 2])
            winner = ""
            potm = ""
            pairings.append(
                {
                    "curr_round": 1,
                    "round_matches": len(op_pairing),
                    "match_id": match_ids[i],
                    "team1": e[0],
                    "team2": e[1],
                    "nom1": Team(e[0]).nominations(),
                    "nom2": Team(e[1]).nominations(),
                    "overs": TOURNAMENT_SETTINGS["overs"],
                    "toss": toss,
                    "winner": winner,
                    "potm": potm
                }
            )
        for i, e in enumerate(op_pairing):
            winner = ""
            potm = ""
            pairings.append(
                {
                    "curr_round": 2,
                    "round_matches": len(op_pairing),
                    "match_id": match_ids[i + int(n2 / 2)],
                    "team1": e[1],
                    "team2": e[0],
                    "nom1": Team(e[1]).nominations(),
                    "nom2": Team(e[0]).nominations(),
                    "overs": TOURNAMENT_SETTINGS["overs"],
                    "toss": 0,
                    "winner": winner,
                    "potm": potm
                }
            )
    # If round-robin is to repeat
    if TOURNAMENT_SETTINGS["series_games"] > 1:
        pairings_original = deepcopy(pairings)
        max_games = max_groupstage_games()
        for i in range(1, TOURNAMENT_SETTINGS["series_games"]):
            next_pairings = deepcopy(pairings_original)
            next_pairings = next_pairing_iteration(next_pairings, 2 * i, max_games)
            pairings += next_pairings
    # Knockout pairings
    return pairings
