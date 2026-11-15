import json
from random import choice, sample
from collections import defaultdict
from django.contrib.staticfiles import finders
from bin.models.team import Team, AbstractPlayer
from bin.mongoinserts.tournament_settings import TOURNAMENT_SETTINGS
from bin.mongodb import mongoclient


def prefix(team_id: str):
    return Team(team_id).prefix()


def default_lineup(team_id: str, ulimit: int=11, exclude: list=[]):
    # Returns the first 11 members regardless.
    # t_prefix = prefix(team_id)
    # return [t_prefix + str(i) for i in range(1, ulimit + 1)]
    lineup = Team(team_id).lineup()[:(ulimit + 1)]
    return [i for i in lineup if i not in exclude]


def lineup_to(team_id: str):
    try:
        live_match = mongoclient.live_db_get_collection(
            mongoclient.CURRENT_MATCH_DETAILS
        )
        live_details = live_match.find_one(0)
        return live_details["nominations"][team_id]["default"]
    except TypeError:
        default_nominations = Team(team_id).nominations()
        return default_nominations["default"]
    except KeyError:
        default_nominations = Team(team_id).nominations()
        return default_nominations["default"]


def keeper_lineup(team_id: str):
    permitted_players = lineup_to(team_id)
    try:
        lineup1 = Team(team_id).get("keeper_lineup")
        if lineup1 is None or len(lineup1) < 1:
            return [
                i["_id"]
                for i in Team(team_id).members()
                if i["wicketkeeper"] is True
                and i["_id"] in permitted_players
            ]
        return [i for i in lineup1 if i in permitted_players]
    except:
        return [
            i["_id"]
            for i in Team(team_id).members()
            if i["wicketkeeper"] is True
            and i["_id"] in permitted_players
        ]


def make_bowlers(b_lineup: list, overs: int, mandatory_bowler=None, mandatory_by=1):
    if overs <= len(b_lineup):
        return sample(b_lineup, overs)
    if len(b_lineup) < 5:
        raise Exception("Insufficient number of bowlers.")
    if len(b_lineup) == 5:
        return b_lineup
    new_lineup = []
    o_limit = overs // 5
    bowl_overs = defaultdict(int)
    previous_bowler = None
    for o_ite in range(overs):
        # do while
        current_bowler = choice([i for i in b_lineup if i != previous_bowler])
        if (
            o_ite < mandatory_by
            and mandatory_bowler is not None 
            and mandatory_bowler in b_lineup
            and mandatory_bowler != previous_bowler
        ):
            if o_ite + 1 == mandatory_by:
                current_bowler = mandatory_bowler
            elif choice([0, 1]) == 1:
                current_bowler = mandatory_bowler
        new_lineup.append(current_bowler)
        bowl_overs[current_bowler] += 1
        if bowl_overs[current_bowler] >= o_limit:
            b_lineup.remove(current_bowler)
        previous_bowler = current_bowler
    return new_lineup


def make_test_bowlers(b_lineup: list, mandatory_bowler=None, mandatory_by=1):
    new_lineup = []
    if len(b_lineup) < 2:
        raise Exception("Insufficient bowlers. At least two required.")
    current_bowler = None
    previous_bowler = None
    first_bowler = None
    for o_ite in range(500):
        # do while
        current_bowler = choice([i for i in b_lineup if i != previous_bowler])
        if (
            o_ite < mandatory_by
            and mandatory_bowler is not None 
            and mandatory_bowler in b_lineup
            and mandatory_bowler != previous_bowler
        ):
            if o_ite + 1 == mandatory_by:
                current_bowler = mandatory_bowler
            elif choice([0, 1]) == 1:
                current_bowler = mandatory_bowler
        if previous_bowler is None:
            first_bowler = current_bowler
        new_lineup.append(current_bowler)
        previous_bowler = current_bowler
    if current_bowler == first_bowler:
        current_bowler = choice([i for i in b_lineup if i != previous_bowler and i != first_bowler])
        new_lineup.append(current_bowler)
    return new_lineup


def make_waveform_bowlers(b_lineup: list, start_bowler_rating=1000):
    current_order = b_lineup[:-1] + list(reversed(b_lineup[1:]))
    start_index = None
    n = min(len(b_lineup), 11)
    b_ratings = [{"index": i, "rating": AbstractPlayer(b_lineup[i]).get("rating_bowl")} for i in range(n)]
    for i in sorted(b_ratings, key=lambda x: x["rating"], reverse=True):
        if i["rating"] <= start_bowler_rating and start_index is None:
            start_index = i["index"]
    if start_index is None:
        start_index = 0
    if start_index == 0:
        return current_order
    return current_order[start_index:] + current_order[:start_index]


def make_progressive_bowlers(b_lineup: list, n_overs=30, test=False, start_bowler_rating=1000):
    if n_overs < 20:
        return make_waveform_bowlers(b_lineup, start_bowler_rating)
    n = min(len(b_lineup), 11)
    if len(b_lineup) < 2:
        raise Exception("Insufficient bowlers. At least two required.")
    total_steps = round(((n_overs - 1) * 5 + 50) / 9)
    steps_per_strength_level = total_steps / (n - 1)
    sequence_indices = [1]
    current_index = 1
    next_level_step = steps_per_strength_level
    for current_step in range(1, total_steps):
        if current_step >= round(next_level_step):
            current_index += 1
            if current_index > n:
                current_index = n
            next_level_step += steps_per_strength_level
        else:
            if current_index > 1:
                sequence_indices.append(current_index - 1)
                sequence_indices.append(current_index)
        if sequence_indices[-1] != current_index:
            sequence_indices.append(current_index)
    new_lineup = [b_lineup[i - 1] for i in sequence_indices][:n_overs]
    if len(new_lineup) > 2:
        if new_lineup[-3] == b_lineup[-2]:
            new_lineup[-2] = b_lineup[-1]
            new_lineup[-1] = b_lineup[-2]
        else:
            new_lineup[-2] = b_lineup[-2]
            new_lineup[-1] = b_lineup[-1]
    if start_bowler_rating <= AbstractPlayer(b_lineup[0]).get("rating_bowl"):
        return new_lineup
    start_index = None
    b_ratings = [{"index": i, "rating": AbstractPlayer(b_lineup[i]).get("rating_bowl")} for i in range(n)]
    for i in sorted(b_ratings, key=lambda x: x["rating"], reverse=True):
        if i["rating"] <= start_bowler_rating and start_index is None:
            start_index = i["index"]
    if start_index is None:
        start_index = n - 1
    if new_lineup[-1] == b_lineup[-1]:
        new_lineup += [b_lineup[-2]] + list(reversed(new_lineup))
    else:
        new_lineup += [b_lineup[-1]] + list(reversed(new_lineup))
    if new_lineup[-1] == b_lineup[0]:
        new_lineup += [b_lineup[1]]
    else:
        new_lineup += [b_lineup[0]]
    try:
        new_lineup_index = new_lineup.index(b_lineup[start_index])
    except ValueError:
        new_lineup_index = 0
    if test:
        new_lineup += new_lineup
        new_lineup = new_lineup[new_lineup_index:] + new_lineup[:new_lineup_index]
    else:
        new_lineup = new_lineup[new_lineup_index:new_lineup_index+n_overs]
    return new_lineup

def change_lineup(bowl_team, bat_team):
    # Bowling lineup location
    base = str(finders.searched_locations[0])
    location = base + "/temp/live/bowlers_"
    location += str(bowl_team) + ".json"
    f = open(location, "w+")
    # Bowling lineup
    permitted_field = lineup_to(bowl_team)
    bowling_lineup = Team(bowl_team).bowling_lineup(nominees=permitted_field)
    bowling_order = []
    if bowling_lineup["selection"] == "fixed":
        bowling_order = [] + bowling_lineup["bowlers"]
    elif bowling_lineup["selection"] == "waveform":
        bowling_order = [] + make_waveform_bowlers(
            bowling_lineup["bowlers"],
            Team(bat_team).aggression_rating()
        )
    elif bowling_lineup["selection"] == "progressive":
        bowling_order = [] + make_progressive_bowlers(
            bowling_lineup["bowlers"],
            TOURNAMENT_SETTINGS.get("overs", 30),
            bool(TOURNAMENT_SETTINGS.get("overs") is None),
            Team(bat_team).aggression_rating()
        )
    elif bowling_lineup["selection"] == "random":
        if TOURNAMENT_SETTINGS.get("overs") is not None:
            bowling_order = [] + make_bowlers(
                bowling_lineup["bowlers"],
                TOURNAMENT_SETTINGS.get("overs")
                )
        else:
            bowling_order = [] + make_test_bowlers(bowling_lineup["bowlers"])
    json.dump(bowling_order, f)
    f.close()
    try:
        f = open(location, "r")
        bowling_order = json.load(f)
        f.close()
    except json.JSONDecodeError:
        pass


def fetch_lineup(bat_team, bowl_team):
    # Usually no change in batting lineup
    batting_order = lineup_to(bat_team)
    # Bowling lineup location
    base = str(finders.searched_locations[0])
    location = base + "/temp/live/bowlers_"
    location += str(bowl_team) + ".json"
    permitted_field = lineup_to(bowl_team)
    try:
        f = open(location, "r")
        f.close()
    except FileNotFoundError:
        # Bowling lineup
        bowling_lineup = Team(bowl_team).bowling_lineup(nominees=permitted_field)
        bowling_order = []
        if bowling_lineup["selection"] == "fixed":
            bowling_order = [] + bowling_lineup["bowlers"]
        elif bowling_lineup["selection"] == "waveform":
            bowling_order = [] + make_waveform_bowlers(
                bowling_lineup["bowlers"],
                Team(bat_team).aggression_rating()
            )
        elif bowling_lineup["selection"] == "progressive":
            bowling_order = [] + make_progressive_bowlers(
                bowling_lineup["bowlers"],
                TOURNAMENT_SETTINGS.get("overs", 30),
                bool(TOURNAMENT_SETTINGS.get("overs") is None),
                Team(bat_team).aggression_rating()
            )
        elif bowling_lineup["selection"] == "random":
            if TOURNAMENT_SETTINGS.get("overs") is not None:
                bowling_order = [] + make_bowlers(
                    bowling_lineup["bowlers"],
                    TOURNAMENT_SETTINGS.get("overs")
                    )
            else:
                bowling_order = [] + make_test_bowlers(bowling_lineup["bowlers"])
        f = open(location, "w+")
        json.dump(bowling_order, f)
        f.close()
    # Fielding order
    if True:
        fielding_order = Team(bowl_team).fielding_lineup(nominees=permitted_field)
        try:
            keeper = choice(keeper_lineup(bowl_team))
        except:
            keeper = prefix(bowl_team) + "6"
    # For a dynamic bowling order
    if True:
        try:
            f = open(location, "r")
            f.close()
        except FileNotFoundError:
            f = open(location, "w+")
            json.dump(bowling_order, f)
            f.close()
        try:
            f = open(location, "r")
            bowling_order = json.load(f)
            f.close()
        except json.JSONDecodeError:
            pass
    return batting_order, bowling_order, fielding_order, keeper


def fetch_opening_bowler(bowl_team, bat_team=None):
    if bat_team is None:
        bat_team = bowl_team
    _, b, _, _ = fetch_lineup(bat_team, bowl_team)
    return b[0]
