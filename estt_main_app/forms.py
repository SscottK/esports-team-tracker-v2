from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Team_user, Team, Team_game, Time, Target_times, Level, Organization, Org_user, Org_join_code, GameSuggestion







class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']


class TeamUserForm(forms.ModelForm):
    user = forms.CharField(widget=forms.TextInput(attrs={'id': 'user-search'}))
    class Meta:
        model = Team_user
        fields = ['user', 'isCoach']

    def clean_user(self):
        user_id = self.cleaned_data['user']
        try:
            return User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise forms.ValidationError("Selected user does not exist.")


class EditProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username']

class NewTeamForm(forms.ModelForm):
    class Meta:
        model = Team
        fields = ['name']


class AddTeamUserOnTeamCreationForm(forms.ModelForm):
    class Meta:
        model = Team_user
        exclude = ['user', 'team', 'isCoach']

        
class TeamGameForm(forms.ModelForm):
    class Meta:
        model = Team_game
        fields = ['game']


class TimeCreationForm(forms.ModelForm):
    # add the level stuff from tarrget times creation form exactly.
    level = forms.ModelChoiceField(
        queryset=Level.objects.none(),  # Default queryset; will be updated dynamically
        empty_label="Select a level"
    )
    class Meta:
        model = Time
        fields = ['level', 'time']

    def __init__(self, *args, **kwargs):
        game_id = kwargs.pop('game_id', None)  # Extract game_id from kwargs
        super().__init__(*args, **kwargs)  # Call the parent initializer
        if game_id:
            # Filter the queryset based on game_id
            self.fields['level'].queryset = Level.objects.filter(game=game_id)
        # else:
        #     # Empty queryset if game_id is not provided
        #     self.fields['level'].queryset = Level.objects.none()


class TimeUpdateForm(forms.ModelForm):
    class Meta:
        model = Time
        fields = ['time']




class TargetTimesCreationForm(forms.ModelForm):
    level = forms.ModelChoiceField(
        queryset=Level.objects.none(),  # Default queryset; will be updated dynamically
        empty_label="Select a level"
    )
    class Meta:
        model = Target_times
        fields = ['level', 'high_target', 'low_target']

    def __init__(self, *args, **kwargs):
        game_id = kwargs.pop('game_id', None)  # Extract game_id from kwargs
        super().__init__(*args, **kwargs)  # Call the parent initializer
        if game_id:
            # Filter the queryset based on game_id
            self.fields['level'].queryset = Level.objects.filter(game=game_id)
        else:
            # Empty queryset if game_id is not provided
            self.fields['level'].queryset = Level.objects.none()


class NewOrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name']


class AddOrgUserOnOrgCreationForm(forms.ModelForm):
    class Meta:
        model = Org_user
        exclude = ['user', 'org']

class CreateOrgJoinCode(forms.ModelForm):
    class Meta:
        model = Org_join_code
        exclude = ['code', 'org']

class GameSuggestionForm(forms.ModelForm):
    class Meta:
        model = GameSuggestion
        fields = ['game_name']
        widgets = {
            'game_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter game name'})
        }

class CreateOrgForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'})
        }

class CreateOrgUserForm(forms.ModelForm):
    class Meta:
        model = Org_user
        fields = []  # No fields needed since role will be set automatically

class JoinOrgForm(forms.Form):
    join_code = forms.CharField(max_length=8, widget=forms.TextInput(attrs={'class': 'form-control'}))