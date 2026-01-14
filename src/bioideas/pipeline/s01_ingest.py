"""
Step 01: Ingest transcripts and split into chunks.

Загружает .txt/.md файлы из data/raw/, разбивает на чанки,
сохраняет episodes.jsonl и chunks.jsonl.

Поддерживает инкрементальную загрузку — уже обработанные файлы пропускаются.
"""
from pathlib import Path
from tqdm import tqdm
from rich.console import Console

from ..config import RAW_DIR, PROCESSED_DIR
from ..chunking import process_transcript_file
from ..models import Episode, Chunk
from ..storage import append_jsonl, read_jsonl, load_processed_ids

console = Console()

EPISODES_FILE = PROCESSED_DIR / "episodes.jsonl"
CHUNKS_FILE = PROCESSED_DIR / "chunks.jsonl"


def get_transcript_files() -> list[Path]:
    """Находит все файлы транскриптов в RAW_DIR."""
    files = []
    for ext in ["*.txt", "*.md"]:
        files.extend(RAW_DIR.glob(ext))
    return sorted(files)


def main():
    console.print("[bold blue]Step 01: Ingest Transcripts[/bold blue]")
    
    processed_files = load_processed_ids(EPISODES_FILE, "filename")
    transcript_files = get_transcript_files()
    
    if not transcript_files:
        console.print(f"[yellow]No transcript files found in {RAW_DIR}[/yellow]")
        console.print("Place your .txt or .md transcript files there and run again.")
        return
    
    new_files = [f for f in transcript_files if f.name not in processed_files]
    
    if not new_files:
        console.print("[green]All files already processed.[/green]")
        existing_episodes = read_jsonl(EPISODES_FILE, Episode)
        existing_chunks = read_jsonl(CHUNKS_FILE, Chunk)
        console.print(f"  Episodes: {len(existing_episodes)}")
        console.print(f"  Chunks: {len(existing_chunks)}")
        return
    
    console.print(f"Found {len(new_files)} new files to process")
    
    total_episodes = 0
    total_chunks = 0
    
    for filepath in tqdm(new_files, desc="Processing transcripts"):
        try:
            episode, chunks = process_transcript_file(filepath)
            
            append_jsonl(EPISODES_FILE, episode)
            for chunk in chunks:
                append_jsonl(CHUNKS_FILE, chunk)
            
            total_episodes += 1
            total_chunks += len(chunks)
            
        except Exception as e:
            console.print(f"[red]Error processing {filepath.name}: {e}[/red]")
            continue
    
    console.print(f"[green]Done![/green]")
    console.print(f"  New episodes: {total_episodes}")
    console.print(f"  New chunks: {total_chunks}")
    
    all_episodes = read_jsonl(EPISODES_FILE, Episode)
    all_chunks = read_jsonl(CHUNKS_FILE, Chunk)
    console.print(f"  Total episodes: {len(all_episodes)}")
    console.print(f"  Total chunks: {len(all_chunks)}")


if __name__ == "__main__":
    main()
