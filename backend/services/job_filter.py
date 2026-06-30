from typing import Dict


STRONG_TITLE_KEYWORDS = [
    "data engineer",
    "data analyst",
    "analytics engineer",
    "business intelligence",
    "bi analyst",
    "software engineer",
    "backend engineer",
    "python developer",
    "machine learning engineer",
    "ml engineer",
    "ai engineer",
    "database developer",
    "sql developer",
    "etl developer",
    "data technician",
    "service desk analyst",
]


TECH_KEYWORDS = [
    "python",
    "sql",
    "postgresql",
    "mysql",
    "snowflake",
    "bigquery",
    "redshift",
    "spark",
    "pyspark",
    "airflow",
    "dbt",
    "etl",
    "elt",
    "data pipeline",
    "data pipelines",
    "data warehouse",
    "data lake",
    "aws",
    "azure",
    "gcp",
    "docker",
    "kubernetes",
    "api",
    "rest api",
    "machine learning",
    "nlp",
    "pandas",
    "numpy",
    "tableau",
    "power bi",
    "looker",
    "github",
    "git",
]


BLOCKED_TITLE_KEYWORDS = [
    "social media",
    "brand manager",
    "category manager",
    "sneakers",
    "courier",
    "executive assistant",
    "hr assistant",
    "hr administrative",
    "advertising",
    "marketing",
    "clinical",
    "pharmaceutical",
    "environmental health",
    "safety officer",
    "supply chain",
    "logistics coordinator",
    "contact center",
    "learning and development",
    "content creator",
]


def normalize_text(value: str | None) -> str:
    """
    Converts text to lowercase safe text for matching.
    """

    if not value:
        return ""

    return value.lower().strip()


def is_relevant_job(job: Dict) -> bool:
    """
    Returns True only for jobs relevant to data/software/AI career paths.
    """

    title = normalize_text(job.get("title"))
    description = normalize_text(job.get("description"))

    combined_text = f"{title} {description}"

    for blocked_keyword in BLOCKED_TITLE_KEYWORDS:
        if blocked_keyword in title:
            return False

    for title_keyword in STRONG_TITLE_KEYWORDS:
        if title_keyword in title:
            return True

    tech_match_count = 0

    for tech_keyword in TECH_KEYWORDS:
        if tech_keyword in combined_text:
            tech_match_count += 1

    return tech_match_count >= 2