from django import forms
from .models import Profile
from django.contrib.auth.models import User

class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match.")

class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)

# This form will allow users to update their username, email, profile image, bio, and location.
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email']

class ProfileUpdateForm(forms.ModelForm):
    TITLE_CHOICES = [
        ('Data Analyst', 'Data Analyst'),
        ('Software Developer', 'Software Developer'),
        ('Product Manager', 'Product Manager'),
        ('Designer', 'Designer'),
        ('Other', 'Other'),
    ]

    title = forms.ChoiceField(choices=TITLE_CHOICES, required=False)
    custom_title = forms.CharField(max_length=50, required=False)

    class Meta:
        model = Profile
        fields = ['profile_picture', 'bio', 'location', 'skills', 'title', 'custom_title']  # ADDED custom_title

    def clean(self):
        cleaned_data = super().clean()
        title = cleaned_data.get('title')
        custom_title = cleaned_data.get('custom_title')

        if title == 'Other' and not custom_title:
            self.add_error('custom_title', 'Please enter your title.')

        if title != 'Other':
            cleaned_data['title'] = title
        else:
            cleaned_data['title'] = custom_title

        return cleaned_data
