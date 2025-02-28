# myapp/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_register_view, name='login_register'),
    path('login/', views.login_view, name='login'),
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