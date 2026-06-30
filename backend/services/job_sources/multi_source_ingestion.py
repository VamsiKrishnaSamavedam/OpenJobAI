from typing import Dict, List, Optional

from backend.config import (
    APIFY_LINKEDIN_TASK_ID,
    APIFY_INDEED_TASK_ID,
    APIFY_MAX_ITEMS,
)
from backend.services.job_sources.apify_task_source import fetch_jobs_from_apify_task


def fetch_jobs_from_multiple_sources(
    search_query: Optional[str] = None,
    location: Optional[str] = None,
    max_items: Optional[int] = None,
) -> List[Dict]:
    """
    Fetches jobs from preferred job-board sources.

    Current active sources:
    1. LinkedIn through Apify task
    2. Indeed through Apify task

    If search_query is provided, it is passed into Apify dynamically so the
    user can search like LinkedIn/Indeed.
    """

    all_jobs = []

    item_limit = max_items or APIFY_MAX_ITEMS

    apify_sources = [
        {
            "source": "linkedin_apify",
            "task_id": APIFY_LINKEDIN_TASK_ID,
        },
        {
            "source": "indeed_apify",
            "task_id": APIFY_INDEED_TASK_ID,
        },
    ]

    for apify_source in apify_sources:
        source_name = apify_source["source"]
        task_id = apify_source["task_id"]

        if not task_id:
            print(f"{source_name} skipped because task ID is empty.")
            continue

        try:
            print(f"Running Apify source: {source_name}")
            print(f"Task ID configured: {task_id}")

            if search_query:
                print(f"Search query: {search_query}")

            if location:
                print(f"Search location: {location}")

            apify_jobs = fetch_jobs_from_apify_task(
                source=source_name,
                task_id=task_id,
                max_items=item_limit,
                search_query=search_query,
                location=location,
            )

            print(f"{source_name} fetched {len(apify_jobs)} jobs")

            all_jobs.extend(apify_jobs)

        except Exception as error:
            print(f"{source_name} Apify fetch failed: {error}")

    print(f"Total Apify jobs before deduplication: {len(all_jobs)}")

    unique_jobs = deduplicate_jobs(all_jobs)

    print(f"Total Apify jobs after deduplication: {len(unique_jobs)}")

    return unique_jobs


def deduplicate_jobs(jobs: List[Dict]) -> List[Dict]:
    """
    Removes duplicate jobs across sources.

    Uses title + company + location as the duplicate key.
    """

    seen = set()
    unique_jobs = []

    for job in jobs:
        title = (job.get("title") or "").lower().strip()
        company = (job.get("company") or "").lower().strip()
        location = (job.get("location") or "").lower().strip()

        duplicate_key = f"{title}|{company}|{location}"

        if duplicate_key in seen:
            continue

        seen.add(duplicate_key)
        unique_jobs.append(job)

    return unique_jobs