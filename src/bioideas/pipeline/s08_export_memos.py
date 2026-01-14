"""
Step 08: Export decision memos for top ideas.

Генерирует 1-страничные decision memo для топ-5 идей.
"""
from pathlib import Path
from tqdm import tqdm
from rich.console import Console

from ..config import PROCESSED_DIR, MEMOS_DIR
from ..models import IdeaCard, ScoreCard, EloRating, Nugget
from ..storage import read_jsonl
from ..llm import generate_text

console = Console()

IDEAS_FILE = PROCESSED_DIR / "ideas.jsonl"
IDEAS_DEDUPED_FILE = PROCESSED_DIR / "ideas_deduped.jsonl"
SCORES_FILE = PROCESSED_DIR / "scores.jsonl"
ELO_FILE = PROCESSED_DIR / "elo_ratings.jsonl"
NUGGETS_FILE = PROCESSED_DIR / "nuggets.jsonl"

TOP_N_MEMOS = 10  # Расширено: было 5

SYSTEM_PROMPT = """Ты венчурный аналитик. Напиши краткий decision memo для инвестиционного комитета.

ФОРМАТ MEMO (строго на русском):

# [Название идеи]

## Суть (1-2 предложения)
Что строим и для кого.

## Проблема
Кто страдает и почему это важно сейчас.

## Решение
Что именно делает продукт.

## MVP (3-6 месяцев)
Конкретный функционал первой версии.

## Почему сейчас
Что изменилось, что делает это возможным/нужным.

## Голубой океан
В чём уникальность и почему конкуренты не займут эту нишу быстро.

## Путь к traction
Как привлечь первых пользователей и создать buzz.

## Монетизация
Как появятся первые деньги.

## Exit thesis
Кто может купить через 2-3 года и почему.

## Риски и митигация
Топ-3 риска и как их снизить.

## Доказательства
Ссылки на конкретные nuggets/цитаты из подкастов.

---

Пиши кратко, по делу, без воды. Максимум 500 слов."""


def get_top_ideas(n: int = TOP_N_MEMOS) -> list[tuple[IdeaCard, ScoreCard | None, EloRating | None]]:
    """Получает топ-N идей по Elo (или по score, если турнира не было)."""
    
    ideas_file = IDEAS_DEDUPED_FILE if IDEAS_DEDUPED_FILE.exists() else IDEAS_FILE
    ideas = read_jsonl(ideas_file, IdeaCard)
    scores = read_jsonl(SCORES_FILE, ScoreCard)
    elo_ratings = read_jsonl(ELO_FILE, EloRating)
    
    ideas_map = {i.idea_id: i for i in ideas}
    scores_map = {s.idea_id: s for s in scores}
    
    if elo_ratings:
        elo_ratings.sort(key=lambda e: e.elo, reverse=True)
        top_ids = [e.idea_id for e in elo_ratings[:n]]
        elo_map = {e.idea_id: e for e in elo_ratings}
    else:
        scores.sort(key=lambda s: s.total_score, reverse=True)
        top_ids = [s.idea_id for s in scores[:n]]
        elo_map = {}
    
    result = []
    for idea_id in top_ids:
        idea = ideas_map.get(idea_id)
        if idea:
            result.append((
                idea,
                scores_map.get(idea_id),
                elo_map.get(idea_id)
            ))
    
    return result


def get_nuggets_for_idea(idea: IdeaCard, all_nuggets: list[Nugget]) -> list[Nugget]:
    """Находит nuggets, на которых основана идея."""
    nugget_map = {n.nugget_id: n for n in all_nuggets}
    return [nugget_map[nid] for nid in idea.source_nugget_ids if nid in nugget_map]


def generate_memo(
    idea: IdeaCard,
    score: ScoreCard | None,
    elo: EloRating | None,
    nuggets: list[Nugget]
) -> str:
    """Генерирует decision memo для идеи."""
    
    nuggets_text = ""
    for n in nuggets[:5]:
        quotes = ", ".join([f'"{e.quote}"' for e in n.evidence[:2]])
        nuggets_text += f"- [{n.kind}] {n.text_ru} ({quotes})\n"
    
    score_text = ""
    if score:
        score_text = f"""
SCORES:
- Horizon: {score.score_horizon}/10
- Blue Ocean: {score.score_blue_ocean}/10  
- Solo Start: {score.score_solo_start}/10
- Community 6m: {score.score_community_6m}/10
- Exit 2-3y: {score.score_exit_2_3y}/10
- Total: {score.total_score}/50
- Risks: data={score.data_access_risk}, regulatory={score.regulatory_risk}, execution={score.execution_risk}
"""
    
    elo_text = f"Elo: {elo.elo:.0f} ({elo.wins}W-{elo.losses}L)" if elo else ""
    
    user_prompt = f"""IDEA CARD:
- Title: {idea.title_ru}
- One-liner: {idea.one_liner_ru}
- Category: {idea.category}
- Horizon: {idea.horizon} лет
- Problem: {idea.problem_ru}
- Solution: {idea.solution_ru}
- Wedge: {idea.wedge_ru}
- MVP: {idea.mvp_3_6m_ru}
- Blue Ocean: {idea.blue_ocean_thesis_ru}
- Community Hook: {idea.community_hook_ru}
- Monetization: {idea.early_monetization_ru}
- Acquirers: {', '.join(idea.acquirer_types_ru)}
- Risks: {', '.join(idea.key_risks_ru)}
{score_text}
{elo_text}

SOURCE NUGGETS:
{nuggets_text}

Напиши decision memo по формату."""

    return generate_text(
        system=SYSTEM_PROMPT,
        user=user_prompt,
        max_output_tokens=1500,
        temperature=0.5,
    )


def main():
    console.print("[bold blue]Step 08: Export Decision Memos[/bold blue]")
    
    top_ideas = get_top_ideas(TOP_N_MEMOS)
    if not top_ideas:
        console.print("[yellow]No ideas found. Run previous steps first.[/yellow]")
        return
    
    all_nuggets = read_jsonl(NUGGETS_FILE, Nugget)
    
    console.print(f"Generating memos for top {len(top_ideas)} ideas...")
    
    for i, (idea, score, elo) in enumerate(tqdm(top_ideas, desc="Generating memos"), 1):
        nuggets = get_nuggets_for_idea(idea, all_nuggets)
        
        memo = generate_memo(idea, score, elo, nuggets)
        
        safe_title = "".join(c if c.isalnum() or c in " -_" else "_" for c in idea.title_ru)[:50]
        filename = f"{i:02d}_{safe_title}.md"
        filepath = MEMOS_DIR / filename
        
        filepath.write_text(memo, encoding="utf-8")
        print(f"  Saved memo {i}")
    
    print(f"Done! Memos saved to {MEMOS_DIR}")


if __name__ == "__main__":
    main()
