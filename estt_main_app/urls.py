from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('home/', views.home, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login')
    ]