"""
Step 05: Deduplicate and cluster ideas.

Создаёт эмбеддинги идей, находит похожие через Qdrant,
кластеризует с помощью HDBSCAN, помечает дубликаты.
"""
import numpy as np
from tqdm import tqdm
from rich.console import Console
from sklearn.metrics.pairwise import cosine_similarity
import hdbscan

from ..config import PROCESSED_DIR, settings
from ..models import IdeaCard
from ..storage import read_jsonl, write_jsonl
from ..embeddings import embed_texts
from ..vectorstore import (
    get_client, ensure_collection, upsert_vectors,
    search_similar, VECTOR_SIZE_LARGE
)

console = Console()

IDEAS_FILE = PROCESSED_DIR / "ideas.jsonl"
IDEAS_DEDUPED_FILE = PROCESSED_DIR / "ideas_deduped.jsonl"

SIMILARITY_THRESHOLD = 0.85


def create_idea_embedding_text(idea: IdeaCard) -> str:
    """Создаёт текст для эмбеддинга идеи."""
    return f"{idea.title_ru}. {idea.problem_ru}. {idea.solution_ru}. {idea.wedge_ru}"


def find_duplicates(ideas: list[IdeaCard], embeddings: list[list[float]]) -> dict[str, str]:
    """
    Находит дубликаты по косинусной близости.
    Возвращает {duplicate_id: canonical_id}.
    """
    if len(ideas) < 2:
        return {}
    
    emb_matrix = np.array(embeddings)
    sim_matrix = cosine_similarity(emb_matrix)
    
    duplicates = {}
    seen = set()
    
    for i in range(len(ideas)):
        if ideas[i].idea_id in seen:
            continue
        
        for j in range(i + 1, len(ideas)):
            if ideas[j].idea_id in seen:
                continue
            
            if sim_matrix[i, j] >= SIMILARITY_THRESHOLD:
                duplicates[ideas[j].idea_id] = ideas[i].idea_id
                seen.add(ideas[j].idea_id)
    
    return duplicates


def cluster_ideas(embeddings: list[list[float]], min_cluster_size: int = 3) -> list[int]:
    """
    Кластеризует идеи с помощью HDBSCAN.
    Возвращает список cluster_id для каждой идеи (-1 = шум).
    """
    if len(embeddings) < min_cluster_size:
        return [-1] * len(embeddings)
    
    emb_matrix = np.array(embeddings)
    
    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=min_cluster_size,
        metric='euclidean',
        cluster_selection_method='eom'
    )
    
    cluster_labels = clusterer.fit_predict(emb_matrix)
    return cluster_labels.tolist()


def main():
    console.print("[bold blue]Step 05: Dedupe & Cluster Ideas[/bold blue]")
    
    ideas = read_jsonl(IDEAS_FILE, IdeaCard)
    if not ideas:
        console.print("[yellow]No ideas found. Run step 04 first.[/yellow]")
        return
    
    console.print(f"Found {len(ideas)} ideas")
    
    console.print("Creating embeddings for ideas...")
    texts = [create_idea_embedding_text(idea) for idea in ideas]
    embeddings = embed_texts(texts)
    
    client = get_client()
    ensure_collection(client, settings.qdrant_ideas_collection, VECTOR_SIZE_LARGE)
    
    ids = [idea.idea_id for idea in ideas]
    payloads = [
        {
            "idea_id": idea.idea_id,
            "title": idea.title_ru,
            "category": idea.category,
            "doc_id": idea.doc_id,
        }
        for idea in ideas
    ]
    upsert_vectors(client, settings.qdrant_ideas_collection, ids, embeddings, payloads)
    
    console.print("Finding duplicates...")
    duplicates = find_duplicates(ideas, embeddings)
    console.print(f"  Found {len(duplicates)} duplicates")
    
    console.print("Clustering ideas...")
    cluster_labels = cluster_ideas(embeddings)
    n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
    console.print(f"  Found {n_clusters} clusters")
    
    unique_ideas = []
    for i, idea in enumerate(ideas):
        if idea.idea_id not in duplicates:
            idea_dict = idea.model_dump()
            idea_dict["cluster_id"] = cluster_labels[i]
            idea_dict["is_duplicate"] = False
            unique_ideas.append(IdeaCard.model_validate(idea_dict))
    
    write_jsonl(IDEAS_DEDUPED_FILE, unique_ideas)
    
    console.print(f"[green]Done![/green]")
    console.print(f"  Original ideas: {len(ideas)}")
    console.print(f"  Unique ideas: {len(unique_ideas)}")
    console.print(f"  Removed duplicates: {len(duplicates)}")
    
    cluster_counts = {}
    for label in cluster_labels:
        if label >= 0:
            cluster_counts[label] = cluster_counts.get(label, 0) + 1
    if cluster_counts:
        console.print(f"  Cluster sizes: {sorted(cluster_counts.values(), reverse=True)[:10]}")


if __name__ == "__main__":
    main()
