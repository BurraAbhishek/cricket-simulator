from django import forms


class MidPhaseCommentary(forms.Form):

    match_session_id = forms.IntegerField()

    comment_type = forms.ChoiceField(
        choices=[
            ("Text", "Text"),
            ("Image", "Image")
        ]
    )

    comments = forms.CharField(widget=forms.Textarea, required=False)

    image_location = forms.CharField(required=False)
