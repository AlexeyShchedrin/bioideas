"""
Step 04: Synthesize Idea Cards from nuggets.

Группирует nuggets по doc_id (эпизодам) и синтезирует Idea Cards.
Каждая идея ссылается на source_nugget_ids — без выдумывания новых фактов.
"""
import uuid
from collections import defaultdict
from tqdm import tqdm
from rich.console import Console

from ..config import PROCESSED_DIR, settings
from ..models import Nugget, IdeaCard, IdeaCardList
from ..storage import read_jsonl, append_jsonl, load_processed_ids
from ..llm import parse_structured

console = Console()

NUGGETS_FILE = PROCESSED_DIR / "nuggets.jsonl"
IDEAS_FILE = PROCESSED_DIR / "ideas.jsonl"

SYSTEM_PROMPT = """Ты продукт-аналитик и основатель стартапов в biotech.
Твоя задача — создать проектные идеи (Idea Cards) из списка nuggets.

ЖЁСТКИЕ ПРАВИЛА:
1. Нельзя добавлять факты, которых нет в nuggets.
2. Нельзя ссылаться на внешние источники.
3. Каждая идея должна ссылаться на 2-6 source_nugget_ids из предоставленного списка.
4. Идеи должны быть SOFTWARE-FIRST: реализуемые "из дома" (онлайн + ИИ), без wet-lab.
5. MVP должен быть реализуем за 3-6 месяцев одним разработчиком.

КРИТЕРИИ ХОРОШЕЙ ИДЕИ:
- Перспективность на горизонте 1-10 лет
- Потенциальный "голубой океан" — уникальный угол атаки
- Возможность быстро заинтересовать сообщество (open-source, бенчмарк, каталог)
- Понятный путь к монетизации и потенциальной продаже через 2-3 года

КАТЕГОРИИ:
- bioinformatics: инструменты для биоинформатиков
- biotech_ops: автоматизация операций (QC, LIMS, документация)
- omics: анализ и интерпретация omics-данных
- med_ai: ИИ для медицины (без диагностики!)
- community: комьюнити-продукты (каталоги, бенчмарки)
- education: образовательные инструменты

Пиши на русском, термины можно оставлять на английском."""


def synthesize_ideas_for_batch(doc_id: str, nuggets: list[Nugget], batch_num: int) -> list[IdeaCard]:
    """Синтезирует идеи из одного батча nuggets."""
    
    nuggets_text = "\n".join(
        f"- [{n.nugget_id}] ({n.kind}, {n.confidence}) {n.text_ru}"
        for n in nuggets
    )
    
    user_prompt = f"""DOC_ID: {doc_id}
BATCH: {batch_num}

NUGGETS ({len(nuggets)} штук):
{nuggets_text}

Сгенерируй 3-5 Idea Cards на основе этих nuggets.
Для каждой идеи укажи source_nugget_ids — ID nuggets, на которых она основана."""

    try:
        result: IdeaCardList = parse_structured(
            system=SYSTEM_PROMPT,
            user=user_prompt,
            schema=IdeaCardList,
            max_output_tokens=settings.max_output_tokens_idea,
        )
        
        for idea in result.ideas:
            if not idea.idea_id:
                idea.idea_id = f"idea_{uuid.uuid4().hex[:10]}"
            idea.doc_id = doc_id
        
        return result.ideas
        
    except Exception as e:
        console.print(f"[red]Error synthesizing batch {batch_num} for {doc_id}: {e}[/red]")
        return []


def synthesize_ideas_for_doc(doc_id: str, nuggets: list[Nugget]) -> list[IdeaCard]:
    """Синтезирует идеи из nuggets одного документа, разбивая на батчи."""
    
    BATCH_SIZE = 15  # nuggets на батч — достаточно для контекста, но не переполняет токены
    
    all_ideas = []
    
    # Разбиваем nuggets на батчи
    for i in range(0, len(nuggets), BATCH_SIZE):
        batch = nuggets[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        
        ideas = synthesize_ideas_for_batch(doc_id, batch, batch_num)
        all_ideas.extend(ideas)
    
    return all_ideas


def main():
    console.print("[bold blue]Step 04: Synthesize Ideas[/bold blue]")
    
    nuggets = read_jsonl(NUGGETS_FILE, Nugget)
    if not nuggets:
        console.print("[yellow]No nuggets found. Run step 03 first.[/yellow]")
        return
    
    by_doc = defaultdict(list)
    for n in nuggets:
        by_doc[n.doc_id].append(n)
    
    console.print(f"Found {len(nuggets)} nuggets from {len(by_doc)} documents")
    
    existing_ideas = read_jsonl(IDEAS_FILE, IdeaCard)
    processed_docs = {idea.doc_id for idea in existing_ideas if idea.doc_id}
    
    new_docs = {doc_id: nug for doc_id, nug in by_doc.items() if doc_id not in processed_docs}
    
    if not new_docs:
        console.print(f"[green]All documents processed. Total ideas: {len(existing_ideas)}[/green]")
        return
    
    console.print(f"Processing {len(new_docs)} new documents...")
    
    total_ideas = 0
    
    for doc_id, doc_nuggets in tqdm(new_docs.items(), desc="Synthesizing ideas"):
        if len(doc_nuggets) < 3:
            console.print(f"[yellow]Skipping {doc_id}: only {len(doc_nuggets)} nuggets[/yellow]")
            continue
        
        ideas = synthesize_ideas_for_doc(doc_id, doc_nuggets)
        
        for idea in ideas:
            append_jsonl(IDEAS_FILE, idea)
            total_ideas += 1
    
    all_ideas = read_jsonl(IDEAS_FILE, IdeaCard)
    console.print(f"[green]Done![/green]")
    console.print(f"  New ideas: {total_ideas}")
    console.print(f"  Total ideas: {len(all_ideas)}")
    
    by_category = {}
    for idea in all_ideas:
        by_category[idea.category] = by_category.get(idea.category, 0) + 1
    console.print("  By category:", by_category)


if __name__ == "__main__":
    main()
