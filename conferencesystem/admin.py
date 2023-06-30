from django import forms
from django.contrib import admin
from django.contrib.auth.models import User
from .models import Conference, Track, Chair, Author, Reviewer, Paper, Review

class ConferenceAdminForm(forms.ModelForm):
    class Meta:
        model = Conference
        fields = '__all__'

    chairs = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.SelectMultiple(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['chairs'].initial = self.instance.chair_set.values_list('user', flat=True)

    def save(self, commit=True):
        # To allow for users to be added as chairs

        instance = super().save(commit=False)
        instance.save()

        selected_users = self.cleaned_data.get('chairs', [])
        chairs = Chair.objects.filter(user__in=selected_users, conferences=instance)
        existing_chairs = set(chairs.values_list('user', flat=True))
        new_chairs = []

        for user in selected_users:
            if user not in existing_chairs:
                chair, created = Chair.objects.get_or_create(user=user)
                chair.conferences.add(instance)
                new_chairs.append(chair)

        chairs = Chair.objects.filter(pk__in=[chair.pk for chair in chairs])
        new_chairs = Chair.objects.filter(pk__in=[chair.pk for chair in new_chairs])

        for chair in chairs.union(new_chairs):
            chair.conferences.add(instance)

        return instance
    
    def get_chairs(self, obj):
        chairs = obj.chairs.all()
        return ', '.join(str(chair) for chair in chairs)
    
    get_chairs.short_description = 'Chairs'


class ConferenceAdmin(admin.ModelAdmin):
    form = ConferenceAdminForm

admin.site.register(Conference, ConferenceAdmin)
admin.site.register(Track)
admin.site.register(Author)
admin.site.register(Chair)
admin.site.register(Reviewer)
admin.site.register(Paper)
admin.site.register(Review)