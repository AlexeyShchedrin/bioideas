"""
Step 06: Score ideas by 5 criteria.

Оценивает каждую идею по 5 критериям (1-10) + риски.
Применяет "нокаут-фильтры" для отсева слабых идей.
"""
from tqdm import tqdm
from rich.console import Console

from ..config import PROCESSED_DIR, settings
from ..models import IdeaCard, ScoreCard
from ..storage import read_jsonl, append_jsonl, write_jsonl, load_processed_ids
from ..llm import parse_structured

console = Console()

IDEAS_DEDUPED_FILE = PROCESSED_DIR / "ideas_deduped.jsonl"
IDEAS_FILE = PROCESSED_DIR / "ideas.jsonl"
SCORES_FILE = PROCESSED_DIR / "scores.jsonl"

SYSTEM_PROMPT = """Ты венчурный аналитик, специализирующийся на biotech-стартапах.
Оцени идею строго по 5 критериям (1-10) и выстави риски.

КРИТЕРИИ:

1. **score_horizon** (Перспективность 1-10 лет):
   - 3: тренд "шумный", но непонятно, что будет драйвером
   - 6: есть понятные драйверы (стоимость, регуляторика, compute)
   - 9: очевидная волна + уже есть ранние внедрения

2. **score_blue_ocean** (Голубой океан):
   - 3: много прямых аналогов, конкуренция фичами и ценой
   - 6: конкуренты есть, но можно занять узкий wedge/данные/канал
   - 9: новая категория или редкое пересечение (ниша+данные+дистрибуция)

3. **score_solo_start** (Старт из дома, онлайн + ИИ):
   - 3: нужно железо/лаб/доступ к закрытым данным/дорогие лицензии
   - 6: можно сделать прототип на открытых данных
   - 9: MVP полностью софт/контент, быстрый цикл обратной связи

4. **score_community_6m** (Интерес сообществу за 3-6 месяцев):
   - 3: ценность появится только после длинной разработки
   - 6: можно сделать бесплатный полезный инструмент для early adopters
   - 9: есть "магнит" (open-source, бенчмарк), который люди начнут шарить

5. **score_exit_2_3y** (Продажа через 2-3 года):
   - 3: value capture туманен, трудно доказать метрики
   - 6: понятны B2B-покупатели или метрики traction
   - 9: очевидный стратегический покупатель + защита (данные, lock-in)

РИСКИ (low/medium/high):
- data_access_risk: насколько критичен доступ к данным
- regulatory_risk: регуляторные/этические риски
- execution_risk: сложность реализации

ПРАВИЛА:
- Опирайся ТОЛЬКО на поля IdeaCard. Не добавляй внешние факты.
- В rationale_ru кратко обоснуй ключевые оценки (2-3 предложения).
- В dealbreakers_ru укажи стоп-факторы, если есть."""


def score_idea(idea: IdeaCard) -> ScoreCard | None:
    """Оценивает одну идею."""
    
    idea_text = f"""IDEA CARD:
- Title: {idea.title_ru}
- One-liner: {idea.one_liner_ru}
- Category: {idea.category}
- Horizon: {idea.horizon} лет
- Problem: {idea.problem_ru}
- Solution: {idea.solution_ru}
- Wedge: {idea.wedge_ru}
- MVP (3-6m): {idea.mvp_3_6m_ru}
- Blue Ocean Thesis: {idea.blue_ocean_thesis_ru}
- Community Hook: {idea.community_hook_ru}
- Early Monetization: {idea.early_monetization_ru}
- Acquirer Types: {', '.join(idea.acquirer_types_ru)}
- Key Risks: {', '.join(idea.key_risks_ru)}"""

    try:
        score: ScoreCard = parse_structured(
            system=SYSTEM_PROMPT,
            user=idea_text,
            schema=ScoreCard,
            max_output_tokens=settings.max_output_tokens_score,
        )
        
        score.idea_id = idea.idea_id
        score.total_score = (
            score.score_horizon +
            score.score_blue_ocean +
            score.score_solo_start +
            score.score_community_6m +
            score.score_exit_2_3y
        )
        
        return score
        
    except Exception as e:
        console.print(f"[red]Error scoring {idea.idea_id}: {e}[/red]")
        return None


def apply_knockout_filters(scores: list[ScoreCard]) -> tuple[list[ScoreCard], list[ScoreCard]]:
    """
    Применяет нокаут-фильтры.
    Возвращает (passed, knocked_out).
    """
    passed = []
    knocked_out = []
    
    for s in scores:
        if s.score_solo_start < 5:
            knocked_out.append(s)
        elif s.score_community_6m < 4:
            knocked_out.append(s)
        elif s.data_access_risk == "high" and s.score_solo_start < 7:
            knocked_out.append(s)
        else:
            passed.append(s)
    
    return passed, knocked_out


def main():
    console.print("[bold blue]Step 06: Score Ideas[/bold blue]")
    
    ideas_file = IDEAS_DEDUPED_FILE if IDEAS_DEDUPED_FILE.exists() else IDEAS_FILE
    ideas = read_jsonl(ideas_file, IdeaCard)
    
    if not ideas:
        console.print("[yellow]No ideas found. Run step 04/05 first.[/yellow]")
        return
    
    console.print(f"Found {len(ideas)} ideas to score")
    
    processed_ids = load_processed_ids(SCORES_FILE, "idea_id")
    new_ideas = [i for i in ideas if i.idea_id not in processed_ids]
    
    if not new_ideas:
        existing_scores = read_jsonl(SCORES_FILE, ScoreCard)
        passed, knocked = apply_knockout_filters(existing_scores)
        console.print(f"[green]All ideas already scored.[/green]")
        console.print(f"  Total: {len(existing_scores)}, Passed filters: {len(passed)}, Knocked out: {len(knocked)}")
        return
    
    console.print(f"Scoring {len(new_ideas)} new ideas...")
    
    for idea in tqdm(new_ideas, desc="Scoring"):
        score = score_idea(idea)
        if score:
            append_jsonl(SCORES_FILE, score)
    
    all_scores = read_jsonl(SCORES_FILE, ScoreCard)
    passed, knocked = apply_knockout_filters(all_scores)
    
    console.print(f"[green]Done![/green]")
    console.print(f"  Total scored: {len(all_scores)}")
    console.print(f"  Passed filters: {len(passed)}")
    console.print(f"  Knocked out: {len(knocked)}")
    
    if passed:
        top_5 = sorted(passed, key=lambda s: s.total_score, reverse=True)[:5]
        console.print("\n[bold]Top 5 by total score:[/bold]")
        for s in top_5:
            console.print(f"  {s.total_score}: {s.idea_id}")


if __name__ == "__main__":
    main()
