from typing import Dict, List


def safe_list(value):
    """
    Converts list/string/None values into a clean Python list.
    """

    if value is None:
        return []

    if isinstance(value, list):
        return value

    if isinstance(value, str):
        cleaned_value = value.strip()

        if not cleaned_value:
            return []

        try:
            import json

            parsed_value = json.loads(cleaned_value)

            if isinstance(parsed_value, list):
                return parsed_value

        except Exception:
            return [
                item.strip()
                for item in cleaned_value.split(",")
                if item.strip()
            ]

    return []


def normalize_score(value):
    """
    Converts score values into 0-100 scale.
    """

    try:
        numeric_value = float(value)

        if numeric_value <= 1:
            numeric_value = numeric_value * 100

        return numeric_value

    except Exception:
        return 0.0


def build_xgb_features_from_match(match: Dict, job: Dict) -> Dict:
    """
    Builds one feature row for XGBoost from one resume-job match.
    """

    matched_skills = safe_list(match.get("matched_skills"))
    missing_skills = safe_list(match.get("missing_skills"))
    job_skills = safe_list(job.get("extracted_skills") or job.get("skills"))

    source = (job.get("source") or "").lower()

    title = (job.get("title") or "").lower()
    description = (job.get("description") or "").lower()

    text = f"{title} {description}"

    ats_compatibility_score = normalize_score(
        match.get("ats_compatibility_score")
        or match.get("ats_score")
        or match.get("final_score")
        or match.get("score")
        or match.get("match_score")
    )

    return {
        "ats_compatibility_score": ats_compatibility_score,

        "baseline_final_score": normalize_score(
            match.get("final_score")
            or match.get("score")
            or match.get("match_score")
        ),

        "semantic_score": normalize_score(
            match.get("semantic_score")
        ),

        "skill_score": normalize_score(
            match.get("skill_score")
        ),

        "required_skill_score": normalize_score(
            match.get("required_skill_score")
        ),

        "preferred_skill_score": normalize_score(
            match.get("preferred_skill_score")
        ),

        "experience_score": normalize_score(
            match.get("experience_score")
        ),

        "title_score": normalize_score(
            match.get("title_score")
        ),

        "education_score": normalize_score(
            match.get("education_score")
        ),

        "keyword_context_score": normalize_score(
            match.get("keyword_context_score")
        ),

        "location_score": normalize_score(
            match.get("location_score")
        ),

        "knockout_count": len(
            safe_list(match.get("knockout_flags"))
        ),

        "matched_skills_count": len(matched_skills),
        "missing_skills_count": len(missing_skills),
        "job_skills_count": len(job_skills),

        "missing_skill_ratio": (
            len(missing_skills) / len(job_skills)
            if len(job_skills) > 0
            else 0.0
        ),

        "source_is_linkedin": 1 if "linkedin" in source else 0,
        "source_is_indeed": 1 if "indeed" in source else 0,

        "title_has_data": 1 if "data" in title else 0,
        "title_has_engineer": 1 if "engineer" in title else 0,
        "title_has_analyst": 1 if "analyst" in title else 0,
        "title_has_python": 1 if "python" in title else 0,
        "title_has_software": 1 if "software" in title else 0,

        "text_has_sql": 1 if "sql" in text else 0,
        "text_has_python": 1 if "python" in text else 0,
        "text_has_etl": 1 if "etl" in text else 0,
        "text_has_cloud": 1 if (
            "aws" in text
            or "azure" in text
            or "gcp" in text
            or "cloud" in text
        ) else 0,
    }


def get_feature_columns() -> List[str]:
    """
    Fixed feature order for XGBoost training and prediction.
    """

    return [
        "ats_compatibility_score",
        "baseline_final_score",
        "semantic_score",
        "skill_score",

        "required_skill_score",
        "preferred_skill_score",
        "experience_score",
        "title_score",
        "education_score",
        "keyword_context_score",
        "location_score",
        "knockout_count",

        "matched_skills_count",
        "missing_skills_count",
        "job_skills_count",
        "missing_skill_ratio",

        "source_is_linkedin",
        "source_is_indeed",

        "title_has_data",
        "title_has_engineer",
        "title_has_analyst",
        "title_has_python",
        "title_has_software",

        "text_has_sql",
        "text_has_python",
        "text_has_etl",
        "text_has_cloud",
    ]