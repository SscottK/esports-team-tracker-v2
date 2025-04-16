from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, GameSuggestionForm
from django.urls import reverse_lazy
from .models import Team_user, Team, Team_game, Game, Level, Time, Organization, Org_user, Org_join_code, Org_team, GameSuggestion, Target_times
from django.contrib.auth.models import User
from django.views.generic.edit import CreateView, UpdateView
from .forms import TeamUserForm, EditProfileForm, NewTeamForm, AddTeamUserOnTeamCreationForm, TeamGameForm, TimeCreationForm, TimeUpdateForm, TargetTimesCreationForm, NewOrganizationForm, AddOrgUserOnOrgCreationForm, CreateOrgJoinCode
from django.http import HttpResponse
from django.http import JsonResponse
import random
import string
import csv
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from io import StringIO
import re
from django.contrib.admin.views.decorators import staff_member_required



# Create your views here.

# View for the home page
def home(request):
    return render(request, 'home.html')

# View for the User Dashboard Page
@login_required
def userDashboard(request):
    teams = Team_user.objects.filter(user=request.user)
    times = Time.objects.filter(user=request.user)
    user_org = Org_user.objects.filter(user=request.user).first()

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
    user_org = Org_user.objects.filter(user=request.user).first()
    if user_org:
        org = Organization.objects.filter(name=user_org.org).first()
    else:
        org = ""
    team_user = get_object_or_404(Team_user, team=teamID, user=request.user)
    teams = Team.objects.all()
    active_members = []
    for member in members:
        if member.user.is_active:
            active_members.append(member)

    return render(request, 'team/team_details.html', {
        'members': active_members,
        'games': games,
        'team': team,
        'team_user': team_user,
        'teams': teams,
        'org': org
    })

# Add member to team
@login_required
def add_team_member(request, teamID, org_id):
    try:
        # Input validation
        if not teamID or not org_id:
            messages.error(request, 'Invalid team or organization ID.')
            return redirect('dashboard')
            
        # Get team and organization with error handling
        try:
            team = get_object_or_404(Team, id=teamID)
            org = get_object_or_404(Organization, id=org_id)
        except (Team.DoesNotExist, Organization.DoesNotExist):
            messages.error(request, 'Team or organization not found.')
            return redirect('dashboard')
            
        # Check if user is a coach
        try:
            team_user = get_object_or_404(Team_user, team=teamID, user=request.user)
            if not team_user.isCoach:
                messages.error(request, 'You do not have permission to add members.')
                return redirect('team-details', teamID=teamID)
        except Team_user.DoesNotExist:
            messages.error(request, 'You are not a member of this team.')
            return redirect('dashboard')
        
        # Get whether this is a coach addition from the URL parameter
        is_coach = request.GET.get('is_coach', 'false').lower() == 'true'
        
        if request.method == 'POST':
            try:
                # Validate user ID
                user_id = request.POST.get('user')
                if not user_id:
                    return render(request, 'team/add_team_user.html', {
                        'team': team,
                        'org': org,
                        'is_coach': is_coach,
                        'error_message': 'Please select a user to add.'
                    })
                    
                # Get user with error handling
                try:
                    user = get_object_or_404(User, id=user_id)
                except User.DoesNotExist:
                    return render(request, 'team/add_team_user.html', {
                        'team': team,
                        'org': org,
                        'is_coach': is_coach,
                        'error_message': 'Selected user not found.'
                    })
                
                # Check if user is active
                if not user.is_active:
                    return render(request, 'team/add_team_user.html', {
                        'team': team,
                        'org': org,
                        'is_coach': is_coach,
                        'error_message': 'Cannot add an inactive user to the team.'
                    })
                
                # Check if user is already in the team
                existing_team_user = Team_user.objects.filter(team=team, user=user).first()
                
                if existing_team_user:
                    if is_coach and not existing_team_user.isCoach:
                        # If promoting a member to coach
                        existing_team_user.isCoach = True
                        existing_team_user.save()
                        messages.success(request, f'Promoted {user.username} to coach.')
                        return redirect('team-details', teamID=teamID)
                    elif not is_coach and existing_team_user.isCoach:
                        # If demoting a coach to member
                        existing_team_user.isCoach = False
                        existing_team_user.save()
                        messages.success(request, f'Changed {user.username} to team member.')
                        return redirect('team-details', teamID=teamID)
                    else:
                        role = 'coach' if existing_team_user.isCoach else 'member'
                        return render(request, 'team/add_team_user.html', {
                            'team': team,
                            'org': org,
                            'is_coach': is_coach,
                            'error_message': f'This user is already a {role} of the team.'
                        })
                
                # Create new team user with coach status from URL
                new_team_user = Team_user(
                    team=team,
                    user=user,
                    isCoach=is_coach
                )
                new_team_user.save()
                messages.success(request, f'Added {user.username} as {"coach" if is_coach else "member"}.')
                
                return redirect('team-details', teamID=teamID)
                
            except Exception as e:
                return render(request, 'team/add_team_user.html', {
                    'team': team,
                    'org': org,
                    'is_coach': is_coach,
                    'error_message': f'Error adding team member: {str(e)}'
                })
        else:
            form = TeamUserForm()
        
        return render(request, 'team/add_team_user.html', {
            'form': form,
            'team': team,
            'org': org,
            'is_coach': is_coach,
        })
        
    except Exception as e:
        messages.error(request, f'An unexpected error occurred: {str(e)}')
        return redirect('dashboard')

# Autocomplete for user search to add user to team
@login_required
def search_users(request):
    try:
        # Sanitize and validate search query
        query = request.GET.get('q', '').strip()
        if not query:
            return JsonResponse([], safe=False)
            
        # Sanitize and validate organization ID
        organization_id = request.GET.get('organization_id')
        if not organization_id:
            return JsonResponse([], safe=False)
            
        try:
            organization_id = int(organization_id)
        except (TypeError, ValueError):
            return JsonResponse([], safe=False)
        
        # Get organization with error handling
        try:
            organization = Organization.objects.get(pk=organization_id)
        except Organization.DoesNotExist:
            return JsonResponse([], safe=False)
        
        # Sanitize query to prevent SQL injection
        # Django's ORM already handles this, but we'll add extra validation
        if not all(c.isalnum() or c.isspace() or c in '-_' for c in query):
            return JsonResponse([], safe=False)
            
        # Filter users who are members of the organization
        # Limit results to prevent abuse
        org_users = Org_user.objects.filter(
            org=organization,
            user__username__icontains=query,
            user__is_active=True
        )[:10]
        
        # Extract the user objects from Org_user instances
        users = [org_user.user for org_user in org_users]
        results = [{'id': user.id, 'username': user.username} for user in users]
        
        return JsonResponse(results, safe=False)
        
    except Exception as e:
        # Log the error for debugging
        print(f"Error in search_users: {str(e)}")
        return JsonResponse([], safe=False)

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
            
            # Check for duplicate team name
            team_name = request.POST.get('name', '').strip()
            if Team.objects.filter(name=team_name).exists():
                return render(request, 'team/new_team.html', {
                    'form_one': form_one,
                    'form_two': form_two,
                    'error_message': 'A team with this name already exists.'
                })
                
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
        # Validate game_id parameter
        game_id = request.GET.get('game_id')
        if not game_id:
            return JsonResponse({"error": "Game ID is required"}, status=400)
            
        try:
            game_id = int(game_id)
        except (TypeError, ValueError):
            return JsonResponse({"error": "Invalid game ID format"}, status=400)
        
        # Get team game and game with error handling
        try:
            team_game = get_object_or_404(Team_game, game=game_id)
            game = get_object_or_404(Game, id=game_id)
        except (Team_game.DoesNotExist, Game.DoesNotExist):
            return JsonResponse({"error": "Game not found"}, status=404)
            
        # Get team members
        team_members = Team_user.objects.filter(
            team_id=team_game.team.id,
            isCoach=False  # Only get non-coach members
        ).select_related('user')
        if not team_members.exists():
            return JsonResponse({'error': 'No team members found'}, status=404)
        
        # Filter active members and convert to serializable format
        active_members = []
        for member in team_members:
            try:
                user = get_object_or_404(User, id=member.user.id)
                if user.is_active:
                    active_members.append({
                        'id': user.id,
                        'username': user.username
                    })
            except User.DoesNotExist:
                continue
                
        # Get levels for the game
        levels = Level.objects.filter(game=game).values('id', 'level_name')
        
        # Get times for non-coach users
        times = Time.objects.filter(
            level__game=game,
            user_id__in=[member['id'] for member in active_members]
        ).values('level_id', 'user_id', 'time')
        
        # Create time dictionary
        time_dict = {f"{time['level_id']}-{time['user_id']}": time['time'] for time in times}
        
        # Prepare response data
        response_data = {
            'users': active_members,
            'levels': list(levels),
            'times': time_dict,
            'game': str(game),
            'game_id': game_id,
            'team_id': team_game.team.id
        }
        
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({"error": f"An unexpected error occurred: {str(e)}"}, status=500)

# Add game to team
@login_required
def create_team_game(request, team_id):
    try:
        team = get_object_or_404(Team, id=team_id)
        # Check if the user is a coach for the team
        team_user = get_object_or_404(Team_user, team=team, user=request.user)
        if not team_user.isCoach:
            messages.error(request, 'You are not allowed to add a game to this team.')
            return redirect('team-details', teamID=team_id)
        
        if request.method == 'POST':
            form = TeamGameForm(request.POST)
            
            if form.is_valid():
                game = form.cleaned_data['game']
                # Check if the game already exists for this team
                if Team_game.objects.filter(team=team, game=game).exists():
                    messages.error(request, 'This game is already added to the team.')
                    return render(request, 'team/add_team_game.html', {
                        'team': team,
                        'form': form,
                        'error_message': 'This game is already added to the team.'
                    })
                
                new_team_game = form.save(commit=False)
                new_team_game.team = team
                new_team_game.save()
                messages.success(request, 'Game successfully added to the team.')
                return redirect('team-details', teamID=team_id)
        else:
            form = TeamGameForm()

        return render(request, 'team/add_team_game.html', {
            'team': team,
            'form': form
        })
        
    except Exception as e:
        messages.error(request, f'An unexpected error occurred: {str(e)}')
        return redirect('team-details', teamID=team_id)

# Add new time
@login_required
def create_new_time(request):
    try:
        if request.method == 'POST':
            # Validate required parameters
            level_id = request.POST.get('level')
            game_id = request.POST.get('game')
            time_str = request.POST.get('time', '').strip()
            
            if not level_id or not game_id or not time_str:
                return JsonResponse({
                    'success': False,
                    'errors': "Level, game, and time are required."
                }, status=400)
                
            # Validate time format (accepts both MM:SS.mmm and M:SS.mm)
            if not re.match(r'^\d{1,2}:\d{2}\.\d{2,3}$', time_str):
                return JsonResponse({
                    'success': False,
                    'errors': "Invalid time format. Please use format M:SS.mm or MM:SS.mmm"
                }, status=400)
                
            # Normalize time format to MM:SS.mmm
            if ':' in time_str:
                minutes, rest = time_str.split(':')
                if len(minutes) == 1:
                    time_str = f"0{minutes}:{rest}"
                if len(rest.split('.')[1]) == 2:
                    time_str = f"{time_str}0"
                
            try:
                level_id = int(level_id)
                game_id = int(game_id)
            except (TypeError, ValueError):
                return JsonResponse({
                    'success': False,
                    'errors': "Invalid level or game ID format."
                }, status=400)
            
            # Check if time already exists
            try:
                existing_time = Time.objects.filter(level=level_id, user=request.user).first()
                if existing_time:
                    return JsonResponse({
                        'success': False,
                        'errors': "You already have a time for that level. Please update the existing time entry."
                    }, status=400)
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'errors': f"Error checking existing time: {str(e)}"
                }, status=500)
            
            # Validate form data
            form = TimeCreationForm(request.POST, game_id=game_id)
            if not form.is_valid():
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                }, status=400)
            
            try:
                # Create new time record
                time_instance = form.save(commit=False)
                time_instance.user = request.user
                time_instance.time = time_str  # Use normalized time
                time_instance.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Time saved successfully!'
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'errors': f"Error saving time: {str(e)}"
                }, status=500)
                
        else:
            # GET request - show the form
            return render(request, 'time/add_time.html')
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'errors': f"An unexpected error occurred: {str(e)}"
        }, status=500)

# Update time and confirm
@login_required
def update_time(request, time_id):
    try:
        # Validate time_id parameter
        if not time_id:
            return redirect('dashboard')
            
        try:
            time_id = int(time_id)
        except (TypeError, ValueError):
            return redirect('dashboard')
        
        # Get time record with error handling
        try:
            time = get_object_or_404(Time, id=time_id)
        except Time.DoesNotExist:
            return redirect('dashboard')
            
        # Check if user owns the time record
        if time.user != request.user:
            return HttpResponse('You are not authorized to update this time.', status=403)
        
        if request.method == 'POST':
            try:
                # Get the time from the form data
                time_str = request.POST.get('time', '').strip()
                
                # Validate time format (accepts both MM:SS.mmm and M:SS.mm)
                if not re.match(r'^\d{1,2}:\d{2}\.\d{2,3}$', time_str):
                    return JsonResponse({
                        'success': False,
                        'errors': "Invalid time format. Please use format M:SS.mm or MM:SS.mmm"
                    }, status=400)
                
                # Normalize time format to MM:SS.mmm
                if ':' in time_str:
                    minutes, rest = time_str.split(':')
                    if len(minutes) == 1:
                        time_str = f"0{minutes}:{rest}"
                    if len(rest.split('.')[1]) == 2:
                        time_str = f"{time_str}0"
                
                # Validate form data first
                form = TimeUpdateForm(request.POST, instance=time)
                if not form.is_valid():
                    return render(request, 'time/update_form.html', {
                        'form': form,
                        'error_message': 'Please correct the errors below.'
                    })
                
                # Update the time
                time.time = time_str  # Use normalized time
                time.save()
                
                messages.success(request, 'Time updated successfully!')
                return redirect('dashboard')
                    
            except Exception as e:
                return render(request, 'time/update_form.html', {
                    'form': TimeUpdateForm(instance=time),
                    'error_message': f'Error updating time: {str(e)}'
                })
        else:
            form = TimeUpdateForm(instance=time)
            
        return render(request, 'time/update_form.html', {
            'form': form
        })
        
    except Exception as e:
        return redirect('dashboard')

#create target times for selected game
@login_required
def create_target_times(request, team_id, game_id):
    try:
        # Validate team_id and game_id parameters
        if not team_id or not game_id:
            messages.error(request, 'Invalid team or game ID.')
            return redirect('dashboard')
            
        try:
            team_id = int(team_id)
            game_id = int(game_id)
        except (TypeError, ValueError):
            messages.error(request, 'Invalid team or game ID format.')
            return redirect('dashboard')
        
        # Get team and game with error handling
        try:
            team = get_object_or_404(Team, id=team_id)
            game = get_object_or_404(Game, id=game_id)
        except (Team.DoesNotExist, Game.DoesNotExist):
            messages.error(request, 'Team or game not found.')
            return redirect('dashboard')
            
        # Check if user is a coach
        try:
            team_user = get_object_or_404(Team_user, team=team, user=request.user)
            if not team_user.isCoach:
                messages.error(request, 'You do not have permission to create target times.')
                return redirect('team-details', teamID=team_id)
        except Team_user.DoesNotExist:
            messages.error(request, 'You are not a member of this team.')
            return redirect('dashboard')
        
        # Get levels for the game
        try:
            levels = Level.objects.filter(game=game_id)
            if not levels.exists():
                messages.error(request, 'No levels found for this game.')
                return redirect('team-details', teamID=team_id)
        except Exception as e:
            messages.error(request, f'Error getting levels: {str(e)}')
            return redirect('team-details', teamID=team_id)
        
        # Prepare initial data
        initial_data = {
            'options': levels,
            'high_target': "00:00.00",
            'low_target': "00:00.00"
        }
        
        if request.method == 'POST':
            # Check if this is a CSV upload
            if 'csv_upload' in request.POST:
                if 'csv_file' not in request.FILES:
                    messages.error(request, 'No CSV file uploaded.')
                    return redirect('new-target-times', team_id=team_id, game_id=game_id)
                
                csv_file = request.FILES['csv_file']
                if not csv_file.name.endswith('.csv'):
                    messages.error(request, 'Please upload a CSV file.')
                    return redirect('new-target-times', team_id=team_id, game_id=game_id)
                
                upload_errors = []
                try:
                    # Read CSV file
                    csv_data = csv.reader(csv_file.read().decode('utf-8').splitlines())
                    next(csv_data)  # Skip header row
                    
                    for row_num, row in enumerate(csv_data, start=2):  # Start from 2 to account for header
                        if len(row) < 3:
                            upload_errors.append(f"Row {row_num}: Invalid format - missing columns")
                            continue
                            
                        level_name, high_target, low_target = row[:3]
                        level_name = level_name.strip()
                        high_target = high_target.strip()
                        low_target = low_target.strip()
                        
                        # Validate time formats
                        time_pattern = r'^\d{1,2}:\d{2}\.\d{2,3}$|^\d{1,2}:\d{2}\.\d{2}$'
                        if not re.match(time_pattern, high_target) or not re.match(time_pattern, low_target):
                            upload_errors.append(f"Row {row_num}: Invalid time format")
                            continue
                            
                        # Normalize time format to MM:SS.mmm
                        for time in [high_target, low_target]:
                            if ':' in time:
                                minutes, rest = time.split(':')
                                if len(minutes) == 1:
                                    time = f"0{minutes}:{rest}"
                                if len(rest.split('.')[1]) == 2:
                                    time = f"{time}0"
                        
                        # Find level
                        try:
                            level = Level.objects.get(level_name=level_name, game=game)
                        except Level.DoesNotExist:
                            # TODO: Add level suggestion feature
                            upload_errors.append(f"Row {row_num}: Level '{level_name}' not found")
                            continue
                            
                        # Create or update target time
                        target_time, created = Target_times.objects.get_or_create(
                            level=level,
                            team=team,
                            defaults={
                                'high_target': high_target,
                                'low_target': low_target
                            }
                        )
                        
                        if not created:
                            target_time.high_target = high_target
                            target_time.low_target = low_target
                            target_time.save()
                            
                except Exception as e:
                    upload_errors.append(f"Error processing CSV: {str(e)}")
                
                if upload_errors:
                    form = TargetTimesCreationForm(initial=initial_data, game_id=game_id)
                    form.fields['level'].queryset = levels
                    return render(request, 'target_time/add_tt.html', {
                        'form': form,
                        'game': game,
                        'team': team.id,
                        'upload_errors': upload_errors
                    })
                
                messages.success(request, 'Target times uploaded successfully.')
                return redirect('team-details', teamID=team_id)
            
            # Handle single target time creation
            try:
                # Validate form data
                form = TargetTimesCreationForm(request.POST, initial=initial_data, game_id=game_id)
                if not form.is_valid():
                    return render(request, 'target_time/add_tt.html', {
                        'form': form,
                        'game': game,
                        'team': team.id,
                        'error_message': 'Please correct the errors below.'
                    })
                
                # Create target times
                try:
                    new_target_times = form.save(commit=False)
                    new_target_times.team = team
                    new_target_times.save()
                    messages.success(request, 'Target times created successfully.')
                    return redirect('team-details', teamID=team_id)
                except Exception as e:
                    messages.error(request, f'Error creating target times: {str(e)}')
                    return redirect('team-details', teamID=team_id)
                    
            except Exception as e:
                messages.error(request, f'Error processing form: {str(e)}')
                return redirect('team-details', teamID=team_id)
        else:
            form = TargetTimesCreationForm(initial=initial_data, game_id=game_id)
            form.fields['level'].queryset = levels

        return render(request, 'target_time/add_tt.html', {
            'form': form,
            'game': game,
            'team': team.id
        })
        
    except Exception as e:
        messages.error(request, f'An unexpected error occurred: {str(e)}')
        return redirect('dashboard')

# Get all games for new time
@login_required
def new_time_get_games(request):
    try:
        if request.method != 'GET':
            return JsonResponse({
                'success': False,
                'errors': 'Invalid request method'
            }, status=405)
            
        try:
            # Get all games
            games = Game.objects.all().values('id', 'game')
            if not games.exists():
                return JsonResponse({
                    'success': False,
                    'errors': 'No games available'
                }, status=404)
                
            return JsonResponse({
                'success': True,
                'games': list(games)
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'errors': f'Error retrieving games: {str(e)}'
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'errors': f'An unexpected error occurred: {str(e)}'
        }, status=500)

# Get levels for game when creating new time
@login_required
def get_levels(request):
    try:
        if request.method != 'GET':
            return JsonResponse({
                'success': False,
                'errors': 'Invalid request method'
            }, status=405)
            
        # Validate game_id parameter
        game_id = request.GET.get('game_id')
        if not game_id:
            return JsonResponse({
                'success': False,
                'errors': 'Game ID is required'
            }, status=400)
            
        try:
            game_id = int(game_id)
        except (TypeError, ValueError):
            return JsonResponse({
                'success': False,
                'errors': 'Invalid game ID format'
            }, status=400)
            
        try:
            # Verify game exists
            game = get_object_or_404(Game, id=game_id)
            
            # Get levels for the game
            levels = Level.objects.filter(game_id=game_id).values('id', 'level_name')
            if not levels.exists():
                return JsonResponse({
                    'success': False,
                    'errors': 'No levels available for this game'
                }, status=404)
                
            return JsonResponse({
                'success': True,
                'levels': list(levels)
            })
            
        except Game.DoesNotExist:
            return JsonResponse({
                'success': False,
                'errors': 'The specified game does not exist'
            }, status=404)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'errors': f'Error retrieving levels: {str(e)}'
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'errors': f'An unexpected error occurred: {str(e)}'
        }, status=500)


#create new organization
def create_org(request):
    try:
        if request.method == 'POST':
            try:
                # Validate form data
                form_one = NewOrganizationForm(request.POST)
                form_two = AddOrgUserOnOrgCreationForm(request.POST)
                
                if not form_one.is_valid() or not form_two.is_valid():
                    error_messages = []
                    if form_one.errors:
                        error_messages.extend(form_one.errors.values())
                    if form_two.errors:
                        error_messages.extend(form_two.errors.values())
                        
                    return render(request, 'organization/new_org.html', {
                        'form_one': form_one,
                        'form_two': form_two,
                        'error_message': 'Please correct the errors below.',
                        'errors': error_messages
                    })
                
                # Create new organization
                try:
                    new_org = form_one.save(commit=False)
                    new_org.save()
                except Exception as e:
                    return render(request, 'organization/new_org.html', {
                        'form_one': form_one,
                        'form_two': form_two,
                        'error_message': f'Error creating organization: {str(e)}'
                    })
                
                # Create organization user
                try:
                    org_user = form_two.save(commit=False)
                    org_user.org = new_org
                    org_user.user = request.user
                    org_user.save()
                except Exception as e:
                    # Rollback organization creation if user creation fails
                    new_org.delete()
                    return render(request, 'organization/new_org.html', {
                        'form_one': form_one,
                        'form_two': form_two,
                        'error_message': f'Error creating organization user: {str(e)}'
                    })
                
                messages.success(request, 'Organization created successfully.')
                return redirect('dashboard')
                
            except Exception as e:
                return render(request, 'organization/new_org.html', {
                    'form_one': NewOrganizationForm(),
                    'form_two': AddOrgUserOnOrgCreationForm(),
                    'error_message': f'Error processing form: {str(e)}'
                })
        else:
            form_one = NewOrganizationForm()
            form_two = AddOrgUserOnOrgCreationForm()
        
        return render(request, 'organization/new_org.html', {
            'form_one': form_one,
            'form_two': form_two,
        })
        
    except Exception as e:
        messages.error(request, f'An unexpected error occurred: {str(e)}')
        return redirect('dashboard')


#generate join code
def generate_join_code(request, org_id):
    try:
        # Validate organization ID
        if not org_id:
            messages.error(request, 'Organization ID is required.')
            return redirect('dashboard')
            
        try:
            org_id = int(org_id)
        except (TypeError, ValueError):
            messages.error(request, 'Invalid organization ID format.')
            return redirect('dashboard')
        
        # Get organization with error handling
        try:
            org = get_object_or_404(Organization, id=org_id)
        except Organization.DoesNotExist:
            messages.error(request, 'Organization not found.')
            return redirect('dashboard')
            
        # Check if user is a member of the organization
        try:
            org_user = get_object_or_404(Org_user, org=org, user=request.user)
        except Org_user.DoesNotExist:
            messages.error(request, 'You are not a member of this organization.')
            return redirect('dashboard')
        
        def generate_random_code(length=8):
            """Generate a random alphanumeric code of specified length."""
            characters = string.ascii_letters + string.digits
            while True:
                code = ''.join(random.choice(characters) for _ in range(length))
                # Ensure code doesn't already exist
                if not Org_join_code.objects.filter(code=code).exists():
                    return code
        
        # Get the user's team in this organization
        team = Team.objects.filter(org_team__org=org, team_user__user=request.user).first()
        if not team:
            messages.error(request, 'You are not a member of any team in this organization.')
            return redirect('dashboard')

        if request.method == 'GET':
            try:
                # Check for existing code
                existing_code = Org_join_code.objects.filter(org=org).first()
                if existing_code:
                    return render(request, 'organization/org_code_generator.html', {
                        'error': 'A join code already exists. Please use the current one.',
                        'org': org,
                        'code': existing_code,
                        'team': team
                    })
                
                # Generate new code
                try:
                    new_join_code = Org_join_code(
                        code=generate_random_code(8),
                        org=org
                    )
                    new_join_code.save()
                    
                    return render(request, 'organization/org_code_generator.html', {
                        'code': new_join_code,
                        'org': org,
                        'team': team
                    })
                    
                except Exception as e:
                    messages.error(request, f'Error generating join code: {str(e)}')
                    return redirect('dashboard')
                    
            except Exception as e:
                messages.error(request, f'Error processing request: {str(e)}')
                return redirect('dashboard')
                
        else:
            messages.error(request, 'Invalid request method.')
            return redirect('dashboard')
            
    except Exception as e:
        messages.error(request, f'An unexpected error occurred: {str(e)}')
        return redirect('dashboard')
    


#join code index
def join_codes(request, org_id):
    try:
        print(f"Starting join_codes view with org_id: {org_id}")
        
        # Validate organization ID
        if not org_id:
            print("No org_id provided")
            messages.error(request, 'Organization ID is required.')
            return redirect('dashboard')
            
        try:
            org_id = int(org_id)
            print(f"Converted org_id to int: {org_id}")
        except (TypeError, ValueError):
            print("Invalid org_id format")
            messages.error(request, 'Invalid organization ID format.')
            return redirect('dashboard')
        
        # Get organization with error handling
        try:
            org = get_object_or_404(Organization, id=org_id)
            print(f"Found organization: {org.name}")
        except Organization.DoesNotExist:
            print("Organization not found")
            messages.error(request, 'Organization not found.')
            return redirect('dashboard')
            
        # Check if user is a member of the organization
        try:
            org_user = get_object_or_404(Org_user, org=org, user=request.user)
            print(f"Found org_user for {request.user.username}")
        except Org_user.DoesNotExist:
            print(f"User {request.user.username} is not a member of org {org.name}")
            messages.error(request, 'You are not a member of this organization.')
            return redirect('dashboard')
        
        # Get the user's team in this organization using org_team relationship
        team = Team.objects.filter(org_team__org=org, team_user__user=request.user).first()
        print(f"Team query result: {team}")
        if not team:
            print(f"No team found for user {request.user.username} in org {org.name}")
            messages.error(request, 'You are not a member of any team in this organization.')
            return redirect('dashboard')
        
        # Get join code with error handling
        try:
            code = Org_join_code.objects.filter(org=org).first()
            print(f"Join code query result: {code}")
            if not code:
                print("No join code exists")
                messages.error(request, 'No join code exists for this organization.')
                return redirect('dashboard')
                
            print("Rendering template with code, org, and team")
            return render(request, 'organization/org_code_generator.html', {
                'code': code,
                'org': org,
                'team': team
            })
            
        except Exception as e:
            print(f"Error retrieving join code: {str(e)}")
            messages.error(request, f'Error retrieving join code: {str(e)}')
            return redirect('dashboard')
            
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        messages.error(request, f'An unexpected error occurred: {str(e)}')
        return redirect('dashboard')
    


#join an org form page
def join_org(request):
    try:
        if request.method != 'GET':
            messages.error(request, 'Invalid request method.')
            return redirect('dashboard')
            
        # Check if user is already in an organization
        try:
            existing_org_user = Org_user.objects.filter(user=request.user).first()
            if existing_org_user:
                messages.error(request, 'You are already a member of an organization.')
                return redirect('dashboard')
        except Exception as e:
            messages.error(request, f'Error checking organization membership: {str(e)}')
            return redirect('dashboard')
        
        return render(request, 'organization/join_org.html')
        
    except Exception as e:
        messages.error(request, f'An unexpected error occurred: {str(e)}')
        return redirect('dashboard')
    
#create org_user for user to join an org
def create_org_user(request, join_code):
    try:
        # Validate join code
        if not join_code:
            messages.error(request, 'Join code is required.')
            return redirect('join-org')
            
        # Sanitize join code
        join_code = join_code.strip()
        if not join_code:
            messages.error(request, 'Invalid join code format.')
            return redirect('join-org')
        
        # Check if user is already in an organization
        try:
            existing_org_user = Org_user.objects.filter(user=request.user).first()
            if existing_org_user:
                messages.error(request, 'You are already a member of an organization.')
                return redirect('dashboard')
        except Exception as e:
            messages.error(request, f'Error checking organization membership: {str(e)}')
            return redirect('dashboard')
        
        # Get organization join code
        try:
            org_join_code = Org_join_code.objects.filter(code=join_code).first()
            if not org_join_code:
                messages.error(request, 'Invalid join code.')
                return redirect('join-org')
        except Exception as e:
            messages.error(request, f'Error validating join code: {str(e)}')
            return redirect('join-org')
        
        # Get organization
        try:
            org = get_object_or_404(Organization, id=org_join_code.org.id)
        except Organization.DoesNotExist:
            messages.error(request, 'Organization not found.')
            return redirect('join-org')
        
        # Create organization user
        try:
            new_org_user = Org_user(user=request.user, org=org)
            new_org_user.save()
            messages.success(request, f'Successfully joined {org.name}.')
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, f'Error joining organization: {str(e)}')
            return redirect('join-org')
            
    except Exception as e:
        messages.error(request, f'An unexpected error occurred: {str(e)}')
        return redirect('dashboard')

# Deactivate account
@login_required
def deactivate_account(request):
    try:
        if request.method != 'POST':
            return render(request, 'users/deactivate_confirm.html')
            
        try:
            # Mark the user as inactive
            user = request.user
            user.is_active = False
            user.save()
            
            # Log the user out
            from django.contrib.auth import logout
            logout(request)
            
            messages.success(request, 'Your account has been deactivated.')
            return redirect('goodbye')
            
        except Exception as e:
            messages.error(request, f'Error deactivating account: {str(e)}')
            return redirect('dashboard')
            
    except Exception as e:
        messages.error(request, f'An unexpected error occurred: {str(e)}')
        return redirect('dashboard')

def goodbye_page(request):
    try:
        if request.method != 'GET':
            return redirect('home')
            
        return render(request, 'users/goodbye.html')
        
    except Exception as e:
        return redirect('home')

def parse_mk8_times(csv_file, team_id):
    """
    Parse Mario Kart 8 times from CSV file.
    Returns a dictionary with user times for each level.
    """
    times_data = {}
    current_cup = None
    
    try:
        # Read the CSV file
        csv_reader = csv.reader(csv_file)
        
        # Get the header row with usernames
        try:
            header = next(csv_reader)
        except StopIteration:
            raise ValueError("CSV file is empty")
            
        if len(header) < 12:
            raise ValueError("CSV file has invalid format: missing columns")
            
        # Extract and sanitize usernames
        usernames = []
        for name in header[2:12]:
            if name:
                sanitized_name = name.strip()
                if sanitized_name:
                    usernames.append(sanitized_name)
                    
        if not usernames:
            raise ValueError("No valid usernames found in CSV header")
        
        # Process each row
        for row in csv_reader:
            if not row:  # Skip empty rows
                continue
                
            # Check if this is a cup name row
            if row[0] and not row[1]:  # If first column has value and second is empty
                current_cup = row[0].strip()
                continue
                
            # Process level times
            if row[1]:  # If there's a level name
                # Sanitize level name
                level_name = row[1].strip()
                if not level_name:
                    continue
                    
                times_data[level_name] = {}
                
                # Get times for each user
                for i, time_str in enumerate(row[2:12]):
                    if i >= len(usernames):
                        break
                        
                    if time_str:  # If there's a time value
                        username = usernames[i]
                        # Sanitize time string
                        time_str = time_str.strip()
                        if not time_str:
                            continue
                            
                        # Convert time format from 1:44.680 to 01:44.680
                        if ':' in time_str:
                            minutes, rest = time_str.split(':')
                            if len(minutes) == 1:
                                time_str = f"0{minutes}:{rest}"
                                
                        # Validate time format
                        if not re.match(r'^\d{2}:\d{2}\.\d{3}$', time_str):
                            continue
                            
                        times_data[level_name][username] = time_str
        
        if not times_data:
            raise ValueError("No valid times found in CSV file")
            
        return times_data
        
    except csv.Error as e:
        raise ValueError(f"Error parsing CSV file: {str(e)}")
    except Exception as e:
        raise ValueError(f"Unexpected error while parsing CSV: {str(e)}")

@login_required
def upload_times(request, org_id, team_id):
    try:
        # Input validation
        if not org_id or not team_id:
            messages.error(request, 'Invalid organization or team ID.')
            return redirect('dashboard')
            
        # Get team and organization with error handling
        try:
            team = get_object_or_404(Team, id=team_id)
            org = get_object_or_404(Organization, id=org_id)
        except (Team.DoesNotExist, Organization.DoesNotExist):
            messages.error(request, 'Team or organization not found.')
            return redirect('dashboard')
            
        # Check if user is a coach
        try:
            team_user = get_object_or_404(Team_user, team=team_id, user=request.user)
            if not team_user.isCoach:
                messages.error(request, 'You do not have permission to upload times.')
                return redirect('team-details', teamID=team_id)
        except Team_user.DoesNotExist:
            messages.error(request, 'You are not a member of this team.')
            return redirect('dashboard')
        
        if request.method == 'POST':
            try:
                # Validate file upload
                if 'csv_file' not in request.FILES:
                    messages.error(request, 'No file was uploaded.')
                    return redirect('team-details', teamID=team_id)
                    
                csv_file = request.FILES['csv_file']
                if not csv_file.name.endswith('.csv'):
                    messages.error(request, 'Please upload a CSV file.')
                    return redirect('team-details', teamID=team_id)
                    
                # Validate game selection
                game_id = request.POST.get('game')
                if not game_id:
                    messages.error(request, 'Please select a game.')
                    return redirect('team-details', teamID=team_id)
                    
                try:
                    game = Game.objects.get(id=game_id)
                except Game.DoesNotExist:
                    messages.error(request, 'Selected game not found.')
                    return redirect('team-details', teamID=team_id)
                
                # Decode the file content to text
                try:
                    csv_content = csv_file.read().decode('utf-8')
                except UnicodeDecodeError:
                    messages.error(request, 'Invalid file encoding. Please upload a UTF-8 encoded CSV file.')
                    return redirect('team-details', teamID=team_id)
                    
                # Create a StringIO object to simulate a file
                csv_file_obj = StringIO(csv_content)
                
                # Parse the CSV file
                times_data = parse_mk8_times(csv_file_obj, team_id)
                
                # Track skipped users and reasons
                skipped_users = {
                    'not_found': [],
                    'not_in_team': [],
                    'inactive': []
                }
                
                # Process each level's times
                for level_name, user_times in times_data.items():
                    # Sanitize level name
                    level_name = level_name.strip()
                    if not level_name:
                        continue
                        
                    # Get or create the level
                    level, created = Level.objects.get_or_create(
                        level_name=level_name,
                        game=game
                    )
                    
                    # Process each user's time
                    for username, time in user_times.items():
                        # Sanitize username and time
                        username = username.strip()
                        time = time.strip()
                        
                        if not username or not time:
                            continue
                            
                        try:
                            user = User.objects.get(username=username)
                            
                            # Check if user is in the team
                            if not Team_user.objects.filter(team=team, user=user).exists():
                                skipped_users['not_in_team'].append(username)
                                continue
                                
                            # Check if user is active
                            if not user.is_active:
                                skipped_users['inactive'].append(username)
                                continue
                                
                            # Update or create the time record
                            Time.objects.update_or_create(
                                user=user,
                                level=level,
                                defaults={'time': time}
                            )
                            
                        except User.DoesNotExist:
                            skipped_users['not_found'].append(username)
                            continue
                
                # Prepare success message with skipped users summary
                success_message = 'Times have been successfully uploaded and processed.'
                
                if skipped_users['not_found']:
                    success_message += f" Skipped {len(skipped_users['not_found'])} users not found in the system: {', '.join(skipped_users['not_found'])}."
                    
                if skipped_users['not_in_team']:
                    success_message += f" Skipped {len(skipped_users['not_in_team'])} users not in the team: {', '.join(skipped_users['not_in_team'])}."
                    
                if skipped_users['inactive']:
                    success_message += f" Skipped {len(skipped_users['inactive'])} inactive users: {', '.join(skipped_users['inactive'])}."
                
                messages.success(request, success_message)
                
            except Exception as e:
                messages.error(request, f'Error processing the file: {str(e)}')
                
            return redirect('team-details', teamID=team_id)
        
        # GET request - show the upload form
        team_games = Team_game.objects.filter(team=team)
        
        return render(request, 'time/upload_times.html', {
            'team': team,
            'team_games': team_games,
            'org_id': org_id
        })
        
    except Exception as e:
        messages.error(request, f'An unexpected error occurred: {str(e)}')
        return redirect('dashboard')

# Demote coach to regular player
@login_required
def demote_coach(request, teamID, userID):
    # Get the current user's team_user object
    current_team_user = get_object_or_404(Team_user, team=teamID, user=request.user)
    
    # Check if the current user is a coach
    if not current_team_user.isCoach:
        return HttpResponse('You are not allowed to do that', status=403)
    
    # Get the team user to demote
    team_user_to_demote = get_object_or_404(Team_user, team=teamID, user=userID)
    
    # Prevent self-demotion
    if team_user_to_demote.user == request.user:
        messages.error(request, 'You cannot demote yourself.')
        return redirect('team-details', teamID=teamID)
    
    # Demote the coach
    team_user_to_demote.isCoach = False
    team_user_to_demote.save()
    
    messages.success(request, f'{team_user_to_demote.user.username} has been demoted to a regular player.')
    return redirect('team-details', teamID=teamID)

# Remove team member
@login_required
def remove_team_member(request, teamID, userID):
    # Get the current user's team_user object
    current_team_user = get_object_or_404(Team_user, team=teamID, user=request.user)
    
    # Check if the current user is a coach
    if not current_team_user.isCoach:
        return HttpResponse('You are not allowed to do that', status=403)
    
    # Get the team user to remove
    team_user_to_remove = get_object_or_404(Team_user, team=teamID, user=userID)
    
    # Prevent self-removal
    if team_user_to_remove.user == request.user:
        messages.error(request, 'You cannot remove yourself from the team.')
        return redirect('team-details', teamID=teamID)
    
    # Remove the team user
    team_user_to_remove.delete()
    
    messages.success(request, f'{team_user_to_remove.user.username} has been removed from the team.')
    return redirect('team-details', teamID=teamID)

# Remove coach
@login_required
def remove_coach(request, teamID, userID):
    # Get the current user's team_user object
    current_team_user = get_object_or_404(Team_user, team=teamID, user=request.user)
    
    # Check if the current user is a coach
    if not current_team_user.isCoach:
        return HttpResponse('You are not allowed to do that', status=403)
    
    # Get the team user to remove
    team_user_to_remove = get_object_or_404(Team_user, team=teamID, user=userID)
    
    # Prevent self-removal
    if team_user_to_remove.user == request.user:
        messages.error(request, 'You cannot remove yourself from the team.')
        return redirect('team-details', teamID=teamID)
    
    # Remove the team user
    team_user_to_remove.delete()
    
    messages.success(request, f'{team_user_to_remove.user.username} has been removed from the team.')
    return redirect('team-details', teamID=teamID)

@login_required
def suggest_game(request):
    if request.method == 'POST':
        form = GameSuggestionForm(request.POST)
        if form.is_valid():
            suggestion = form.save(commit=False)
            suggestion.suggested_by = request.user
            suggestion.save()
            messages.success(request, 'Game suggestion submitted successfully!')
            return redirect('dashboard')
    else:
        form = GameSuggestionForm()
    
    return render(request, 'estt_main_app/suggest_game.html', {'form': form})

@staff_member_required
def manage_game_suggestions(request):
    search_query = request.GET.get('search', '')
    suggestions = GameSuggestion.objects.all().order_by('-created_at')
    
    if search_query:
        suggestions = suggestions.filter(game_name__icontains=search_query)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_suggestion':
            suggestion_id = request.POST.get('suggestion_id')
            try:
                suggestion = GameSuggestion.objects.get(id=suggestion_id)
                # Create new game from suggestion
                Game.objects.create(game=suggestion.game_name)
                suggestion.delete()
                messages.success(request, f'Game "{suggestion.game_name}" has been added successfully!')
            except GameSuggestion.DoesNotExist:
                messages.error(request, 'Selected suggestion not found.')
            except Exception as e:
                messages.error(request, f'Error adding game: {str(e)}')
                
        elif action == 'add_custom':
            game_name = request.POST.get('game_name', '').strip()
            if game_name:
                try:
                    Game.objects.create(game=game_name)
                    messages.success(request, f'Game "{game_name}" has been added successfully!')
                except Exception as e:
                    messages.error(request, f'Error adding game: {str(e)}')
            else:
                messages.error(request, 'Please enter a game name.')
                
        elif action == 'delete_suggestion':
            suggestion_id = request.POST.get('suggestion_id')
            try:
                suggestion = GameSuggestion.objects.get(id=suggestion_id)
                suggestion.delete()
                messages.success(request, f'Suggestion "{suggestion.game_name}" has been deleted.')
            except GameSuggestion.DoesNotExist:
                messages.error(request, 'Selected suggestion not found.')
            except Exception as e:
                messages.error(request, f'Error deleting suggestion: {str(e)}')
    
    return render(request, 'admin/manage_game_suggestions.html', {
        'suggestions': suggestions,
        'search_query': search_query
    })

@login_required
def view_target_times(request, team_id, game_id):
    try:
        # Get team and game
        team = get_object_or_404(Team, id=team_id)
        game = get_object_or_404(Game, id=game_id)
        
        # Check if user is a team member
        try:
            team_user = Team_user.objects.get(team=team, user=request.user)
        except Team_user.DoesNotExist:
            messages.error(request, 'You are not a member of this team.')
            return redirect('dashboard')
        
        # Get target times for this team and game
        target_times = Target_times.objects.filter(
            team=team,
            level__game=game
        ).select_related('level').order_by('level__level_name')
        
        context = {
            'team': team,
            'game': game,
            'target_times': target_times,
        }
        
        return render(request, 'target_time/view_tt.html', context)
        
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('team-details', teamID=team_id)

@login_required
def get_target_times(request, team_id, game_id):
    try:
        # Verify team membership
        team = get_object_or_404(Team, id=team_id)
        try:
            Team_user.objects.get(team=team, user=request.user)
        except Team_user.DoesNotExist:
            return JsonResponse({'error': 'Not a team member'}, status=403)
            
        # Get target times for this team and game with level information
        target_times = Target_times.objects.filter(
            team=team,
            level__game_id=game_id
        ).select_related('level').values(
            'level_id',
            'level__level_name',
            'high_target',
            'low_target'
        )
        
        # Convert to list and format the data
        formatted_times = []
        for tt in target_times:
            formatted_times.append({
                'level': tt['level_id'],
                'level_name': tt['level__level_name'],
                'high_target': tt['high_target'],
                'low_target': tt['low_target']
            })
        
        return JsonResponse(formatted_times, safe=False)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def compare_times(request, team_id, game_id):
    team = get_object_or_404(Team, id=team_id)
    game = get_object_or_404(Game, id=game_id)
    
    # Check if user is a member of the team
    team_user = Team_user.objects.filter(team=team, user=request.user).first()
    if not team_user:
        return redirect('home')
    
    context = {
        'team': team,
        'game': game,
    }
    return render(request, 'time/compare_times.html', context)

@login_required
def get_compare_data(request):
    try:
        game_id = request.GET.get('game_id')
        team_id = request.GET.get('team_id')
        
        if not game_id or not team_id:
            return JsonResponse({'error': 'Missing game_id or team_id'}, status=400)
            
        try:
            game_id = int(game_id)
            team_id = int(team_id)
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Invalid game_id or team_id format'}, status=400)
        
        # Get team members
        team_members = Team_user.objects.filter(
            team_id=team_id,
            isCoach=False  # Only get non-coach members
        ).select_related('user')
        if not team_members.exists():
            return JsonResponse({'error': 'No team members found'}, status=404)
            
        members = [{'id': member.user.id, 'username': member.user.username} for member in team_members]
        
        # Get game levels
        levels = Level.objects.filter(game_id=game_id).values('id', 'level_name')
        if not levels.exists():
            return JsonResponse({'error': 'No levels found for this game'}, status=404)
        
        # Get all times for this game and team
        times = {}
        member_times = Time.objects.filter(
            level__game_id=game_id,
            user__in=[member.user for member in team_members]
        ).select_related('user', 'level')
        
        for time in member_times:
            key = f"{time.level.id}-{time.user.id}"
            times[key] = time.time

        # Get target times
        target_times = Target_times.objects.filter(
            team_id=team_id,
            level__game_id=game_id
        ).select_related('level')

        # Add special "members" for high and low targets
        members.extend([
            {'id': 'high_target', 'username': 'High Target'},
            {'id': 'low_target', 'username': 'Low Target'}
        ])

        # Add target times to times dictionary
        for target in target_times:
            times[f"{target.level.id}-high_target"] = target.high_target
            times[f"{target.level.id}-low_target"] = target.low_target
        
        # Create member names mapping
        member_names = {member.user.id: member.user.username for member in team_members}
        member_names.update({
            'high_target': 'High Target',
            'low_target': 'Low Target'
        })
        
        return JsonResponse({
            'members': members,
            'levels': list(levels),
            'times': times,
            'member_names': member_names
        })
        
    except Exception as e:
        import traceback
        print(f"Error in get_compare_data: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({'error': str(e)}, status=500)