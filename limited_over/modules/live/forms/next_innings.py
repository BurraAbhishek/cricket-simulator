from django import forms
from modules.live.forms.fields.teamfield import TeamField


class NextInningsForm(forms.Form):

    is_chasing = forms.ChoiceField(
        choices=[
            (True, True),
            (False, False)
        ]
    )

    team_1 = TeamField()

    team_2 = TeamField()
