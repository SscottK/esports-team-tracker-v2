from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from .forms import CustomUserCreationForm
from django.urls import reverse_lazy

# Create your views here.

#View for the home page
def home(request):
    
    return render(request, 'home.html')

#view for the User Dashboard Page
def userDashboard(request):
    
    return render(request, 'users/dashboard.html')

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
            # login(request, user)
            return redirect('home')  # Redirect to a welcome page or dashboard
        else:
            error_message = 'Invalid sign up - try again'
    else:
        # Render signup.html with an empty form
        form = CustomUserCreationForm()
    
    # Render the signup page with form and potential error message
    context = {'form': form, 'error_message': error_message}
    return render(request, 'signup.html', context)
