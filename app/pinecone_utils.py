import os
from pinecone import Pinecone, ServerlessSpec
from .models import Book
from sentence_transformers import SentenceTransformer

from django.conf import settings

# Initialize Pinecone
pc = Pinecone(api_key=settings.PINECONE_API_KEY)

# Index setup
index_name = settings.PINECONE_INDEX_NAME
environment = settings.PINECONE_ENVIRONMENT

# Make sure index exists
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=384,  # Change this to match your embedding model's output size
        metric='cosine',
        spec=ServerlessSpec(cloud='aws', region=environment)
    )

index = pc.Index(index_name)

# Load embedding model (adjust if you're using a different one)
embedder = SentenceTransformer("all-MiniLM-L6-v2")

def embed_and_push_books():
    books = Book.objects.all()

    vectors = []
    for book in books:
        text = f"{book.title} {book.subjects or ''}"
        embedding = embedder.encode(text).tolist()
        vectors.append({
            "id": str(book.id),
            "values": embedding,
            "metadata": {
                "title": book.title,
                "author": book.author,
                "cover_id": book.cover_id,
                "subjects": book.subjects
            }
        })

    index.upsert(vectors=vectors)

def search_similar_books(query, top_k=5):
    embedding = embedder.encode(query).tolist()
    result = index.query(vector=embedding, top_k=top_k, include_metadata=True)

    recommendations = []
    for match in result['matches']:
        metadata = match['metadata']
        recommendations.append({
            "title": metadata["title"],
            "author": metadata["author"],
            "cover_id": metadata["cover_id"],
            "subjects": metadata["subjects"],
            "score": match["score"]
        })
    
    return recommendations
