from backend.database import SessionLocal
from backend.services.resume_parser import parse_resume_file
from backend.services.skill_extractor import extract_skills
from backend.services.embedding_service import generate_embedding
from backend.repositories.resume_repository import save_resume, get_resume_by_id


print("Step 1: Starting test script")

file_path = "sample_resume.pdf"

print("Step 2: Reading resume file")

with open(file_path, "rb") as file:
    file_bytes = file.read()

print("Step 3: Resume file read successfully")
print("File size:", len(file_bytes), "bytes")

print("Step 4: Parsing resume text")

resume_text = parse_resume_file(file_path, file_bytes)

print("Step 5: Resume parsed successfully")
print("Text length:", len(resume_text))

print("Step 6: Extracting skills")

skills = extract_skills(resume_text)

print("Step 7: Skills extracted")
print("Skills:", skills)

print("Step 8: Generating embedding")

embedding = generate_embedding(resume_text)

print("Step 9: Embedding generated")
print("Embedding length:", len(embedding))

print("Step 10: Creating database session")

db = SessionLocal()

print("Step 11: Database session created")

try:
    print("Step 12: Saving resume into database")

    resume_id = save_resume(
        db=db,
        filename=file_path,
        raw_text=resume_text,
        skills=skills,
        embedding=embedding
    )

    print("Step 13: Resume saved successfully")
    print("Resume ID:", resume_id)

    print("Step 14: Reading saved resume from database")

    saved_resume = get_resume_by_id(db, resume_id)

    print("Step 15: Saved resume fetched successfully")
    print("Saved resume filename:", saved_resume["filename"])
    print("Saved resume skills:", saved_resume["parsed_skills"])
    print("Saved resume created_at:", saved_resume["created_at"])

except Exception as error:
    print("ERROR OCCURRED:")
    print(error)

finally:
    print("Step 16: Closing database session")
    db.close()