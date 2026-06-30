from pydantic import BaseModel
from typing import List, Optional


class ResumeUploadResponse(BaseModel):
    """
    Response returned after uploading and saving a resume.
    """

    resume_id: int
    filename: str
    text_length: int
    extracted_skills: List[str]
    embedding_length: int
    message: str


class ResumeResponse(BaseModel):
    """
    Response returned when fetching a saved resume.
    """

    id: int
    filename: str
    raw_text: Optional[str]
    parsed_skills: Optional[list]
    created_at: str


class JobFetchResponse(BaseModel):
    fetched_count: int
    saved_job_ids: List[int]
    message: str


class JobResponse(BaseModel):
    id: int
    source: Optional[str]
    source_job_id: Optional[str]
    title: Optional[str]
    company: Optional[str]
    location: Optional[str]
    description: Optional[str]
    apply_url: Optional[str]
    extracted_skills: Optional[list]
    created_at: str


class MatchJobResponse(BaseModel):
    resume_id: int
    job_id: int
    title: Optional[str]
    company: Optional[str]
    location: Optional[str]
    apply_url: Optional[str]
    semantic_score: float
    skill_score: float
    final_score: float
    matched_skills: List[str]
    missing_skills: List[str]


class MatchResponse(BaseModel):
    resume_id: int
    matched_count: int
    saved_match_ids: List[int]
    matches: List[MatchJobResponse]
    message: str


class ApplicationSaveRequest(BaseModel):
    job_id: int
    status: str = "saved"
    notes: Optional[str] = None


class ApplicationStatusUpdateRequest(BaseModel):
    status: str
    notes: Optional[str] = None


class ApplicationResponse(BaseModel):
    application_id: int
    job_id: int
    status: str
    notes: Optional[str]
    applied_at: Optional[str]
    created_at: str
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    apply_url: Optional[str] = None
    source: Optional[str] = None


class ApplicationSaveResponse(BaseModel):
    application_id: int
    message: str


class ApplicationDeleteResponse(BaseModel):
    application_id: int
    deleted: bool
    message: str

class FeedbackSaveRequest(BaseModel):
    resume_id: int
    job_id: int
    feedback_label: str


class FeedbackResponse(BaseModel):
    feedback_id: int
    resume_id: int
    job_id: int
    feedback_label: str
    created_at: str
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    apply_url: Optional[str] = None


class FeedbackSaveResponse(BaseModel):
    feedback_id: int
    message: str