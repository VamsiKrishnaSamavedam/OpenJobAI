from backend.database import SessionLocal
from backend.services.job_fetcher import fetch_remoteok_jobs
from backend.services.skill_extractor import extract_skills
from backend.services.embedding_service import generate_embedding
from backend.repositories.job_repository import save_jobs_bulk, get_jobs


print("Step 1: Fetching jobs")

jobs = fetch_remoteok_jobs(limit=5)

print("Step 2: Jobs fetched:", len(jobs))

prepared_jobs = []

for job in jobs:
    print("Preparing job:", job["title"])

    job_text = f"""
    {job["title"]}
    {job["company"]}
    {job["location"]}
    {job["description"]}
    """

    skills = extract_skills(job_text)
    embedding = generate_embedding(job_text)

    prepared_jobs.append(
        {
            **job,
            "extracted_skills": skills,
            "embedding": embedding
        }
    )

print("Step 3: Creating database session")

db = SessionLocal()

try:
    print("Step 4: Saving jobs into database")

    saved_job_ids = save_jobs_bulk(db, prepared_jobs)

    print("Step 5: Jobs saved successfully")
    print("Saved job IDs:", saved_job_ids)

    print("Step 6: Reading saved jobs")

    saved_jobs = get_jobs(db, limit=10)

    print("Saved jobs count:", len(saved_jobs))

    for saved_job in saved_jobs:
        print("-" * 80)
        print("Job ID:", saved_job["id"])
        print("Title:", saved_job["title"])
        print("Company:", saved_job["company"])
        print("Skills:", saved_job["extracted_skills"])

except Exception as error:
    print("ERROR OCCURRED:")
    print(error)

finally:
    print("Step 7: Closing database session")
    db.close()