from backend.config import APIFY_LINKEDIN_TASK_ID
from backend.services.job_sources.apify_task_source import (
    run_apify_task,
    normalize_apify_item,
)

print("LinkedIn task configured:", bool(APIFY_LINKEDIN_TASK_ID))

if APIFY_LINKEDIN_TASK_ID:
    print("Task ID preview:", APIFY_LINKEDIN_TASK_ID[:6])

print("Running LinkedIn Apify task once...")

raw_items = run_apify_task(
    task_id=APIFY_LINKEDIN_TASK_ID,
    max_items=10,
)

print("Raw item count:", len(raw_items))

if raw_items:
    print("First raw item keys:")
    print(list(raw_items[0].keys()))

    normalized_jobs = []

    for item in raw_items:
        job = normalize_apify_item(
            source="linkedin_apify",
            item=item,
        )

        if job.get("title") and job.get("company"):
            normalized_jobs.append(job)

    print("Normalized job count:", len(normalized_jobs))

    if normalized_jobs:
        print("First normalized job:")
        print(normalized_jobs[0])
else:
    print("No raw LinkedIn items returned.")