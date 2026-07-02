from functools import lru_cache

from app.core.config import settings


class EmbeddingDimensionError(ValueError):
    pass


@lru_cache(maxsize=1)
def get_embedding_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(settings.EMBEDDING_MODEL_NAME)


def generate_embedding(text: str) -> list[float]:
    embeddings = generate_embeddings([text])
    return embeddings[0]


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    model = get_embedding_model()
    vectors = model.encode(texts, convert_to_numpy=False, normalize_embeddings=True)
    embeddings = [list(map(float, vector)) for vector in vectors]

    for embedding in embeddings:
        if len(embedding) != settings.EMBEDDING_DIMENSION:
            raise EmbeddingDimensionError(
                "Embedding dimension does not match configured EMBEDDING_DIMENSION"
            )

    return embeddings
