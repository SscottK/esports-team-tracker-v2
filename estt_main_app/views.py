from django.shortcuts import render

# Create your views here.

#View for the home page
def home(request):
    
    return render(request, 'home.html')

#view for the User Dashboard Page
def userDashboard(request):
    
    return render(request, 'users/dashboard.html')