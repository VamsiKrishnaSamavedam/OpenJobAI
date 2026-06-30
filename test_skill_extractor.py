from backend.services.skill_extractor import extract_skills


sample_text = """
I have experience with Python, SQL, PostgreSQL, AWS, Docker, FastAPI,
Pandas, NumPy, and machine learning.
"""

skills = extract_skills(sample_text)

print(skills)