from typing import List, Dict, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


VALID_FEEDBACK_LABELS = [
    "interested",
    "not_interested",
    "applied",
    "interviewing",
    "rejected",
    "offer"
]


def save_feedback(
    db: Session,
    resume_id: int,
    job_id: int,
    feedback_label: str
) -> int:
    """
    Saves user feedback for a resume-job match.

    If feedback already exists for the same resume_id + job_id,
    update the existing feedback label.
    """

    if feedback_label not in VALID_FEEDBACK_LABELS:
        raise ValueError(
            f"Invalid feedback label. Use one of: {VALID_FEEDBACK_LABELS}"
        )

    query = text("""
        INSERT INTO user_feedback (
            resume_id,
            job_id,
            feedback_label
        )
        VALUES (
            :resume_id,
            :job_id,
            :feedback_label
        )
        ON CONFLICT (resume_id, job_id)
        DO UPDATE SET
            feedback_label = EXCLUDED.feedback_label,
            created_at = CURRENT_TIMESTAMP
        RETURNING id;
    """)

    result = db.execute(
        query,
        {
            "resume_id": resume_id,
            "job_id": job_id,
            "feedback_label": feedback_label
        }
    )

    feedback_id = result.scalar_one()

    db.commit()

    return feedback_id


def get_all_feedback(
    db: Session,
    limit: int = 100
) -> List[Dict]:
    """
    Gets all user feedback records with job details.
    """

    query = text("""
        SELECT
            user_feedback.id AS feedback_id,
            user_feedback.resume_id,
            user_feedback.job_id,
            user_feedback.feedback_label,
            user_feedback.created_at,
            jobs.title,
            jobs.company,
            jobs.location,
            jobs.apply_url
        FROM user_feedback
        JOIN jobs ON user_feedback.job_id = jobs.id
        ORDER BY user_feedback.created_at DESC
        LIMIT :limit;
    """)

    result = db.execute(
        query,
        {
            "limit": limit
        }
    )

    rows = result.mappings().all()

    return [dict(row) for row in rows]


def get_feedback_by_resume(
    db: Session,
    resume_id: int,
    limit: int = 100
) -> List[Dict]:
    """
    Gets feedback records for one resume.
    """

    query = text("""
        SELECT
            user_feedback.id AS feedback_id,
            user_feedback.resume_id,
            user_feedback.job_id,
            user_feedback.feedback_label,
            user_feedback.created_at,
            jobs.title,
            jobs.company,
            jobs.location,
            jobs.apply_url
        FROM user_feedback
        JOIN jobs ON user_feedback.job_id = jobs.id
        WHERE user_feedback.resume_id = :resume_id
        ORDER BY user_feedback.created_at DESC
        LIMIT :limit;
    """)

    result = db.execute(
        query,
        {
            "resume_id": resume_id,
            "limit": limit
        }
    )

    rows = result.mappings().all()

    return [dict(row) for row in rows]