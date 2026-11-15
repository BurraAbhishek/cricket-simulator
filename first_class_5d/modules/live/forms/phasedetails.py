from django import forms


class PhaseDetails(forms.Form):

    match_session_id = forms.IntegerField()

    start_inning = forms.IntegerField()

    end_inning = forms.IntegerField()

    start_ball = forms.CharField()

    end_ball = forms.CharField()

    capture_end = forms.BooleanField(required=False)
