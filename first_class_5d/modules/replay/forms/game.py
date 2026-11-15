from django import forms
from modules.live.forms.fields.teamfield import TeamField


class Game(forms.Form):

    match_ID = forms.CharField()

    is_test = forms.ChoiceField(
        choices=[
            (True, True),
            (False, False)
        ]
    )

    is_final = forms.ChoiceField(
        choices=[
            (True, True),
            (False, False)
        ]
    )

    is_knockout = forms.ChoiceField(
        choices=[
            (True, True),
            (False, False)
        ]
    )

    overs = forms.IntegerField()

    wickets = forms.ChoiceField(
        choices=[
            (10, 10),
            (9, 9),
            (8, 8),
            (7, 7),
            (6, 6),
            (5, 5),
            (4, 4),
            (3, 3),
            (2, 2),
            (1, 1),
        ]
    )

    team_1 = TeamField()

    team_2 = TeamField()

    toss = forms.ChoiceField(
        choices=[
            (0, 0),
            (1, 1),
            (2, 2)
        ]
    )
