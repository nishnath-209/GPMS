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
        phone = request.POST['phone']
        
        # Basic validation
        if password != password_confirm:
            messages.error(request, 'Passwords do not match')
            return redirect('login_register')

        # hashed_password = hashlib.sha256(password.encode()).hexdigest()
        # print("hi\n")

        with connection.cursor() as cursor:
            try:
                # print("hi\n")
                cursor.execute("""
                    INSERT INTO users 
                    (username, password, email, phone, role) 
                    VALUES (%s, %s, %s, %s, 'citizen')
                """, [username, password, email, phone])
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
        # hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT user_id, username, email, phone, role, registration_date 
                FROM users 
                WHERE username = %s AND password = %s
            """, [username, password])
            
            user = cursor.fetchone()
            
            if user:
                # Store user info in session
                request.session['user_id'] = user[0]
                request.session['username'] = user[1]
                request.session['email'] = user[2]
                request.session['phone'] = user[3]
                request.session['role'] = user[4]
                return redirect('home')
                
                # if user[4] == 'citizen':
                #     return redirect('citizen_home')
                # elif user[4] == 'gm':
                #     return redirect('government_monitors')
                # elif user[4] == 'admin':
                #     return redirect('admin')
                # else:
                #     return redirect('employee_home')  # Go to dashboard page
            else:
                messages.error(request, 'Wrong username or password')
                return redirect('login_register')
    
    return render(request, 'user/login_register.html')



def home_view(request):
    if request.session['role'] == 'citizen':
        return redirect('citizen_home')
    elif request.session['role'] == 'gm':
        return redirect('government_monitors')
    elif request.session['role'] == 'admin':
        return redirect('admin')
    else:
        return redirect('employee_home')


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
    
    user_id = request.session['user_id']
    
    # Get user data from session
    context = {
        'user_id': user_id,
        'username': request.session['username'],
        'email': request.session['email'],
        'phone': request.session['phone'],
        'role': request.session['role'],
    }
    
    with connection.cursor() as cursor:
        # Get all citizen information
        cursor.execute("""
            SELECT c.citizen_id, c.name, c.address, c.aadhar_number, 
                c.date_of_birth, c.gender, c.occupation, v.village_name,
                v.district, v.state, v.pincode
            FROM CITIZEN c
            JOIN VILLAGE v ON c.village_id = v.village_id
            WHERE c.user_id = %s
        """, [user_id])

        citizen_result = cursor.fetchone()

        # Check if result is not None
        if citizen_result:
            temp = {
                'citizen_id': citizen_result[0],
                'name': citizen_result[1],
                'address': citizen_result[2],
                'aadhar_number': citizen_result[3],
                'date_of_birth': citizen_result[4],
                'gender': citizen_result[5],
                'occupation': citizen_result[6],
                'village_name': citizen_result[7],
                'district': citizen_result[8],
                'state': citizen_result[9],
                'pincode': citizen_result[10],
            }
        else:
            temp = {}

        context = {
            'citizen_result': temp
        }
        
        if citizen_result:
            # Get column names from cursor description
            columns = [col[0] for col in cursor.description]
            citizen_info = dict(zip(columns, citizen_result))
            context['citizen_info'] = citizen_info
            
            citizen_id = citizen_info['citizen_id']
            
            # Continue with your existing queries for tax_records, certificates, etc.
            # Get tax records
            cursor.execute("""
                SELECT tax_type, amount, due_date, payment_date, payment_status, payment_method
                FROM TAX_RECORD
                WHERE citizen_id = %s
                ORDER BY due_date DESC
            """, [citizen_id])
            tax_records = []
            columns = [col[0] for col in cursor.description]
            for row in cursor.fetchall():
                tax_records.append(dict(zip(columns, row)))
            context['tax_records'] = tax_records
            
            # Rest of your existing queries remain the same...
            # Get certificates
            cursor.execute("""
                SELECT certificate_type, issue_date, valid_until
                FROM CERTIFICATE
                WHERE citizen_id = %s
                ORDER BY issue_date DESC
            """, [citizen_id])
            certificates = []
            columns = [col[0] for col in cursor.description]
            for row in cursor.fetchall():
                certificates.append(dict(zip(columns, row)))
            context['certificates'] = certificates
            
            # Get property records
            cursor.execute("""
                SELECT address as name, property_type, area, survey_number as survey_num, 
                       registry_date as registration_date, value
                FROM PROPERTY
                WHERE citizen_id = %s
                ORDER BY registry_date DESC
            """, [citizen_id])
            property_records = []
            columns = [col[0] for col in cursor.description]
            for row in cursor.fetchall():
                property_records.append(dict(zip(columns, row)))
            context['property_records'] = property_records
            
            # Get complaints
            cursor.execute("""
                SELECT description, complaint_type, complaint_date
                FROM COMPLAINT
                WHERE citizen_id = %s
                ORDER BY complaint_date DESC
            """, [citizen_id])
            complaints = []
            columns = [col[0] for col in cursor.description]
            for row in cursor.fetchall():
                complaint_dict = dict(zip(columns, row))
                # Add this method-like attribute to match template's get_complaint_type_display
                complaint_dict['get_complaint_type_display'] = complaint_dict['complaint_type']
                complaints.append(complaint_dict)
            context['complaints'] = complaints
        
        # Get schemes (available to all users regardless of citizen status)
        cursor.execute("""
            SELECT scheme_name as name, start_date, end_date, criteria
            FROM SCHEME
            WHERE end_date IS NULL OR end_date >= CURRENT_DATE
            ORDER BY start_date DESC
        """)
        schemes = []
        columns = [col[0] for col in cursor.description]
        for row in cursor.fetchall():
            schemes.append(dict(zip(columns, row)))
        context['schemes'] = schemes
    
    return render(request, 'user/dashboard.html', context)