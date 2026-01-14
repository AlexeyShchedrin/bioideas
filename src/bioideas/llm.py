import time
import json
from typing import TypeVar
from openai import OpenAI
from pydantic import BaseModel
from .config import settings

client = OpenAI(api_key=settings.openai_api_key)

T = TypeVar("T", bound=BaseModel)


def pydantic_to_json_schema(model: type[BaseModel]) -> dict:
    """Конвертирует Pydantic модель в JSON Schema для Responses API."""
    schema = model.model_json_schema()
    
    def make_strict(s: dict) -> dict:
        if s.get("type") == "object":
            s["additionalProperties"] = False
            if "properties" in s:
                s["required"] = list(s["properties"].keys())
                for prop in s["properties"].values():
                    make_strict(prop)
        if "items" in s:
            make_strict(s["items"])
        if "$defs" in s:
            for defn in s["$defs"].values():
                make_strict(defn)
        return s
    
    return make_strict(schema)


def parse_structured(
    *,
    system: str,
    user: str,
    schema: type[T],
    max_output_tokens: int | None = None,
    temperature: float = 0,
) -> T:
    """
    Вызывает Responses API с structured output.
    Возвращает экземпляр Pydantic модели.
    """
    json_schema = pydantic_to_json_schema(schema)
    
    for attempt in range(settings.llm_retry_attempts):
        try:
            response = client.responses.create(
                model=settings.openai_model,
                input=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": schema.__name__,
                        "schema": json_schema,
                        "strict": True,
                    }
                },
                max_output_tokens=max_output_tokens or settings.max_output_tokens_extract,
                temperature=temperature,
                store=settings.store_responses,
            )
            
            output_text = response.output_text
            data = json.loads(output_text)
            return schema.model_validate(data)
            
        except Exception as e:
            if attempt < settings.llm_retry_attempts - 1:
                time.sleep(settings.llm_retry_delay * (attempt + 1))
                continue
            raise RuntimeError(f"LLM call failed after {settings.llm_retry_attempts} attempts: {e}")


def generate_text(
    *,
    system: str,
    user: str,
    max_output_tokens: int | None = None,
    temperature: float = 0.7,
) -> str:
    """Генерирует обычный текст (для memo и т.п.)."""
    for attempt in range(settings.llm_retry_attempts):
        try:
            response = client.responses.create(
                model=settings.openai_model,
                input=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                max_output_tokens=max_output_tokens or 2000,
                temperature=temperature,
                store=settings.store_responses,
            )
            return response.output_text
            
        except Exception as e:
            if attempt < settings.llm_retry_attempts - 1:
                time.sleep(settings.llm_retry_delay * (attempt + 1))
                continue
            raise RuntimeError(f"LLM call failed after {settings.llm_retry_attempts} attempts: {e}")
