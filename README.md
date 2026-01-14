# BioIdeas

Система извлечения и оценки бизнес-идей из транскриптов биотех-подкастов.

## Установка

```bash
# 1. Создать виртуальное окружение
python -m venv .venv
.venv\Scripts\activate  # Windows

# 2. Установить зависимости
pip install -e .

# 3. Настроить переменные окружения
copy .env.example .env
# Отредактировать .env — добавить OPENAI_API_KEY

# 4. Запустить Qdrant (Docker)
docker run -d -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

## Структура данных

```
data/
  raw/              # Исходные транскрипты (.txt/.md)
  processed/
    chunks.jsonl    # Чанки текста
    nuggets.jsonl   # Извлечённые "зёрна" (pain/trend/opportunity)
    ideas.jsonl     # Идеи проектов (Idea Cards)
    scores.jsonl    # Оценки по 5 критериям
    comparisons.jsonl  # Результаты турнира
    memos/          # Decision memos для топ-идей
```

## Пайплайн

```bash
# 1. Загрузка и разбивка транскриптов на чанки
python -m bioideas.pipeline.s01_ingest

# 2. Создание эмбеддингов чанков
python -m bioideas.pipeline.s02_embed_chunks

# 3. Извлечение nuggets из чанков
python -m bioideas.pipeline.s03_extract_nuggets

# 4. Синтез Idea Cards из nuggets
python -m bioideas.pipeline.s04_synthesize_ideas

# 5. Дедупликация и кластеризация идей
python -m bioideas.pipeline.s05_dedupe_cluster

# 6. Скоринг идей по 5 критериям
python -m bioideas.pipeline.s06_score

# 7. Турнир попарных сравнений (Elo)
python -m bioideas.pipeline.s07_tournament

# 8. Экспорт decision memos для топ-идей
python -m bioideas.pipeline.s08_export_memos
```

## Streamlit UI

```bash
streamlit run app/streamlit_app.py
```

## Критерии оценки идей

1. **Перспективность (1-10 лет)** — тренд + драйверы внедрения
2. **Голубой океан** — уникальность, отсутствие прямых конкурентов
3. **Старт из дома** — можно делать онлайн + ИИ, без wet-lab
4. **Интерес сообществу (3-6 мес)** — быстрый "магнит" (open-source, бенчмарк)
5. **Продажа через 2-3 года** — понятный покупатель и value capture
