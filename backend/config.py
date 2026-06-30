import os
from dotenv import load_dotenv

load_dotenv()

APP_ENV = os.getenv("APP_ENV", "local")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://openjobai_user:openjobai_password@127.0.0.1:55432/openjobai"
)

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2"
)

USE_LLM = os.getenv("USE_LLM", "false").lower() == "true"

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN", "")

APIFY_LINKEDIN_TASK_ID = os.getenv("APIFY_LINKEDIN_TASK_ID", "")
APIFY_INDEED_TASK_ID = os.getenv("APIFY_INDEED_TASK_ID", "")
APIFY_DICE_TASK_ID = os.getenv("APIFY_DICE_TASK_ID", "")

APIFY_MAX_ITEMS = int(os.getenv("APIFY_MAX_ITEMS", "25"))