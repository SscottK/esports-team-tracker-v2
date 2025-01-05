from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Team_user






class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']


class TeamUserForm(forms.ModelForm):
    class Meta:
        model = Team_user
        fields = ['team', 'user']