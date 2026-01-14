import re
import uuid
from pathlib import Path
from .config import settings
from .models import Chunk, Episode

TIMECODE_RE = re.compile(r"(?<!\d)(?:\d{1,2}:)?\d{1,2}:\d{2}(?!\d)")


def normalize_text(text: str) -> str:
    """Нормализует текст: убирает лишние пробелы и переносы."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def extract_metadata(text: str, filename: str) -> tuple[str, Episode]:
    """
    Пытается извлечь метаданные из начала файла.
    Возвращает (очищенный текст, Episode).
    """
    lines = text.split("\n")
    title = filename.replace(".txt", "").replace(".md", "").replace("_", " ").strip()
    date = None
    guests = []
    
    metadata_end = 0
    for i, line in enumerate(lines[:20]):
        line_lower = line.lower().strip()
        if line_lower.startswith("title:") or line_lower.startswith("название:"):
            title = line.split(":", 1)[1].strip()
            metadata_end = i + 1
        elif line_lower.startswith("date:") or line_lower.startswith("дата:"):
            date = line.split(":", 1)[1].strip()
            metadata_end = i + 1
        elif line_lower.startswith("guests:") or line_lower.startswith("гости:"):
            guests_str = line.split(":", 1)[1].strip()
            guests = [g.strip() for g in guests_str.split(",") if g.strip()]
            metadata_end = i + 1
        elif line.strip() == "---":
            metadata_end = i + 1
            break
    
    cleaned_text = "\n".join(lines[metadata_end:]).strip()
    
    doc_id = f"doc_{uuid.uuid4().hex[:12]}"
    episode = Episode(
        doc_id=doc_id,
        title=title,
        filename=filename,
        date=date,
        guests=guests,
        source_path=filename,
    )
    
    return cleaned_text, episode


def split_by_timecodes_or_paragraphs(text: str) -> list[str]:
    """Разбивает текст по таймкодам или абзацам."""
    if TIMECODE_RE.search(text):
        parts = re.split(r"\n(?=(?:\d{1,2}:)?\d{1,2}:\d{2}\b)", text)
        return [p.strip() for p in parts if p.strip()]
    return [p.strip() for p in text.split("\n\n") if p.strip()]


def pack_to_chunks(
    parts: list[str],
    target_chars: int,
    overlap_chars: int
) -> list[tuple[str, int, int]]:
    """
    Собирает части в чанки нужного размера.
    Возвращает [(text, char_start, char_end), ...]
    """
    chunks = []
    buf = ""
    buf_start = 0
    current_pos = 0
    
    for p in parts:
        part_len = len(p)
        
        if len(buf) + len(p) + 2 <= target_chars:
            if buf:
                buf = buf + "\n\n" + p
            else:
                buf = p
                buf_start = current_pos
        else:
            if buf:
                chunks.append((buf, buf_start, buf_start + len(buf)))
            
            if overlap_chars and chunks:
                tail = chunks[-1][0][-overlap_chars:]
                buf = tail + "\n\n" + p
                buf_start = current_pos - len(tail)
            else:
                buf = p
                buf_start = current_pos
        
        current_pos += part_len + 2
    
    if buf:
        chunks.append((buf, buf_start, buf_start + len(buf)))
    
    return chunks


def extract_timecode(text: str) -> str | None:
    """Извлекает первый таймкод из текста."""
    match = TIMECODE_RE.search(text)
    return match.group(0) if match else None


def chunk_document(text: str, doc_id: str) -> list[Chunk]:
    """
    Разбивает документ на чанки.
    Возвращает список Chunk объектов.
    """
    text = normalize_text(text)
    parts = split_by_timecodes_or_paragraphs(text)
    packed = pack_to_chunks(
        parts,
        settings.chunk_target_chars,
        settings.chunk_overlap_chars
    )
    
    chunks = []
    for i, (chunk_text, char_start, char_end) in enumerate(packed):
        start_time = extract_timecode(chunk_text)
        
        chunk = Chunk(
            chunk_id=f"{doc_id}_chunk_{i:04d}",
            doc_id=doc_id,
            order=i,
            text=chunk_text,
            char_start=char_start,
            char_end=char_end,
            start_time=start_time,
        )
        chunks.append(chunk)
    
    return chunks


def process_transcript_file(filepath: Path) -> tuple[Episode, list[Chunk]]:
    """
    Обрабатывает один файл транскрипта.
    Возвращает (Episode, list[Chunk]).
    """
    text = filepath.read_text(encoding="utf-8")
    cleaned_text, episode = extract_metadata(text, filepath.name)
    episode.source_path = str(filepath)
    
    chunks = chunk_document(cleaned_text, episode.doc_id)
    
    return episode, chunks
