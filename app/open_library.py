# open_library.py
import requests
from .models import Book

def fetch_books_from_open_library():
    url = "https://openlibrary.org/subjects/programming.json?limit=50"
    response = requests.get(url)
    data = response.json()
    
    books = []
    for item in data.get("works", []):
        book = {
            "title": item.get("title"),
            "author": item["authors"][0]["name"] if item.get("authors") else "Unknown",
            "cover_id": item.get("cover_id"),
            "subjects": item.get("subject", []),
        }
        books.append(book)
        
        # Optional: Save to DB
        Book.objects.get_or_create(
            title=book["title"],
            author=book["author"],
            cover_id=book["cover_id"],
            subjects=book["subjects"],
        )

    return books
