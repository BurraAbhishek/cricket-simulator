import json
from django import forms
from bin.models.team import Team
from bin.mongoinserts.load_games import TOURNAMENT_GAMES
from modules.stat.all_games import get_match_name


def get_all_game_ids():
    games = []
    for i in TOURNAMENT_GAMES.get("groupstage"):
        games.append({
            "clas": "groupstage",
            "id": i["_id"],
            "team1": i["team1"],
            "team2": i["team2"]
        })
    for i in TOURNAMENT_GAMES.get("knockout"):
        games.append({
            "clas": "knockout",
            "id": i["_id"],
            "team1": i["team1"],
            "team2": i["team2"]
        })
    return games


def get_verbose_match_name(match_id, team1, team2):
    s = get_match_name(match_id)
    s += ", "
    s += Team(team1).name()
    s += " vs. "
    s += Team(team2).name()
    return s


def fc(e):
    return get_verbose_match_name(e["id"], e["team1"], e["team2"])


class GameSelection(forms.Form):

    games = forms.MultipleChoiceField(
        choices=[(json.dumps(i), fc(i)) for i in get_all_game_ids()]
    )
