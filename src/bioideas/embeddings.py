import time
from openai import OpenAI
from .config import settings

client = OpenAI(api_key=settings.openai_api_key)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Создаёт эмбеддинги для списка текстов.
    Обрабатывает батчами для больших списков.
    """
    if not texts:
        return []
    
    all_embeddings = []
    batch_size = settings.embed_batch_size
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        for attempt in range(settings.llm_retry_attempts):
            try:
                response = client.embeddings.create(
                    model=settings.openai_embed_model,
                    input=batch,
                    encoding_format="float",
                )
                batch_embeddings = [d.embedding for d in response.data]
                all_embeddings.extend(batch_embeddings)
                break
                
            except Exception as e:
                if attempt < settings.llm_retry_attempts - 1:
                    time.sleep(settings.llm_retry_delay * (attempt + 1))
                    continue
                raise RuntimeError(f"Embedding failed after {settings.llm_retry_attempts} attempts: {e}")
    
    return all_embeddings


def embed_single(text: str) -> list[float]:
    """Создаёт эмбеддинг для одного текста."""
    result = embed_texts([text])
    return result[0] if result else []
