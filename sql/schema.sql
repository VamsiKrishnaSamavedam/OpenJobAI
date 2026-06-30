CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS resumes (
    id SERIAL PRIMARY KEY,
    filename TEXT NOT NULL,
    raw_text TEXT NOT NULL,
    skills JSONB,
    embedding vector(384),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS jobs (
    id SERIAL PRIMARY KEY,
    source TEXT NOT NULL,
    external_job_id TEXT,
    title TEXT NOT NULL,
    company TEXT,
    location TEXT,
    job_type TEXT,
    url TEXT,
    raw_description TEXT,
    clean_description TEXT,
    required_skills JSONB,
    preferred_skills JSONB,
    embedding vector(384),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source, external_job_id, url)
);

CREATE TABLE IF NOT EXISTS match_scores (
    id SERIAL PRIMARY KEY,
    resume_id INTEGER REFERENCES resumes(id) ON DELETE CASCADE,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    semantic_score FLOAT,
    skill_score FLOAT,
    xgboost_score FLOAT,
    final_score FLOAT,
    matched_skills JSONB,
    missing_skills JSONB,
    model_used TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(resume_id, job_id)
);

CREATE TABLE IF NOT EXISTS applications (
    id SERIAL PRIMARY KEY,
    resume_id INTEGER REFERENCES resumes(id) ON DELETE SET NULL,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'Saved',
    notes TEXT,
    applied_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_feedback (
    id SERIAL PRIMARY KEY,
    resume_id INTEGER REFERENCES resumes(id) ON DELETE CASCADE,
    job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
    feedback_label INTEGER NOT NULL,
    feedback_type TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(resume_id, job_id, feedback_type)
);

CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs(title);
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);

CREATE INDEX IF NOT EXISTS idx_jobs_embedding
ON jobs
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_resumes_embedding
ON resumes
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);