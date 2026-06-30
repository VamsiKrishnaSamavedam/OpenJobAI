from backend.database import SessionLocal
from backend.repositories.application_repository import (
    save_application,
    get_applications,
    get_application_by_id,
    update_application_status,
    delete_application
)


job_id = 3

print("Step 1: Creating database session")

db = SessionLocal()

try:
    print("Step 2: Saving job to application tracker")

    application_id = save_application(
        db=db,
        job_id=job_id,
        status="saved",
        notes="This job looks relevant to my AI/data engineering profile."
    )

    print("Application saved.")
    print("Application ID:", application_id)

    print("Step 3: Reading all applications")

    applications = get_applications(db, limit=10)

    print("Applications count:", len(applications))

    for application in applications:
        print("-" * 80)
        print("Application ID:", application["application_id"])
        print("Job ID:", application["job_id"])
        print("Title:", application["title"])
        print("Company:", application["company"])
        print("Status:", application["status"])
        print("Notes:", application["notes"])

    print("Step 4: Reading one application")

    application = get_application_by_id(
        db=db,
        application_id=application_id
    )

    print("Fetched application:", application)

    print("Step 5: Updating application status")

    updated_application = update_application_status(
        db=db,
        application_id=application_id,
        status="applied",
        notes="Applied through the job posting link."
    )

    print("Updated application:", updated_application)

    print("Step 6: Leaving application in tracker")
    print("Delete test skipped for now.")

except Exception as error:
    print("ERROR OCCURRED:")
    print(error)

finally:
    print("Step 7: Closing database session")
    db.close()