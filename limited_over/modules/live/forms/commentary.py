from django import forms


class MidCommentary(forms.Form):

    innings = forms.IntegerField(label="Innings (starting from 0)", min_value=0)

    ball_id = forms.CharField()

    comment_type = forms.ChoiceField(
        choices=[
            ("Text", "Text"),
            ("Image", "Image")
        ]
    )

    comments = forms.CharField(widget=forms.Textarea, required=False)

    image_location = forms.CharField(required=False)
