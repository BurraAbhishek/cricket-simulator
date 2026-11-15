from django import forms
from modules.live.forms.fields.playerfield import OptionalGamePlayerField


class Innings(forms.Form):

    legal_delivery = forms.ChoiceField(
        choices=[
            (True, True),
            (False, False)
        ]
    )

    bowler = OptionalGamePlayerField(2)

    batter = OptionalGamePlayerField(1)

    nonstriker = OptionalGamePlayerField(1)

    score = forms.ChoiceField(
        choices=[
            (0, 0),
            (1, 1),
            (2, 2),
            (3, 3),
            (4, 4),
            (5, 5),
            (6, 6)
        ],
        label="Runs credited to batter",
    )

    is_batter_out = forms.ChoiceField(
        choices=[
            (False, False),
            (True, True)
        ]
    )

    dismissed_batter = OptionalGamePlayerField(1)

    dismissal = forms.ChoiceField(
        choices=[
            ("", "Not out"),
            ("b", "Bowled"),
            ("c", "Caught"),
            ("lbw", "Leg before wicket"),
            ("st", "Stumped"),
            ("runout", "Run out"),
            ("hitwicket", "Hit Wicket"),
            ("timeout", "Timed out"),
            ("retired", "Retired out"),
            ("hittheballtwice", "Hit the ball twice"),
            ("obstructing", "Obstructing the field")
        ],
        required=False
    )

    fielder = OptionalGamePlayerField(2)

    commentary = forms.CharField(widget=forms.Textarea, required=False)

    wide = forms.ChoiceField(
        choices=[
            (0, "Not a wide"),
            (1, "wide"),
            (2, "2 wides"),
            (3, "3 wides"),
            (4, "4 wides"),
            (5, "wide boundary")
        ]
    )

    no_ball = forms.ChoiceField(
        choices=[
            (0, "Not a no ball"),
            (1, "No ball")
        ]
    )

    bye = forms.ChoiceField(
        choices=[
            (0, "Not a bye"),
            (1, "bye"),
            (2, "2 byes"),
            (3, "3 byes"),
            (4, "4 byes")
        ]
    )

    leg_bye = forms.ChoiceField(
        choices=[
            (0, "Not a leg bye"),
            (1, "leg bye"),
            (2, "2 leg byes"),
            (3, "3 leg byes"),
            (4, "4 leg byes")
        ]
    )

    penalty = forms.ChoiceField(
        choices=[
            (0, 0),
            (5, 5)
        ],
        label="Penalty runs awarded to batting side"
    )