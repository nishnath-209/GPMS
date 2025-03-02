# myapp/views.py
from django.shortcuts import render, redirect
# Add this to your existing views.py file
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import users
import datetime
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


@login_required
def home_view(request):
    """Display the home page after successful login"""
    return render(request, 'user/home.html')

def register_view(request):
    """Handle user registration"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        phone = request.POST.get('phone')

        # Additional citizen details
        aadhar_number = request.POST.get('aadhar_number')
        date_of_birth = request.POST.get('date_of_birth')
        gender = request.POST.get('gender')
        occupation = request.POST.get('occupation')
        house_number = request.POST.get('house_number')

        # **Fetch village_id directly from the form**
        village_id = request.POST.get('village_id')

        # Validate password
        if password != password_confirm:
            messages.error(request, 'Passwords do not match')
            return redirect('login_register')

        with connection.cursor() as cursor:
            try:
                # **Step 1: Insert into users table**
                cursor.execute("""
                    INSERT INTO users (username, password, email, phone, role, registration_date) 
                    VALUES (%s, %s, %s, %s, 'citizen', NOW()) RETURNING user_id
                """, [username, password, email, phone])

                user_id = cursor.fetchone()[0]


                # **Step 2: Insert into citizen table**
                cursor.execute("""
                    INSERT INTO citizen (user_id, village_id, name, house_number, aadhar_number, date_of_birth, gender, occupation) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, [user_id, village_id, username, house_number, aadhar_number, date_of_birth, gender, occupation])

                messages.success(request, 'Registration successful! Please login.')
                return redirect('login_register')

            except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}')
                print("Error:", e)

    return render(request, 'user/login_register.html')


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

            # Fetch citizen details using the user_id
            cursor.execute("""
                SELECT * FROM citizen WHERE user_id = %s
            """, [user[0]])
            
            #citizen = cursor.fetchone()
            cursor.execute("SELECT * FROM citizen WHERE user_id = %s", [user[0]])
            citizen = cursor.fetchone()
            if citizen:
                request.session["citizen_id"] = citizen[0]  # Store citizen_id

            
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

# Original dashboard function
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
            SELECT c.citizen_id, c.name, c.house_number, c.aadhar_number, 
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
                'house_number': citizen_result[2],
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
                SELECT complaint_id, description, complaint_type, complaint_date
                FROM COMPLAINT
                WHERE citizen_id = %s
                ORDER BY complaint_date DESC
            """, [citizen_id])
            complaints = []
            columns = [col[0] for col in cursor.description]
            for row in cursor.fetchall():
                complaint_dict = dict(zip(columns, row))
                complaint_dict["get_complaint_type_display"] = complaint_dict["complaint_type"]
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

# New function to handle profile updates
def update_profile(request):
    # Check if user is logged in
    if 'user_id' not in request.session:
        return redirect('login')
    
    if request.method == 'POST':
        # Get form data
        citizen_id = request.POST.get('citizen_id')
        name = request.POST.get('name')
        house_number = request.POST.get('house_number')
        aadhar_number = request.POST.get('aadhar_number')
        date_of_birth = request.POST.get('date_of_birth')
        occupation = request.POST.get('occupation')
        
        # Validate data
        if not citizen_id or not name or not house_number:
            messages.error(request, "Required fields cannot be empty")
            return redirect('dashboard')
        
        # Update citizen data in the database
        with connection.cursor() as cursor:
            try:
                cursor.execute("""
                    UPDATE CITIZEN
                    SET name = %s, house_number = %s, aadhar_number = %s, 
                        date_of_birth = %s, occupation = %s
                    WHERE citizen_id = %s
                """, [name, house_number, aadhar_number, date_of_birth, occupation, citizen_id])
                
                messages.success(request, "Profile updated successfully")
            except Exception as e:
                messages.error(request, f"Error updating profile: {str(e)}")
    
    return redirect('dashboard')

def add_complaint(request):
    """Handle adding a new complaint."""
    if request.method == "POST":
        citizen_id = request.session.get("citizen_id")
        if not citizen_id:
            return redirect("login")

        complaint_type = request.POST.get("complaint_type")
        description = request.POST.get("description")
        complaint_date = datetime.date.today()

        #print(f"Adding complaint: {complaint_type}, {description}, {complaint_date}")

        # Insert the new complaint
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO COMPLAINT (citizen_id, complaint_type, description, complaint_date)
                VALUES (%s, %s, %s, %s)
            """, [citizen_id, complaint_type, description, complaint_date])

        return redirect("dashboard")


@csrf_exempt
def remove_complaint(request):
    """Handle removing a complaint."""
    if request.method == "POST":
        complaint_id = request.POST.get("complaint_id")

        # Delete the complaint
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM COMPLAINT WHERE complaint_id = %s", [complaint_id])

        return JsonResponse({"success": True})

    return JsonResponse({"success": False}, status=400)


def view_village_info(request, user_id):
    with connection.cursor() as cursor:
        # Get citizen_id and village_id
        cursor.execute("""
            SELECT citizen_id, village_id
            FROM CITIZEN
            WHERE user_id = %s
        """, [user_id])
        result = cursor.fetchone()

        if not result:
            return JsonResponse({"error": "Citizen not found for user"}, status=400)

        citizen_id, village_id = result

        # Retrieve educational records
        cursor.execute("""
            SELECT schools, colleges, students, teachers, literacy_rate, record_date
            FROM education_record
            WHERE village_id = %s
            ORDER BY record_date DESC
        """, [village_id])

        columns = [col[0] for col in cursor.description]
        education_data = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Retrieve agricultural records
        cursor.execute("""
            SELECT total_agricultural_land, irrigated_land, major_crops, farmers_count, subsidy_amount, record_date
            FROM agriculture_record
            WHERE village_id = %s
            ORDER BY record_date DESC
        """, [village_id])

        columns = [col[0] for col in cursor.description]
        agriculture_data = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Retrieve health records
        cursor.execute("""
            SELECT healthcare_facilities, doctors, nurses, beds, patients_treated, vaccination_count, record_date
            FROM HEALTH_RECORD
            WHERE village_id = %s
            ORDER BY record_date DESC
        """, [village_id])

        columns = [col[0] for col in cursor.description]
        health_data = [dict(zip(columns, row)) for row in cursor.fetchall()]

    return render(request, 'user/village_info.html', {'education_data': education_data, 'agriculture_data' : agriculture_data, 'health_data' : health_data})

def update_user_roles(request):
    context = {'users': []}
    
    if request.method == 'POST':
        # Iterate over all POST keys to find role updates
        for key in request.POST:
            if key.startswith('role_'):
                user_id = key.split('_')[1]
                new_role = request.POST.get(key)
                
                # Update user role
                with connection.cursor() as cursor:
                    cursor.execute("""
                        UPDATE users
                        SET role = %s
                        WHERE user_id = %s
                    """, [new_role, user_id])
        
        messages.success(request, "Roles updated successfully")
        return redirect('update_user_roles')

        # GET request handling
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT user_id, username, email, phone, role
            FROM users
            ORDER BY user_id
        """)
        users = []
        for row in cursor.fetchall():
            users.append({
                'user_id': row[0],
                'username': row[1],
                'email': row[2],
                'phone': row[3],
                'role': row[4]
            })
        context['users'] = users
        context['roles'] = ['citizen', 'admin', 'employee', 'government_monitor']
        
    return render(request, 'user/update_user_roles.html', context)

def admin_home(request):
    return render(request, 'user/admin_home.html')

def citizen_admin(request):
    context = {'citizens': []}
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT *
            FROM citizen
            ORDER BY citizen_id
        """)
        citizens= []
        for row in cursor.fetchall():
            citizens.append({
                'citizen_id': row[0],
                'user_id': row[1],
                'village_id': row[2],
                'name': row[3],
                'address': row[4],
                'aadhar_number': row[5],
                'date_of_birth': row[6],
                'gender': row[7],
                'occupation':row[8]
            })
        context['citizens'] = citizens
    return render(request,'user/citizen_admin.html',context)

def employee_home(request):
    return render(request,'user/employee_home.html')


# Add this to your existing views.py file (keep all existing code)

def employee_query(request):
    """Handle database queries from employees"""
    context = {
        'query_executed': False,
        'query_results': None,
        'column_names': None,
        'error_message': None
    }
    
    # Check if user is logged in and is an employee
    if 'user_id' not in request.session or request.session.get('role') != 'employee':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('login_register')
    
    if request.method == 'POST':
        table_selection = request.POST.get('table_selection')
        filter_field = request.POST.get('filter_field')
        filter_value = request.POST.get('filter_value')
        limit = int(request.POST.get('limit', 100))
        
        # Validate limit to prevent excessive data queries
        if limit < 1:
            limit = 1
        elif limit > 1000:
            limit = 1000
            
        # Define allowed tables and their fields for security
        allowed_tables = {
            'citizen': ['citizen_id', 'user_id', 'village_id', 'name', 'house_number', 'aadhar_number', 'date_of_birth', 'gender', 'occupation'],
            'village': ['village_id', 'village_name', 'district', 'state', 'pincode', 'population'],
            'tax_record': ['tax_id', 'citizen_id', 'tax_type', 'amount', 'due_date', 'payment_date', 'payment_status', 'payment_method'],
            'certificate': ['certificate_id', 'citizen_id', 'certificate_type', 'issue_date', 'valid_until'],
            'property': ['property_id', 'citizen_id', 'address', 'property_type', 'area', 'survey_number', 'registry_date', 'value'],
            'complaint': ['complaint_id', 'citizen_id', 'complaint_type', 'description', 'complaint_date', 'status'],
            'scheme': ['scheme_id', 'scheme_name', 'start_date', 'end_date', 'criteria', 'benefits']
        }
        
        # Validate inputs
        if table_selection not in allowed_tables:
            context['error_message'] = "Invalid table selection"
            return render(request, 'user/employee_query.html', context)
            
        if filter_field and filter_field not in allowed_tables[table_selection]:
            context['error_message'] = "Invalid filter field"
            return render(request, 'user/employee_query.html', context)
            
        try:
            with connection.cursor() as cursor:
                # Construct query safely (avoiding SQL injection)
                query = f"SELECT * FROM {table_selection}"
                params = []
                
                if filter_field and filter_value:
                    query += f" WHERE {filter_field} = %s"
                    params.append(filter_value)
                    
                query += f" LIMIT {limit}"
                
                # Execute query
                cursor.execute(query, params)
                
                # Get column names
                column_names = [col[0] for col in cursor.description]
                
                # Fetch results
                results = cursor.fetchall()
                
                context['query_executed'] = True
                context['query_results'] = results
                context['column_names'] = column_names
                
        except Exception as e:
            context['error_message'] = f"Query error: {str(e)}"
            
    return render(request, 'user/employee_query.html', context)


# Add these updated functions to your views.py file

def advanced_query_begin(request):
    """Initial entry point for advanced query - shows table selection form"""
    # Get all available tables for selection
    tables = {
        "citizen": "Citizen",
        "village": "Village",
        "tax_record": "Tax Record",
        "certificate": "Certificate",
        "property": "Property",
        "complaint": "Complaint",
        "scheme": "Scheme",
        "users": "Users",
        # Add more tables as needed
    }
    
    # Clear any previous query state
    if 'selected_tables' in request.session:
        del request.session['selected_tables']
    if 'selected_columns' in request.session:
        del request.session['selected_columns']
    if 'filters' in request.session:
        del request.session['filters']
    
    return render(request, 'user/advanced_query_step1.html', {'tables': tables})

def advanced_query_step1(request):
    """Process table selection and show column/filter selection form"""
    if request.method == "POST":
        # Get selected tables from form
        selected_tables = request.POST.getlist('tables')
        
        if not selected_tables:
            messages.error(request, "Please select at least one table")
            return redirect('advanced_query_begin')
        
        # Store selected tables in session
        request.session['selected_tables'] = selected_tables
        
        # Define available columns for each selected table
        table_columns = {
            'citizen': ['citizen_id', 'user_id', 'village_id', 'name', 'house_number', 'aadhar_number', 'date_of_birth', 'gender', 'occupation'],
            'village': ['village_id', 'village_name', 'district', 'state', 'pincode', 'population'],
            'tax_record': ['tax_id', 'citizen_id', 'tax_type', 'amount', 'due_date', 'payment_date', 'payment_status', 'payment_method'],
            'certificate': ['certificate_id', 'citizen_id', 'certificate_type', 'issue_date', 'valid_until'],
            'property': ['property_id', 'citizen_id', 'address', 'property_type', 'area', 'survey_number', 'registry_date', 'value'],
            'complaint': ['complaint_id', 'citizen_id', 'complaint_type', 'description', 'complaint_date', 'status'],
            'scheme': ['scheme_id', 'scheme_name', 'start_date', 'end_date', 'criteria', 'benefits'],
            'users': ['user_id', 'username', 'email', 'phone', 'role', 'registration_date'],
            # Add more table column definitions as needed
        }
        
        # Create a dict of only the selected tables and their columns
        selected_tables_columns = {}
        for table in selected_tables:
            if table in table_columns:
                selected_tables_columns[table] = table_columns[table]
        
        return render(request, 'user/advanced_query_step2.html', {'selected_tables': selected_tables_columns})
    
    # If not a POST request, redirect back to the beginning
    return redirect('advanced_query_begin')

def advanced_query_step2(request):
    """Process column/filter selection and execute query"""
    # Get selected tables from session
    selected_tables = request.session.get('selected_tables', [])
    
    if not selected_tables:
        # If no tables in session, start over
        return redirect('advanced_query_begin')
    
    if request.method == "POST":
        # Initialize containers for filters and display columns
        filters = {}
        display_columns = []
        
        # Process the form data
        for key, value in request.POST.items():
            # Check for display column selections
            if key.startswith('display_'):
                # Format: display_table_column
                parts = key.split('_', 2)
                if len(parts) == 3:
                    table, column = parts[1], parts[2]
                    display_columns.append(f"{table}.{column}")
            
            # Check for filter values
            elif key.startswith('filter_'):
                # Format: filter_table_column
                parts = key.split('_', 2)
                if len(parts) == 3 and value.strip():
                    table, column = parts[1], parts[2]
                    filters[f"{table}.{column}"] = value.strip()
        
        # Store in session for use in execute
        request.session['filters'] = filters
        request.session['display_columns'] = display_columns
        request.session.modified = True  # Ensure session is saved
        
        # Redirect to execute the query
        return redirect('advanced_query_execute')
    
    # If not a POST request (or session is missing data)
    return redirect('advanced_query_begin')

def advanced_query_execute(request):
    """Execute the query and display results"""
    # Get data from session
    selected_tables = request.session.get('selected_tables', [])
    filters = request.session.get('filters', {})
    display_columns = request.session.get('display_columns', [])
    
    if not selected_tables:
        messages.error(request, "Missing query parameters. Please start over.")
        return redirect('advanced_query_begin')
    
    try:
        # Define relationships between tables for joins
        table_relationships = {
            'citizen': {'village': ('village_id', 'village_id')},
            'tax_record': {'citizen': ('citizen_id', 'citizen_id')},
            'certificate': {'citizen': ('citizen_id', 'citizen_id')},
            'property': {'citizen': ('citizen_id', 'citizen_id')},
            'complaint': {'citizen': ('citizen_id', 'citizen_id')},
            'users': {'citizen': ('user_id', 'user_id')}
            # Add more relationships as needed
        }
        
        # Build the SELECT clause with only the requested display columns
        if not display_columns:
            # If no columns explicitly selected, select all from all tables
            select_parts = []
            for table in selected_tables:
                select_parts.append(f"{table}.*")
            select_clause = "SELECT " + ", ".join(select_parts)
        else:
            # Use selected columns
            select_clause = "SELECT " + ", ".join(display_columns)
        
        # Start with the first table
        from_clause = f"FROM {selected_tables[0]}"
        
        # Add JOINS for remaining tables based on defined relationships
        join_clauses = []
        if len(selected_tables) > 1:
            # First, build a graph of connected tables
            connected = {selected_tables[0]}
            remaining = set(selected_tables[1:])
            
            # Keep adding joins while there are tables to connect
            while remaining:
                added_any = False
                
                for curr_table in list(remaining):
                    # Try to find a connection from any already connected table
                    for connected_table in connected:
                        # Check direct relationship
                        if connected_table in table_relationships and curr_table in table_relationships[connected_table]:
                            local_col, foreign_col = table_relationships[connected_table][curr_table]
                            join_clauses.append(f"LEFT JOIN {curr_table} ON {connected_table}.{local_col} = {curr_table}.{foreign_col}")
                            connected.add(curr_table)
                            remaining.remove(curr_table)
                            added_any = True
                            break
                            
                        # Check reverse relationship
                        elif curr_table in table_relationships and connected_table in table_relationships[curr_table]:
                            local_col, foreign_col = table_relationships[curr_table][connected_table]
                            join_clauses.append(f"LEFT JOIN {curr_table} ON {curr_table}.{local_col} = {connected_table}.{foreign_col}")
                            connected.add(curr_table)
                            remaining.remove(curr_table)
                            added_any = True
                            break
                            
                    if added_any:
                        break
                
                # If we couldn't find any joins, use a CROSS JOIN for the next table
                if not added_any and remaining:
                    next_table = remaining.pop()
                    join_clauses.append(f"CROSS JOIN {next_table}")
                    connected.add(next_table)
        
        # Build the WHERE clause for filters
        where_clauses = []
        params = []
        for filter_col, filter_val in filters.items():
            where_clauses.append(f"{filter_col} = %s")
            params.append(filter_val)
        
        # Assemble the complete query
        query_sql = select_clause + " " + from_clause
        if join_clauses:
            query_sql += " " + " ".join(join_clauses)
        if where_clauses:
            query_sql += " WHERE " + " AND ".join(where_clauses)
        
        # Add a reasonable limit
        query_sql += " LIMIT 1000"
        
        # Execute the query
        with connection.cursor() as cursor:
            cursor.execute(query_sql, params)
            
            # Get column names
            column_names = [col[0] for col in cursor.description]
            
            # Fetch the results
            query_results = cursor.fetchall()
        
        # Render the results page
        return render(request, 'user/query_results.html', {
            'query_sql': query_sql,
            'query_results': query_results,
            'column_names': column_names
        })
    
    except Exception as e:
        messages.error(request, f"Query execution error: {str(e)}")
        return redirect('advanced_query_begin')

# Update the employee_home view to include a link to the advanced query page
def employee_home(request):
    return render(request, 'user/employee_home.html')