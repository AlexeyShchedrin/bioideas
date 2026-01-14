"""Тесты для диагностики системы BioIdeas."""
import sys
sys.path.insert(0, "src")

from rich.console import Console
console = Console()


def test_env():
    """Проверка переменных окружения."""
    console.print("\n[bold]1. Проверка .env[/bold]")
    from bioideas.config import settings
    
    if settings.openai_api_key:
        console.print(f"  ✅ OPENAI_API_KEY: {settings.openai_api_key[:20]}...")
    else:
        console.print("  ❌ OPENAI_API_KEY не найден!")
        return False
    
    console.print(f"  ✅ Model: {settings.openai_model}")
    console.print(f"  ✅ Qdrant URL: {settings.qdrant_url}")
    return True


def test_qdrant():
    """Проверка подключения к Qdrant."""
    console.print("\n[bold]2. Проверка Qdrant[/bold]")
    try:
        from bioideas.vectorstore import get_client
        client = get_client()
        collections = client.get_collections()
        console.print(f"  ✅ Qdrant доступен, коллекций: {len(collections.collections)}")
        return True
    except Exception as e:
        console.print(f"  ❌ Qdrant недоступен: {e}")
        return False


def test_openai_simple():
    """Простой тест OpenAI API."""
    console.print("\n[bold]3. Проверка OpenAI API (простой)[/bold]")
    try:
        from openai import OpenAI
        from bioideas.config import settings
        
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.responses.create(
            model=settings.openai_model,
            input=[{"role": "user", "content": "Say 'OK' if you work."}],
            max_output_tokens=20,
        )
        console.print(f"  ✅ OpenAI ответил: {response.output_text}")
        return True
    except Exception as e:
        console.print(f"  ❌ OpenAI ошибка: {e}")
        return False


def test_structured_output():
    """Тест Structured Outputs."""
    console.print("\n[bold]4. Проверка Structured Outputs[/bold]")
    try:
        from pydantic import BaseModel
        from bioideas.llm import parse_structured
        
        class TestResponse(BaseModel):
            answer: str
            number: int
        
        result = parse_structured(
            system="You are a helpful assistant.",
            user="What is 2+2? Answer with the word and number.",
            schema=TestResponse,
            max_output_tokens=50,
        )
        console.print(f"  ✅ Structured output: answer={result.answer}, number={result.number}")
        return True
    except Exception as e:
        console.print(f"  ❌ Structured output ошибка: {e}")
        return False


def test_nugget_extraction():
    """Тест извлечения nuggets из короткого текста."""
    console.print("\n[bold]5. Проверка извлечения Nuggets[/bold]")
    try:
        from bioideas.models import Chunk, NuggetList
        from bioideas.llm import parse_structured
        
        test_chunk = Chunk(
            chunk_id="test_chunk_001",
            doc_id="test_doc",
            order=0,
            text="""The biotech industry is facing a major challenge with data management. 
            Many companies struggle to integrate their LIMS systems with analysis pipelines.
            This creates a huge opportunity for software solutions that can bridge this gap.
            As one expert noted: "We spend 40% of our time just moving data between systems."
            """,
            char_start=0,
            char_end=300,
        )
        
        system = """Extract 1-2 nuggets from the text. Each nugget must have:
- nugget_id: unique id starting with "n_"
- doc_id: the document id provided
- kind: one of "pain", "trend", "opportunity", "constraint", "buyer_signal"
- text_ru: description in Russian
- text_en: description in English  
- evidence: list with at least one item containing chunk_id and a quote from the text
- confidence: "low", "medium", or "high"
"""
        
        user = f"CHUNK_ID: {test_chunk.chunk_id}\nDOC_ID: {test_chunk.doc_id}\n\nTEXT:\n{test_chunk.text}"
        
        result: NuggetList = parse_structured(
            system=system,
            user=user,
            schema=NuggetList,
            max_output_tokens=800,
        )
        
        console.print(f"  ✅ Извлечено nuggets: {len(result.nuggets)}")
        for n in result.nuggets:
            console.print(f"     - [{n.kind}] {n.text_en[:50]}...")
        return True
    except Exception as e:
        console.print(f"  ❌ Nugget extraction ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    console.print("[bold blue]===== BioIdeas System Tests =====[/bold blue]")
    
    results = []
    results.append(("ENV", test_env()))
    results.append(("Qdrant", test_qdrant()))
    results.append(("OpenAI Simple", test_openai_simple()))
    results.append(("Structured Output", test_structured_output()))
    results.append(("Nugget Extraction", test_nugget_extraction()))
    
    console.print("\n[bold]===== Результаты =====[/bold]")
    for name, ok in results:
        status = "✅" if ok else "❌"
        console.print(f"  {status} {name}")
    
    all_ok = all(r[1] for r in results)
    if all_ok:
        console.print("\n[bold green]Все тесты пройдены![/bold green]")
    else:
        console.print("\n[bold red]Есть проблемы, см. выше.[/bold red]")


if __name__ == "__main__":
    main()
