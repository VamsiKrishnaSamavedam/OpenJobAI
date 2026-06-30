import json
import re
from typing import Dict, List, Optional


def safe_list(value):
    """
    Converts list/string/None into a clean Python list.
    """

    if value is None:
        return []

    if isinstance(value, list):
        return [
            str(item).strip().lower()
            for item in value
            if str(item).strip()
        ]

    if isinstance(value, str):
        cleaned_value = value.strip()

        if not cleaned_value:
            return []

        try:
            parsed_value = json.loads(cleaned_value)

            if isinstance(parsed_value, list):
                return [
                    str(item).strip().lower()
                    for item in parsed_value
                    if str(item).strip()
                ]
        except Exception:
            return [
                item.strip().lower()
                for item in cleaned_value.split(",")
                if item.strip()
            ]

    return []


def normalize_text(value) -> str:
    if value is None:
        return ""

    return str(value).lower()


def normalize_score(value) -> float:
    try:
        numeric_value = float(value)

        if numeric_value <= 1:
            numeric_value = numeric_value * 100

        return max(0.0, min(100.0, numeric_value))

    except Exception:
        return 0.0


def score_overlap(resume_items: List[str], required_items: List[str]) -> float:
    """
    Scores how many required/preferred items are present in the resume.
    """

    resume_set = set([item.lower().strip() for item in resume_items if item])
    required_set = set([item.lower().strip() for item in required_items if item])

    if not required_set:
        return 100.0

    matched = resume_set.intersection(required_set)

    return round((len(matched) / len(required_set)) * 100, 2)


def extract_preferred_skills(job_description: str, job_skills: List[str]) -> List[str]:
    """
    Tries to identify preferred/nice-to-have skills from the preferred section.
    """

    preferred_markers = [
        "preferred qualifications",
        "bonus points",
        "nice to have",
        "preferred",
        "plus if",
        "a plus",
    ]

    preferred_section = ""

    for marker in preferred_markers:
        marker_index = job_description.find(marker)

        if marker_index != -1:
            preferred_section = job_description[marker_index:]
            break

    if not preferred_section:
        return []

    preferred_skills = []

    for skill in job_skills:
        if skill.lower() in preferred_section:
            preferred_skills.append(skill)

    return preferred_skills


def extract_required_years(job_description: str) -> int:
    """
    Extracts required years of experience from job description.
    """

    patterns = [
        r"minimum\s+(\d+)\+?\s+years",
        r"(\d+)\+?\s+years\s+of\s+experience",
        r"(\d+)\+?\s+yrs\s+of\s+experience",
        r"(\d+)\+?\s+years'\s+experience",
        r"(\d+)\+?\s+years\s+work\s+experience",
    ]

    years = []

    for pattern in patterns:
        matches = re.findall(pattern, job_description)

        for match in matches:
            try:
                year_value = int(match)

                if 0 < year_value <= 20:
                    years.append(year_value)
            except Exception:
                pass

    if not years:
        return 0

    return max(years)


def extract_resume_years(resume_text: str) -> int:
    """
    Tries to infer years of experience from resume text.
    """

    patterns = [
        r"(\d+)\+?\s+years\s+of\s+experience",
        r"(\d+)\+?\s+yrs\s+of\s+experience",
        r"(\d+)\+?\s+years'\s+experience",
        r"(\d+)\+?\s+years\s+experience",
    ]

    years = []

    for pattern in patterns:
        matches = re.findall(pattern, resume_text)

        for match in matches:
            try:
                year_value = int(match)

                if 0 < year_value <= 20:
                    years.append(year_value)
            except Exception:
                pass

    if not years:
        return 0

    return max(years)


def calculate_experience_score(
    job_description: str,
    resume_text: str,
) -> Dict:
    required_years = extract_required_years(job_description)
    resume_years = extract_resume_years(resume_text)

    if required_years == 0:
        return {
            "experience_score": 100.0,
            "required_years": 0,
            "resume_years": resume_years,
            "experience_gap": False,
        }

    if resume_years == 0:
        return {
            "experience_score": 55.0,
            "required_years": required_years,
            "resume_years": 0,
            "experience_gap": True,
        }

    if resume_years >= required_years:
        return {
            "experience_score": 100.0,
            "required_years": required_years,
            "resume_years": resume_years,
            "experience_gap": False,
        }

    score = round((resume_years / required_years) * 100, 2)

    return {
        "experience_score": max(30.0, score),
        "required_years": required_years,
        "resume_years": resume_years,
        "experience_gap": True,
    }


def calculate_title_score(job_title: str, resume_text: str) -> float:
    """
    Measures whether the resume aligns with the job title/role.
    """

    stop_words = {
        "i",
        "ii",
        "iii",
        "senior",
        "junior",
        "lead",
        "staff",
        "principal",
        "associate",
        "developer",
        "engineer",
        "analyst",
        "specialist",
        "manager",
        "remote",
        "hybrid",
        "full",
        "time",
    }

    title_words = re.findall(r"[a-zA-Z]+", job_title.lower())

    meaningful_words = [
        word
        for word in title_words
        if len(word) > 2 and word not in stop_words
    ]

    if not meaningful_words:
        return 70.0

    matched_words = [
        word
        for word in meaningful_words
        if word in resume_text
    ]

    return round((len(matched_words) / len(meaningful_words)) * 100, 2)


def calculate_education_score(job_description: str, resume_text: str) -> Dict:
    """
    Checks whether job degree requirements appear satisfied.
    """

    degree_keywords = [
        "bachelor",
        "bachelor's",
        "bs ",
        "b.s.",
        "master",
        "master's",
        "ms ",
        "m.s.",
        "degree",
    ]

    job_requires_degree = any(
        keyword in job_description
        for keyword in degree_keywords
    )

    resume_has_degree = any(
        keyword in resume_text
        for keyword in degree_keywords
    )

    if not job_requires_degree:
        return {
            "education_score": 100.0,
            "degree_required": False,
            "degree_found": resume_has_degree,
            "education_gap": False,
        }

    if resume_has_degree:
        return {
            "education_score": 100.0,
            "degree_required": True,
            "degree_found": True,
            "education_gap": False,
        }

    return {
        "education_score": 50.0,
        "degree_required": True,
        "degree_found": False,
        "education_gap": True,
    }


def calculate_location_score(job_description: str, job_location: str) -> Dict:
    """
    Location is neutral for now because the app does not yet store user location preference.
    Later, this can compare remote/hybrid/onsite and preferred location.
    """

    text = f"{job_description} {job_location}".lower()

    is_remote = "remote" in text
    is_hybrid = "hybrid" in text
    is_onsite = "onsite" in text or "on-site" in text or "in person" in text

    return {
        "location_score": 100.0,
        "is_remote": is_remote,
        "is_hybrid": is_hybrid,
        "is_onsite": is_onsite,
    }


def calculate_ats_compatibility(
    resume: Dict,
    job: Dict,
    match: Optional[Dict] = None,
) -> Dict:
    """
    Calculates a more realistic ATS Compatibility Score.

    Formula:
    30% Required Skills Match
    20% Preferred Skills Match
    15% Experience Match
    10% Role / Title Match
    10% Education Match
    10% Keyword Context Match
    5% Location / Work Arrangement Fit
    """

    match = match or {}

    resume_text = normalize_text(
        resume.get("raw_text")
        or resume.get("resume_text")
        or resume.get("text")
        or resume.get("content")
        or ""
    )

    job_title = normalize_text(job.get("title") or "")
    job_description = normalize_text(job.get("description") or "")
    job_location = normalize_text(job.get("location") or "")

    resume_skills = safe_list(
        resume.get("skills")
        or resume.get("extracted_skills")
        or []
    )

    job_skills = safe_list(
        job.get("extracted_skills")
        or job.get("skills")
        or []
    )

    matched_skills = safe_list(match.get("matched_skills"))
    missing_skills = safe_list(match.get("missing_skills"))

    if not job_skills and (matched_skills or missing_skills):
        job_skills = sorted(set(matched_skills + missing_skills))

    if not resume_skills and matched_skills:
        resume_skills = matched_skills

    preferred_skills = extract_preferred_skills(
        job_description=job_description,
        job_skills=job_skills,
    )

    required_skills = [
        skill
        for skill in job_skills
        if skill not in preferred_skills
    ]

    if not required_skills:
        required_skills = job_skills

    required_skill_score = score_overlap(
        resume_items=resume_skills,
        required_items=required_skills,
    )

    preferred_skill_score = score_overlap(
        resume_items=resume_skills,
        required_items=preferred_skills,
    )

    experience_result = calculate_experience_score(
        job_description=job_description,
        resume_text=resume_text,
    )

    title_score = calculate_title_score(
        job_title=job_title,
        resume_text=resume_text,
    )

    education_result = calculate_education_score(
        job_description=job_description,
        resume_text=resume_text,
    )

    location_result = calculate_location_score(
        job_description=job_description,
        job_location=job_location,
    )

    keyword_context_score = normalize_score(
        match.get("semantic_score")
        or match.get("semantic_match_score")
        or 0
    )

    skill_score = normalize_score(
        match.get("skill_score")
        or match.get("skill_match_score")
        or required_skill_score
    )

    ats_score = (
        required_skill_score * 0.30
        + preferred_skill_score * 0.20
        + experience_result["experience_score"] * 0.15
        + title_score * 0.10
        + education_result["education_score"] * 0.10
        + keyword_context_score * 0.10
        + location_result["location_score"] * 0.05
    )

    knockout_flags = []

    if required_skill_score < 45:
        knockout_flags.append(
            "Low required-skill match. Resume may miss important required skills."
        )
        ats_score = min(ats_score, 60)

    if experience_result["experience_gap"]:
        knockout_flags.append(
            f"Experience gap detected. Job appears to require {experience_result['required_years']}+ years."
        )
        ats_score = min(ats_score, 65)

    if education_result["education_gap"]:
        knockout_flags.append(
            "Education requirement may be missing or unclear in the resume."
        )
        ats_score = min(ats_score, 70)

    if "sponsorship" in job_description or "work authorization" in job_description:
        knockout_flags.append(
            "Job mentions work authorization or sponsorship. This may require manual review."
        )

    ats_score = round(max(0.0, min(100.0, ats_score)))

    ats_explanation = []

    if required_skill_score >= 70:
        ats_explanation.append("Strong match on required skills.")
    elif required_skill_score >= 45:
        ats_explanation.append("Partial match on required skills.")
    else:
        ats_explanation.append("Weak match on required skills.")

    if preferred_skills:
        ats_explanation.append(
            f"Preferred skills detected: {', '.join(preferred_skills[:6])}."
        )

    if missing_skills:
        ats_explanation.append(
            f"Missing skills include: {', '.join(missing_skills[:6])}."
        )

    if experience_result["required_years"] > 0:
        ats_explanation.append(
            f"Job appears to require {experience_result['required_years']}+ years of experience."
        )

    return {
        "ats_compatibility_score": ats_score,
        "required_skill_score": round(required_skill_score),
        "preferred_skill_score": round(preferred_skill_score),
        "experience_score": round(experience_result["experience_score"]),
        "title_score": round(title_score),
        "education_score": round(education_result["education_score"]),
        "keyword_context_score": round(keyword_context_score),
        "location_score": round(location_result["location_score"]),
        "semantic_score": round(keyword_context_score),
        "skill_score": round(skill_score),
        "required_years": experience_result["required_years"],
        "resume_years": experience_result["resume_years"],
        "degree_required": education_result["degree_required"],
        "degree_found": education_result["degree_found"],
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "knockout_flags": knockout_flags,
        "ats_explanation": ats_explanation,
    }