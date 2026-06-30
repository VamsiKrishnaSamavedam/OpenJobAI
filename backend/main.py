import json
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.config import APP_ENV, EMBEDDING_MODEL, USE_LLM
from backend.database import get_db, test_database_connection

from backend.services.resume_parser import parse_resume_file
from backend.services.skill_extractor import extract_skills
from backend.services.embedding_service import generate_embedding
from backend.services.job_fetcher import fetch_remoteok_jobs
from backend.services.matcher import match_resume_to_jobs
from backend.services.ats_compatibility_service import calculate_ats_compatibility
from backend.services.job_sources.multi_source_ingestion import (
    fetch_jobs_from_multiple_sources,
)
from backend.services.xgb_learning_service import (
    train_xgb_job_ranker,
    predict_ml_preference_scores,
)

from backend.repositories.resume_repository import (
    save_resume,
    get_resume_by_id,
    get_all_resumes,
)
from backend.repositories.job_repository import (
    save_jobs_bulk,
    save_job,
    get_jobs,
    get_job_by_id,
)
from backend.repositories.application_repository import (
    save_application,
    get_application_by_id,
    get_applications,
    update_application_status,
    delete_application,
)
from backend.repositories.feedback_repository import (
    save_feedback,
    get_all_feedback,
    get_feedback_by_resume,
)
from backend.repositories.match_repository import (
    get_jobs_for_matching,
    get_resume_for_matching,
    save_match_results_bulk,
)

from backend.schemas import (
    ResumeUploadResponse,
    ResumeResponse,
    JobFetchResponse,
    JobResponse,
    ApplicationResponse,
    ApplicationDeleteResponse,
    ApplicationSaveRequest,
    ApplicationSaveResponse,
    ApplicationStatusUpdateRequest,
    FeedbackResponse,
    FeedbackSaveRequest,
    FeedbackSaveResponse,
)


app = FastAPI(
    title="OpenJobAI Backend",
    description="AI job matching and resume tracking backend",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------------------------------------------------------------------
# General helpers
# -------------------------------------------------------------------


def convert_score_to_percent(value) -> int:
    """
    Converts scores to a 0-100 percentage.
    Handles values like 0.83 and 83.
    """

    try:
        numeric_value = float(value)

        if numeric_value <= 1:
            numeric_value = numeric_value * 100

        return round(numeric_value)

    except Exception:
        return 0


def get_match_job_id(match: dict):
    """
    Safely gets job ID from match result.
    Different matching functions may return job_id or id.
    """

    return (
        match.get("job_id")
        or match.get("id")
        or match.get("job", {}).get("id")
    )


def convert_datetime_fields(record: dict, fields: list[str]) -> dict:
    """
    Converts datetime fields to strings so FastAPI returns clean JSON.
    """

    for field in fields:
        if record.get(field) is not None:
            record[field] = str(record[field])

    return record


def parse_resume_skills(value):
    """
    Safely converts resume skills from list/string/json into a Python list.
    """

    if value is None:
        return []

    if isinstance(value, list):
        return [
            str(skill).strip()
            for skill in value
            if str(skill).strip()
        ]

    if isinstance(value, str):
        try:
            parsed_value = json.loads(value)

            if isinstance(parsed_value, list):
                return [
                    str(skill).strip()
                    for skill in parsed_value
                    if str(skill).strip()
                ]

        except Exception:
            return [
                skill.strip()
                for skill in value.split(",")
                if skill.strip()
            ]

    return []


def get_resume_skills_for_api(resume: dict, raw_text: str) -> list[str]:
    """
    Gets resume skills for the frontend.

    First tries stored skill fields.
    If stored skills are missing, extracts skills again from resume text.
    This fixes Resume Center showing 0 extracted skills.
    """

    possible_skill_fields = [
        "extracted_skills",
        "skills",
        "parsed_skills",
        "resume_skills",
        "skill_list",
    ]

    for field_name in possible_skill_fields:
        parsed_skills = parse_resume_skills(resume.get(field_name))

        if parsed_skills:
            return parsed_skills

    if raw_text and raw_text.strip():
        try:
            return extract_skills(raw_text)
        except Exception as error:
            print(f"Resume skill fallback extraction failed: {error}")
            return []

    return []


def prepare_job_for_json(job: dict) -> dict:
    """
    Cleans a job record before sending it to frontend.
    """

    if job.get("created_at") is not None:
        job["created_at"] = str(job["created_at"])

    job.pop("embedding", None)

    return job


def build_job_text(job: dict) -> str:
    """
    Builds text used for skill extraction and embeddings.
    """

    return f"""
    {job.get("title", "")}
    {job.get("company", "")}
    {job.get("location", "")}
    {job.get("description", "")}
    """


def enrich_jobs_with_scores(
    db: Session,
    jobs: list[dict],
    resume_id: Optional[int],
) -> list[dict]:
    """
    Adds ATS score, ML preference score, recommended score,
    and ATS details to visible job records.
    """

    if resume_id is None:
        return jobs

    selected_resume = get_resume_for_matching(
        db=db,
        resume_id=resume_id,
    )

    if selected_resume is None:
        raise HTTPException(
            status_code=404,
            detail=f"Resume with ID {resume_id} was not found.",
        )

    visible_job_ids = {
        job.get("id")
        for job in jobs
        if job.get("id") is not None
    }

    matching_jobs = get_jobs_for_matching(
        db=db,
        limit=5000,
    )

    matching_jobs = [
        job
        for job in matching_jobs
        if job.get("id") in visible_job_ids
    ]

    matching_jobs_by_id = {
        job.get("id"): job
        for job in matching_jobs
        if job.get("id") is not None
    }

    match_results = match_resume_to_jobs(
        resume=selected_resume,
        jobs=matching_jobs,
    )

    ml_preference_scores = predict_ml_preference_scores(
        match_results=match_results,
        jobs=matching_jobs,
        resume=selected_resume,
    )

    match_by_job_id = {}

    for match in match_results:
        match_job_id = get_match_job_id(match)

        if match_job_id is not None:
            match_by_job_id[int(match_job_id)] = match

    for job in jobs:
        job_id = job.get("id")

        if job_id not in match_by_job_id:
            continue

        match = match_by_job_id[job_id]
        matching_job = matching_jobs_by_id.get(job_id, job)

        ats_result = calculate_ats_compatibility(
            resume=selected_resume,
            job=matching_job,
            match=match,
        )

        ats_score = convert_score_to_percent(
            ats_result.get("ats_compatibility_score")
        )

        semantic_score = convert_score_to_percent(
            ats_result.get("semantic_score")
        )

        skill_score = convert_score_to_percent(
            ats_result.get("skill_score")
        )

        ml_preference_score = ml_preference_scores.get(
            int(job_id),
            None,
        )

        if ml_preference_score is not None:
            recommended_score = round(
                (ats_score * 0.70)
                + (ml_preference_score * 0.30)
            )
        else:
            recommended_score = ats_score

        job["ats_score"] = ats_score
        job["ats_compatibility_score"] = ats_score
        job["ml_preference_score"] = ml_preference_score
        job["recommended_score"] = recommended_score

        job["ats_details"] = {
            "score": ats_score,
            "final_score": ats_score,
            "ats_score": ats_score,
            "ats_compatibility_score": ats_score,
            "semantic_score": semantic_score,
            "skill_score": skill_score,
            "ml_preference_score": ml_preference_score,
            "recommended_score": recommended_score,
            "required_skill_score": ats_result.get("required_skill_score"),
            "preferred_skill_score": ats_result.get("preferred_skill_score"),
            "experience_score": ats_result.get("experience_score"),
            "title_score": ats_result.get("title_score"),
            "education_score": ats_result.get("education_score"),
            "keyword_context_score": ats_result.get("keyword_context_score"),
            "location_score": ats_result.get("location_score"),
            "required_years": ats_result.get("required_years"),
            "resume_years": ats_result.get("resume_years"),
            "degree_required": ats_result.get("degree_required"),
            "degree_found": ats_result.get("degree_found"),
            "required_skills": ats_result.get("required_skills") or [],
            "preferred_skills": ats_result.get("preferred_skills") or [],
            "matched_skills": match.get("matched_skills") or [],
            "missing_skills": match.get("missing_skills") or [],
            "knockout_flags": ats_result.get("knockout_flags") or [],
            "ats_explanation": ats_result.get("ats_explanation") or [],
        }

    jobs = sorted(
        jobs,
        key=lambda job: job.get(
            "recommended_score",
            job.get("ats_score", 0),
        ),
        reverse=True,
    )

    return jobs


# -------------------------------------------------------------------
# Root and health
# -------------------------------------------------------------------


@app.get("/")
def root():
    return {
        "message": "OpenJobAI backend is running",
        "environment": APP_ENV,
    }


@app.get("/health")
def health_check():
    database_ok, database_error = test_database_connection()

    return {
        "status": "healthy" if database_ok else "unhealthy",
        "database_connected": database_ok,
        "database_error": database_error,
        "embedding_model": EMBEDDING_MODEL,
        "use_llm": USE_LLM,
    }


# -------------------------------------------------------------------
# Dashboard stats and DB helpers
# -------------------------------------------------------------------


def table_exists(db: Session, table_name: str) -> bool:
    """
    Checks whether a table exists in the public schema.
    """

    result = db.execute(
        text("SELECT to_regclass(:table_name)"),
        {"table_name": f"public.{table_name}"},
    ).scalar()

    return result is not None


def column_exists(db: Session, table_name: str, column_name: str) -> bool:
    """
    Checks whether a column exists in a table.
    """

    result = db.execute(
        text(
            """
            SELECT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = :table_name
                AND column_name = :column_name
            )
            """
        ),
        {
            "table_name": table_name,
            "column_name": column_name,
        },
    ).scalar()

    return bool(result)


def count_table_if_exists(db: Session, table_name: str) -> int:
    """
    Safely counts a table only if it exists.
    """

    allowed_tables = {
        "resumes",
        "jobs",
        "applications",
    }

    if table_name not in allowed_tables:
        return 0

    if not table_exists(db, table_name):
        return 0

    return db.execute(
        text(f"SELECT COUNT(*) FROM {table_name}")
    ).scalar() or 0


def get_latest_resume_id_if_exists(db: Session) -> Optional[int]:
    """
    Safely gets the latest resume ID if resumes table exists.
    """

    if not table_exists(db, "resumes"):
        return None

    latest_resume_id = db.execute(
        text("SELECT id FROM resumes ORDER BY id DESC LIMIT 1")
    ).scalar()

    return latest_resume_id


def get_feedback_count_safely(db: Session) -> int:
    """
    Counts feedback using the existing feedback repository.

    This avoids directly querying a physical table named feedback,
    because your database showed that table does not exist.
    """

    try:
        feedback_records = get_all_feedback(
            db=db,
            limit=100000,
        )

        return len(feedback_records)

    except Exception as error:
        print(f"Dashboard feedback count skipped: {error}")
        return 0


def delete_resume_dependencies_if_exist(db: Session, resume_id: int) -> None:
    """
    Deletes rows in related tables that may reference a resume.
    This prevents foreign key errors when deleting a resume.
    """

    possible_dependency_tables = [
        "matches",
        "match_results",
        "resume_matches",
        "feedback",
        "feedbacks",
        "job_feedback",
        "resume_job_feedback",
        "user_feedback",
    ]

    for table_name in possible_dependency_tables:
        try:
            if table_exists(db, table_name) and column_exists(
                db=db,
                table_name=table_name,
                column_name="resume_id",
            ):
                db.execute(
                    text(f"DELETE FROM {table_name} WHERE resume_id = :resume_id"),
                    {"resume_id": resume_id},
                )

        except Exception as error:
            print(f"Skipping dependency cleanup for {table_name}: {error}")


@app.get("/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Returns live dashboard counts.
    """

    total_resumes = count_table_if_exists(db, "resumes")
    total_jobs = count_table_if_exists(db, "jobs")
    total_applications = count_table_if_exists(db, "applications")
    total_feedback = get_feedback_count_safely(db)

    latest_resume_id = get_latest_resume_id_if_exists(db)

    xgb_model_path = (
        Path(__file__).resolve().parent
        / "models"
        / "xgb_job_ranker.json"
    )

    return {
        "total_resumes": total_resumes,
        "total_jobs": total_jobs,
        "total_applications": total_applications,
        "total_feedback": total_feedback,
        "latest_resume_id": latest_resume_id,
        "xgb_model_trained": xgb_model_path.exists(),
    }


# -------------------------------------------------------------------
# Resume routes
# -------------------------------------------------------------------


@app.post("/resumes/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Uploads a resume file, extracts text, extracts skills,
    generates embedding, and saves everything to PostgreSQL.
    """

    try:
        file_bytes = await file.read()

        resume_text = parse_resume_file(
            filename=file.filename,
            file_bytes=file_bytes,
        )

        if not resume_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Could not extract text from the uploaded resume.",
            )

        skills = extract_skills(resume_text)
        embedding = generate_embedding(resume_text)

        resume_id = save_resume(
            db=db,
            filename=file.filename,
            raw_text=resume_text,
            skills=skills,
            embedding=embedding,
        )

        return ResumeUploadResponse(
            resume_id=resume_id,
            filename=file.filename,
            text_length=len(resume_text),
            extracted_skills=skills,
            embedding_length=len(embedding),
            message="Resume uploaded and saved successfully.",
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Resume upload failed: {str(error)}",
        )


@app.get("/resumes")
def read_all_resumes(db: Session = Depends(get_db)):
    """
    Gets all stored resumes so frontend can choose the active resume.
    """

    try:
        resumes = get_all_resumes(db)

        cleaned_resumes = []

        for resume in resumes:
            resume_id = resume.get("id")

            filename = (
                resume.get("filename")
                or resume.get("file_name")
                or resume.get("name")
                or f"Resume {resume_id}"
            )

            raw_text = (
                resume.get("raw_text")
                or resume.get("resume_text")
                or resume.get("text")
                or resume.get("content")
                or ""
            )

            raw_text = str(raw_text)

            parsed_skills = get_resume_skills_for_api(
                resume=resume,
                raw_text=raw_text,
            )

            created_at = resume.get("created_at")

            cleaned_resumes.append(
                {
                    "id": resume_id,
                    "filename": filename,
                    "created_at": str(created_at) if created_at else "",
                    "text_length": len(raw_text),
                    "text_preview": raw_text[:250],
                    "extracted_skills": parsed_skills,
                    "skills_count": len(parsed_skills),
                }
            )

        return cleaned_resumes

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Reading resumes failed: {str(error)}",
        )


@app.get("/resumes/{resume_id}", response_model=ResumeResponse)
def read_resume(
    resume_id: int,
    db: Session = Depends(get_db),
):
    """
    Fetches a saved resume by ID.
    """

    resume = get_resume_by_id(db, resume_id)

    if resume is None:
        raise HTTPException(
            status_code=404,
            detail="Resume not found.",
        )

    if resume.get("created_at") is not None:
        resume["created_at"] = str(resume["created_at"])

    return resume


@app.delete("/resumes/{resume_id}")
def delete_resume(
    resume_id: int,
    db: Session = Depends(get_db),
):
    """
    Deletes a resume and related resume-dependent records if they exist.
    """

    try:
        if not table_exists(db, "resumes"):
            raise HTTPException(
                status_code=404,
                detail="Resumes table not found.",
            )

        existing_resume = db.execute(
            text("SELECT id FROM resumes WHERE id = :resume_id"),
            {"resume_id": resume_id},
        ).scalar()

        if existing_resume is None:
            raise HTTPException(
                status_code=404,
                detail="Resume not found.",
            )

        delete_resume_dependencies_if_exist(
            db=db,
            resume_id=resume_id,
        )

        result = db.execute(
            text("DELETE FROM resumes WHERE id = :resume_id"),
            {"resume_id": resume_id},
        )

        db.commit()

        if result.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail="Resume not found.",
            )

        return {
            "resume_id": resume_id,
            "deleted": True,
            "message": "Resume deleted successfully.",
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Deleting resume failed: {str(error)}",
        )


# -------------------------------------------------------------------
# Job routes
# -------------------------------------------------------------------


@app.post("/jobs/fetch", response_model=JobFetchResponse)
def fetch_and_save_jobs(
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """
    Fetches jobs from RemoteOK, extracts skills,
    generates embeddings, and saves them into PostgreSQL.
    """

    try:
        raw_jobs = fetch_remoteok_jobs(limit=limit)

        prepared_jobs = []

        for job in raw_jobs:
            job_text = build_job_text(job)

            skills = extract_skills(job_text)
            embedding = generate_embedding(job_text)

            prepared_jobs.append(
                {
                    **job,
                    "extracted_skills": skills,
                    "embedding": embedding,
                }
            )

        saved_job_ids = save_jobs_bulk(db, prepared_jobs)

        return JobFetchResponse(
            fetched_count=len(prepared_jobs),
            saved_job_ids=saved_job_ids,
            message="Jobs fetched and saved successfully.",
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Job fetch failed: {str(error)}",
        )


@app.get("/jobs")
def read_jobs(
    limit: int = 20,
    offset: int = 0,
    search: Optional[str] = None,
    source_filter: str = "all",
    freshness: str = "all",
    relevant_only: bool = False,
    resume_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Gets available jobs.

    If resume_id is provided, this endpoint calculates:
    - ATS Compatibility Score
    - ML Preference Score
    - Recommended Score
    """

    try:
        jobs = get_jobs(
            db=db,
            limit=limit,
            offset=offset,
            search=search,
            source_filter=source_filter,
            freshness=freshness,
            relevant_only=relevant_only,
        )

        jobs = enrich_jobs_with_scores(
            db=db,
            jobs=jobs,
            resume_id=resume_id,
        )

        jobs = [
            prepare_job_for_json(job)
            for job in jobs
        ]

        return jobs

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Reading jobs failed: {str(error)}",
        )


@app.get("/jobs/{job_id}", response_model=JobResponse)
def read_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    """
    Gets one saved job by ID.
    """

    job = get_job_by_id(db, job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found.",
        )

    job = prepare_job_for_json(job)

    return job


@app.post("/jobs/search-fetch")
def search_and_fetch_jobs(
    query: str,
    location: Optional[str] = None,
    limit: int = 20,
    resume_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Searches live jobs from Apify sources using a user-entered query.

    Flow:
    - User enters role/title.
    - Backend fetches fresh jobs from Apify.
    - Jobs are saved to PostgreSQL.
    - Saved/scored jobs are returned.
    """

    try:
        if not query or not query.strip():
            raise HTTPException(
                status_code=400,
                detail="Search query is required.",
            )

        fetched_jobs = fetch_jobs_from_multiple_sources(
            search_query=query.strip(),
            location=location,
            max_items=limit,
        )

        saved_count = 0

        for job in fetched_jobs:
            try:
                job_text = build_job_text(job)

                job_skills = extract_skills(job_text)
                job_embedding = generate_embedding(job_text)

                save_job(
                    db=db,
                    source=job.get("source") or "unknown",
                    source_job_id=job.get("source_job_id") or "",
                    title=job.get("title") or "",
                    company=job.get("company") or "",
                    location=job.get("location") or "",
                    description=job.get("description") or "",
                    apply_url=job.get("apply_url") or "",
                    extracted_skills=job_skills,
                    embedding=job_embedding,
                )

                saved_count += 1

            except Exception as save_error:
                print(f"Failed to save searched job: {save_error}")

        jobs = get_jobs(
            db=db,
            limit=limit,
            offset=0,
            search=query.strip(),
            source_filter="all",
            freshness="all",
            relevant_only=False,
        )

        jobs = enrich_jobs_with_scores(
            db=db,
            jobs=jobs,
            resume_id=resume_id,
        )

        jobs = [
            prepare_job_for_json(job)
            for job in jobs
        ]

        return {
            "query": query,
            "location": location,
            "fetched_count": len(fetched_jobs),
            "saved_count": saved_count,
            "jobs": jobs,
            "message": f"Fetched {saved_count} new jobs for '{query}'.",
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Live job search failed: {str(error)}",
        )


@app.post("/jobs/fetch/multi-source", response_model=JobFetchResponse)
def fetch_multi_source_jobs_endpoint(db: Session = Depends(get_db)):
    """
    Fetches jobs from multi-source ingestion,
    extracts skills, generates embeddings, and saves jobs.
    """

    try:
        raw_jobs = fetch_jobs_from_multiple_sources()

        if not raw_jobs:
            raise HTTPException(
                status_code=404,
                detail="No jobs were fetched from any source.",
            )

        prepared_jobs = []

        for job in raw_jobs:
            job_text = build_job_text(job)

            skills = extract_skills(job_text)
            embedding = generate_embedding(job_text)

            prepared_jobs.append(
                {
                    **job,
                    "extracted_skills": skills,
                    "embedding": embedding,
                }
            )

        job_ids = save_jobs_bulk(db, prepared_jobs)

        return JobFetchResponse(
            fetched_count=len(job_ids),
            saved_job_ids=job_ids,
            message="Multi-source jobs fetched and saved successfully.",
        )

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Multi-source job fetch failed: {str(error)}",
        )


# -------------------------------------------------------------------
# Matching route
# -------------------------------------------------------------------


@app.post("/match/resume/{resume_id}")
def match_resume(
    resume_id: int,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """
    Matches one saved resume against saved jobs.

    Returns:
    - ATS Compatibility Score
    - ML Preference Score
    - Recommended Score
    - Full ATS component scores
    """

    try:
        resume = get_resume_for_matching(
            db=db,
            resume_id=resume_id,
        )

        if resume is None:
            raise HTTPException(
                status_code=404,
                detail="Resume not found.",
            )

        jobs = get_jobs_for_matching(
            db=db,
            limit=limit,
        )

        if not jobs:
            raise HTTPException(
                status_code=404,
                detail="No jobs found. Please fetch jobs first.",
            )

        jobs_by_id = {
            job.get("id"): job
            for job in jobs
            if job.get("id") is not None
        }

        matches = match_resume_to_jobs(
            resume=resume,
            jobs=jobs,
        )

        ml_preference_scores = predict_ml_preference_scores(
            match_results=matches,
            jobs=jobs,
            resume=resume,
        )

        enhanced_matches = []

        for match in matches:
            job_id = get_match_job_id(match)

            if job_id is None:
                continue

            job = jobs_by_id.get(int(job_id))

            if job is None:
                continue

            ats_result = calculate_ats_compatibility(
                resume=resume,
                job=job,
                match=match,
            )

            ats_score = convert_score_to_percent(
                ats_result.get("ats_compatibility_score")
            )

            semantic_score = convert_score_to_percent(
                ats_result.get("semantic_score")
            )

            skill_score = convert_score_to_percent(
                ats_result.get("skill_score")
            )

            ml_preference_score = ml_preference_scores.get(
                int(job_id),
                None,
            )

            if ml_preference_score is not None:
                recommended_score = round(
                    (ats_score * 0.70)
                    + (ml_preference_score * 0.30)
                )
            else:
                recommended_score = ats_score

            enhanced_match = {
                **match,
                "job_id": int(job_id),
                "ats_score": ats_score,
                "final_score": ats_score,
                "ats_compatibility_score": ats_score,
                "semantic_score": semantic_score,
                "skill_score": skill_score,
                "ml_preference_score": ml_preference_score,
                "recommended_score": recommended_score,
                "required_skill_score": ats_result.get("required_skill_score"),
                "preferred_skill_score": ats_result.get("preferred_skill_score"),
                "experience_score": ats_result.get("experience_score"),
                "title_score": ats_result.get("title_score"),
                "education_score": ats_result.get("education_score"),
                "keyword_context_score": ats_result.get("keyword_context_score"),
                "location_score": ats_result.get("location_score"),
                "required_years": ats_result.get("required_years"),
                "resume_years": ats_result.get("resume_years"),
                "degree_required": ats_result.get("degree_required"),
                "degree_found": ats_result.get("degree_found"),
                "required_skills": ats_result.get("required_skills") or [],
                "preferred_skills": ats_result.get("preferred_skills") or [],
                "knockout_flags": ats_result.get("knockout_flags") or [],
                "ats_explanation": ats_result.get("ats_explanation") or [],
            }

            enhanced_matches.append(enhanced_match)

        enhanced_matches = sorted(
            enhanced_matches,
            key=lambda match: match.get(
                "recommended_score",
                match.get("ats_score", 0),
            ),
            reverse=True,
        )

        try:
            saved_match_ids = save_match_results_bulk(
                db=db,
                match_results=matches,
            )
        except Exception:
            saved_match_ids = []

        return {
            "resume_id": resume_id,
            "matched_count": len(enhanced_matches),
            "saved_match_ids": saved_match_ids,
            "matches": enhanced_matches,
            "message": "Resume matched successfully with upgraded ATS Compatibility and XGBoost learning scores.",
        }

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Resume matching failed: {str(error)}",
        )


# -------------------------------------------------------------------
# Application routes
# -------------------------------------------------------------------


@app.post("/applications/save", response_model=ApplicationSaveResponse)
def save_job_application(
    request: ApplicationSaveRequest,
    db: Session = Depends(get_db),
):
    """
    Saves a job into the application tracker.
    """

    try:
        application_id = save_application(
            db=db,
            job_id=request.job_id,
            status=request.status,
            notes=request.notes,
        )

        return ApplicationSaveResponse(
            application_id=application_id,
            message="Job saved to application tracker successfully.",
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Saving application failed: {str(error)}",
        )


def convert_application_dates(application: dict) -> dict:
    """
    Converts application datetime fields to strings.
    """

    return convert_datetime_fields(
        application,
        fields=["applied_at", "created_at"],
    )


@app.get("/applications", response_model=List[ApplicationResponse])
def read_applications(
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """
    Gets all tracked applications.
    """

    applications = get_applications(
        db=db,
        limit=limit,
    )

    applications = [
        convert_application_dates(application)
        for application in applications
    ]

    return applications


@app.get("/applications/{application_id}", response_model=ApplicationResponse)
def read_application(
    application_id: int,
    db: Session = Depends(get_db),
):
    """
    Gets one tracked application.
    """

    application = get_application_by_id(
        db=db,
        application_id=application_id,
    )

    if application is None:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    return convert_application_dates(application)


@app.patch("/applications/{application_id}/status", response_model=ApplicationResponse)
def update_application(
    application_id: int,
    request: ApplicationStatusUpdateRequest,
    db: Session = Depends(get_db),
):
    """
    Updates application status and notes.
    """

    try:
        updated_application = update_application_status(
            db=db,
            application_id=application_id,
            status=request.status,
            notes=request.notes,
        )

        if updated_application is None:
            raise HTTPException(
                status_code=404,
                detail="Application not found.",
            )

        full_application = get_application_by_id(
            db=db,
            application_id=application_id,
        )

        return convert_application_dates(full_application)

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )


@app.delete("/applications/{application_id}", response_model=ApplicationDeleteResponse)
def remove_application(
    application_id: int,
    db: Session = Depends(get_db),
):
    """
    Deletes an application from the tracker.
    """

    deleted = delete_application(
        db=db,
        application_id=application_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Application not found.",
        )

    return ApplicationDeleteResponse(
        application_id=application_id,
        deleted=True,
        message="Application deleted successfully.",
    )


# -------------------------------------------------------------------
# Feedback and ML routes
# -------------------------------------------------------------------


def convert_feedback_dates(feedback: dict) -> dict:
    """
    Converts feedback datetime fields to strings.
    """

    return convert_datetime_fields(
        feedback,
        fields=["created_at"],
    )


@app.post("/ml/train-xgb-ranker")
def train_xgb_ranker_endpoint(db: Session = Depends(get_db)):
    """
    Trains the XGBoost learning-to-rank model using user feedback.
    """

    try:
        result = train_xgb_job_ranker(db)

        return result

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"XGBoost training failed: {str(error)}",
        )


@app.post("/feedback", response_model=FeedbackSaveResponse)
def create_feedback(
    request: FeedbackSaveRequest,
    db: Session = Depends(get_db),
):
    """
    Saves user feedback for a resume-job pair.
    """

    try:
        feedback_id = save_feedback(
            db=db,
            resume_id=request.resume_id,
            job_id=request.job_id,
            feedback_label=request.feedback_label,
        )

        return FeedbackSaveResponse(
            feedback_id=feedback_id,
            message="Feedback saved successfully.",
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Saving feedback failed: {str(error)}",
        )


@app.get("/feedback", response_model=List[FeedbackResponse])
def read_feedback(
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Gets all feedback records.
    """

    feedback_records = get_all_feedback(
        db=db,
        limit=limit,
    )

    feedback_records = [
        convert_feedback_dates(feedback)
        for feedback in feedback_records
    ]

    return feedback_records


@app.get("/feedback/resume/{resume_id}", response_model=List[FeedbackResponse])
def read_feedback_for_resume(
    resume_id: int,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """
    Gets all feedback records for one resume.
    """

    feedback_records = get_feedback_by_resume(
        db=db,
        resume_id=resume_id,
        limit=limit,
    )

    feedback_records = [
        convert_feedback_dates(feedback)
        for feedback in feedback_records
    ]

    return feedback_records