from sentence_transformers import SentenceTransformer

from backend.config import EMBEDDING_MODEL


_model = None


def get_embedding_model():
    """
    Loads the Sentence Transformer model only once.
    This avoids reloading the model every time we need an embedding.
    """

    global _model

    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)

    return _model


def generate_embedding(text: str) -> list[float]:
    """
    Converts text into a numerical vector.

    Example:
        "Python SQL AWS data engineer"
        becomes
        [0.123, -0.456, 0.789, ...]

    This vector helps us compare resume meaning with job description meaning.
    """

    if not text:
        return []

    model = get_embedding_model()

    embedding = model.encode(text)

    return embedding.tolist()