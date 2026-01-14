from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from .config import settings

VECTOR_SIZE_LARGE = 3072
VECTOR_SIZE_SMALL = 1536


def get_client() -> QdrantClient:
    """Возвращает клиент Qdrant."""
    return QdrantClient(url=settings.qdrant_url)


def ensure_collection(
    client: QdrantClient,
    name: str,
    vector_size: int = VECTOR_SIZE_LARGE
) -> None:
    """Создаёт коллекцию, если её нет."""
    if not client.collection_exists(name):
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            ),
        )


def upsert_vectors(
    client: QdrantClient,
    collection: str,
    ids: list[str],
    vectors: list[list[float]],
    payloads: list[dict]
) -> None:
    """Добавляет или обновляет векторы в коллекции."""
    points = [
        PointStruct(
            id=i,
            vector=vectors[i],
            payload={**payloads[i], "_str_id": ids[i]}
        )
        for i in range(len(ids))
    ]
    
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        client.upsert(
            collection_name=collection,
            points=batch,
            wait=True
        )


def search_similar(
    client: QdrantClient,
    collection: str,
    query_vector: list[float],
    limit: int = 10,
    score_threshold: float | None = None,
    filter_doc_id: str | None = None,
) -> list[dict]:
    """
    Ищет похожие векторы.
    Возвращает список {id, score, payload}.
    """
    search_filter = None
    if filter_doc_id:
        search_filter = Filter(
            must=[
                FieldCondition(
                    key="doc_id",
                    match=MatchValue(value=filter_doc_id)
                )
            ]
        )
    
    results = client.search(
        collection_name=collection,
        query_vector=query_vector,
        limit=limit,
        score_threshold=score_threshold,
        query_filter=search_filter,
    )
    
    return [
        {
            "id": r.payload.get("_str_id", str(r.id)),
            "score": r.score,
            "payload": r.payload
        }
        for r in results
    ]


def get_all_points(
    client: QdrantClient,
    collection: str,
    limit: int = 10000
) -> list[dict]:
    """Получает все точки из коллекции."""
    results = client.scroll(
        collection_name=collection,
        limit=limit,
        with_payload=True,
        with_vectors=True,
    )
    
    points = []
    for r in results[0]:
        points.append({
            "id": r.payload.get("_str_id", str(r.id)),
            "vector": r.vector,
            "payload": r.payload
        })
    
    return points


def delete_collection(client: QdrantClient, name: str) -> None:
    """Удаляет коллекцию."""
    if client.collection_exists(name):
        client.delete_collection(name)
