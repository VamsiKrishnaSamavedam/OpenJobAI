import math
from typing import List, Dict


def cosine_similarity(vector_a: list[float], vector_b: list[float]) -> float:
    """
    Calculates cosine similarity between two vectors.

    Output range:
    - 1.0 means very similar
    - 0.0 means not similar
    """

    if not vector_a or not vector_b:
        return 0.0

    dot_product = 0.0
    magnitude_a = 0.0
    magnitude_b = 0.0

    for a, b in zip(vector_a, vector_b):
        dot_product += a * b
        magnitude_a += a * a
        magnitude_b += b * b

    magnitude_a = math.sqrt(magnitude_a)
    magnitude_b = math.sqrt(magnitude_b)

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


def calculate_skill_score(
    resume_skills: list[str],
    job_skills: list[str]
) -> tuple[float, list[str], list[str]]:
    """
    Compares resume skills with job skills.

    Returns:
    - skill_score
    - matched_skills
    - missing_skills
    """

    resume_skill_set = set(resume_skills or [])
    job_skill_set = set(job_skills or [])

    if not job_skill_set:
        return 0.0, [], []

    matched_skills = sorted(list(resume_skill_set.intersection(job_skill_set)))
    missing_skills = sorted(list(job_skill_set.difference(resume_skill_set)))

    skill_score = len(matched_skills) / len(job_skill_set)

    return skill_score, matched_skills, missing_skills


def calculate_final_score(
    semantic_score: float,
    skill_score: float
) -> float:
    """
    Combines semantic similarity and skill overlap into one final score.
    """

    final_score = (semantic_score * 0.70) + (skill_score * 0.30)

    return round(final_score, 4)


def match_resume_to_jobs(
    resume: Dict,
    jobs: List[Dict]
) -> List[Dict]:
    """
    Matches one resume against many jobs.
    """

    results = []

    resume_embedding = resume["embedding"]
    resume_skills = resume["parsed_skills"] or []

    for job in jobs:
        job_embedding = job["embedding"]
        job_skills = job["extracted_skills"] or []

        semantic_score = cosine_similarity(
            resume_embedding,
            job_embedding
        )

        skill_score, matched_skills, missing_skills = calculate_skill_score(
            resume_skills=resume_skills,
            job_skills=job_skills
        )

        final_score = calculate_final_score(
            semantic_score=semantic_score,
            skill_score=skill_score
        )

        results.append(
            {
                "resume_id": resume["id"],
                "job_id": job["id"],
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "apply_url": job["apply_url"],
                "semantic_score": round(semantic_score, 4),
                "skill_score": round(skill_score, 4),
                "final_score": final_score,
                "matched_skills": matched_skills,
                "missing_skills": missing_skills
            }
        )

    results = sorted(
        results,
        key=lambda item: item["final_score"],
        reverse=True
    )

    return results