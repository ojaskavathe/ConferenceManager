from django import forms
from django.contrib.auth.forms import UserCreationForm
from phonenumber_field.formfields import PhoneNumberField

from .models import User, Paper, Review

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(label = "Email")
    first_name = forms.CharField(label = "First name")
    last_name = forms.CharField(label = "Last name")
    phone = PhoneNumberField()

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone"]

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.email = self.cleaned_data["email"]
        user.phone = self.cleaned_data["phone"]
        if commit:
            user.save()
        return user

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