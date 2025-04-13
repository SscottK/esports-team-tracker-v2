from django.urls import path
from . import views
# from .views import CreateOrganization
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'), 
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('dashboard/', views.userDashboard, name='dashboard'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('team-details/<int:teamID>', views.team_detail, name='team-details'),
    path('team/<int:org_id>/<int:teamID>/add-member/', views.add_team_member, name='add_team_member'),
    path('team/<int:teamID>/remove-member/<int:userID>', views.remove_team_member, name='remove_team_member'),
    path('team/<int:teamID>/remove-coach/<int:userID>', views.remove_coach, name='remove_coach'),
    path('team/<int:teamID>/demote-coach/<int:userID>', views.demote_coach, name='demote_coach'),
    path('team/<int:team_id>/add-game', views.create_team_game, name='add_team_game'),
    path('edit-profile/<int:user_id>/', views.edit_profile, name='edit-profile'),
    path('new-team/', views.create_team, name='new-team'),
    path('api/games/', views.get_games, name='get_games'),
    path('api/table-data/', views.get_table_data, name='get_table_data'),
    path('add-time/', views.create_new_time, name='add-time'),
    path('update-time/<int:time_id>', views.update_time, name='update-time'),
    path('new-target-times/<int:team_id>/<int:game_id>/', views.create_target_times, name='new-target-times'),
    path('search-users/', views.search_users, name='search-users'),
    path('api/new-time-get-games/', views.new_time_get_games, name='new-time-get-games'),
    path('api/get-levels/', views.get_levels, name='get-levels'),
    path('new-org/', views.create_org, name='new-org'),
    path('join-codes/<int:org_id>', views.join_codes, name='join-codes'),
    path('generate-code/<int:org_id>', views.generate_join_code, name='generate-code'),
    path('join-org', views.join_org, name='join-org'),
    path('create-org-user/<str:join_code>', views.create_org_user, name='create-org-user'),
    path('deactivate/', views.deactivate_account, name='deactivate_account'),
    path('goodbye/', views.goodbye_page, name='goodbye'),    
    path('team/<int:org_id>/<int:team_id>/upload/', views.upload_times, name='upload_times'),
    path('suggest-game/', views.suggest_game, name='suggest_game'),
    path('manage-game-suggestions/', views.manage_game_suggestions, name='manage-game-suggestions'),
]