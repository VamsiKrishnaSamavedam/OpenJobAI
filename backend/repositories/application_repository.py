from typing import List, Dict, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


VALID_APPLICATION_STATUSES = [
    "saved",
    "applied",
    "interviewing",
    "rejected",
    "offer"
]


def save_application(
    db: Session,
    job_id: int,
    status: str = "saved",
    notes: Optional[str] = None
) -> int:
    """
    Saves a job into the application tracker.

    If the job is already saved, it updates the existing application record.
    """

    if status not in VALID_APPLICATION_STATUSES:
        raise ValueError(
            f"Invalid status. Use one of: {VALID_APPLICATION_STATUSES}"
        )

    query = text("""
        INSERT INTO applications (
            job_id,
            status,
            notes
        )
        VALUES (
            :job_id,
            :status,
            :notes
        )
        ON CONFLICT (job_id)
        DO UPDATE SET
            status = EXCLUDED.status,
            notes = EXCLUDED.notes
        RETURNING id;
    """)

    result = db.execute(
        query,
        {
            "job_id": job_id,
            "status": status,
            "notes": notes
        }
    )

    application_id = result.scalar_one()

    db.commit()

    return application_id


def get_applications(
    db: Session,
    limit: int = 50
) -> List[Dict]:
    """
    Gets all tracked applications with job details.
    """

    query = text("""
        SELECT
            applications.id AS application_id,
            applications.job_id,
            applications.status,
            applications.notes,
            applications.applied_at,
            applications.created_at,
            jobs.title,
            jobs.company,
            jobs.location,
            jobs.apply_url,
            jobs.source
        FROM applications
        JOIN jobs ON applications.job_id = jobs.id
        ORDER BY applications.created_at DESC
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


def get_application_by_id(
    db: Session,
    application_id: int
) -> Optional[Dict]:
    """
    Gets one tracked application by application ID.
    """

    query = text("""
        SELECT
            applications.id AS application_id,
            applications.job_id,
            applications.status,
            applications.notes,
            applications.applied_at,
            applications.created_at,
            jobs.title,
            jobs.company,
            jobs.location,
            jobs.apply_url,
            jobs.source
        FROM applications
        JOIN jobs ON applications.job_id = jobs.id
        WHERE applications.id = :application_id;
    """)

    result = db.execute(
        query,
        {
            "application_id": application_id
        }
    )

    row = result.mappings().first()

    if row is None:
        return None

    return dict(row)


def update_application_status(
    db: Session,
    application_id: int,
    status: str,
    notes: Optional[str] = None
) -> Optional[Dict]:
    """
    Updates the status and notes of a tracked application.
    """

    if status not in VALID_APPLICATION_STATUSES:
        raise ValueError(
            f"Invalid status. Use one of: {VALID_APPLICATION_STATUSES}"
        )

    query = text("""
        UPDATE applications
        SET
            status = :status,
            notes = COALESCE(:notes, notes),
            applied_at = CASE
                WHEN :status = 'applied' AND applied_at IS NULL
                THEN CURRENT_TIMESTAMP
                ELSE applied_at
            END
        WHERE id = :application_id
        RETURNING
            id AS application_id,
            job_id,
            status,
            notes,
            applied_at,
            created_at;
    """)

    result = db.execute(
        query,
        {
            "application_id": application_id,
            "status": status,
            "notes": notes
        }
    )

    row = result.mappings().first()

    db.commit()

    if row is None:
        return None

    return dict(row)


def delete_application(
    db: Session,
    application_id: int
) -> bool:
    """
    Deletes an application from the tracker.
    """

    query = text("""
        DELETE FROM applications
        WHERE id = :application_id
        RETURNING id;
    """)

    result = db.execute(
        query,
        {
            "application_id": application_id
        }
    )

    deleted_id = result.scalar()

    db.commit()

    return deleted_id is not None