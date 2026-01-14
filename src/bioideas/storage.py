"""Утилиты для работы с JSONL файлами."""
import json
from pathlib import Path
from typing import TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def append_jsonl(filepath: Path, obj: BaseModel) -> None:
    """Добавляет объект в JSONL файл."""
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(obj.model_dump_json(ensure_ascii=False) + "\n")


def write_jsonl(filepath: Path, objects: list[BaseModel]) -> None:
    """Записывает список объектов в JSONL файл (перезаписывает)."""
    with open(filepath, "w", encoding="utf-8") as f:
        for obj in objects:
            f.write(obj.model_dump_json(ensure_ascii=False) + "\n")


def read_jsonl(filepath: Path, model: type[T]) -> list[T]:
    """Читает JSONL файл и возвращает список объектов."""
    if not filepath.exists():
        return []
    
    objects = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data = json.loads(line)
                objects.append(model.model_validate(data))
    return objects


def load_processed_ids(filepath: Path, id_field: str = "doc_id") -> set[str]:
    """Загружает множество уже обработанных ID из JSONL."""
    if not filepath.exists():
        return set()
    
    ids = set()
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data = json.loads(line)
                if id_field in data:
                    ids.add(data[id_field])
    return ids
