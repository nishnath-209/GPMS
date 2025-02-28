# myapp/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from .models import users
import hashlib

def login_register_view(request):
    """Display the login/registration page"""
    return render(request, 'user/login_register.html')

def login_before(request):
    """Display the page that should always show pre-login content"""
    # Force this page to ignore login status
    return render(request, 'user/login_before.html', {'ignore_login_status': True})


def base(request):
    """Display the base page"""
    return render(request, 'user/base.html')

def government_monitors(request):
    """Display the Government monitors base page"""
    return render(request, 'user/government_monitors.html')

def citizen_home(request):
    """Display the Government monitors base page"""
    return render(request, 'user/citizen_home.html')




# Add this to your existing views.py file
from django.contrib.auth.decorators import login_required

@login_required
def home_view(request):
    """Display the home page after successful login"""
    return render(request, 'user/home.html')

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

        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        # print("hi\n")

        with connection.cursor() as cursor:
            try:
                # print("hi\n")
                cursor.execute("""
                    INSERT INTO users 
                    (username, password, email, name, role) 
                    VALUES (%s, %s, %s, %s, 'citizen')
                """, [username, hashed_password, email, name])
                # print("hi\n")
                messages.success(request, 'Registration successful! Please login.')
                return redirect('login_register')
            except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}')
        
    # If not POST, redirect to login/register page
    return render(request,'user/login_register.html')

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # Hash the password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, username, email, name, role, created_at 
                FROM users 
                WHERE username = %s AND password = %s
            """, [username, hashed_password])
            
            user = cursor.fetchone()
            
            if user:
                # Store user info in session
                request.session['user_id'] = user[0]
                request.session['username'] = user[1]
                request.session['email'] = user[2]
                request.session['name'] = user[3]
                request.session['role'] = user[4]
                
                if user[4] == 'citizen':
                    return redirect('citizen_home')
                elif user[4] == 'gm':
                    return redirect('government_monitors')
                elif user[4] == 'admin':
                    return redirect('admin')
                else:
                    return redirect('employee_home')  # Go to dashboard page
            else:
                messages.error(request, 'Wrong username or password')
                return redirect('login_register')
    
    return render(request, 'user/login_register.html')


def logout(request):
    """Handle user logout by clearing the session"""
    # Clear all session data
    request.session.flush()
    
    # You can add a success message if you want
    messages.success(request, 'You have been successfully logged out.')
    
    # Redirect to the login page or home page
    return redirect('login_before')  # Or any other page you want to redirect to

def dashboard(request):
    # Check if user is logged in
    if 'user_id' not in request.session:
        return redirect('login')
    
    # Get user data from session
    context = {
        'user_id': request.session['user_id'],
        'username': request.session['username'],
        'email': request.session['email'],
        'name': request.session['name'],
        'role': request.session['role'],
    }
    
    return render(request, 'user/dashboard.html', context)