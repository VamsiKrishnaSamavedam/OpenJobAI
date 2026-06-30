from backend.services.embedding_service import generate_embedding


sample_text = """
I have experience with Python, SQL, PostgreSQL, AWS, Docker,
FastAPI, data pipelines, and machine learning.
"""

embedding = generate_embedding(sample_text)

print("Embedding type:", type(embedding))
print("Embedding length:", len(embedding))
print("First 5 values:", embedding[:5])