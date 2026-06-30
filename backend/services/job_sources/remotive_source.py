from typing import Dict, List
import requests
import re
import html

from backend.services.job_sources.job_normalizer import normalize_job


REMOTIVE_API_URL = "https://remotive.com/api/remote-jobs"


def clean_html_description(raw_description: str) -> str:
    """
    Converts HTML job descriptions into clean readable text.
    """

    if not raw_description:
        return ""

    text = re.sub(r"<script[\s\S]*?</script>", " ", raw_description, flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)

    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text)

    return text.strip()

def fetch_remotive_jobs(
    search: str = "data engineer",
    limit: int = 100,
) -> List[Dict]:
    """
    Fetches jobs from Remotive public API and normalizes them
    into the OpenJobAI job format.
    """

    params = {
        "search": search,
    }

    response = requests.get(
        REMOTIVE_API_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()
    raw_jobs = data.get("jobs", [])

    normalized_jobs = []

    for job in raw_jobs:
        title = job.get("title") or ""
        company = job.get("company_name") or ""
        location = job.get("candidate_required_location") or "Remote"
        description = clean_html_description(job.get("description") or "")
        apply_url = job.get("url") or ""
        source_job_id = job.get("id")

        if not title or not company:
            continue

        normalized_job = normalize_job(
            source="remotive",
            source_job_id=str(source_job_id) if source_job_id else None,
            title=title,
            company=company,
            location=location,
            description=description,
            apply_url=apply_url,
        )

        normalized_jobs.append(normalized_job)

        if len(normalized_jobs) >= limit:
            break

    return normalized_jobs