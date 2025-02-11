from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm
from django.urls import reverse_lazy
from .models import Team_user, Team, Team_game, Game, Level, Time, Organization, Org_user, Org_join_code, Org_team
from django.contrib.auth.models import User
from django.views.generic.edit import CreateView, UpdateView
from .forms import TeamUserForm, EditProfileForm, NewTeamForm, AddTeamUserOnTeamCreationForm, TeamGameForm, TimeCreationForm, TimeUpdateForm, TargetTimesCreationForm, NewOrganizationForm, AddOrgUserOnOrgCreationForm, CreateOrgJoinCode
from django.http import HttpResponse
from django.http import JsonResponse
import random
import string



# Create your views here.

# View for the home page
def home(request):
    return render(request, 'home.html')

# View for the User Dashboard Page
@login_required
def userDashboard(request):
    teams = Team_user.objects.filter(user=request.user)
    times = Time.objects.filter(user=request.user)
    user_org = Org_user.objects.filter(user=request.user)

    return render(request, 'users/dashboard.html', {
        'teams': teams,
        'times': times,
        'org': user_org
    })

# Logout
def logOut(request):
    if 'logout' in request.GET:
        logout(request)
        return redirect('home')

# User sign up
def signup(request):
    error_message = ''
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)            
            user.save()
            login(request, user)
            return redirect('dashboard')
        else:
            error_message = 'Invalid sign up - try again'
    else:
        form = CustomUserCreationForm()
    
    context = {'form': form, 'error_message': error_message}
    return render(request, 'signup.html', context)

# Team details page
@login_required
def team_detail(request, teamID):
    team = get_object_or_404(Team, id=teamID)    
    members = Team_user.objects.filter(team=teamID)
    games = Team_game.objects.filter(team=teamID)
    user_org = Org_user.objects.filter(user=request.user)
    if not user_org:
        user_org = ""
    team_user = get_object_or_404(Team_user, team=teamID, user=request.user)
    teams = Team.objects.all()

    return render(request, 'team/team_details.html', {
        'members': members,
        'games': games,
        'team': team,
        'team_user': team_user,
        'teams': teams,
        'org': user_org
    })

# Add member to team
@login_required
def add_team_member(request, teamID):
    team_user = get_object_or_404(Team_user, team=teamID, user=request.user)
    team = get_object_or_404(Team, id=teamID)

    if not team_user.isCoach:
        return HttpResponse('You are not allowed to do that', status=403)
    
    if request.method == 'POST':
        user_id = request.POST.get('user')        
        user = get_object_or_404(User, id=user_id)
        form = TeamUserForm(request.POST)
        
        if form.is_valid():
            new_team_user = form.save(commit=False)
            new_team_user.team = team
            new_team_user.save()
            return redirect(f'/team-details/{teamID}')
    else:
        form = TeamUserForm()
    
    return render(request, 'team/add_team_user.html', {
        'form': form,
        'team': team,
    })

# Autocomplete for user search to add user to team
@login_required
def search_users(request):
    query = request.GET.get('q', '')
    users = User.objects.filter(username__icontains=query)[:10]
    results = [{'id': user.id, 'username': user.username} for user in users]
    return JsonResponse(results, safe=False)

# Edit profile view
@login_required
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

# Create a new team
@login_required
def create_team(request):
    try:
        if request.method == 'POST':
            form_one = NewTeamForm(request.POST)
            form_two = AddTeamUserOnTeamCreationForm(request.POST)
            if form_one.is_valid() and form_two.is_valid():
                new_team = form_one.save(commit=False)
                new_team.save()            
                team_user = form_two.save(commit=False)
                team_user.team = new_team
                team_user.user = request.user
                team_user.isCoach = True
                team_user.save()
                return redirect('dashboard')
            else:
                return render(request, 'team/new_team.html', {
                    'form_one': form_one,
                    'form_two': form_two,
                    'error_message': 'Please correct the errors below.'
                })
        else:
            form_one = NewTeamForm()
            form_two = AddTeamUserOnTeamCreationForm()
        
        return render(request, 'team/new_team.html', {
            'form_one': form_one,
            'form_two': form_two,
        })
    except Exception as e:
        return JsonResponse({"error": "An unexpected error occurred while creating the team. Please try again."}, status=500)

# Get games by team
@login_required
def get_games(request):
    try:
        team_id = request.GET.get('team_id')
        
        if not team_id:
            return JsonResponse({"error": "Team is required"}, status=400)
        
        games = Team_game.objects.filter(team_id=team_id).values('game_id', 'game__game')
        
        if not games:
            return JsonResponse({"error": "No games found for this team"}, status=404)
        
        return JsonResponse(list(games), safe=False)
    except Exception as e:
        return JsonResponse({"error": f"An unexpected error occurred: {str(e)}"}, status=500)

# Gather table data
@login_required
def get_table_data(request):
    try:
        game_id = request.GET.get('game_id')
        
        if not game_id:
            return JsonResponse({"error": "Game is required"}, status=400)
        
        team_game = get_object_or_404(Team_game, game=game_id)
        game = get_object_or_404(Game, id=game_id)

        team_members = Team_user.objects.filter(team=team_game.team).values('user', 'user__username')
        levels = Level.objects.filter(game=game).values('id', 'level_name')
        times = Time.objects.filter(level__game=game).values('level_id', 'user_id', 'time')
        
        time_dict = {f"{time['level_id']}-{time['user_id']}": time['time'] for time in times}
        
        return JsonResponse({
            'users': list(team_members.filter(isCoach=False)),
            'levels': list(levels),
            'times': time_dict,
            'game': str(game),
            'game_id': game_id,
            'team_id': team_game.team.id            
        })
    except Exception as e:
        return JsonResponse({"error": f"An unexpected error occurred: {str(e)}"}, status=500)

# Add game to team
@login_required
def create_team_game(request, team_id):
    team = get_object_or_404(Team, id=team_id)
    # Check if the user is a coach for the team
    team_user = get_object_or_404(Team_user, team=team, user=request.user)
    if not team_user.isCoach:
        return HttpResponse('You are not allowed to add a game to this team.', status=403)
    
    if request.method == 'POST':
        form = TeamGameForm(request.POST)
        
        if form.is_valid():
            new_team_game = form.save(commit=False)
            new_team_game.team = team
            new_team_game.save()
            return redirect(f'/team-details/{team_id}')
    else:
        form = TeamGameForm()

    return render(request, 'team/add_team_game.html', {
        'team': team,
        'form': form        
    })

# Add new time
@login_required
def create_new_time(request):
    try:
        if request.method == 'POST':
            game_id = request.POST.get('game')
            form = TimeCreationForm(request.POST, game_id=game_id)
            
            if form.is_valid():
                time_instance = form.save(commit=False)
                time_instance.user = request.user
                time_instance.save()
                return JsonResponse({'success': True, 'message': 'Time saved successfully!'})
            else:
                return JsonResponse({'success': False, 'errors': form.errors}, status=400)
        else:
            game_id = request.GET.get('game')
            form = TimeCreationForm(game_id=game_id)
            return render(request, 'time/add_time.html', {
                'form': form
            })
    except Exception as e:
        return JsonResponse({"error": "An unexpected error occurred while creating new time. Please try again."}, status=500)

# Update time and confirm
@login_required
def update_time(request, time_id):
    try:
        time = get_object_or_404(Time, id=time_id)
        
        if request.method == 'POST':
            form = TimeUpdateForm(request.POST, instance=time)
            if form.is_valid():
                if "confirm" in request.POST:                
                    form.save()
                    return redirect('dashboard')
                else:
                    new_time = form.cleaned_data
                    return render(request, 'time/update_confirm.html', {
                        'old_time': str(time).split(',')[2],
                        'new_time': new_time,
                        'form': form
                    })
        else:
            form = TimeUpdateForm(instance=time)
            
        return render(request, 'time/update_form.html', {
            'form': form
        })
    except Exception as e:
        return JsonResponse({"error": "An unexpected error occurred while updating the time. Please try again."}, status=500)
#create target times for selected game
@login_required
def create_target_times(request, team_id, game_id):
    try:
        game = get_object_or_404(Game, id=game_id)
        team = get_object_or_404(Team, id=team_id)
        levels = Level.objects.filter(game=game_id)
        
        initial_data = {
            'options': levels,
            'high_target': "00:00.00",
            'low_target': "00:00.00"
        }
        if request.method == 'POST':
            form = TargetTimesCreationForm(request.POST, initial=initial_data, game_id=game_id)
            
            if form.is_valid():
                new_target_times = form.save(commit=False)
                new_target_times.team = team
                new_target_times.save()
                return redirect(f'/team-details/{team_id}')
        else:
            form = TargetTimesCreationForm(initial=initial_data, game_id=game_id)

        form.fields['level'].queryset = levels

        return render(request, 'target_time/add_tt.html', {
            'form.levels': levels,
            'game': game,
            'form': form,
            'team': team.id
        })
    except Exception as e:
        return JsonResponse({"error": "An unexpected error occurred while creating target times. Please try again."}, status=500)

# Get all games for new time
@login_required
def new_time_get_games(request):    
    if request.method == 'GET':
        games = Game.objects.values('id', 'game')
        return JsonResponse(list(games), safe=False)
    return JsonResponse({'error': 'Invalid request method'}, status=400)

# Get levels for game when creating new time
@login_required
def get_levels(request):
    game_id = request.GET.get('game_id')
    if game_id:
        levels = Level.objects.filter(game_id=game_id).values('id', 'level_name')
        return JsonResponse(list(levels), safe=False)
    return JsonResponse({'error': 'Game ID not provided'}, status=400)


#create new organization
def create_org(request):
    # try:
        if request.method == 'POST':
            form_one = NewOrganizationForm(request.POST)
            form_two = AddOrgUserOnOrgCreationForm(request.POST)
            if form_one.is_valid() and form_two.is_valid():
                new_org = form_one.save(commit=False)
                new_org.save()            
                org_user = form_two.save(commit=False)
                org_user.org = new_org
                org_user.user = request.user
                
                org_user.save()
                return redirect('dashboard')
            else:
                return render(request, 'organization/new_org.html', {
                    'form_one': form_one,
                    'form_two': form_two,
                    'error_message': 'Please correct the errors below.'
                })
        else:
            form_one = NewOrganizationForm()
            form_two = AddOrgUserOnOrgCreationForm()
        
        return render(request, 'organization/new_org.html', {
            'form_one': form_one,
            'form_two': form_two,
        })
    # except Exception as e:
        # return JsonResponse({"error": "An unexpected error occurred while creating the organization. Please try again."}, status=500)


#generate join code
def generate_join_code(request, org_id):
    # try:
        def generate_random_code(length=8):
            characters = string.ascii_letters + string.digits
            random_code = ''.join(random.choice(characters) for _ in range(length))
            return random_code
        
        org = get_object_or_404(Organization, id=org_id)
        codes = Org_join_code.objects.filter(org=org.id)
        new_join_code = Org_join_code(code=generate_random_code(8), org=org)
        
        new_join_code.save()
        return render(request, 'organization/org_code_generator.html', {
            'codes': codes,
            'org': org

        })
    # except Exception as e:
        # return JsonResponse({"error": "An unexpected error occurred while generating the join code. Please try again."}, status=500)
    


#join code index
def join_codes(request, org_id):
    try:        
        org = get_object_or_404(Organization, id=org_id)
        codes = Org_join_code.objects.filter(org=org.id)
        return render(request, 'organization/org_code_generator.html', {
            'codes': codes,
            'org': org

        })
    except Exception as e:
        return JsonResponse({"error": "An unexpected error occurred while getting the join code. Please try again."}, status=500)