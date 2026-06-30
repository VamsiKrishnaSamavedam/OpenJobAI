from backend.database import SessionLocal
from backend.repositories.feedback_repository import (
    save_feedback,
    get_all_feedback,
    get_feedback_by_resume
)


resume_id = 1
job_id = 3

print("Step 1: Creating database session")

db = SessionLocal()

try:
    print("Step 2: Saving feedback")

    feedback_id = save_feedback(
        db=db,
        resume_id=resume_id,
        job_id=job_id,
        feedback_label="interested"
    )

    print("Feedback saved.")
    print("Feedback ID:", feedback_id)

    print("Step 3: Reading all feedback")

    all_feedback = get_all_feedback(db, limit=10)

    print("Feedback count:", len(all_feedback))

    for feedback in all_feedback:
        print("-" * 80)
        print("Feedback ID:", feedback["feedback_id"])
        print("Resume ID:", feedback["resume_id"])
        print("Job ID:", feedback["job_id"])
        print("Title:", feedback["title"])
        print("Company:", feedback["company"])
        print("Label:", feedback["feedback_label"])

    print("Step 4: Reading feedback by resume")

    resume_feedback = get_feedback_by_resume(
        db=db,
        resume_id=resume_id,
        limit=10
    )

    print("Resume feedback count:", len(resume_feedback))

except Exception as error:
    print("ERROR OCCURRED:")
    print(error)

finally:
    print("Step 5: Closing database session")
    db.close()