from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime


class Episode(BaseModel):
    """Метаданные эпизода подкаста."""
    doc_id: str
    title: str
    filename: str
    date: str | None = None
    guests: list[str] = Field(default_factory=list)
    source_path: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class Chunk(BaseModel):
    """Чанк текста из транскрипта."""
    chunk_id: str
    doc_id: str
    order: int
    text: str
    char_start: int
    char_end: int
    start_time: str | None = None
    end_time: str | None = None


class Evidence(BaseModel):
    """Доказательство — цитата из чанка."""
    chunk_id: str
    quote: str = Field(description="Verbatim quote from that chunk (<= 25 words).")


class Nugget(BaseModel):
    """Извлечённое 'зерно' — боль, тренд, возможность."""
    nugget_id: str
    doc_id: str
    kind: Literal["pain", "trend", "opportunity", "constraint", "buyer_signal"]
    text_ru: str = Field(description="Краткое описание на русском")
    text_en: str = Field(description="Brief description in English")
    evidence: list[Evidence] = Field(default_factory=list)
    confidence: Literal["low", "medium", "high"]


class NuggetList(BaseModel):
    """Список nuggets, извлечённых из одного чанка."""
    nuggets: list[Nugget] = Field(default_factory=list)


class IdeaCard(BaseModel):
    """Карточка идеи проекта."""
    idea_id: str
    doc_id: str | None = None

    title_ru: str = Field(description="Рабочее название идеи")
    one_liner_ru: str = Field(description="Одно предложение — суть идеи")

    category: str = Field(description="Категория: bioinformatics, biotech_ops, omics, med_ai, community, education")
    horizon: Literal["1-3", "3-5", "5-10"] = Field(description="Горизонт в годах")

    problem_ru: str = Field(description="Кто страдает и почему это важно")
    solution_ru: str = Field(description="Что именно строим")

    wedge_ru: str = Field(description="Самый маленький полезный продукт для старта из дома")
    mvp_3_6m_ru: str = Field(description="MVP за 3-6 месяцев — что будет работать")
    blue_ocean_thesis_ru: str = Field(description="Почему это может быть голубым океаном")
    community_hook_ru: str = Field(description="Крючок для сообщества (open-source, бенчмарк, каталог)")

    early_monetization_ru: str = Field(description="Как появятся первые деньги/контракты")
    acquirer_types_ru: list[str] = Field(description="Типы потенциальных покупателей через 2-3 года")
    key_risks_ru: list[str] = Field(description="Ключевые риски")

    source_nugget_ids: list[str] = Field(description="ID nuggets, на которых основана идея")


class IdeaCardList(BaseModel):
    """Список идей, синтезированных из nuggets."""
    ideas: list[IdeaCard] = Field(default_factory=list)


class ScoreCard(BaseModel):
    """Оценка идеи по 5 критериям."""
    idea_id: str

    score_horizon: int = Field(ge=1, le=10, description="Перспективность 1-10 лет")
    score_blue_ocean: int = Field(ge=1, le=10, description="Голубой океан")
    score_solo_start: int = Field(ge=1, le=10, description="Старт из дома (онлайн + ИИ)")
    score_community_6m: int = Field(ge=1, le=10, description="Интерес сообществу за 3-6 мес")
    score_exit_2_3y: int = Field(ge=1, le=10, description="Продажа через 2-3 года")

    total_score: int = Field(default=0, description="Сумма 5 критериев")

    data_access_risk: Literal["low", "medium", "high"]
    regulatory_risk: Literal["low", "medium", "high"]
    execution_risk: Literal["low", "medium", "high"]

    rationale_ru: str = Field(description="Краткая аргументация оценок")
    dealbreakers_ru: list[str] = Field(default_factory=list, description="Стоп-факторы")


class Comparison(BaseModel):
    """Результат попарного сравнения в турнире."""
    comparison_id: str
    idea_a_id: str
    idea_b_id: str
    winner_id: str
    reasoning_ru: str
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class EloRating(BaseModel):
    """Elo-рейтинг идеи после турнира."""
    idea_id: str
    elo: float = 1500.0
    wins: int = 0
    losses: int = 0
    comparisons: int = 0
