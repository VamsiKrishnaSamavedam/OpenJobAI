import re


SKILLS = [
    # Programming languages
    "python",
    "java",
    "javascript",
    "typescript",
    "c++",
    "c#",
    "sql",
    "r",

    # Databases
    "postgresql",
    "mysql",
    "mongodb",
    "sqlite",
    "redis",

    # Data engineering
    "etl",
    "data pipeline",
    "data pipelines",
    "airflow",
    "dbt",
    "spark",
    "pyspark",
    "kafka",
    "hadoop",

    # Cloud
    "aws",
    "azure",
    "gcp",
    "s3",
    "lambda",
    "glue",
    "rds",
    "ec2",
    "cloudwatch",

    # Machine learning / NLP
    "machine learning",
    "deep learning",
    "nlp",
    "scikit-learn",
    "tensorflow",
    "pytorch",
    "xgboost",
    "sentence transformers",

    # Backend / APIs
    "fastapi",
    "flask",
    "django",
    "rest api",
    "api",

    # DevOps / tools
    "docker",
    "kubernetes",
    "git",
    "github",
    "linux",

    # Data analysis / visualization
    "pandas",
    "numpy",
    "matplotlib",
    "seaborn",
    "power bi",
    "tableau",
    "excel",
    "data analysis",
"data analyst",
"analytics",
"data entry",
"data cleaning",
"data quality",
"reporting",
"dashboard",
"dashboards",
"business intelligence",
"bi",
"excel",
"google sheets",
"spreadsheet",
"spreadsheets",
"powerpoint",
"research",
"market research",
"web research",
"search engine evaluation",
"data annotation",
"data labeling",
"quality assurance",
"qa",
"documentation",
"operations",
"jira",
"servicenow",
"zendesk",
"crm",
"erp",
"netsuite",
"sap",
"odoo",
"etl",
"elt",
"sql",
"postgresql",
"mysql",
"snowflake",
"bigquery",
"redshift",
"python",
"pandas",
"numpy",
"power bi",
"tableau",
"looker",
"azure",
"aws",
"gcp",
"spark",
"pyspark",
"airflow",
"dbt",
"machine learning",
"ml",
"nlp",
"api",
"rest api",
"github",
"git"
]


def clean_text(text: str) -> str:
    """
    Converts text into a clean lowercase format.
    This helps us compare skills correctly.
    """

    if not text:
        return ""

    text = text.lower()
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def extract_skills(text: str) -> list[str]:
    """
    Extracts unique skills from text.
    Keeps the order from the SKILLS list and avoids duplicate skill values.
    """

    if not text:
        return []

    cleaned_text = clean_text(text)

    extracted_skills = []
    seen_skills = set()

    for skill in SKILLS:
        normalized_skill = skill.lower().strip()

        if not normalized_skill:
            continue

        if normalized_skill in seen_skills:
            continue

        if normalized_skill in cleaned_text:
            extracted_skills.append(normalized_skill)
            seen_skills.add(normalized_skill)

    return extracted_skills