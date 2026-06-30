import json
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


def save_resume(
    db: Session,
    filename: str,
    raw_text: str,
    skills: list[str],
    embedding: list[float]
) -> int:
    """
    Saves resume information into the resumes table.

    Returns the saved resume ID.
    """

    query = text("""
        INSERT INTO resumes (
            filename,
            raw_text,
            parsed_skills,
            embedding
        )
        VALUES (
            :filename,
            :raw_text,
            :parsed_skills,
            :embedding
        )
        RETURNING id;
    """)

    result = db.execute(
        query,
        {
            "filename": filename,
            "raw_text": raw_text,
            "parsed_skills": json.dumps(skills),
            "embedding": embedding
        }
    )

    resume_id = result.scalar_one()

    db.commit()

    return resume_id


def get_resume_by_id(db: Session, resume_id: int) -> Optional[dict]:
    """
    Gets one resume from the database by ID.
    """

    query = text("""
        SELECT
            id,
            filename,
            raw_text,
            parsed_skills,
            created_at
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

    return dict(row)



def get_all_resumes(db):
    """
    Gets all resumes without assuming exact column names.
    This prevents 500 errors if column names are slightly different.
    """

    query = text("""
        SELECT *
        FROM resumes
        ORDER BY id DESC
    """)

    result = db.execute(query).mappings().all()

    return [dict(row) for row in result]