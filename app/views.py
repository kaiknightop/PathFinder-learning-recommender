import requests
from django.shortcuts import render
from .models import Book
import numpy as np
from .forms import RegisterForm
from django.contrib.auth.decorators import login_required
import os
from .models import Profile
from .forms import LoginForm
from .forms import UserUpdateForm, ProfileUpdateForm
from django.http import JsonResponse
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.contrib import messages
from .pinecone_utils import embed_and_push_books
from .pinecone_utils import search_similar_books
from django.http import HttpResponse
from dotenv import load_dotenv
from django.shortcuts import render, get_object_or_404
import json
from django.views.decorators.csrf import csrf_exempt
from .open_library import fetch_books_from_open_library


def sync_books_to_pinecone(request):
    embed_and_push_books()
    return JsonResponse({'status': 'Books synced to Pinecone'})


def home(request):
    return render(request, 'index.html')


def get_books(request):
    query = request.GET.get('q', '')
    if not query:
        return JsonResponse({'error': 'Missing query'}, status=400)

    url = f'https://openlibrary.org/search.json?q={query}'
    response = requests.get(url)

    if response.status_code != 200:
        return JsonResponse({'error': 'Failed to fetch data'}, status=500)

    data = response.json()
    books = []

    for doc in data.get('docs', [])[:10]:
        title = doc.get('title')
        author = doc.get('author_name', ['Unknown'])[0]
        cover_id = doc.get('cover_i')
        subjects = doc.get('subject', [])
        subject_str = ', '.join(subjects) if subjects else ''

        # Save to DB (check if it already exists to avoid duplicates)
        if not Book.objects.filter(title=title, author=author).exists():
            Book.objects.create(
                title=title,
                author=author,
                cover_id=cover_id,
                subjects=subject_str
            )

        books.append({
            'title': title,
            'author': author,
            'cover_id': cover_id,
            'subjects': subjects[:5]
        })

    return JsonResponse({'results': books})

@csrf_exempt
def recommend_books(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST requests allowed.'}, status=405)

    try:
        data = json.loads(request.body)
        query = data.get('query', '').strip()
        if not query:
            return JsonResponse({'error': 'Query is required.'}, status=400)

        # Use Pinecone to get recommendations
        recommendations = search_similar_books(query)
        return JsonResponse({'recommendations': recommendations})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
@csrf_exempt
def sync_books_to_pinecone(request):
    if request.method == 'POST':
        try:
            books = fetch_books_from_open_library()
            return JsonResponse({'status': f'{len(books)} books fetched and stored in Pinecone.'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Only POST requests allowed.'}, status=405)

def show_results(request):
    query = request.GET.get('q', '')
    if not query:
        return render(request, 'results.html', {'query': '', 'recommendations': [], 'videos': []})

    # Fetch book recommendations
    recommendations = search_similar_books(query)


    # Fetch videos
    videos = get_videos(query)

    return render(request, 'results.html', {
        'query': query,
        'recommendations': recommendations,
        'videos': videos
    })

def seed_books(request):
    topics = [
        "math", "history", "fiction", "romance", "science", "philosophy", 
        "poetry", "programming", "space", "psychology", "biology", "literature"
    ]

    for topic in topics:
        url = f'https://openlibrary.org/search.json?q={topic}'
        response = requests.get(url)

        if response.status_code != 200:
            continue

        data = response.json()
        for doc in data.get('docs', [])[:15]:  # limit to 15 books per topic
            title = doc.get('title')
            author = doc.get('author_name', ['Unknown'])[0]
            cover_id = doc.get('cover_i')
            subjects = doc.get('subject', [])
            subject_str = ', '.join(subjects) if subjects else ''

            if not Book.objects.filter(title=title, author=author).exists():
                Book.objects.create(
                    title=title,
                    author=author,
                    cover_id=cover_id,
                    subjects=subject_str
                )

    return JsonResponse({'status': 'Books seeded successfully'})


def get_videos(query, max_results=5):
    api_key = settings.YOUTUBE_API_KEY
    search_url = 'https://www.googleapis.com/youtube/v3/search'
    params = {
        'part': 'snippet',
        'q': query,
        'type': 'video',
        'maxResults': max_results,
        'key': api_key
    }
    response = requests.get(search_url, params=params)
    if response.status_code != 200:
        return []
    data = response.json()
    videos = []
    for item in data.get('items', []):
        video = {
            'title': item['snippet']['title'],
            'channel': item['snippet']['channelTitle'],
            'thumbnail': item['snippet']['thumbnails']['medium']['url'],
            'video_url': f"https://www.youtube.com/watch?v={item['id']['videoId']}"
        }
        videos.append(video)
    return videos



def register_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('register_user')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('register_user')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect('register_user')

        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()
        messages.success(request, "Account created! You can now log in.")
        return redirect('login_user')

    return render(request, 'register.html')

def login_user(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')
    return render(request, 'login.html')

def logout_user(request):
    logout(request)
    return redirect('login_user')


# In views.py (temporary for testing)
from .pinecone_utils import embed_and_push_books

def sync_books_to_pinecone(request):
    embed_and_push_books()
    return JsonResponse({'status': 'Books synced to Pinecone'})


@login_required
def profile(request):
    try:
        # Check if user has a profile
        profile = request.user.profile
    except Profile.DoesNotExist:
        profile = None  # Avoid redirection; just handle the missing profile gracefully

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('profile')

    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile)

    # Pass the profile object to the template for display
    return render(request, 'profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile
    })

@login_required
def update_profile_picture(request):
    if request.method == 'POST':
        profile = request.user.profile
        if 'profile_picture' in request.FILES:
            profile.profile_picture = request.FILES['profile_picture']
            profile.save()
            return redirect('profile')  # Redirect to profile page after saving
    return redirect('profile')  # Redirect even if no file uploaded


def about(request):
    return render(request, 'about.html')


@login_required
def edit_profile(request):
    profile = request.user.profile

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)

        # If remove_picture button was clicked
        if 'remove_picture' in request.POST:
            profile.profile_picture.delete(save=True)  # deletes from MEDIA folder
            profile.profile_picture = None    # set back to default
            profile.save()
            return redirect('edit_profile')

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('profile')

    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=profile)

    return render(request, 'edit_profile.html', {'user_form': user_form, 'profile_form': profile_form})

