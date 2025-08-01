from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('results/', views.show_results, name='show_results'),
    path('api/books/', views.get_books, name='get_books'),
    path('api/recommend/', views.recommend_books, name='recommend_books'),
    path('seed/', views.seed_books, name='seed_books'),
    path('sync/', views.sync_books_to_pinecone, name='sync_books'),
    path('login/', views.login_user, name='login_user'),
    path('logout/', views.logout_user, name='logout_user'),
    path('register/', views.register_user, name='register_user'),
    path('profile/', views.profile, name='profile'),
    path('about/', views.about, name='about'),

]