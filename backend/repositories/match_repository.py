import json
from typing import List, Dict, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


def parse_vector(vector_value) -> list[float]:
    """
    Converts PostgreSQL pgvector output into a Python list of floats.
    """

    if vector_value is None:
        return []

    if isinstance(vector_value, list):
        return vector_value

    vector_text = str(vector_value).strip()

    vector_text = vector_text.replace("[", "").replace("]", "")

    if not vector_text:
        return []

    return [float(value) for value in vector_text.split(",")]


def get_resume_for_matching(
    db: Session,
    resume_id: int
) -> Optional[Dict]:
    """
    Gets resume data needed for matching.
    """

    query = text("""
        SELECT
            id,
            filename,
            parsed_skills,
            embedding::text AS embedding
        FROM resumes
        WHERE id = :resume_id;
    """)

    result = db.execute(
        query,
        {
            "resume_id": resume_id
        }
    )

    row = result.mappings().first()

    if row is None:
        return None

    resume = dict(row)
    resume["embedding"] = parse_vector(resume["embedding"])

    return resume


def get_jobs_for_matching(
    db: Session,
    limit: int = 50
) -> List[Dict]:
    """
    Gets jobs with embeddings for matching.
    """

    query = text("""
        SELECT
            id,
            title,
            company,
            location,
            apply_url,
            extracted_skills,
            embedding::text AS embedding
        FROM jobs
        WHERE embedding IS NOT NULL
        ORDER BY created_at DESC
        LIMIT :limit;
    """)

    result = db.execute(
        query,
        {
            "limit": limit
        }
    )

    rows = result.mappings().all()

    jobs = []

    for row in rows:
        job = dict(row)
        job["embedding"] = parse_vector(job["embedding"])
        jobs.append(job)

    return jobs


def save_match_result(
    db: Session,
    match_result: Dict
) -> int:
    """
    Saves one match score into the match_scores table.

    If the same resume_id + job_id already exists,
    update the existing match score instead of creating a duplicate.
    """

    query = text("""
        INSERT INTO match_scores (
            resume_id,
            job_id,
            semantic_score,
            skill_score,
            final_score,
            matched_skills,
            missing_skills
        )
        VALUES (
            :resume_id,
            :job_id,
            :semantic_score,
            :skill_score,
            :final_score,
            :matched_skills,
            :missing_skills
        )
        ON CONFLICT (resume_id, job_id)
        DO UPDATE SET
            semantic_score = EXCLUDED.semantic_score,
            skill_score = EXCLUDED.skill_score,
            final_score = EXCLUDED.final_score,
            matched_skills = EXCLUDED.matched_skills,
            missing_skills = EXCLUDED.missing_skills,
            created_at = CURRENT_TIMESTAMP
        RETURNING id;
    """)

    result = db.execute(
        query,
        {
            "resume_id": match_result["resume_id"],
            "job_id": match_result["job_id"],
            "semantic_score": match_result["semantic_score"],
            "skill_score": match_result["skill_score"],
            "final_score": match_result["final_score"],
            "matched_skills": json.dumps(match_result["matched_skills"]),
            "missing_skills": json.dumps(match_result["missing_skills"])
        }
    )

    match_id = result.scalar_one()

    db.commit()

    return match_id


def save_match_results_bulk(
    db: Session,
    match_results: List[Dict]
) -> List[int]:
    """
    Saves multiple match results.
    """

    match_ids = []

    for match_result in match_results:
        match_id = save_match_result(db, match_result)
        match_ids.append(match_id)

    return match_ids