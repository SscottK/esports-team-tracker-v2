from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView


urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'), 
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('dashboard/', views.userDashboard, name='dashboard'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('team-details/<int:teamID>', views.team_detail, name='team-details'),
    path('team/<int:teamID>/add-member/', views.add_team_member, name='add-member')
    ]