from django import forms


class MidCommentary(forms.Form):

    innings = forms.IntegerField()

    ball_id = forms.CharField()

    comment_type = forms.ChoiceField(
        choices=[
            ("Text", "Text"),
            ("Image", "Image")
        ]
    )

    comments = forms.CharField(widget=forms.Textarea, required=False)

    image_location = forms.CharField(required=False)
