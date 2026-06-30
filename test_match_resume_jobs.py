from backend.database import SessionLocal
from backend.repositories.match_repository import (
    get_resume_for_matching,
    get_jobs_for_matching,
    save_match_results_bulk
)
from backend.services.matcher import match_resume_to_jobs


resume_id = 1
job_limit = 10

print("Step 1: Creating database session")

db = SessionLocal()

try:
    print("Step 2: Fetching resume")

    resume = get_resume_for_matching(db, resume_id)

    if resume is None:
        print("Resume not found. Check your resume_id.")
        exit()

    print("Resume found:", resume["filename"])
    print("Resume skills:", resume["parsed_skills"])
    print("Resume embedding length:", len(resume["embedding"]))

    print("Step 3: Fetching jobs")

    jobs = get_jobs_for_matching(db, limit=job_limit)

    print("Jobs found:", len(jobs))

    if not jobs:
        print("No jobs found. Run python test_save_jobs.py first.")
        exit()

    print("Step 4: Matching resume to jobs")

    match_results = match_resume_to_jobs(
        resume=resume,
        jobs=jobs
    )

    print("Step 5: Match results")

    for result in match_results:
        print("-" * 80)
        print("Job ID:", result["job_id"])
        print("Title:", result["title"])
        print("Company:", result["company"])
        print("Semantic score:", result["semantic_score"])
        print("Skill score:", result["skill_score"])
        print("Final score:", result["final_score"])
        print("Matched skills:", result["matched_skills"])
        print("Missing skills:", result["missing_skills"])

    print("Step 6: Saving match results")

    match_ids = save_match_results_bulk(db, match_results)

    print("Saved match IDs:", match_ids)

except Exception as error:
    print("ERROR OCCURRED:")
    print(error)

finally:
    print("Step 7: Closing database session")
    db.close()