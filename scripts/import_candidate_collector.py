from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


OVERPASS_QUERY = """
[out:json][timeout:60];
(
  nwr["aerialway"];
  nwr["railway"="funicular"];
  nwr["railway"="rail"]["rack"="yes"];
  nwr["railway"="monorail"];
);
out center tags;
""".strip()


WIKIDATA_SPARQL_QUERY = """
SELECT ?item ?itemLabel ?itemLabelRu ?itemLabelEn ?itemLabelDe ?coord
       ?countryLabel ?operatorLabel ?officialWebsite
       ?osmRelationId ?osmWayId ?osmNodeId ?instanceOf ?instanceOfLabel
WHERE {
  VALUES ?candidateClass {
    wd:Q1424016   # канатная дорога
    wd:Q857516    # гондольная канатная дорога
    wd:Q193266    # фуникулер
    wd:Q2175765   # зубчатая железная дорога
    wd:Q187934    # монорельс
  }
  ?item wdt:P31/wdt:P279* ?candidateClass.
  OPTIONAL { ?item wdt:P31 ?instanceOf. }
  OPTIONAL { ?item wdt:P625 ?coord. }
  OPTIONAL { ?item wdt:P17 ?country. }
  OPTIONAL { ?item wdt:P137 ?operator. }
  OPTIONAL { ?item wdt:P856 ?officialWebsite. }
  OPTIONAL { ?item wdt:P402 ?osmRelationId. }
  OPTIONAL { ?item wdt:P10689 ?osmWayId. }
  OPTIONAL { ?item wdt:P11693 ?osmNodeId. }
  OPTIONAL { ?item rdfs:label ?itemLabelRu FILTER(LANG(?itemLabelRu) = "ru") }
  OPTIONAL { ?item rdfs:label ?itemLabelEn FILTER(LANG(?itemLabelEn) = "en") }
  OPTIONAL { ?item rdfs:label ?itemLabelDe FILTER(LANG(?itemLabelDe) = "de") }
  SERVICE wikibase:label {
    bd:serviceParam wikibase:language "ru,en,de".
    ?item rdfs:label ?itemLabel.
    ?country rdfs:label ?countryLabel.
    ?operator rdfs:label ?operatorLabel.
    ?instanceOf rdfs:label ?instanceOfLabel.
  }
}
LIMIT 500
""".strip()


REVIEW_NOTE = "Требуется ручная проверка типа, эксплуатационного статуса и русского описания."
STATUS_NOTE = "Черновой статус: OSM/Wikidata не являются источником актуального расписания; нужна ручная проверка."


def load_json(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def collect_candidates(osm_data: dict[str, Any], wikidata_data: dict[str, Any]) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    index: dict[str, int] = {}

    for record in _osm_records(osm_data):
        _merge_record(candidates, index, record)

    for record in _wikidata_records(wikidata_data):
        _merge_record(candidates, index, record)

    candidates.sort(key=lambda item: item["id"])
    return {
        "schema_version": "import-candidates-v1",
        "generated_by": "scripts/import_candidate_collector.py",
        "queries": {
            "overpass": OVERPASS_QUERY,
            "wikidata_sparql": WIKIDATA_SPARQL_QUERY,
        },
        "candidates": candidates,
    }


def write_staging_json(payload: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def validate_if_available(output_path: Path) -> str:
    for validator in _validator_candidates():
        if validator.exists():
            result = subprocess.run(
                [sys.executable, str(validator), str(output_path)],
                check=False,
                text=True,
                capture_output=True,
            )
            if result.returncode != 0:
                raise RuntimeError((result.stderr or result.stdout).strip())
            return f"Проверено валидатором {validator}"
    return "Валидатор staging JSON не найден, проверка пропущена"


def fetch_overpass() -> dict[str, Any]:
    data = urllib.parse.urlencode({"data": OVERPASS_QUERY}).encode("utf-8")
    request = urllib.request.Request("https://overpass-api.de/api/interpreter", data=data)
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_wikidata() -> dict[str, Any]:
    params = urllib.parse.urlencode({"query": WIKIDATA_SPARQL_QUERY, "format": "json"})
    request = urllib.request.Request(
        f"https://query.wikidata.org/sparql?{params}",
        headers={"Accept": "application/sparql-results+json"},
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        return json.loads(response.read().decode("utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Собрать staging JSON кандидатов из OSM/Wikidata.")
    parser.add_argument("--osm-json", type=Path, help="Offline JSON-ответ Overpass.")
    parser.add_argument("--wikidata-json", type=Path, help="Offline JSON-ответ Wikidata SPARQL.")
    parser.add_argument("--output", type=Path, required=True, help="Путь к staging JSON.")
    parser.add_argument("--online", action="store_true", help="Выполнить сетевые запросы вместо offline fixtures.")
    parser.add_argument("--print-queries", action="store_true", help="Напечатать Overpass и SPARQL запросы.")
    parser.add_argument("--no-validate", action="store_true", help="Не запускать валидатор staging JSON.")
    args = parser.parse_args(argv)

    if args.print_queries:
        print("# Overpass")
        print(OVERPASS_QUERY)
        print("\n# Wikidata SPARQL")
        print(WIKIDATA_SPARQL_QUERY)

    if args.online:
        osm_data = fetch_overpass()
        wikidata_data = fetch_wikidata()
    else:
        osm_data = load_json(args.osm_json)
        wikidata_data = load_json(args.wikidata_json)

    payload = collect_candidates(osm_data, wikidata_data)
    write_staging_json(payload, args.output)

    if not args.no_validate:
        print(validate_if_available(args.output))
    print(f"Записано кандидатов: {len(payload['candidates'])}")
    print(f"Staging JSON: {args.output}")
    return 0


def _osm_records(osm_data: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for element in osm_data.get("elements", []):
        tags = element.get("tags") or {}
        if not _is_target_osm_element(tags):
            continue
        osm_ref = f"{element.get('type')}/{element.get('id')}"
        title = _first_text(tags, ["name:ru", "name", "official_name", "name:en", "name:de"])
        latitude, longitude = _osm_coordinates(element)
        source_urls = [_osm_url(osm_ref)]
        if tags.get("website"):
            source_urls.append(str(tags["website"]))
        if tags.get("contact:website"):
            source_urls.append(str(tags["contact:website"]))
        if tags.get("wikidata"):
            source_urls.append(_wikidata_url(str(tags["wikidata"])))

        record = _blank_record(
            id=_record_id(str(tags.get("wikidata") or ""), osm_ref, title),
            title=title or f"Кандидат OSM {osm_ref}",
            latitude=latitude,
            longitude=longitude,
            transport_type_id=_draft_type_from_osm(tags),
        )
        record["operator"] = str(tags.get("operator", ""))
        record["opened_year"] = _year_from_text(str(tags.get("start_date") or tags.get("opening_date") or "")) or None
        record["localized"]["en"]["title"] = str(tags.get("name:en", ""))
        record["localized"]["de"]["title"] = str(tags.get("name:de", ""))
        record["source_ids"]["osm"] = [osm_ref]
        if tags.get("wikidata"):
            record["source_ids"]["wikidata"] = str(tags["wikidata"])
        if tags.get("operator:wikidata"):
            record["source_ids"]["operator_wikidata"] = str(tags["operator:wikidata"])
        record["source_urls"] = _unique(source_urls)
        records.append(record)
    return records


def _wikidata_records(wikidata_data: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    for binding in wikidata_data.get("results", {}).get("bindings", []):
        qid = _qid(_value(binding, "item"))
        if not qid:
            continue
        title_ru = _value(binding, "itemLabelRu") or _value(binding, "itemLabel")
        title_en = _value(binding, "itemLabelEn")
        title_de = _value(binding, "itemLabelDe")
        latitude, longitude = _wikidata_coordinates(_value(binding, "coord"))
        source_urls = [_wikidata_url(qid)]
        if _value(binding, "officialWebsite"):
            source_urls.append(_value(binding, "officialWebsite"))

        record = _blank_record(
            id=_record_id(qid, "", title_ru),
            title=title_ru or f"Кандидат Wikidata {qid}",
            latitude=latitude,
            longitude=longitude,
            transport_type_id=_draft_type_from_wikidata(binding),
        )
        record["country"] = _value(binding, "countryLabel") or "Страна требует ручной проверки"
        record["operator"] = _value(binding, "operatorLabel")
        record["localized"]["en"]["title"] = title_en
        record["localized"]["de"]["title"] = title_de
        record["source_ids"]["wikidata"] = qid
        osm_refs = []
        if _value(binding, "osmRelationId"):
            record["source_ids"]["wikidata_osm_relation"] = _value(binding, "osmRelationId")
            osm_refs.append(f"relation/{_value(binding, 'osmRelationId')}")
        if _value(binding, "osmWayId"):
            record["source_ids"]["wikidata_osm_way"] = _value(binding, "osmWayId")
            osm_refs.append(f"way/{_value(binding, 'osmWayId')}")
        if _value(binding, "osmNodeId"):
            record["source_ids"]["wikidata_osm_node"] = _value(binding, "osmNodeId")
            osm_refs.append(f"node/{_value(binding, 'osmNodeId')}")
        if osm_refs:
            record["source_ids"]["osm"] = osm_refs
            source_urls.extend(_osm_url(ref) for ref in osm_refs)
        record["source_urls"] = _unique(source_urls)
        records.append(record)
    return records


def _merge_record(candidates: list[dict[str, Any]], index: dict[str, int], record: dict[str, Any]) -> None:
    keys = _merge_keys(record)
    existing_indexes = sorted({index[key] for key in keys if key in index})
    if not existing_indexes:
        candidates.append(record)
        candidate_index = len(candidates) - 1
        for key in keys:
            index[key] = candidate_index
        return

    target_index = existing_indexes[0]
    target = candidates[target_index]
    _overlay_record(target, record)
    for duplicate_index in reversed(existing_indexes[1:]):
        _overlay_record(target, candidates[duplicate_index])
        del candidates[duplicate_index]
        for key, value in list(index.items()):
            if value == duplicate_index:
                index[key] = target_index
            elif value > duplicate_index:
                index[key] = value - 1
    for key in _merge_keys(target):
        index[key] = target_index


def _merge_keys(record: dict[str, Any]) -> set[str]:
    source_ids = record.get("source_ids", {})
    keys = set()
    if source_ids.get("wikidata"):
        keys.add(f"wikidata:{source_ids['wikidata']}")
    for osm_ref in source_ids.get("osm", []):
        keys.add(f"osm:{osm_ref}")
    for field, prefix in [
        ("wikidata_osm_relation", "relation"),
        ("wikidata_osm_way", "way"),
        ("wikidata_osm_node", "node"),
    ]:
        if source_ids.get(field):
            keys.add(f"osm:{prefix}/{source_ids[field]}")
    return keys


def _overlay_record(target: dict[str, Any], record: dict[str, Any]) -> None:
    for field in ["country", "region", "city", "operator", "manufacturer", "status_source_url"]:
        if not target.get(field) and record.get(field):
            target[field] = record[field]
    for field in ["latitude", "longitude", "opened_year"]:
        if target.get(field) in ("", None, 0) and record.get(field) not in ("", None, 0):
            target[field] = record[field]
    if target.get("transport_type_id") == "special_transport_system" and record.get("transport_type_id"):
        target["transport_type_id"] = record["transport_type_id"]

    for lang, data in record.get("localized", {}).items():
        target.setdefault("localized", {}).setdefault(lang, {})
        for text_field, value in data.items():
            if not target["localized"][lang].get(text_field) and value:
                target["localized"][lang][text_field] = value

    target.setdefault("source_ids", {})
    if record.get("source_ids", {}).get("wikidata"):
        target["source_ids"]["wikidata"] = record["source_ids"]["wikidata"]
    target["source_ids"]["osm"] = _unique(
        list(target["source_ids"].get("osm", [])) + list(record.get("source_ids", {}).get("osm", []))
    )
    for field, value in record.get("source_ids", {}).items():
        if field not in {"osm", "wikidata"} and value and not target["source_ids"].get(field):
            target["source_ids"][field] = value
    target["source_urls"] = _unique(list(target.get("source_urls", [])) + list(record.get("source_urls", [])))


def _blank_record(
    id: str,
    title: str,
    latitude: float | None,
    longitude: float | None,
    transport_type_id: str,
) -> dict[str, Any]:
    return {
        "id": id,
        "transport_type_id": transport_type_id,
        "visit_status_id": "not_visited",
        "country": "Страна требует ручной проверки",
        "region": "",
        "city": "",
        "latitude": latitude,
        "longitude": longitude,
        "localized": {
            "ru": {
                "title": title,
                "description": "Черновой кандидат из OSM/Wikidata. Описание требует ручной редакторской проверки.",
            },
            "de": {"title": "", "description": ""},
            "en": {"title": "", "description": ""},
        },
        "opened_year": None,
        "operator": "",
        "manufacturer": "",
        "operational_status": "unknown",
        "status_checked_at": "",
        "status_source_url": "",
        "status_note": STATUS_NOTE,
        "source_ids": {},
        "source_urls": [],
        "review": {
            "state": "candidate",
            "reviewed_by": "",
            "reviewed_at": "",
            "notes": REVIEW_NOTE,
        },
    }


def _is_target_osm_element(tags: dict[str, Any]) -> bool:
    if "aerialway" in tags:
        return True
    if tags.get("railway") == "funicular":
        return True
    if tags.get("railway") == "rail" and tags.get("rack") == "yes":
        return True
    return tags.get("railway") == "monorail"


def _draft_type_from_osm(tags: dict[str, Any]) -> str:
    if tags.get("aerialway") == "gondola":
        return "cable_gondola"
    if tags.get("aerialway") == "cable_car":
        return "cable_aerial_tram"
    if tags.get("railway") == "funicular":
        return "funicular_classic"
    if tags.get("railway") == "rail" and tags.get("rack") == "yes":
        return "rail_cog"
    if tags.get("railway") == "monorail" and tags.get("monorail") == "hanging":
        return "suspended_train"
    if tags.get("railway") == "monorail":
        return "monorail"
    return "special_transport_system"


def _draft_type_from_wikidata(binding: dict[str, Any]) -> str:
    labels = " ".join(
        [
            _value(binding, "itemLabel"),
            _value(binding, "itemLabelEn"),
            _value(binding, "itemLabelRu"),
            _value(binding, "instanceOfLabel"),
        ]
    ).lower()
    if "funicular" in labels or "фуникулер" in labels:
        return "funicular_classic"
    if "rack" in labels or "cog" in labels or "зубчат" in labels:
        return "rail_cog"
    if "monorail" in labels or "монорельс" in labels:
        return "monorail"
    if "gondola" in labels or "гондоль" in labels:
        return "cable_gondola"
    if "cable car" in labels or "канат" in labels:
        return "cable_aerial_tram"
    return "special_transport_system"


def _osm_coordinates(element: dict[str, Any]) -> tuple[float | None, float | None]:
    if "lat" in element and "lon" in element:
        return float(element["lat"]), float(element["lon"])
    center = element.get("center") or {}
    if "lat" in center and "lon" in center:
        return float(center["lat"]), float(center["lon"])
    return None, None


def _wikidata_coordinates(value: str) -> tuple[float | None, float | None]:
    match = re.match(r"Point\(([-0-9.]+) ([-0-9.]+)\)", value)
    if not match:
        return None, None
    return float(match.group(2)), float(match.group(1))


def _record_id(qid: str, osm_ref: str, title: str) -> str:
    slug = _slugify(title)
    if slug:
        return slug
    if qid:
        return f"wikidata-{qid.lower()}"
    return f"osm-{osm_ref.replace('/', '-')}"


def _slugify(text: str) -> str:
    translit = {
        "а": "a",
        "б": "b",
        "в": "v",
        "г": "g",
        "д": "d",
        "е": "e",
        "ё": "e",
        "ж": "zh",
        "з": "z",
        "и": "i",
        "й": "y",
        "к": "k",
        "л": "l",
        "м": "m",
        "н": "n",
        "о": "o",
        "п": "p",
        "р": "r",
        "с": "s",
        "т": "t",
        "у": "u",
        "ф": "f",
        "х": "h",
        "ц": "ts",
        "ч": "ch",
        "ш": "sh",
        "щ": "sch",
        "ы": "y",
        "э": "e",
        "ю": "yu",
        "я": "ya",
    }
    lowered = text.lower().replace("ь", "").replace("ъ", "")
    ascii_text = "".join(translit.get(char, char) for char in lowered)
    ascii_text = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    return re.sub(r"-+", "-", ascii_text)


def _first_text(source: dict[str, Any], keys: list[str]) -> str:
    for key in keys:
        if source.get(key):
            return str(source[key])
    return ""


def _year_from_text(text: str) -> int | None:
    match = re.search(r"\b(18|19|20)\d{2}\b", text)
    if not match:
        return None
    return int(match.group(0))


def _value(binding: dict[str, Any], key: str) -> str:
    return str(binding.get(key, {}).get("value", ""))


def _qid(value: str) -> str:
    match = re.search(r"/entity/(Q\d+)$", value)
    if match:
        return match.group(1)
    if re.fullmatch(r"Q\d+", value):
        return value
    return ""


def _osm_url(osm_ref: str) -> str:
    kind, id_value = osm_ref.split("/", 1)
    return f"https://www.openstreetmap.org/{kind}/{id_value}"


def _wikidata_url(qid: str) -> str:
    return f"https://www.wikidata.org/wiki/{qid}"


def _unique(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def _validator_candidates() -> list[Path]:
    root = Path(__file__).resolve().parents[1]
    return [
        root / "scripts" / "validate_import_candidates.py",
        root / "scripts" / "validate_staging_candidates.py",
        root / "scripts" / "validate_candidate_staging.py",
    ]


if __name__ == "__main__":
    raise SystemExit(main())
