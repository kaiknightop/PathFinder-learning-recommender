from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.templatetags.static import static
from django.conf import settings
import os

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    skills = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=100, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    title = models.CharField(max_length=50, blank=True, null=True)

    def get_profile_picture_url(self):
        if self.profile_picture:
            file_path = os.path.join(settings.MEDIA_ROOT, str(self.profile_picture))
            if os.path.exists(file_path) and self.profile_picture.name != 'default.jpg':
                return self.profile_picture.url
        return static('website/default.jpg')

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    cover_id = models.IntegerField(null=True, blank=True)
    subjects = models.TextField(null=True, blank=True)  # comma-separated

    def __str__(self):
        return self.title
