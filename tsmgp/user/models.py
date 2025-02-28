from django.db import models

# Create your models here.
# users model
class users(models.Model):
    username = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True)
    name = models.CharField(max_length=50)
    role = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'users'  # Specify the exact table name
        
    def __str__(self):
        return self.username