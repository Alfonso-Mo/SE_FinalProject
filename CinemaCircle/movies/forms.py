from django import forms

from .models import Comment

SCORE_CHOICES = [(i, str(i)) for i in range(1, 11)]


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("body",)
        widgets = {
            "body": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Share your thoughts...",
                    "class": "comment-textarea",
                }
            ),
        }
        labels = {"body": ""}


class MovieScoresForm(forms.Form):
    rating = forms.TypedChoiceField(
        choices=SCORE_CHOICES,
        coerce=int,
        label="Your rating",
        widget=forms.Select(attrs={"class": "score-select"}),
    )
    worth_watching = forms.TypedChoiceField(
        choices=SCORE_CHOICES,
        coerce=int,
        label="Worth watching",
        widget=forms.Select(attrs={"class": "score-select"}),
    )
