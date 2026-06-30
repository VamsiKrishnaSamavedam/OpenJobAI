from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.config import DATABASE_URL


engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db():
    """
    Gives one database session to each API request.
    Closes the session after the request finishes.
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


def test_database_connection():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return True, None

    except Exception as error:
        return False, str(error)