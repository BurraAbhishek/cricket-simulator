from django import forms
from bin.mongodb import mongoclient


class TeamField(forms.ChoiceField):

    def __init__(self) -> None:
            team = list(mongoclient.tournament_db_get_collection(
                mongoclient.TOURNAMENT_TEAMS
            ).find())
            choices = []
            for i in team:
                choices.append((i["_id"], i["name"]))
            super().__init__(choices=choices)
