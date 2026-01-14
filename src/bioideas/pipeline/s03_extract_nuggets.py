"""
Step 03: Extract nuggets from chunks.

Для каждого чанка извлекает 0-3 "зерна" (pain/trend/opportunity/constraint/buyer_signal)
с обязательными цитатами. Валидирует, что цитаты есть в исходном тексте.
"""
import uuid
from tqdm import tqdm
from rich.console import Console

from ..config import PROCESSED_DIR, settings
from ..models import Chunk, Nugget, NuggetList, Evidence
from ..storage import read_jsonl, append_jsonl, load_processed_ids
from ..llm import parse_structured

console = Console()

CHUNKS_FILE = PROCESSED_DIR / "chunks.jsonl"
NUGGETS_FILE = PROCESSED_DIR / "nuggets.jsonl"

SYSTEM_PROMPT = """Ты аналитик венчурных возможностей в biotech.
Задача: извлечь из текста только то, что реально сказано, без добавления фактов.

Категории nuggets:
- pain: боль/проблема, с которой сталкиваются люди в индустрии
- trend: наблюдаемый тренд или изменение
- opportunity: возможность для нового продукта/сервиса
- constraint: ограничение или барьер (регуляторика, данные, технологии)
- buyer_signal: сигнал о готовности платить или потребности в решении

ЖЁСТКИЕ ПРАВИЛА:
1. Если в тексте нет ничего полезного — верни пустой список nuggets.
2. Evidence.quote: ДОСЛОВНАЯ цитата из текста (≤ 25 слов). НЕ перефразируй.
3. Не выдумывай названия компаний/цифры/результаты, которых нет в тексте.
4. Максимум 3 nuggets на чанк. Лучше меньше, но точнее.
5. chunk_id в evidence должен совпадать с ID анализируемого чанка."""


def validate_quotes(chunk_text: str, nuggets: NuggetList) -> list[str]:
    """Проверяет, что цитаты действительно есть в тексте."""
    errors = []
    lowered = chunk_text.lower()
    
    for n in nuggets.nuggets:
        if not n.evidence:
            errors.append(f"{n.nugget_id}: no evidence provided")
            continue
        
        for ev in n.evidence:
            quote = ev.quote.strip().lower()
            if not quote:
                errors.append(f"{n.nugget_id}: empty quote")
                continue
            
            words = quote.split()
            if len(words) < 3:
                continue
            
            key_phrase = " ".join(words[:5])
            if key_phrase not in lowered:
                alt_phrase = " ".join(words[-5:])
                if alt_phrase not in lowered:
                    errors.append(f"{n.nugget_id}: quote not found in chunk")
    
    return errors


def extract_nuggets_from_chunk(chunk: Chunk) -> list[Nugget]:
    """Извлекает nuggets из одного чанка."""
    user_prompt = f"""CHUNK_ID: {chunk.chunk_id}
DOC_ID: {chunk.doc_id}

TEXT:
---
{chunk.text}
---

Извлеки 0-3 nuggets. Для каждого укажи chunk_id="{chunk.chunk_id}" в evidence."""

    try:
        result: NuggetList = parse_structured(
            system=SYSTEM_PROMPT,
            user=user_prompt,
            schema=NuggetList,
            max_output_tokens=settings.max_output_tokens_extract,
        )
        
        for n in result.nuggets:
            if not n.nugget_id:
                n.nugget_id = f"n_{uuid.uuid4().hex[:10]}"
            n.doc_id = chunk.doc_id
            
            for ev in n.evidence:
                ev.chunk_id = chunk.chunk_id
        
        errors = validate_quotes(chunk.text, result)
        if errors:
            console.print(f"[yellow]Validation warnings for {chunk.chunk_id}: {errors}[/yellow]")
        
        return result.nuggets
        
    except Exception as e:
        console.print(f"[red]Error extracting from {chunk.chunk_id}: {e}[/red]")
        return []


def main():
    console.print("[bold blue]Step 03: Extract Nuggets[/bold blue]")
    
    chunks = read_jsonl(CHUNKS_FILE, Chunk)
    if not chunks:
        console.print("[yellow]No chunks found. Run step 01 first.[/yellow]")
        return
    
    processed_chunks = load_processed_ids(NUGGETS_FILE, "nugget_id")
    existing_nuggets = read_jsonl(NUGGETS_FILE, Nugget)
    processed_chunk_ids = {n.evidence[0].chunk_id for n in existing_nuggets if n.evidence}
    
    new_chunks = [c for c in chunks if c.chunk_id not in processed_chunk_ids]
    
    if not new_chunks:
        console.print(f"[green]All chunks processed. Total nuggets: {len(existing_nuggets)}[/green]")
        return
    
    console.print(f"Processing {len(new_chunks)} new chunks...")
    
    total_nuggets = 0
    
    for chunk in tqdm(new_chunks, desc="Extracting nuggets"):
        nuggets = extract_nuggets_from_chunk(chunk)
        
        for nugget in nuggets:
            append_jsonl(NUGGETS_FILE, nugget)
            total_nuggets += 1
    
    all_nuggets = read_jsonl(NUGGETS_FILE, Nugget)
    console.print(f"[green]Done![/green]")
    console.print(f"  New nuggets: {total_nuggets}")
    console.print(f"  Total nuggets: {len(all_nuggets)}")
    
    by_kind = {}
    for n in all_nuggets:
        by_kind[n.kind] = by_kind.get(n.kind, 0) + 1
    console.print("  By kind:", by_kind)


if __name__ == "__main__":
    main()
