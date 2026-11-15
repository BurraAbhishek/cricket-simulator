import random
from bin.models.team import Team
from bin.mongoinserts.load_games import get_match_ids, count_games_per_team
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS
from bin.mongoinserts.load_teams import TOURNAMENT_TEAMS


TEST = True
BOT = True


TEAMS_ROSTER = list(TOURNAMENT_TEAMS.keys())
TEAMS_ROSTER.sort(key=lambda x: Team(x).init_rating(), reverse=True)
TEAMS = [i for i in TEAMS_ROSTER if not Team(i).ai()]
BOTS = [i for i in TEAMS_ROSTER if Team(i).ai()]


def get_test_pairings():
    pairings = get_test_pairings_round()
    # If round-robin is to repeat
    start_week = 1
    num_weeks, _ = count_games_per_team()
    if TOURNAMENT_SETTINGS["series_games"] > 1:
        # Only valid for parody
        num_weeks = num_weeks / TOURNAMENT_SETTINGS["series_games"]
        for j in range(1, TOURNAMENT_SETTINGS["series_games"]):
            reverse = bool(j % 2 == 1)
            start_week += int(num_weeks)
            next_pairings = get_test_pairings_round(start_week, reverse)
            pairings += next_pairings
    return pairings


def get_test_pairings_round(start_week=1, reverse=False):
    pairings = []
    if BOT and TOURNAMENT_SETTINGS.get("bot_group", True):
        n1 = len(TEAMS)
        n2 = n1 * n1
        teams = list(TEAMS)
        bots = list(BOTS)
        match_ids = []
        for i in range(start_week, n1 + start_week):
            for j in range(1, n1 + 1):
                match_ids.append(get_match_ids(i, None, j))
        i = 0
        if len(teams) != len(bots):
            return pairings
        for _ in range(n1):
            for j in range(n1):
                toss = random.choice([1, 2])
                # custom toss, if any
                # end custom toss
                # winner and potm
                winner = ""
                potm = ""
                # end winner
                if toss == 1:
                    pairings.append(
                        {
                            "match_id": match_ids[i],
                            "team1": teams[j],
                            "team2": bots[j],
                            "nom1": Team(teams[j]).nominations(),
                            "nom2": Team(bots[j]).nominations(),
                            "toss": 1,
                            "winner": winner,
                            "potm": potm
                        }
                    )
                else:
                    pairings.append(
                        {
                            "match_id": match_ids[i],
                            "team1": bots[j],
                            "team2": teams[j],
                            "nom1": Team(bots[j]).nominations(),
                            "nom2": Team(teams[j]).nominations(),
                            "toss": 2,
                            "winner": winner,
                            "potm": potm
                        }
                    )
                i += 1
            bot = bots.pop(0)
            bots = bots + [bot]
    elif BOT:
        n1 = len(TEAMS) + len(BOTS)
        if n1 % 2 == 1:
            return pairings
        n2 = int(n1 // 2)
        if TOURNAMENT_SETTINGS.get("bot_order") == 1:
            teams = list(TEAMS) + list(BOTS)
        else:
            bot_teams = [] + BOTS
            bot_teams.reverse()
            teams = list(TEAMS) + list(bot_teams)
        match_ids = []
        for i in range(start_week, n1 + start_week):
            for j in range(1, n2 + 1):
                match_ids.append(get_match_ids(i, None, j))
        i = 0
        op_pairing = []
        first_round_pairing = []
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
        team2 = teams.pop()
        team1 = teams.pop(0)
        teams = [team1] + [team2] + teams
        for i, e in enumerate(op_pairing):
            toss = random.choice([1, 2])
            # insert teams that only prefer batting first
            # if both sides only prefer batting first, one is picked at random
            only_first_bat_teams = []
            winner = ""
            potm = ""
            if e[1] in only_first_bat_teams:
                toss = 1
            if reverse:
                pairings.append(
                    {
                        "match_id": match_ids[i],
                        "team1": e[1],
                        "team2": e[0],
                        "nom1": Team(e[1]).nominations(),
                        "nom2": Team(e[0]).nominations(),
                        "toss": (toss % 2) + 1,
                        "winner": winner,
                        "potm": potm
                    }
                )
            else:
                pairings.append(
                    {
                        "match_id": match_ids[i],
                        "team1": e[0],
                        "team2": e[1],
                        "nom1": Team(e[0]).nominations(),
                        "nom2": Team(e[1]).nominations(),
                        "toss": toss,
                        "winner": winner,
                        "potm": potm
                    }
                )
    else:
        n1 = len(TEAMS)
        if n1 % 2 == 1:
            return pairings
        n2 = int(n1 // 2)
        teams = list(TEAMS)
        match_ids = []
        for i in range(start_week, n1 + start_week):
            for j in range(1, n2 + 1):
                match_ids.append(get_match_ids(i, None, j))
        i = 0
        op_pairing = []
        first_round_pairing = []
        for _ in range(n1 - 2):
            for j in range(int(n1 / 2)):
                x = random.choice([1, 2])
                if x == 2:
                    op_pairing.append([teams[n1 - 1 - j], teams[j]])
                else:
                    op_pairing.append([teams[j], teams[n1 - 1 - j]])
            team2 = teams.pop()
            team1 = teams.pop(0)
            teams = [team1] + [team2] + teams
        for j in range(int(n1 / 2)):
            print(j, n1 - i - j)
            x = random.choice([1, 2])
            if x == 2:
                first_round_pairing.append([teams[n1 - 1 - j], teams[j]])
            else:
                first_round_pairing.append([teams[j], teams[n1 - 1 - j]])
        team2 = teams.pop()
        team1 = teams.pop(0)
        teams = [team1] + [team2] + teams
        op_pairing = [] + first_round_pairing + op_pairing
        for i, e in enumerate(op_pairing):
            toss = random.choice([1, 2])
            # insert teams that only prefer batting first
            # if both sides only prefer batting first, one is picked at random
            only_first_bat_teams = []
            winner = ""
            potm = ""
            if e[1] in only_first_bat_teams:
                toss = 1
            pairings.append(
                {
                    "match_id": match_ids[i],
                    "team1": e[0],
                    "team2": e[1],
                    "nom1": Team(e[0]).nominations(),
                    "nom2": Team(e[1]).nominations(),
                    "toss": toss,
                    "winner": winner,
                    "potm": potm
                }
            )
    return pairings
