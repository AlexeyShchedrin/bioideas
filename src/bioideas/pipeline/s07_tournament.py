"""
Step 07: Pairwise tournament with Elo rating.

Проводит попарные сравнения топ-идей для более точного ранжирования.
Использует Elo-рейтинг для финального ранга.
"""
import random
import uuid
from dataclasses import dataclass
from tqdm import tqdm
from rich.console import Console
from pydantic import BaseModel, Field

from ..config import PROCESSED_DIR
from ..models import IdeaCard, ScoreCard, Comparison, EloRating
from ..storage import read_jsonl, write_jsonl, append_jsonl
from ..llm import parse_structured

console = Console()

SCORES_FILE = PROCESSED_DIR / "scores.jsonl"
IDEAS_FILE = PROCESSED_DIR / "ideas.jsonl"
IDEAS_DEDUPED_FILE = PROCESSED_DIR / "ideas_deduped.jsonl"
COMPARISONS_FILE = PROCESSED_DIR / "comparisons.jsonl"
ELO_FILE = PROCESSED_DIR / "elo_ratings.jsonl"

K_FACTOR = 32
INITIAL_ELO = 1500
TOP_N_FOR_TOURNAMENT = 100  # Расширено: было 25
COMPARISONS_PER_IDEA = 8     # Расширено: было 4


class ComparisonResult(BaseModel):
    """Результат сравнения двух идей."""
    winner_id: str = Field(description="ID идеи-победителя (idea_a_id или idea_b_id)")
    reasoning_ru: str = Field(description="Краткое обоснование выбора (2-3 предложения)")


SYSTEM_PROMPT = """Ты венчурный аналитик. Сравни две идеи и выбери ОДНУ более перспективную.

КРИТЕРИИ СРАВНЕНИЯ (в порядке важности):
1. Возможность стартовать одному из дома (software-first)
2. Быстрый интерес сообщества (3-6 месяцев)
3. Потенциал голубого океана
4. Понятный путь к продаже через 2-3 года
5. Перспективность на горизонте 1-10 лет

ПРАВИЛА:
- Выбери РОВНО ОДНУ идею как winner_id
- winner_id должен быть либо idea_a_id, либо idea_b_id
- В reasoning_ru объясни ключевое преимущество победителя"""


def compare_ideas(idea_a: IdeaCard, idea_b: IdeaCard) -> ComparisonResult | None:
    """Сравнивает две идеи."""
    
    user_prompt = f"""IDEA A (id: {idea_a.idea_id}):
- Title: {idea_a.title_ru}
- Problem: {idea_a.problem_ru}
- Solution: {idea_a.solution_ru}
- Wedge: {idea_a.wedge_ru}
- Community Hook: {idea_a.community_hook_ru}

IDEA B (id: {idea_b.idea_id}):
- Title: {idea_b.title_ru}
- Problem: {idea_b.problem_ru}
- Solution: {idea_b.solution_ru}
- Wedge: {idea_b.wedge_ru}
- Community Hook: {idea_b.community_hook_ru}

Какая идея лучше? Ответь winner_id = "{idea_a.idea_id}" или winner_id = "{idea_b.idea_id}"."""

    try:
        result: ComparisonResult = parse_structured(
            system=SYSTEM_PROMPT,
            user=user_prompt,
            schema=ComparisonResult,
            max_output_tokens=400,
        )
        
        if result.winner_id not in [idea_a.idea_id, idea_b.idea_id]:
            result.winner_id = idea_a.idea_id
        
        return result
        
    except Exception as e:
        console.print(f"[red]Error comparing: {e}[/red]")
        return None


def update_elo(ratings: dict[str, float], winner_id: str, loser_id: str) -> None:
    """Обновляет Elo-рейтинги после матча."""
    winner_elo = ratings.get(winner_id, INITIAL_ELO)
    loser_elo = ratings.get(loser_id, INITIAL_ELO)
    
    expected_winner = 1 / (1 + 10 ** ((loser_elo - winner_elo) / 400))
    expected_loser = 1 - expected_winner
    
    ratings[winner_id] = winner_elo + K_FACTOR * (1 - expected_winner)
    ratings[loser_id] = loser_elo + K_FACTOR * (0 - expected_loser)


def generate_matchups(idea_ids: list[str], comparisons_per_idea: int) -> list[tuple[str, str]]:
    """Генерирует пары для сравнения (швейцарская система)."""
    matchups = []
    match_counts = {id_: 0 for id_ in idea_ids}
    
    shuffled = idea_ids.copy()
    random.shuffle(shuffled)
    
    for _ in range(len(idea_ids) * comparisons_per_idea // 2):
        available = [id_ for id_ in shuffled if match_counts[id_] < comparisons_per_idea]
        if len(available) < 2:
            break
        
        id_a = random.choice(available)
        available.remove(id_a)
        id_b = random.choice(available)
        
        matchups.append((id_a, id_b))
        match_counts[id_a] += 1
        match_counts[id_b] += 1
    
    return matchups


def main():
    console.print("[bold blue]Step 07: Tournament[/bold blue]")
    
    scores = read_jsonl(SCORES_FILE, ScoreCard)
    if not scores:
        console.print("[yellow]No scores found. Run step 06 first.[/yellow]")
        return
    
    # Мягкий фильтр: минимум 25 баллов
    passed = [s for s in scores if s.total_score >= 25]
    passed.sort(key=lambda s: s.total_score, reverse=True)
    
    top_scores = passed[:TOP_N_FOR_TOURNAMENT]
    top_ids = [s.idea_id for s in top_scores]
    
    console.print(f"Tournament with top {len(top_ids)} ideas")
    
    ideas_file = IDEAS_DEDUPED_FILE if IDEAS_DEDUPED_FILE.exists() else IDEAS_FILE
    all_ideas = read_jsonl(ideas_file, IdeaCard)
    ideas_map = {i.idea_id: i for i in all_ideas}
    
    matchups = generate_matchups(top_ids, COMPARISONS_PER_IDEA)
    console.print(f"Generated {len(matchups)} matchups")
    
    ratings = {id_: INITIAL_ELO for id_ in top_ids}
    wins = {id_: 0 for id_ in top_ids}
    losses = {id_: 0 for id_ in top_ids}
    
    for id_a, id_b in tqdm(matchups, desc="Running tournament"):
        idea_a = ideas_map.get(id_a)
        idea_b = ideas_map.get(id_b)
        
        if not idea_a or not idea_b:
            continue
        
        result = compare_ideas(idea_a, idea_b)
        if not result:
            continue
        
        winner_id = result.winner_id
        loser_id = id_b if winner_id == id_a else id_a
        
        update_elo(ratings, winner_id, loser_id)
        wins[winner_id] = wins.get(winner_id, 0) + 1
        losses[loser_id] = losses.get(loser_id, 0) + 1
        
        comparison = Comparison(
            comparison_id=f"cmp_{uuid.uuid4().hex[:10]}",
            idea_a_id=id_a,
            idea_b_id=id_b,
            winner_id=winner_id,
            reasoning_ru=result.reasoning_ru,
        )
        append_jsonl(COMPARISONS_FILE, comparison)
    
    elo_ratings = []
    for idea_id in top_ids:
        elo = EloRating(
            idea_id=idea_id,
            elo=ratings[idea_id],
            wins=wins.get(idea_id, 0),
            losses=losses.get(idea_id, 0),
            comparisons=wins.get(idea_id, 0) + losses.get(idea_id, 0),
        )
        elo_ratings.append(elo)
    
    elo_ratings.sort(key=lambda e: e.elo, reverse=True)
    write_jsonl(ELO_FILE, elo_ratings)
    
    console.print(f"[green]Done![/green]")
    console.print("\n[bold]Final Elo Rankings (Top 10):[/bold]")
    for i, elo in enumerate(elo_ratings[:10], 1):
        idea = ideas_map.get(elo.idea_id)
        title = idea.title_ru if idea else elo.idea_id
        console.print(f"  {i}. Elo {elo.elo:.0f} ({elo.wins}W-{elo.losses}L): {title[:50]}")


if __name__ == "__main__":
    main()
