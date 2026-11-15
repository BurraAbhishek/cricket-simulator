from django import forms
from bin.mongoinserts.load_teams import TOURNAMENT_TEAMS


class TeamField(forms.ChoiceField):

    def __init__(self) -> None:
            teams = TOURNAMENT_TEAMS.keys()
            choices = []
            for i in teams:
                choices.append(
                    (
                        TOURNAMENT_TEAMS.get(i)["_id"],
                        TOURNAMENT_TEAMS.get(i)["name"]
                    )
                )
            super().__init__(choices=choices)
