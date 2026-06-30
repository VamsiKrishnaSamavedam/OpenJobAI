import re
from typing import List, Dict, Optional

import requests


REMOTE_OK_API_URL = "https://remoteok.com/api"

def normalize_apply_url(url: Optional[str]) -> str:
    """
    Converts job apply URL into a full external URL.
    """

    if not url:
        return ""

    url = url.strip()

    if url.startswith("http://") or url.startswith("https://"):
        return url

    if url.startswith("/"):
        return f"https://remoteok.com{url}"

    return f"https://remoteok.com/{url}"

def clean_html(raw_html: Optional[str]) -> str:
    """
    Removes basic HTML tags from job descriptions.
    """

    if not raw_html:
        return ""

    clean_text = re.sub(r"<.*?>", " ", raw_html)
    clean_text = re.sub(r"\s+", " ", clean_text)

    return clean_text.strip()


def fetch_remoteok_jobs(limit: int = 25) -> List[Dict]:
    """
    Fetches remote jobs from RemoteOK public API.

    RemoteOK returns a list where the first item is metadata,
    so we skip the first item.

    This function also removes duplicate jobs based on title + company.
    """

    headers = {
        "User-Agent": "OpenJobAI/0.1"
    }

    response = requests.get(
        REMOTE_OK_API_URL,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    jobs = data[1:]

    cleaned_jobs = []
    seen_jobs = set()

    for job in jobs:
        title = job.get("position") or ""
        company = job.get("company") or ""
        location = job.get("location") or "Remote"
        description = clean_html(job.get("description") or "")
        apply_url = normalize_apply_url(job.get("url") or "")
        source_job_id = str(job.get("id") or "")

        if not title or not company:
            continue

        duplicate_key = f"{title.strip().lower()}::{company.strip().lower()}"

        if duplicate_key in seen_jobs:
            continue

        seen_jobs.add(duplicate_key)

        cleaned_jobs.append(
            {
                "source": "remoteok",
                "source_job_id": source_job_id,
                "title": title.strip(),
                "company": company.strip(),
                "location": location.strip(),
                "description": description,
                "apply_url": apply_url.strip()
            }
        )

        if len(cleaned_jobs) >= limit:
            break

    return cleaned_jobs