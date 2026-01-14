"""
Step 02: Create embeddings for chunks and store in Qdrant.

Читает chunks.jsonl, создаёт эмбеддинги через OpenAI,
сохраняет в Qdrant для последующего поиска.
"""
from tqdm import tqdm
from rich.console import Console

from ..config import PROCESSED_DIR, settings
from ..models import Chunk
from ..storage import read_jsonl
from ..embeddings import embed_texts
from ..vectorstore import get_client, ensure_collection, upsert_vectors, VECTOR_SIZE_LARGE

console = Console()

CHUNKS_FILE = PROCESSED_DIR / "chunks.jsonl"


def main():
    console.print("[bold blue]Step 02: Embed Chunks[/bold blue]")
    
    chunks = read_jsonl(CHUNKS_FILE, Chunk)
    if not chunks:
        console.print("[yellow]No chunks found. Run step 01 first.[/yellow]")
        return
    
    console.print(f"Found {len(chunks)} chunks")
    
    client = get_client()
    ensure_collection(
        client,
        settings.qdrant_chunks_collection,
        VECTOR_SIZE_LARGE
    )
    
    existing_count = client.count(settings.qdrant_chunks_collection).count
    if existing_count >= len(chunks):
        console.print(f"[green]Chunks already embedded ({existing_count} vectors).[/green]")
        return
    
    console.print("Creating embeddings...")
    
    batch_size = settings.embed_batch_size
    all_ids = []
    all_vectors = []
    all_payloads = []
    
    for i in tqdm(range(0, len(chunks), batch_size), desc="Embedding batches"):
        batch = chunks[i:i + batch_size]
        texts = [c.text for c in batch]
        
        vectors = embed_texts(texts)
        
        for j, chunk in enumerate(batch):
            all_ids.append(chunk.chunk_id)
            all_vectors.append(vectors[j])
            all_payloads.append({
                "chunk_id": chunk.chunk_id,
                "doc_id": chunk.doc_id,
                "order": chunk.order,
                "text_preview": chunk.text[:500],
            })
    
    console.print("Upserting to Qdrant...")
    upsert_vectors(
        client,
        settings.qdrant_chunks_collection,
        all_ids,
        all_vectors,
        all_payloads
    )
    
    final_count = client.count(settings.qdrant_chunks_collection).count
    console.print(f"[green]Done! {final_count} chunk vectors in Qdrant.[/green]")


if __name__ == "__main__":
    main()
