import json
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
from xgboost import XGBClassifier

from backend.repositories.feedback_repository import get_all_feedback
from backend.repositories.match_repository import (
    get_resume_for_matching,
    get_jobs_for_matching,
)
from backend.services.matcher import match_resume_to_jobs
from backend.services.ml_feature_builder import (
    build_xgb_features_from_match,
    get_feature_columns,
)
from backend.services.ats_compatibility_service import calculate_ats_compatibility


MODEL_DIR = Path("backend/models")
MODEL_PATH = MODEL_DIR / "xgb_job_ranker.json"
FEATURE_COLUMNS_PATH = MODEL_DIR / "xgb_feature_columns.json"


def feedback_label_to_target(feedback_label: str):
    """
    Converts feedback labels into ML target values.
    """

    label = (feedback_label or "").lower().strip()

    if label in {"interested", "applied"}:
        return 1

    if label in {"not_interested", "not interested"}:
        return 0

    return None


def get_match_job_id(match: Dict):
    """
    Gets the job ID from different possible match result shapes.
    """

    return (
        match.get("job_id")
        or match.get("id")
        or match.get("job", {}).get("id")
    )


def load_xgb_job_ranker():
    """
    Loads the trained XGBoost model if it exists.
    """

    if not MODEL_PATH.exists():
        return None

    model = XGBClassifier()
    model.load_model(str(MODEL_PATH))

    return model


def load_feature_columns_for_prediction() -> List[str]:
    """
    Loads the feature columns used by the saved model.
    This prevents feature mismatch when the formula changes.
    """

    if FEATURE_COLUMNS_PATH.exists():
        with open(FEATURE_COLUMNS_PATH, "r", encoding="utf-8") as file:
            return json.load(file)

    return get_feature_columns()


def build_training_dataset(db) -> pd.DataFrame:
    """
    Builds an XGBoost training dataset from feedback records.
    """

    feedback_records = get_all_feedback(
        db=db,
        limit=10000,
    )

    if not feedback_records:
        return pd.DataFrame()

    all_matching_jobs = get_jobs_for_matching(
        db=db,
        limit=10000,
    )

    jobs_by_id = {
        job.get("id"): job
        for job in all_matching_jobs
        if job.get("id") is not None
    }

    training_rows = []

    for feedback in feedback_records:
        resume_id = feedback.get("resume_id")
        job_id = feedback.get("job_id")
        feedback_label = feedback.get("feedback_label")

        target = feedback_label_to_target(feedback_label)

        if target is None:
            continue

        resume = get_resume_for_matching(
            db=db,
            resume_id=resume_id,
        )

        job = jobs_by_id.get(job_id)

        if resume is None or job is None:
            continue

        match_results = match_resume_to_jobs(
            resume=resume,
            jobs=[job],
        )

        if not match_results:
            continue

        match = match_results[0]

        ats_result = calculate_ats_compatibility(
            resume=resume,
            job=job,
            match=match,
        )

        enhanced_match = {
            **match,
            **ats_result,
            "ats_score": ats_result["ats_compatibility_score"],
            "final_score": ats_result["ats_compatibility_score"],
        }

        feature_row = build_xgb_features_from_match(
            match=enhanced_match,
            job=job,
        )

        feature_row["target"] = target
        feature_row["resume_id"] = resume_id
        feature_row["job_id"] = job_id
        feature_row["feedback_label"] = feedback_label

        training_rows.append(feature_row)

    return pd.DataFrame(training_rows)


def train_xgb_job_ranker(db) -> Dict:
    """
    Trains an XGBoost classifier using user feedback and the upgraded
    ATS Compatibility features.
    """

    training_df = build_training_dataset(db)

    if training_df.empty:
        return {
            "trained": False,
            "reason": "No feedback records available for training.",
            "training_rows": 0,
        }

    feature_columns = get_feature_columns()

    for column in feature_columns:
        if column not in training_df.columns:
            training_df[column] = 0

    X = training_df[feature_columns]
    y = training_df["target"]

    class_count = y.nunique()

    if len(training_df) < 10:
        return {
            "trained": False,
            "reason": "At least 10 feedback records are recommended before training.",
            "training_rows": len(training_df),
            "positive_labels": int((y == 1).sum()),
            "negative_labels": int((y == 0).sum()),
        }

    if class_count < 2:
        return {
            "trained": False,
            "reason": "Need both positive and negative feedback labels.",
            "training_rows": len(training_df),
            "positive_labels": int((y == 1).sum()),
            "negative_labels": int((y == 0).sum()),
        }

    model = XGBClassifier(
        n_estimators=120,
        max_depth=3,
        learning_rate=0.07,
        subsample=0.9,
        colsample_bytree=0.9,
        eval_metric="logloss",
        random_state=42,
    )

    model.fit(X, y)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    model.save_model(str(MODEL_PATH))

    with open(FEATURE_COLUMNS_PATH, "w", encoding="utf-8") as file:
        json.dump(feature_columns, file, indent=2)

    feature_importance = []

    for feature_name, importance_value in zip(
        feature_columns,
        model.feature_importances_,
    ):
        feature_importance.append(
            {
                "feature": feature_name,
                "importance": float(importance_value),
            }
        )

    feature_importance = sorted(
        feature_importance,
        key=lambda item: item["importance"],
        reverse=True,
    )

    return {
        "trained": True,
        "training_rows": len(training_df),
        "positive_labels": int((y == 1).sum()),
        "negative_labels": int((y == 0).sum()),
        "model_path": str(MODEL_PATH),
        "feature_columns": feature_columns,
        "feature_importance": feature_importance,
    }


def predict_ml_preference_scores(
    match_results: List[Dict],
    jobs: List[Dict],
    resume: Optional[Dict] = None,
) -> Dict[int, float]:
    """
    Predicts ML preference scores for visible jobs using the trained XGBoost model.
    """

    model = load_xgb_job_ranker()

    if model is None:
        return {}

    feature_columns = load_feature_columns_for_prediction()

    jobs_by_id = {
        job.get("id"): job
        for job in jobs
        if job.get("id") is not None
    }

    prediction_rows = []
    prediction_job_ids = []

    for match in match_results:
        job_id = get_match_job_id(match)

        if job_id is None:
            continue

        job = jobs_by_id.get(int(job_id))

        if job is None:
            continue

        enhanced_match = dict(match)

        if resume is not None:
            ats_result = calculate_ats_compatibility(
                resume=resume,
                job=job,
                match=match,
            )

            enhanced_match = {
                **enhanced_match,
                **ats_result,
                "ats_score": ats_result["ats_compatibility_score"],
                "final_score": ats_result["ats_compatibility_score"],
            }

        feature_row = build_xgb_features_from_match(
            match=enhanced_match,
            job=job,
        )

        prediction_rows.append(feature_row)
        prediction_job_ids.append(int(job_id))

    if not prediction_rows:
        return {}

    prediction_df = pd.DataFrame(prediction_rows)

    for column in feature_columns:
        if column not in prediction_df.columns:
            prediction_df[column] = 0

    X = prediction_df[feature_columns]

    probabilities = model.predict_proba(X)[:, 1]

    scores = {}

    for job_id, probability in zip(prediction_job_ids, probabilities):
        scores[job_id] = round(float(probability) * 100, 2)

    return scores