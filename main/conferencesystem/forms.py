from django import forms
from django.contrib.auth.models import User
from .models import Paper, Review


class PaperSubmissionForm(forms.ModelForm):
    authors = forms.ModelMultipleChoiceField(queryset=User.objects.all(), required=False)
    class Meta:
        model = Paper
        fields = ['title', 'abstract', 'file', 'track', 'authors']
    
    def __init__(self, conference, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.conference = conference
        self.fields['track'].queryset = self.conference.track_set.all()

    def clean(self):
        cleaned_data = super().clean()
        track = cleaned_data.get('track')

        if track and track.conference != self.conference:
            self.add_error('track', "Invalid track selected.")

        return cleaned_data

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['score', 'comments']