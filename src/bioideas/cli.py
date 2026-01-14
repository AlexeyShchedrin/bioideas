"""
CLI для запуска пайплайна BioIdeas.
"""
import typer
from rich.console import Console

app = typer.Typer(help="BioIdeas - Extract biotech startup ideas from podcast transcripts")
console = Console()


@app.command()
def ingest():
    """Step 01: Загрузить транскрипты и разбить на чанки."""
    from .pipeline.s01_ingest import main
    main()


@app.command()
def embed():
    """Step 02: Создать эмбеддинги чанков."""
    from .pipeline.s02_embed_chunks import main
    main()


@app.command()
def extract():
    """Step 03: Извлечь nuggets из чанков."""
    from .pipeline.s03_extract_nuggets import main
    main()


@app.command()
def synthesize():
    """Step 04: Синтезировать Idea Cards."""
    from .pipeline.s04_synthesize_ideas import main
    main()


@app.command()
def dedupe():
    """Step 05: Дедупликация и кластеризация идей."""
    from .pipeline.s05_dedupe_cluster import main
    main()


@app.command()
def score():
    """Step 06: Оценить идеи по 5 критериям."""
    from .pipeline.s06_score import main
    main()


@app.command()
def tournament():
    """Step 07: Провести турнир попарных сравнений."""
    from .pipeline.s07_tournament import main
    main()


@app.command()
def export():
    """Step 08: Экспортировать decision memos."""
    from .pipeline.s08_export_memos import main
    main()


@app.command()
def run_all():
    """Запустить весь пайплайн последовательно."""
    console.print("[bold blue]Running full pipeline...[/bold blue]\n")
    
    from .pipeline import s01_ingest, s02_embed_chunks, s03_extract_nuggets
    from .pipeline import s04_synthesize_ideas, s05_dedupe_cluster, s06_score
    from .pipeline import s07_tournament, s08_export_memos
    
    steps = [
        ("01. Ingest", s01_ingest.main),
        ("02. Embed Chunks", s02_embed_chunks.main),
        ("03. Extract Nuggets", s03_extract_nuggets.main),
        ("04. Synthesize Ideas", s04_synthesize_ideas.main),
        ("05. Dedupe & Cluster", s05_dedupe_cluster.main),
        ("06. Score Ideas", s06_score.main),
        ("07. Tournament", s07_tournament.main),
        ("08. Export Memos", s08_export_memos.main),
    ]
    
    for name, func in steps:
        console.print(f"\n[bold]{'='*50}[/bold]")
        console.print(f"[bold green]{name}[/bold green]")
        console.print(f"[bold]{'='*50}[/bold]\n")
        try:
            func()
        except Exception as e:
            console.print(f"[red]Error in {name}: {e}[/red]")
            raise typer.Exit(1)
    
    console.print("\n[bold green]Pipeline complete![/bold green]")


@app.command()
def ui():
    """Запустить Streamlit UI."""
    import subprocess
    import sys
    from pathlib import Path
    
    app_path = Path(__file__).parent.parent.parent / "app" / "streamlit_app.py"
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(app_path)])


if __name__ == "__main__":
    app()
