from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from .forms import CustomUserCreationForm
from django.urls import reverse_lazy
from .models import Team_user, Team, Team_game
from django.contrib.auth.models import User
from django.views.generic.edit import CreateView, UpdateView
from .forms import TeamUserForm, EditProfileForm, NewTeamForm, AddTeamUserOnTeamCreationForm
from django.http import HttpResponse

# Create your views here.

#View for the home page
def home(request):
    
    return render(request, 'home.html')

#view for the User Dashboard Page
def userDashboard(request):
    teams = Team_user.objects.filter(user=request.user)
    
    
    return render(request, 'users/dashboard.html', {
        'teams': teams
    })

#logout
def logOut(request):
    if 'logout' in request.GET:
        logout(request)
        return redirect('home')
    

#user sign up
def signup(request):
    error_message = ''
    if request.method == 'POST':
        # Create a user form object with POST data
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Add the user to the database
            user = form.save(commit=False)            
            user.save()
            # Log the user in
            login(request, user)
            return redirect('dashboard')  # Redirect to a welcome page or dashboard
        else:
            error_message = 'Invalid sign up - try again'
    else:
        # Render signup.html with an empty form
        form = CustomUserCreationForm()
    
    # Render the signup page with form and potential error message
    context = {'form': form, 'error_message': error_message}
    return render(request, 'signup.html', context)

#Team details page
def team_detail(request, teamID):
    team = get_object_or_404(Team, id=teamID)    
    members = Team_user.objects.filter(team=teamID)
    games = Team_game.objects.filter(team=teamID)
    team_user = get_object_or_404(Team_user, team=teamID,user=request.user)


    print(f'{team_user.isCoach}')

    return render(request, 'team/team_details.html', {
        'members': members,
        'games': games,
        'team': team,
        'team_user': team_user,
    })
#add member to team
def add_team_member(request, teamID):
    team_user = get_object_or_404(Team_user, team=teamID,user=request.user)
    team = get_object_or_404(Team, id=teamID)
    

    if not team_user.isCoach:
        raise HttpResponse('You are not allowed to do that')
    
    if request.method == 'POST':
        form = TeamUserForm(request.POST)
        if form.is_valid():
            team_user = form.save(commit=False)
            team_user.team = team
            team_user.save()
            return redirect(f'/team-details/{teamID}')
    else:
        form = TeamUserForm()
    
    return render(request, 'team/add_team_user.html', {
        'form': form,
        'team': team,
        
    })


#edit profile view
def edit_profile(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = EditProfileForm(instance=user)
        
    return render(request, 'users/edit_profile.html', {
        'form': form,
        'user': user,
        })


#Create a new team
def create_team(request):
    user = get_object_or_404(User, id=request.user.id)

    if request.method == 'POST':
        form_one = NewTeamForm(request.POST)
        form_two = AddTeamUserOnTeamCreationForm(request.POST)
        if form_one.is_valid():
            new_team = form_one.save(commit=False)
            new_team.save()            
            team_user = form_two.save(commit=False)
            team_user.team = get_object_or_404(Team, id=new_team.id)
            team_user.user = get_object_or_404(User, id=request.user.id)
            team_user.isCoach = True
            team_user.save()
        return redirect('dashboard')
    else:
        form_one = NewTeamForm()
        form_two = AddTeamUserOnTeamCreationForm()
    
    return render(request, 'team/new_team.html', {
        'user': user,
        'form_one': form_one,
        'form_two': form_two,
        
    })
            
