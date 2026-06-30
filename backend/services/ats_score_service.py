import json
import math
from typing import Any, Dict, List


def safe_list(value: Any) -> List[str]:
    """
    Converts database JSON/list/string values into a clean Python list.
    """

    if value is None:
        return []

    if isinstance(value, list):
        return [str(item).lower().strip() for item in value if str(item).strip()]

    if isinstance(value, str):
        try:
            parsed_value = json.loads(value)

            if isinstance(parsed_value, list):
                return [
                    str(item).lower().strip()
                    for item in parsed_value
                    if str(item).strip()
                ]

        except Exception:
            return []

    return []


def safe_vector(value: Any) -> List[float]:
    """
    Converts pgvector/list/string embeddings into a Python float list.
    """

    if value is None:
        return []

    if isinstance(value, list):
        return [float(item) for item in value]

    if hasattr(value, "tolist"):
        return [float(item) for item in value.tolist()]

    if isinstance(value, str):
        cleaned_value = value.strip().replace("[", "").replace("]", "")

        if not cleaned_value:
            return []

        return [
            float(item.strip())
            for item in cleaned_value.split(",")
            if item.strip()
        ]

    try:
        return [float(item) for item in value]
    except Exception:
        return []


def cosine_similarity(vector_a: List[float], vector_b: List[float]) -> float:
    """
    Calculates cosine similarity between two embedding vectors.
    """

    if not vector_a or not vector_b:
        return 0.0

    if len(vector_a) != len(vector_b):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
    magnitude_a = math.sqrt(sum(a * a for a in vector_a))
    magnitude_b = math.sqrt(sum(b * b for b in vector_b))

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


def calculate_skill_score(
    resume_skills: List[str],
    job_skills: List[str],
) -> float:
    """
    Calculates percentage of job-required skills found in the resume.
    """

    resume_skill_set = set(resume_skills)
    job_skill_set = set(job_skills)

    if not job_skill_set:
        return 0.0

    matched_skills = resume_skill_set.intersection(job_skill_set)

    return (len(matched_skills) / len(job_skill_set)) * 100


def calculate_missing_skills(
    resume_skills: List[str],
    job_skills: List[str],
) -> List[str]:
    """
    Returns job skills that are missing from the resume.
    """

    resume_skill_set = set(resume_skills)
    job_skill_set = set(job_skills)

    missing_skills = job_skill_set.difference(resume_skill_set)

    return sorted(list(missing_skills))


def calculate_ats_score(resume: Dict, job: Dict) -> Dict:
    """
    Calculates ATS-style resume match score for one job.
    """

    resume_embedding = safe_vector(resume.get("embedding") or resume.get("resume_embedding"))
    job_embedding = safe_vector(job.get("embedding") or job.get("job_embedding"))

    resume_skills = safe_list(resume.get("extracted_skills") or resume.get("skills"))
    job_skills = safe_list(job.get("extracted_skills") or job.get("skills"))

    semantic_score = cosine_similarity(resume_embedding, job_embedding) * 100
    skill_score = calculate_skill_score(resume_skills, job_skills)

    if semantic_score > 0:
        final_score = (semantic_score * 0.70) + (skill_score * 0.30)
    else:
        final_score = skill_score

    final_score = max(0, min(100, final_score))

    return {
        "score": round(final_score),
        "semantic_score": round(semantic_score),
        "skill_score": round(skill_score),
        "missing_skills": calculate_missing_skills(resume_skills, job_skills),
    }