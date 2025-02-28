# myapp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.government_monitors, name='government_monitors'),
    path('login_before/', views.login_before, name='login_before'),
    path('base/', views.base, name='base'),
    path('login/', views.login_view, name='login'),
    path('login_register/', views.login_register_view, name='login_register'),
    path('register/', views.register_view, name='register'),
    # Add your home/dashboard URL
    path('home/', views.home_view, name='home'),  # Create this view
]



# Add this to your project's urls.py
# from django.urls import path, include
# 
# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('', include('myapp.urls')),
# ]