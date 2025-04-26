from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from django.contrib.admin.views.decorators import staff_member_required
from .models import Team_user, Team, Team_game, Game, Level, Time, Organization, Org_user, Org_join_code, Org_team, GameSuggestion, Target_times, Diamond_times, Org_leader
from django.views.generic.edit import CreateView, UpdateView
from .forms import (
    CustomUserCreationForm, TeamUserForm, EditProfileForm, NewTeamForm,
    AddTeamUserOnTeamCreationForm, TeamGameForm, TimeCreationForm, TimeUpdateForm,
    TargetTimesCreationForm, NewOrganizationForm, AddOrgUserOnOrgCreationForm,
    CreateOrgJoinCode, GameSuggestionForm, CreateOrgForm, CreateOrgUserForm, JoinOrgForm
)
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
import logging

logger = logging.getLogger(__name__)

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
    try:
        team = get_object_or_404(Team, id=teamID)    
        members = Team_user.objects.filter(team=teamID)
        games = Team_game.objects.filter(team=teamID)
        user_org = Org_user.objects.filter(user=request.user).first()
        
        # Check if user is a member of the team
        team_user = Team_user.objects.filter(team=teamID, user=request.user).first()
        if not team_user:
            messages.error(request, 'You are not a member of this team.')
            return redirect('dashboard')
        
        if user_org:
            # Check if the team belongs to the user's organization
            team_in_org = Org_team.objects.filter(team=team, org=user_org.org).exists()
            if not team_in_org:
                messages.error(request, 'You can only view teams in your organization.')
                return redirect('org-details')
        else:
            messages.error(request, 'You must be part of an organization to view team details.')
            return redirect('org-details')

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
            'org': user_org.org if user_org else None
        })
        
    except Exception as e:
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('dashboard')

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
        # Get user's organization first
        org_user = Org_user.objects.filter(user=request.user).first()
        if not org_user:
            messages.error(request, 'You must be a member of an organization to create a team.')
            return redirect('dashboard')

        if request.method == 'POST':
            # Check if user is an organization leader
            is_org_leader = Org_leader.objects.filter(user=request.user, org=org_user.org).exists()
            if not is_org_leader:
                form_one = NewTeamForm()
                form_two = AddTeamUserOnTeamCreationForm()
                return render(request, 'team/new_team.html', {
                    'form_one': form_one,
                    'form_two': form_two,
                    'error_message': 'Only organization leaders can create teams.'
                })

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
                try:
                    # Create the team
                    new_team = form_one.save(commit=False)
                    new_team.save()
                    
                    # Create the team user (coach)
                    team_user = form_two.save(commit=False)
                    team_user.team = new_team
                    team_user.user = request.user
                    team_user.isCoach = True
                    team_user.save()
                    
                    # Create the org_team record
                    Org_team.objects.create(
                        team=new_team,
                        org=org_user.org
                    )
                    
                    messages.success(request, 'Team created successfully!')
                    return redirect('dashboard')
                except Exception as e:
                    # If anything fails, delete the team to maintain consistency
                    if new_team.id:
                        new_team.delete()
                    messages.error(request, f'Error creating team: {str(e)}')
                    return render(request, 'team/new_team.html', {
                        'form_one': form_one,
                        'form_two': form_two,
                        'error_message': 'Error creating team. Please try again.'
                    })
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
        messages.error(request, f'An unexpected error occurred: {str(e)}')
        return redirect('dashboard')

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
        team_id = request.GET.get('team_id')  # Add team_id parameter
        
        if not game_id or not team_id:
            return JsonResponse({"error": "Game ID and Team ID are required"}, status=400)
            
        try:
            game_id = int(game_id)
            team_id = int(team_id)
        except (TypeError, ValueError):
            return JsonResponse({"error": "Invalid game ID or team ID format"}, status=400)
        
        # Get team game and game with error handling
        try:
            # Get the team game for this specific game and team
            team_game = Team_game.objects.filter(game=game_id, team=team_id).first()
            if not team_game:
                return JsonResponse({"error": "Game not found for this team"}, status=404)
                
            game = get_object_or_404(Game, id=game_id)
        except Game.DoesNotExist:
            return JsonResponse({"error": "Game not found"}, status=404)
            
        # Get team members
        team_members = Team_user.objects.filter(
            team_id=team_id,  # Use the team_id parameter
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
            'team_id': team_id
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
def create_target_times(request, teamID):
    try:
        logger.info(f"Starting target times creation for team {teamID} by user {request.user.username}")
        # Get team
        team = get_object_or_404(Team, id=teamID)
        
        # Check if user is a member of the team
        team_user = Team_user.objects.filter(team=team, user=request.user).first()
        if not team_user:
            logger.warning(f"User {request.user.username} attempted to create target times but is not a team member")
            messages.error(request, 'You are not a member of this team.')
            return redirect('team-details', teamID=teamID)
            
        # Check if user is a coach
        if not team_user.isCoach:
            logger.warning(f"User {request.user.username} attempted to create target times but is not a coach")
            messages.error(request, 'Only coaches can create target times.')
            return redirect('team-details', teamID=teamID)
        
        # Get all games for this team
        team_games = Team_game.objects.filter(team=team).select_related('game')
        logger.info(f"Retrieved {team_games.count()} games for team {teamID}")
        
        if request.method == 'POST':
            form_type = request.POST.get('form_type')
            
            if form_type == 'single':
                logger.info(f"Processing single target time creation by {request.user.username}")
                form = TargetTimesCreationForm(request.POST, team_id=teamID, game_id=request.POST.get('game'))
                if form.is_valid():
                    game = form.cleaned_data['game']
                    level = form.cleaned_data['level']
                    high_target = form.cleaned_data['high_target']
                    low_target = form.cleaned_data['low_target']
                    
                    logger.info(f"Creating target times for game {game.game}, level {level.level_name}")
                    logger.info(f"High target: {high_target}, Low target: {low_target}")
                    
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
                        logger.info(f"Updating existing target times for level {level.level_name}")
                        target_time.high_target = high_target
                        target_time.low_target = low_target
                        target_time.save()
                    
                    logger.info("Target times created/updated successfully")
                    messages.success(request, 'Target times created successfully.')
                    return redirect('view-target-times', teamID=teamID, game_id=game.id)
                else:
                    logger.warning(f"Invalid form submission: {form.errors}")
                    messages.error(request, 'Please correct the errors below.')
            
            elif form_type == 'csv':
                logger.info(f"Processing CSV upload by {request.user.username}")
                csv_file = request.FILES.get('csv_file')
                game_id = request.POST.get('game')
                
                if not csv_file:
                    logger.error("No CSV file was uploaded")
                    messages.error(request, "No CSV file was uploaded.")
                    return redirect('create-target-times', teamID=teamID)
                    
                if not game_id:
                    logger.error("No game was selected for target times upload")
                    messages.error(request, "No game was selected.")
                    return redirect('create-target-times', teamID=teamID)
                    
                try:
                    game = Game.objects.get(id=game_id)
                    logger.info(f"Selected game: {game.game}")
                except Game.DoesNotExist:
                    logger.error(f"Invalid game ID {game_id} selected for target times upload")
                    messages.error(request, "Invalid game selected.")
                    return redirect('create-target-times', teamID=teamID)
                
                # Process CSV file
                try:
                    logger.info("Starting CSV processing for target times")
                    csv_reader = csv.reader(csv_file.read().decode('utf-8').splitlines())
                    empty_lines = []
                    upload_errors = []
                    skipped_levels = []  # Track levels that don't exist
                    
                    for line_num, row in enumerate(csv_reader, start=1):
                        if not row or all(not cell.strip() for cell in row):
                            empty_lines.append(line_num)
                            continue
                            
                        if len(row) < 3:
                            upload_errors.append({
                                'line': line_num,
                                'error': 'Invalid format. Expected: Level Name, High Target Time, Low Target Time'
                            })
                            continue
                            
                        level_name = row[0].strip()
                        high_target = row[1].strip()
                        low_target = row[2].strip()
                        
                        if not level_name or not high_target or not low_target:
                            upload_errors.append({
                                'line': line_num,
                                'error': 'Missing required values'
                            })
                            continue
                            
                        try:
                            # Only use existing levels
                            try:
                                level = Level.objects.get(level_name=level_name, game=game)
                            except Level.DoesNotExist:
                                skipped_levels.append(level_name)
                                continue
                            
                            # Create or update target times
                            target_time_obj, created = Target_times.objects.get_or_create(
                                level=level,
                                team=team,
                                defaults={
                                    'high_target': high_target,
                                    'low_target': low_target
                                }
                            )
                            
                            if not created:
                                target_time_obj.high_target = high_target
                                target_time_obj.low_target = low_target
                                target_time_obj.save()
                                
                        except Exception as e:
                            upload_errors.append({
                                'line': line_num,
                                'error': str(e)
                            })
                            continue
                    
                    if upload_errors or empty_lines or skipped_levels:
                        logger.warning(f"CSV processing completed with {len(upload_errors)} errors, {len(empty_lines)} empty lines, and {len(skipped_levels)} skipped levels")
                        return render(request, 'target_time/add_tt.html', {
                            'team': team,
                            'team_games': team_games,
                            'upload_errors': upload_errors,
                            'empty_lines': empty_lines,
                            'skipped_levels': skipped_levels
                        })
                    
                    logger.info("CSV processing completed successfully")
                    messages.success(request, "Target times uploaded successfully.")
                    return redirect('view-target-times', teamID=teamID, game_id=game_id)
                    
                except Exception as e:
                    logger.error(f"Error processing CSV file: {str(e)}", exc_info=True)
                    messages.error(request, f"Error processing CSV file: {str(e)}")
                    return redirect('create-target-times', teamID=teamID)
            
            else:
                logger.warning("Invalid form type submitted")
                messages.error(request, 'Invalid form submission.')
                return redirect('create-target-times', teamID=teamID)
        
        # Initialize form with team_id and game_id from GET parameters
        game_id = request.GET.get('game_id')
        form = TargetTimesCreationForm(team_id=teamID, game_id=game_id)
        
        return render(request, 'target_time/add_tt.html', {
            'form': form,
            'team': team,
            'team_games': team_games
        })
        
    except Team.DoesNotExist:
        logger.error(f"Team {teamID} not found for target times creation")
        messages.error(request, 'Team not found.')
        return redirect('dashboard')
    except Exception as e:
        logger.error(f"Unexpected error in create_target_times: {str(e)}", exc_info=True)
        messages.error(request, f'An error occurred: {str(e)}')
        return render(request, 'target_time/add_tt.html', {
            'form': TargetTimesCreationForm(team_id=teamID),
            'team': team,
            'team_games': team_games,
            'error_message': str(e)
        })

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
            # Check if user is already in an organization
            existing_org_user = Org_user.objects.filter(user=request.user).first()
            if existing_org_user:
                org_name = existing_org_user.org.name
                return render(request, 'organization/new_org.html', {
                    'form_one': NewOrganizationForm(),
                    'form_two': AddOrgUserOnOrgCreationForm(),
                    'error_message': f'You are currently a member of {org_name}. You must leave your current organization before creating or joining another one.'
                })

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
                
                # Create organization leader
                try:
                    Org_leader.objects.create(
                        user=request.user,
                        org=new_org
                    )
                except Exception as e:
                    # Rollback organization and user creation if leader creation fails
                    new_org.delete()
                    return render(request, 'organization/new_org.html', {
                        'form_one': form_one,
                        'form_two': form_two,
                        'error_message': f'Error creating organization leader: {str(e)}'
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
            'warning_message': 'Note: You can only be a member of one organization at a time. If you are currently in an organization, you must leave it before creating or joining another one.'
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
        print(f"[DEBUG] Starting join_codes view with org_id: {org_id}")
        
        # Validate organization ID
        if not org_id:
            print("[DEBUG] No org_id provided")
            messages.error(request, 'Organization ID is required.')
            return redirect('dashboard')
            
        try:
            org_id = int(org_id)
            print(f"[DEBUG] Converted org_id to int: {org_id}")
        except (TypeError, ValueError):
            print("[DEBUG] Invalid org_id format")
            messages.error(request, 'Invalid organization ID format.')
            return redirect('dashboard')
        
        # Get organization with error handling
        try:
            org = get_object_or_404(Organization, id=org_id)
            print(f"[DEBUG] Found organization: {org.name}")
        except Organization.DoesNotExist:
            print("[DEBUG] Organization not found")
            messages.error(request, 'Organization not found.')
            return redirect('dashboard')
            
        # Check if user is a member of the organization
        try:
            org_user = get_object_or_404(Org_user, org=org, user=request.user)
            print(f"[DEBUG] Found org_user for {request.user.username}")
        except Org_user.DoesNotExist:
            print(f"[DEBUG] User {request.user.username} is not a member of org {org.name}")
            messages.error(request, 'You are not a member of this organization.')
            return redirect('dashboard')
        
        # First get all teams the user is a member of
        user_teams = Team.objects.filter(team_user__user=request.user)
        print(f"[DEBUG] Found {user_teams.count()} teams for user")
        
        # Then check which of these teams belong to the organization
        team = None
        for user_team in user_teams:
            if Org_team.objects.filter(team=user_team, org=org).exists():
                team = user_team
                break
                
        print(f"[DEBUG] Team found in organization: {team}")
        
        if not team:
            print(f"[DEBUG] No team found for user {request.user.username} in org {org.name}")
            messages.error(request, 'You are not a member of any team in this organization.')
            return redirect('dashboard')
        
        # Get join code if it exists
        code = Org_join_code.objects.filter(org=org).first()
        print(f"[DEBUG] Join code query result: {code}")
            
        # Always render the template, whether code exists or not
        print("[DEBUG] Rendering template with code, org, and team")
        return render(request, 'organization/org_code_generator.html', {
            'code': code,
            'org': org,
            'team': team
        })
            
    except Exception as e:
        print(f"[DEBUG] Unexpected error: {str(e)}")
        print(f"[DEBUG] Full error details: ", e.__class__.__name__)
        import traceback
        print("[DEBUG] Traceback: ", traceback.format_exc())
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
    Returns a dictionary with user times for each level and a list of any errors encountered.
    """
    times_data = {}
    current_cup = None
    empty_lines = []
    errors = []
    
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
        for row_num, row in enumerate(csv_reader, start=2):
            # Check for empty lines
            if not row or all(not cell.strip() for cell in row):
                empty_lines.append(row_num)
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
                    errors.append({
                        'line': row_num,
                        'error': 'Empty level name'
                    })
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
                            errors.append({
                                'line': row_num,
                                'error': f'Invalid time format for user {username}: {time_str}'
                            })
                            continue
                            
                        times_data[level_name][username] = time_str
        
        if not times_data:
            raise ValueError("No valid times found in CSV file")
            
        return times_data, empty_lines, errors
        
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
                times_data, empty_lines, parse_errors = parse_mk8_times(csv_file_obj, team_id)
                
                # Track skipped users and reasons
                skipped_users = {
                    'not_found': [],
                    'not_in_team': [],
                    'inactive': []
                }
                skipped_levels = []  # Track levels that don't exist

                # Process each level's times
                for level_name, user_times in times_data.items():
                    # Sanitize level name
                    level_name = level_name.strip()
                    if not level_name:
                        continue
                        
                    # Only use existing levels
                    try:
                        level = Level.objects.get(level_name=level_name, game=game)
                    except Level.DoesNotExist:
                        skipped_levels.append(level_name)
                        continue
                    
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
                
                context = {
                    'team': team,
                    'team_games': Team_game.objects.filter(team=team),
                    'org_id': org_id,
                    'empty_lines': empty_lines,
                    'parse_errors': parse_errors,
                    'skipped_users': skipped_users,
                    'skipped_levels': skipped_levels
                }
                
                if empty_lines or parse_errors or any(skipped_users.values()) or skipped_levels:
                    return render(request, 'time/upload_times.html', context)
                
                messages.success(request, 'Times have been successfully uploaded and processed.')
                return redirect('team-details', teamID=team_id)
                
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
def view_target_times(request, teamID, game_id=None):
    try:
        logger.info(f"Starting view_target_times for team {teamID}, game {game_id} by user {request.user.username}")
        
        # Get team
        team = get_object_or_404(Team, id=teamID)
        logger.info(f"Found team: {team.name}")
        
        # Check if user is a team member
        try:
            team_user = Team_user.objects.get(team=team, user=request.user)
            logger.info(f"User {request.user.username} is a member of team {team.name}")
        except Team_user.DoesNotExist:
            logger.warning(f"User {request.user.username} attempted to view target times but is not a member of team {team.name}")
            messages.error(request, 'You are not a member of this team.')
            return redirect('dashboard')
            
        # Get all games for this team
        team_games = Team_game.objects.filter(team=team).select_related('game')
        logger.info(f"Found {team_games.count()} games for team {team.name}")
        
        # If no game_id provided, use the first game
        if not game_id and team_games.exists():
            first_game = team_games.first().game
            logger.info(f"No game_id provided, redirecting to first game: {first_game.game}")
            return redirect('view-target-times', teamID=teamID, game_id=first_game.id)
        elif not game_id:
            logger.warning(f"No game_id provided and no games exist for team {team.name}")
            messages.error(request, 'No games available for this team.')
            return redirect('team-details', teamID=teamID)
            
        # Get the selected game
        try:
            game = Game.objects.get(id=game_id)
            team_game = Team_game.objects.get(team=team, game=game)
            logger.info(f"Found selected game: {game.game}")
        except Game.DoesNotExist:
            logger.error(f"Invalid game_id {game_id} selected for team {team.name}")
            messages.error(request, 'Invalid game selected.')
            if team_games.exists():
                first_game = team_games.first().game
                logger.info(f"Redirecting to first available game: {first_game.game}")
                return redirect('view-target-times', teamID=teamID, game_id=first_game.id)
            return redirect('team-details', teamID=teamID)
        except Team_game.DoesNotExist:
            logger.error(f"Game {game_id} exists but is not associated with team {team.name}")
            messages.error(request, 'This game is not available for your team.')
            if team_games.exists():
                first_game = team_games.first().game
                logger.info(f"Redirecting to first available game: {first_game.game}")
                return redirect('view-target-times', teamID=teamID, game_id=first_game.id)
            return redirect('team-details', teamID=teamID)
            
        # Get all levels for the game
        levels = Level.objects.filter(game=game).order_by('level_name')
        logger.info(f"Found {levels.count()} levels for game {game.game}")
        
        # Get target times for each level
        target_times = {}
        diamond_times = {}
        for level in levels:
            try:
                target_time = Target_times.objects.get(team=team, level=level)
                target_times[level.id] = {
                    'high_target': target_time.high_target,
                    'low_target': target_time.low_target
                }
            except Target_times.DoesNotExist:
                target_times[level.id] = {
                    'high_target': None,
                    'low_target': None
                }
                
            try:
                diamond_time = Diamond_times.objects.get(team=team, level=level)
                diamond_times[level.id] = diamond_time.diamond_target
            except Diamond_times.DoesNotExist:
                diamond_times[level.id] = None
                
        context = {
            'team': team,
            'game': game,
            'team_games': team_games,
            'levels': levels,
            'target_times': target_times,
            'diamond_times': diamond_times,
            'is_coach': team_user.isCoach
        }
        
        logger.info(f"Rendering view_target_times template for team {team.name}, game {game.game}")
        return render(request, 'target_time/view_target_times.html', context)
        
    except Exception as e:
        logger.error(f"Unexpected error in view_target_times: {str(e)}", exc_info=True)
        messages.error(request, f'An error occurred: {str(e)}')
        return redirect('team-details', teamID=teamID)

@login_required
def get_target_times(request, teamID, game_id):
    try:
        # Verify team membership
        team = get_object_or_404(Team, id=teamID)
        try:
            team_user = Team_user.objects.get(team=team, user=request.user)
        except Team_user.DoesNotExist:
            return JsonResponse({'error': 'Not a team member'}, status=403)
            
        # Get all levels for this game
        levels = Level.objects.filter(game_id=game_id).values('id', 'level_name')
        
        # Get target times as a dictionary for easy lookup
        target_times = {
            tt['level_id']: tt 
            for tt in Target_times.objects.filter(
                team=team,
                level__game_id=game_id
            ).values('level_id', 'high_target', 'low_target')
        }
        
        # Get diamond times for all team members
        diamond_times = {
            dt['level_id']: dt['diamond_target'] 
            for dt in Diamond_times.objects.filter(
                team=team,
                level__game_id=game_id
            ).values('level_id', 'diamond_target')
        }
        
        # Convert to list and format the data for all levels
        formatted_times = []
        for level in levels:
            level_id = level['id']
            target_time = target_times.get(level_id, {})
            formatted_times.append({
                'level': level_id,
                'level_name': level['level_name'],
                'high_target': target_time.get('high_target', '-'),
                'low_target': target_time.get('low_target', '-'),
                'diamond_target': diamond_times.get(level_id, '-')  # Show diamond times to all team members
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

@login_required
def upload_diamond_times(request, teamID):
    try:
        logger.info(f"Starting diamond times upload for team {teamID} by user {request.user.username}")
        team = Team.objects.get(id=teamID)
        
        # Check if user is a member of the team
        team_user = Team_user.objects.filter(team=team, user=request.user).first()
        if not team_user:
            logger.warning(f"User {request.user.username} attempted to upload diamond times but is not a team member")
            messages.error(request, "You are not a member of this team.")
            return redirect('dashboard')
            
        if not team_user.isCoach:
            logger.warning(f"User {request.user.username} attempted to upload diamond times but is not a coach")
            messages.error(request, "Only coaches can upload diamond times.")
            return redirect('view-target-times', team_id=teamID)
            
        if request.method == 'POST':
            logger.info(f"Processing POST request for diamond times upload by {request.user.username}")
            csv_file = request.FILES.get('csv_file')
            if not csv_file:
                logger.error("No CSV file was uploaded")
                messages.error(request, "No CSV file was uploaded.")
                return redirect('upload-diamond-times', teamID=teamID)
                
            game_id = request.POST.get('game')
            if not game_id:
                logger.error("No game was selected for diamond times upload")
                messages.error(request, "No game was selected.")
                return redirect('upload-diamond-times', teamID=teamID)
                
            try:
                game = Game.objects.get(id=game_id)
                logger.info(f"Selected game: {game.game}")
            except Game.DoesNotExist:
                logger.error(f"Invalid game ID {game_id} selected for diamond times upload")
                messages.error(request, "Invalid game selected.")
                return redirect('upload-diamond-times', teamID=teamID)
                
            # Process CSV file
            try:
                logger.info("Starting CSV processing for diamond times")
                csv_reader = csv.reader(csv_file.read().decode('utf-8').splitlines())
                empty_lines = []
                upload_errors = []
                skipped_levels = []  # Track levels that don't exist
                
                for line_num, row in enumerate(csv_reader, start=1):
                    if not row or all(not cell.strip() for cell in row):
                        empty_lines.append(line_num)
                        continue
                        
                    if len(row) < 2:
                        upload_errors.append({
                            'line': line_num,
                            'error': 'Invalid format. Expected: Level Name, Diamond Time (MM:SS.mmm)'
                        })
                        continue
                        
                    level_name = row[0].strip()
                    diamond_time = row[1].strip()
                    
                    if not level_name or not diamond_time:
                        upload_errors.append({
                            'line': line_num,
                            'error': 'Missing required values'
                        })
                        continue
                        
                    try:
                        # Only use existing levels
                        try:
                            level = Level.objects.get(level_name=level_name, game=game)
                        except Level.DoesNotExist:
                            skipped_levels.append(level_name)
                            continue
                        
                        # Create or update diamond time
                        diamond_time_obj, created = Diamond_times.objects.get_or_create(
                            level=level,
                            team=team,
                            defaults={
                                'diamond_target': diamond_time
                            }
                        )
                        
                        if not created:
                            logger.info(f"Updating existing diamond time for level {level.level_name}")
                            diamond_time_obj.diamond_target = diamond_time
                            diamond_time_obj.save()
                            
                    except Exception as e:
                        upload_errors.append({
                            'line': line_num,
                            'error': str(e)
                        })
                        continue
                
                if upload_errors or empty_lines or skipped_levels:
                    logger.warning(f"CSV processing completed with {len(upload_errors)} errors, {len(empty_lines)} empty lines, and {len(skipped_levels)} skipped levels")
                    return render(request, 'target_time/upload_diamond_times.html', {
                        'team': team,
                        'team_games': Team_game.objects.filter(team=team).select_related('game'),
                        'upload_errors': upload_errors,
                        'empty_lines': empty_lines,
                        'skipped_levels': skipped_levels
                    })
                
                logger.info("CSV processing completed successfully")
                messages.success(request, "Diamond times uploaded successfully.")
                return redirect('view-target-times', teamID=teamID, game_id=game_id)
                
            except Exception as e:
                logger.error(f"Error processing CSV file: {str(e)}", exc_info=True)
                messages.error(request, f"Error processing CSV file: {str(e)}")
                return redirect('upload-diamond-times', teamID=teamID)
                
        # Get all games for the team
        team_games = Team_game.objects.filter(team=team).select_related('game')
        logger.info(f"Retrieved {team_games.count()} games for team {teamID}")
        
        context = {
            'team': team,
            'team_games': team_games,
        }
        return render(request, 'target_time/upload_diamond_times.html', context)
    except Team.DoesNotExist:
        logger.error(f"Team {teamID} not found for diamond times upload")
        messages.error(request, "Team not found.")
        return redirect('dashboard')
    except Exception as e:
        logger.error(f"Unexpected error in upload_diamond_times: {str(e)}", exc_info=True)
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('dashboard')

@login_required
def delete_target_times(request, teamID, game_id, level_id):
    try:
        # Get team and verify user is a coach
        team = get_object_or_404(Team, id=teamID)
        team_user = get_object_or_404(Team_user, team=team, user=request.user)
        
        if not team_user.isCoach:
            messages.error(request, 'Only coaches can delete target times.')
            return redirect('view-target-times', teamID=teamID, game_id=game_id)
            
        # Delete the target times
        target_time = get_object_or_404(Target_times, team=team, level_id=level_id)
        target_time.delete()
        
        messages.success(request, 'Target times deleted successfully.')
        
    except Exception as e:
        messages.error(request, f'Error deleting target times: {str(e)}')
        
    return redirect('view-target-times', teamID=teamID, game_id=game_id)

@login_required
def delete_diamond_times(request, teamID, game_id, level_id):
    try:
        # Get team and verify user is a coach
        team = get_object_or_404(Team, id=teamID)
        team_user = get_object_or_404(Team_user, team=team, user=request.user)
        
        if not team_user.isCoach:
            messages.error(request, 'Only coaches can delete diamond times.')
            return redirect('view-target-times', teamID=teamID, game_id=game_id)
            
        # Delete the diamond time
        diamond_time = get_object_or_404(Diamond_times, team=team, level_id=level_id)
        diamond_time.delete()
        
        messages.success(request, 'Diamond time deleted successfully.')
        
    except Exception as e:
        messages.error(request, f'Error deleting diamond time: {str(e)}')
        
    return redirect('view-target-times', teamID=teamID, game_id=game_id)

@login_required
def org_details(request):
    try:
        # Get user's organization membership
        org_user = Org_user.objects.filter(user=request.user).first()
        org = None
        org_leader = None
        teams = None
        user_teams = set()
        is_coach = False
        
        if org_user:
            org = org_user.org
            org_leader = Org_leader.objects.filter(org=org).first()
            # Get all teams in the organization
            teams = Team.objects.filter(org_team__org=org)
            # Get the teams the user is a member of
            user_teams = set(Team.objects.filter(
                org_team__org=org,
                team_user__user=request.user
            ).values_list('id', flat=True))
            # Check if user is a coach in any team
            is_coach = Team_user.objects.filter(
                team__org_team__org=org,
                user=request.user,
                isCoach=True
            ).exists()
        
        return render(request, 'organization/org_details.html', {
            'org': org,
            'org_user': org_user,
            'org_leader': org_leader,
            'teams': teams,
            'user_teams': user_teams,
            'is_coach': is_coach
        })
    except Exception as e:
        messages.error(request, f'An unexpected error occurred: {str(e)}')
        return redirect('dashboard')

@login_required
def leave_org(request):
    try:
        if request.method != 'POST':
            return redirect('org-details')
            
        # Get user's organization membership
        org_user = Org_user.objects.filter(user=request.user).first()
        if not org_user:
            messages.error(request, 'You are not a member of any organization.')
            return redirect('org-details')
            
        # Check if user is the organization leader
        is_leader = Org_leader.objects.filter(user=request.user, org=org_user.org).exists()
        
        if is_leader:
            # Get all organization members
            org_members = Org_user.objects.filter(org=org_user.org).exclude(user=request.user)
            
            if org_members.exists():
                # If there are other members, require a replacement leader
                if 'new_leader_id' not in request.POST:
                    # Get all potential new leaders (other members)
                    potential_leaders = org_members.select_related('user')
                    return render(request, 'organization/select_new_leader.html', {
                        'org': org_user.org,
                        'potential_leaders': potential_leaders
                    })
                
                # Get the selected new leader
                new_leader_id = request.POST.get('new_leader_id')
                try:
                    new_leader = User.objects.get(id=new_leader_id)
                    new_leader_org_user = Org_user.objects.get(user=new_leader, org=org_user.org)
                    
                    # Remove current leader
                    Org_leader.objects.filter(user=request.user, org=org_user.org).delete()
                    
                    # Set new leader
                    Org_leader.objects.create(user=new_leader, org=org_user.org)
                    
                    messages.success(request, f'Successfully transferred leadership to {new_leader.username}.')
                except (User.DoesNotExist, Org_user.DoesNotExist):
                    messages.error(request, 'Invalid new leader selected.')
                    return redirect('org-details')
            else:
                # If no other members, delete the organization and all related records
                org = org_user.org
                org_name = org.name
                
                # Delete all related records
                Team_user.objects.filter(team__org_team__org=org).delete()
                Team.objects.filter(org_team__org=org).delete()
                Org_team.objects.filter(org=org).delete()
                Org_join_code.objects.filter(org=org).delete()
                Org_leader.objects.filter(org=org).delete()
                Org_user.objects.filter(org=org).delete()
                org.delete()
                
                messages.success(request, f'Organization {org_name} has been deleted as you were the only member.')
                return redirect('dashboard')
        
        # Get all teams the user is in for this organization
        user_teams = Team.objects.filter(
            org_team__org=org_user.org,
            team_user__user=request.user
        )
        
        # Remove user from all teams in the organization
        for team in user_teams:
            Team_user.objects.filter(team=team, user=request.user).delete()
        
        # Remove organization membership
        org_name = org_user.org.name
        org_user.delete()
        
        messages.success(request, f'You have successfully left {org_name}.')
        return redirect('org-details')
        
    except Exception as e:
        messages.error(request, f'An unexpected error occurred: {str(e)}')
        return redirect('org-details')

#join or create org page
@login_required
def join_create_org(request):
    if request.method == 'POST':
        if 'create' in request.POST:
            org_form = CreateOrgForm(request.POST)
            org_user_form = CreateOrgUserForm(request.POST)
            
            if org_form.is_valid() and org_user_form.is_valid():
                # Create the organization
                organization = org_form.save()
                
                # Create Org_user instance
                Org_user.objects.create(
                    user=request.user,
                    org=organization
                )
                
                # Create Org_leader instance
                Org_leader.objects.create(
                    user=request.user,
                    org=organization
                )
                
                messages.success(request, 'Organization created successfully!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Please correct the errors below.')
        
        elif 'join' in request.POST:
            join_form = JoinOrgForm(request.POST)
            if join_form.is_valid():
                join_code = join_form.cleaned_data['join_code']
                try:
                    org_join_code = Org_join_code.objects.get(code=join_code)
                    organization = org_join_code.org
                    
                    # Check if user is already in the organization
                    if Org_user.objects.filter(user=request.user, org=organization).exists():
                        messages.error(request, 'You are already a member of this organization.')
                        return redirect('join-create-org')
                    
                    # Create Org_user instance
                    Org_user.objects.create(
                        user=request.user,
                        org=organization
                    )
                    
                    messages.success(request, 'Successfully joined the organization!')
                    return redirect('dashboard')
                except Org_join_code.DoesNotExist:
                    messages.error(request, 'Invalid join code.')
            else:
                messages.error(request, 'Please correct the errors below.')
    
    # GET request - display empty forms
    org_form = CreateOrgForm()
    org_user_form = CreateOrgUserForm()
    join_form = JoinOrgForm()
    
    return render(request, 'organization/join_create_org.html', {
        'org_form': org_form,
        'org_user_form': org_user_form,
        'join_form': join_form
    })