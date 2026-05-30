#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "schemas" / "staging_catalog_candidate.schema.json"


class ValidationError(Exception):
    pass


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ValidationError(f"{path}: некорректный JSON: {error}") from error


def validate_candidate(candidate: Any, schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    _validate_schema_node(candidate, schema, "$", schema, errors)
    return errors


def _validate_schema_node(
    value: Any,
    node: dict[str, Any],
    path: str,
    root_schema: dict[str, Any],
    errors: list[str],
) -> None:
    if "$ref" in node:
        ref = node["$ref"]
        if not isinstance(ref, str) or not ref.startswith("#/$defs/"):
            errors.append(f"{path}: валидатор поддерживает только локальные $defs-ссылки")
            return
        definition_name = ref.removeprefix("#/$defs/")
        definition = root_schema.get("$defs", {}).get(definition_name)
        if not isinstance(definition, dict):
            errors.append(f"{path}: в схеме не найдено определение {definition_name}")
            return
        _validate_schema_node(value, definition, path, root_schema, errors)
        return

    if "oneOf" in node:
        variants = node["oneOf"]
        if not isinstance(variants, list):
            errors.append(f"{path}: oneOf в схеме должен быть массивом")
            return
        if _matches_any_variant(value, variants, path, root_schema):
            return
        errors.append(f"{path}: значение не прошло ни один вариант oneOf")
        return

    expected_type = node.get("type")
    if expected_type is not None and not _matches_type(value, expected_type):
        errors.append(f"{path}: ожидается тип {_format_type(expected_type)}")
        return

    if "enum" in node and value not in node["enum"]:
        allowed = ", ".join(node["enum"])
        errors.append(f"{path}: значение {value!r} не входит в разрешенный набор: {allowed}")

    if isinstance(value, str):
        if "minLength" in node and len(value) < int(node["minLength"]):
            errors.append(f"{path}: строка не должна быть пустой")
        pattern = node.get("pattern")
        if isinstance(pattern, str) and re.search(pattern, value) is None:
            errors.append(f"{path}: строка не соответствует шаблону {pattern}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = node.get("minimum")
        maximum = node.get("maximum")
        if minimum is not None and value < minimum:
            errors.append(f"{path}: значение меньше {minimum}")
        if maximum is not None and value > maximum:
            errors.append(f"{path}: значение больше {maximum}")

    if isinstance(value, dict):
        _validate_object(value, node, path, root_schema, errors)
    elif isinstance(value, list):
        _validate_array(value, node, path, root_schema, errors)


def _validate_object(
    value: dict[str, Any],
    node: dict[str, Any],
    path: str,
    root_schema: dict[str, Any],
    errors: list[str],
) -> None:
    required = node.get("required", [])
    if isinstance(required, list):
        for field in required:
            if field not in value:
                errors.append(f"{path}.{field}: обязательное поле отсутствует")

    properties = node.get("properties", {})
    if not isinstance(properties, dict):
        properties = {}

    additional = node.get("additionalProperties", True)
    for key, child_value in value.items():
        child_path = f"{path}.{key}"
        if key in properties:
            _validate_schema_node(child_value, properties[key], child_path, root_schema, errors)
        elif isinstance(additional, dict):
            _validate_schema_node(child_value, additional, child_path, root_schema, errors)
        elif additional is False:
            errors.append(f"{child_path}: поле не описано в схеме")


def _validate_array(
    value: list[Any],
    node: dict[str, Any],
    path: str,
    root_schema: dict[str, Any],
    errors: list[str],
) -> None:
    items = node.get("items")
    if not isinstance(items, dict):
        return
    for index, item in enumerate(value):
        _validate_schema_node(item, items, f"{path}[{index}]", root_schema, errors)


def _matches_any_variant(
    value: Any,
    variants: list[Any],
    path: str,
    root_schema: dict[str, Any],
) -> bool:
    for variant in variants:
        if not isinstance(variant, dict):
            continue
        errors: list[str] = []
        _validate_schema_node(value, variant, path, root_schema, errors)
        if not errors:
            return True
    return False


def _matches_type(value: Any, expected_type: Any) -> bool:
    if isinstance(expected_type, list):
        return any(_matches_type(value, single_type) for single_type in expected_type)
    if expected_type == "object":
        return isinstance(value, dict)
    if expected_type == "array":
        return isinstance(value, list)
    if expected_type == "string":
        return isinstance(value, str)
    if expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected_type == "null":
        return value is None
    if expected_type == "boolean":
        return isinstance(value, bool)
    return False


def _format_type(expected_type: Any) -> str:
    if isinstance(expected_type, list):
        return " или ".join(str(item) for item in expected_type)
    return str(expected_type)


def _candidate_items(document: Any) -> list[Any]:
    if isinstance(document, list):
        return document
    if isinstance(document, dict) and isinstance(document.get("candidates"), list):
        return document["candidates"]
    return [document]


def validate_file(path: Path, schema: dict[str, Any]) -> list[str]:
    document = load_json(path)
    errors: list[str] = []
    for index, candidate in enumerate(_candidate_items(document)):
        for error in validate_candidate(candidate, schema):
            errors.append(f"{path}#{index}: {error}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Проверяет staging JSON-кандидатов каталога по локальной схеме."
    )
    parser.add_argument("paths", nargs="+", type=Path, help="JSON-файлы кандидатов")
    parser.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA,
        help="Путь к JSON Schema staging-кандидата",
    )
    args = parser.parse_args(argv)

    try:
        schema = load_json(args.schema)
        all_errors: list[str] = []
        for path in args.paths:
            all_errors.extend(validate_file(path, schema))
    except ValidationError as error:
        print(error, file=sys.stderr)
        return 2

    if all_errors:
        for error in all_errors:
            print(error, file=sys.stderr)
        return 1

    print("Staging-кандидаты прошли проверку.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
