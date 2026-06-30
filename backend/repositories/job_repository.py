import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.services.job_filter import is_relevant_job

try:
    from backend.services.job_filter import is_relevant_job
except ImportError:
    def is_relevant_job(job):
        return True
    
def save_job(
    db: Session,
    job: Optional[Dict] = None,
    source: Optional[str] = None,
    source_job_id: Optional[str] = None,
    title: Optional[str] = None,
    company: Optional[str] = None,
    location: Optional[str] = None,
    description: Optional[str] = None,
    apply_url: Optional[str] = None,
    extracted_skills: Optional[list[str]] = None,
    embedding: Optional[list[float]] = None,
) -> int:
    """
    Saves one job into the jobs table.

    Supports both formats:

    1. New format:
       save_job(db=db, job=job)

    2. Old format:
       save_job(
           db=db,
           source=...,
           source_job_id=...,
           title=...,
           company=...,
           location=...,
           description=...,
           apply_url=...,
           extracted_skills=...,
           embedding=...
       )

    If the same source + source_job_id already exists,
    it updates the existing job instead of creating a duplicate.
    """

    import hashlib

    if job is not None:
        source = job.get("source", source)
        source_job_id = job.get("source_job_id", source_job_id)
        title = job.get("title", title)
        company = job.get("company", company)
        location = job.get("location", location)
        description = job.get("description", description)
        apply_url = job.get("apply_url", apply_url)
        extracted_skills = job.get("extracted_skills", extracted_skills)
        embedding = job.get("embedding", embedding)

    source = source or "unknown"
    title = title or ""
    company = company or ""
    location = location or ""
    description = description or ""
    apply_url = apply_url or ""

    if not source_job_id:
        fallback_value = f"{source}|{title}|{company}|{location}|{apply_url}".lower()
        source_job_id = hashlib.sha256(
            fallback_value.encode("utf-8")
        ).hexdigest()[:32]

    if extracted_skills is None:
        extracted_skills = []

    if isinstance(extracted_skills, str):
        try:
            extracted_skills = json.loads(extracted_skills)
        except Exception:
            extracted_skills = [
                skill.strip()
                for skill in extracted_skills.split(",")
                if skill.strip()
            ]

    if embedding is None:
        embedding = []

    query = text("""
        INSERT INTO jobs (
            source,
            source_job_id,
            title,
            company,
            location,
            description,
            apply_url,
            extracted_skills,
            embedding
        )
        VALUES (
            :source,
            :source_job_id,
            :title,
            :company,
            :location,
            :description,
            :apply_url,
            :extracted_skills,
            :embedding
        )
        ON CONFLICT (source, source_job_id)
        DO UPDATE SET
            title = EXCLUDED.title,
            company = EXCLUDED.company,
            location = EXCLUDED.location,
            description = EXCLUDED.description,
            apply_url = EXCLUDED.apply_url,
            extracted_skills = EXCLUDED.extracted_skills,
            embedding = EXCLUDED.embedding
        RETURNING id;
    """)

    result = db.execute(
        query,
        {
            "source": source,
            "source_job_id": source_job_id,
            "title": title,
            "company": company,
            "location": location,
            "description": description,
            "apply_url": apply_url,
            "extracted_skills": json.dumps(extracted_skills),
            "embedding": embedding,
        },
    )

    job_id = result.scalar_one()

    db.commit()

    return job_id


def save_jobs_bulk(db: Session, jobs: List[Dict]) -> List[int]:
    """
    Saves multiple jobs into the database.

    Supports job dictionaries produced by:
    - RemoteOK fetcher
    - Apify LinkedIn fetcher
    - Apify Indeed fetcher
    - Live search-fetch endpoint
    """

    saved_job_ids = []

    for job in jobs:
        job_id = save_job(
            db=db,
            job=job,
        )

        saved_job_ids.append(job_id)

    return saved_job_ids


def normalize_value(value) -> str:
    if value is None:
        return ""

    return str(value).lower().strip()


def build_search_terms(search: str) -> list[str]:
    cleaned_search = normalize_value(search)

    if not cleaned_search:
        return []

    terms = [cleaned_search]

    for key, expanded_terms in SEARCH_EXPANSIONS.items():
        if cleaned_search in key or key in cleaned_search:
            terms.extend(expanded_terms)

    for word in cleaned_search.split():
        if len(word) > 2:
            terms.append(word)

    unique_terms = []

    for term in terms:
        term = normalize_value(term)

        if term and term not in unique_terms:
            unique_terms.append(term)

    return unique_terms


def job_matches_search(job: Dict, search: Optional[str]) -> bool:
    cleaned_search = normalize_value(search)

    if not cleaned_search:
        return True

    terms = build_search_terms(cleaned_search)

    skills = job.get("extracted_skills") or []

    if isinstance(skills, list):
        skills_text = " ".join(str(skill) for skill in skills)
    else:
        skills_text = str(skills)

    title = normalize_value(job.get("title"))
    company = normalize_value(job.get("company"))
    location = normalize_value(job.get("location"))
    description = normalize_value(job.get("description"))

    combined_text = f"""
    {title}
    {company}
    {location}
    {description}
    {skills_text}
    """.lower()

    score = 0

    if cleaned_search in title:
        score += 5
    elif cleaned_search in combined_text:
        score += 4

    for term in terms:
        if term == cleaned_search:
            continue

        if term in title:
            score += 2
        elif term in combined_text:
            score += 1

    return score >= 2
def normalize_value(value) -> str:
    if value is None:
        return ""

    return str(value).lower().strip()


def get_skill_text(job: Dict) -> str:
    skills = job.get("extracted_skills") or []

    if isinstance(skills, list):
        return " ".join(str(skill) for skill in skills).lower()

    return str(skills).lower()


def matches_data_engineer(job: Dict) -> bool:
    title = normalize_value(job.get("title"))
    description = normalize_value(job.get("description"))
    skills_text = get_skill_text(job)
    combined_text = f"{title} {description} {skills_text}"

    strong_title_terms = [
        "data engineer",
        "analytics engineer",
        "etl developer",
        "data pipeline",
        "big data engineer",
    ]

    for term in strong_title_terms:
        if term in title:
            return True

    if "engineer" in title and "data" in title:
        return True

    technical_terms = [
        "etl",
        "elt",
        "data pipeline",
        "data pipelines",
        "airflow",
        "spark",
        "pyspark",
        "dbt",
        "snowflake",
        "bigquery",
        "redshift",
        "data warehouse",
        "postgresql",
        "sql",
    ]

    match_count = 0

    for term in technical_terms:
        if term in combined_text:
            match_count += 1

    return match_count >= 3


def matches_data_analyst(job: Dict) -> bool:
    title = normalize_value(job.get("title"))
    description = normalize_value(job.get("description"))
    skills_text = get_skill_text(job)
    combined_text = f"{title} {description} {skills_text}"

    strong_title_terms = [
        "data analyst",
        "business analyst",
        "bi analyst",
        "analytics analyst",
        "reporting analyst",
        "data technician",
    ]

    for term in strong_title_terms:
        if term in title:
            return True

    if "analyst" in title and ("data" in title or "analytics" in title):
        return True

    analyst_terms = [
        "sql",
        "excel",
        "tableau",
        "power bi",
        "dashboard",
        "dashboards",
        "reporting",
        "data analysis",
        "analytics",
        "business intelligence",
    ]

    match_count = 0

    for term in analyst_terms:
        if term in combined_text:
            match_count += 1

    return "analyst" in title and match_count >= 2


def matches_software_engineer(job: Dict) -> bool:
    title = normalize_value(job.get("title"))
    description = normalize_value(job.get("description"))
    skills_text = get_skill_text(job)
    combined_text = f"{title} {description} {skills_text}"

    strong_title_terms = [
        "software engineer",
        "software developer",
        "backend engineer",
        "backend developer",
        "frontend engineer",
        "frontend developer",
        "full stack engineer",
        "full stack developer",
        "python developer",
        "java developer",
        "react developer",
        "application developer",
        "web developer",
    ]

    for term in strong_title_terms:
        if term in title:
            return True

    technical_terms = [
        "python",
        "java",
        "javascript",
        "typescript",
        "react",
        "next.js",
        "node",
        "api",
        "rest api",
        "backend",
        "frontend",
        "database",
        "docker",
        "kubernetes",
        "git",
        "github",
    ]

    match_count = 0

    for term in technical_terms:
        if term in combined_text:
            match_count += 1

    if "engineer" in title and match_count >= 3:
        return True

    if "developer" in title and match_count >= 2:
        return True

    return False


def matches_machine_learning(job: Dict) -> bool:
    title = normalize_value(job.get("title"))
    description = normalize_value(job.get("description"))
    skills_text = get_skill_text(job)
    combined_text = f"{title} {description} {skills_text}"

    strong_title_terms = [
        "machine learning engineer",
        "ml engineer",
        "ai engineer",
        "data scientist",
        "nlp engineer",
        "deep learning engineer",
    ]

    for term in strong_title_terms:
        if term in title:
            return True

    ml_terms = [
        "machine learning",
        "deep learning",
        "nlp",
        "pytorch",
        "tensorflow",
        "scikit-learn",
        "llm",
        "model training",
        "classification",
        "regression",
    ]

    match_count = 0

    for term in ml_terms:
        if term in combined_text:
            match_count += 1

    return match_count >= 2


def job_matches_search(job: Dict, search: Optional[str]) -> bool:
    cleaned_search = normalize_value(search)

    if not cleaned_search:
        return True

    title = normalize_value(job.get("title"))
    company = normalize_value(job.get("company"))
    location = normalize_value(job.get("location"))
    description = normalize_value(job.get("description"))
    skills_text = get_skill_text(job)

    combined_text = f"""
    {title}
    {company}
    {location}
    {description}
    {skills_text}
    """

    if "data engineer" in cleaned_search:
        return matches_data_engineer(job)

    if "data analyst" in cleaned_search:
        return matches_data_analyst(job)

    if "software engineer" in cleaned_search:
        return matches_software_engineer(job)

    if "machine learning" in cleaned_search or cleaned_search == "ml":
        return matches_machine_learning(job)

    search_words = [
        word
        for word in cleaned_search.split()
        if len(word) >= 2
    ]

    if cleaned_search in title:
        return True

    if cleaned_search in skills_text:
        return True

    if cleaned_search in combined_text:
        return True

    for word in search_words:
        if word in title or word in skills_text:
            return True

    return False

def job_matches_source(job: Dict, source_filter: Optional[str]) -> bool:
    source = (job.get("source") or "").lower().strip()

    if not source_filter or source_filter == "all":
        return source in {
            "indeed_apify",
            "linkedin_apify",
        }

    if source_filter == "indeed":
        return source == "indeed_apify"

    if source_filter == "linkedin":
        return source == "linkedin_apify"

    return True


def job_matches_freshness(job: Dict, freshness: Optional[str]) -> bool:
    if not freshness or freshness == "all":
        return True

    created_at = job.get("created_at")

    if created_at is None:
        return False

    now = datetime.now()

    if freshness == "24h":
        return created_at >= now - timedelta(hours=24)

    if freshness == "7d":
        return created_at >= now - timedelta(days=7)

    return True

def get_jobs(
    db,
    limit=50,
    offset=0,
    search=None,
    source_filter="all",
    freshness="all",
    relevant_only=False
):
    query = text("""
        SELECT
            id,
            source,
            source_job_id,
            title,
            company,
            location,
            description,
            apply_url,
            extracted_skills,
            embedding,
            created_at
        FROM jobs
        ORDER BY created_at DESC
        LIMIT 1000
    """)

    result = db.execute(query).mappings().all()

    all_jobs = [dict(row) for row in result]

    filtered_jobs = []

    for job in all_jobs:
        if not job_matches_source(job, source_filter):
            continue

        if not job_matches_freshness(job, freshness):
            continue

        if relevant_only and not is_relevant_job(job):
            continue

        if not job_matches_search(job, search):
            continue

        filtered_jobs.append(job)

    return filtered_jobs[offset:offset + limit]

def get_job_by_id(db: Session, job_id: int) -> Optional[Dict]:
    """
    Gets one saved job by ID.
    """

    query = text("""
        SELECT
            id,
            source,
            source_job_id,
            title,
            company,
            location,
            description,
            apply_url,
            extracted_skills,
            created_at
        FROM jobs
        WHERE id = :job_id;
    """)

    result = db.execute(
        query,
        {
            "job_id": job_id
        }
    )

    row = result.mappings().first()

    if row is None:
        return None

    return dict(row)