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


class Article(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    tags = models.TextField()  # Store as comma-separated values
    topic = models.CharField(max_length=255)
    read_time = models.IntegerField()
    claps = models.IntegerField()
    content = models.CharField(max_length=1000)
    url = models.URLField()
    date_posted = models.DateField()
    subject = models.CharField(max_length=255)

    def __str__(self):
        return self.title
    

class UserReaction(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='reactions')
    article = models.ForeignKey(Article, on_delete=models.CASCADE, related_name='reactions')
    rating = models.IntegerField(default=0)  # Store rating (1 to 5)

    class Meta:
        unique_together = ('user_profile', 'article')  # One rating per article per user

    def __str__(self):
        return f"{self.user_profile.user.username} - {self.article.title} - {self.rating} stars"