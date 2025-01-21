from django.contrib.auth.models import User
from django.db import models

class UserProfile(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()
    birthday = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    interests = models.TextField(blank=True)

    def __str__(self):
        return self.user.username

# added this model on 21/01/2025
class Article(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    tags = models.TextField()  # Store as comma-separated values
    topic = models.CharField(max_length=255)
    read_time = models.IntegerField()
    claps = models.IntegerField()
    url = models.URLField()
    date_posted = models.DateField()
    subject = models.CharField(max_length=255)

    def __str__(self):
        return self.title
    
