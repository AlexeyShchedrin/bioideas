import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
MEMOS_DIR = PROCESSED_DIR / "memos"


class Settings(BaseModel):
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-5.2")
    openai_embed_model: str = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-large")
    qdrant_url: str = os.getenv("QDRANT_URL", "http://localhost:6333")

    chunk_target_chars: int = 4500
    chunk_overlap_chars: int = 300

    max_nuggets_per_chunk: int = 3
    max_ideas_per_episode: int = 12

    max_output_tokens_extract: int = 800
    max_output_tokens_idea: int = 8000
    max_output_tokens_score: int = 800

    embed_batch_size: int = 100
    llm_retry_attempts: int = 3
    llm_retry_delay: float = 2.0

    store_responses: bool = False

    qdrant_chunks_collection: str = "bioideas_chunks"
    qdrant_ideas_collection: str = "bioideas_ideas"


settings = Settings()

RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
MEMOS_DIR.mkdir(parents=True, exist_ok=True)
