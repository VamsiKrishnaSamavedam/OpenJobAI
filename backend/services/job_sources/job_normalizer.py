from typing import Dict, Optional
import hashlib


def make_source_job_id(source: str, title: str, company: str, location: str, apply_url: str) -> str:
    """
    Creates a stable ID when a source does not provide a clean job ID.
    """

    raw_value = f"{source}|{title}|{company}|{location}|{apply_url}".lower()
    return hashlib.sha256(raw_value.encode("utf-8")).hexdigest()[:32]


def normalize_job(
    source: str,
    source_job_id: Optional[str],
    title: Optional[str],
    company: Optional[str],
    location: Optional[str],
    description: Optional[str],
    apply_url: Optional[str],
) -> Dict:
    """
    Converts any job source into our standard OpenJobAI job format.
    """

    clean_title = (title or "").strip()
    clean_company = (company or "").strip()
    clean_location = (location or "Remote").strip()
    clean_description = (description or "").strip()
    clean_apply_url = (apply_url or "").strip()

    if not source_job_id:
        source_job_id = make_source_job_id(
            source=source,
            title=clean_title,
            company=clean_company,
            location=clean_location,
            apply_url=clean_apply_url,
        )

    return {
        "source": source,
        "source_job_id": str(source_job_id),
        "title": clean_title,
        "company": clean_company,
        "location": clean_location,
        "description": clean_description,
        "apply_url": clean_apply_url,
    }