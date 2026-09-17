"""
GrowX AI Structured Output Engine.
Handles JSON extraction, markdown stripping, heuristic repair, and Pydantic validation.
"""

import json
import re
from typing import Any, Dict, Optional, Tuple, Type
from pydantic import BaseModel, ValidationError
from growx_crawl.ai.errors import AISchemaValidationError


def extract_json_block(text: str) -> str:
    """Extracts JSON content from text, handling markdown code fences."""
    clean = (text or "").strip()
    # Match ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", clean, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Match first '{' to last '}'
    first_brace = clean.find("{")
    last_brace = clean.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        return clean[first_brace : last_brace + 1].strip()

    # Match first '[' to last ']'
    first_bracket = clean.find("[")
    last_bracket = clean.rfind("]")
    if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
        return clean[first_bracket : last_bracket + 1].strip()

    return clean


def repair_json_text(text: str) -> str:
    """Attempts lightweight local heuristic repairs on common LLM JSON syntax mistakes."""
    repaired = text

    # Remove trailing commas in objects: {"a": 1,} -> {"a": 1}
    repaired = re.sub(r",\s*\}", "}", repaired)

    # Remove trailing commas in arrays: [1, 2,] -> [1, 2]
    repaired = re.sub(r",\s*\]", "]", repaired)

    # Replace python None, True, False if unquoted
    repaired = re.sub(r"\bNone\b", "null", repaired)
    repaired = re.sub(r"\bTrue\b", "true", repaired)
    repaired = re.sub(r"\bFalse\b", "false", repaired)

    return repaired


def parse_and_validate_structured(
    text: str,
    schema_class: Optional[Type[BaseModel]] = None,
    task: str = "",
) -> Tuple[Dict[str, Any], Optional[BaseModel]]:
    """
    Parses LLM output into a dictionary and validates it against a Pydantic schema if provided.
    Returns (dict_data, validated_pydantic_instance_or_none).
    Raises AISchemaValidationError if parsing or validation cannot be satisfied.
    """
    raw_block = extract_json_block(text)
    data: Optional[Dict[str, Any]] = None

    # Attempt 1: Direct parse
    try:
        data = json.loads(raw_block)
    except Exception:
        # Attempt 2: Local heuristic repair
        repaired = repair_json_text(raw_block)
        try:
            data = json.loads(repaired)
        except Exception as e:
            raise AISchemaValidationError(
                message=f"Could not parse valid JSON from AI output: {e}",
                raw_output=text[:500],
                schema_name=schema_class.__name__ if schema_class else "dict",
                task=task,
            )

    if not isinstance(data, dict) and not isinstance(data, list):
        raise AISchemaValidationError(
            message=f"Expected JSON object/array from AI output, got {type(data).__name__}",
            raw_output=text[:500],
            schema_name=schema_class.__name__ if schema_class else "dict",
            task=task,
        )

    # Validate against Pydantic schema
    instance: Optional[BaseModel] = None
    if schema_class and issubclass(schema_class, BaseModel) and isinstance(data, dict):
        try:
            instance = schema_class.model_validate(data)
            data = instance.model_dump()
        except ValidationError as val_err:
            raise AISchemaValidationError(
                message=f"Structured AI output failed schema validation: {val_err}",
                raw_output=text[:500],
                schema_name=schema_class.__name__,
                task=task,
            )

    return data, instance
