# myapp/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.contrib import messages

def login_register_view(request):
    """Display the login/registration page"""
    return render(request, 'myapp/login_register.html')

def login_view(request):
    """Handle user login"""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Redirect to home page or dashboard
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password')
            return redirect('login_register')
    
    # If not POST, redirect to login/register page
    return redirect('login_register')

# Add this to your existing views.py file
from django.contrib.auth.decorators import login_required

@login_required
def home_view(request):
    """Display the home page after successful login"""
    return render(request, 'myapp/home.html')

def register_view(request):
    """Handle user registration"""
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password_confirm = request.POST['password_confirm']
        name = request.POST['name']
        
        # Basic validation
        if password != password_confirm:
            messages.error(request, 'Passwords do not match')
            return redirect('login_register')
            
        # Check if username exists
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('login_register')
            
        # Check if email exists
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return redirect('login_register')
            
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        # Set first name if provided
        if name:
            name_parts = name.split()
            if len(name_parts) > 0:
                user.first_name = name_parts[0]
            if len(name_parts) > 1:
                user.last_name = ' '.join(name_parts[1:])
            user.save()
            
        # Log in the user
        login(request, user)
        messages.success(request, 'Registration successful!')
        return redirect('home')
        
    # If not POST, redirect to login/register page
    return redirect('login_register')