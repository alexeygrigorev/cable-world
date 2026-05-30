# Прототип сборщика кандидатов OSM/Wikidata

Документ описывает прототип для GitHub issue #29. Он не является production importer: скрипт пишет только staging JSON, не меняет SQLite, seed, UI, `VERSION`, export presets и release workflow.

## CLI

Offline-режим используется по умолчанию:

```bash
python3 scripts/import_candidate_collector.py \
  --osm-json tests/fixtures/import_candidates/osm_overpass_sample.json \
  --wikidata-json tests/fixtures/import_candidates/wikidata_sparql_sample.json \
  --output /tmp/cable-world-import-candidates.json
```

Сетевой вызов включается только явно через `--online`. Запросы можно посмотреть без импорта:

```bash
python3 scripts/import_candidate_collector.py --print-queries --output /tmp/candidates.json --no-validate
```

Если в репозитории появится валидатор staging JSON из issue #28, CLI попробует запустить один из файлов:

- `scripts/validate_import_candidates.py`;
- `scripts/validate_staging_candidates.py`;
- `scripts/validate_candidate_staging.py`.

Staging JSON читается единообразно импортными CLI: одиночная запись, массив записей,
объект `{ "records": [...] }` и payload collector с `{ "candidates": [...] }`.

## Источники

Overpass-запрос собирает:

- `aerialway=*`;
- `railway=funicular`;
- `railway=rail` + `rack=yes`;
- `railway=monorail`.

Wikidata SPARQL-запрос выбирает кандидатов через `P31` с учетом `P279` и вытаскивает:

- `P625` координаты;
- `P17` страну;
- `P137` оператора;
- `P856` официальный сайт;
- `P402` OSM relation id;
- `P10689` OSM way id;
- `P11693` OSM node id.

## Merge

Кандидаты объединяются по стабильным source-ключам:

- OSM `wikidata=*`;
- OSM element id в форме `node/123`, `way/123`, `relation/123`;
- Wikidata `P402`, `P10689`, `P11693`, приведенным к тем же OSM element id.

`transport_type_id` и `operational_status` остаются черновыми. `operational_status` всегда `unknown`, а `review.notes` и `status_note` явно требуют ручной проверки перед seed.
