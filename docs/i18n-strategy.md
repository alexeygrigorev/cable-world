# Стратегия i18n

Документ фиксирует подготовку «Мира Троссов» к будущей многоязычности без массового перевода текущего интерфейса. Сейчас основной язык продукта - русский. Русский UX не должен ухудшаться: существующие строки остаются видимыми на русском, пока конкретный экран не переводится планово.

Целевые языки первого этапа i18n: `ru`, `de`, `en`.

## Принципы

- Стабильные идентификаторы не являются текстом интерфейса. `id`, `transport_type_id`, `visit_status_id`, `operational_status`, `kind` и будущие enum-поля хранят ASCII slug в нижнем регистре: `cable_gondola`, `not_visited`, `active_seasonal`.
- Русские строки используются как display labels и контент, но не как ключи данных, enum-id, имена миграций или имена storage-полей.
- Перевод UI и перевод каталога разделены. UI-строки идут через Godot translations, каталог объектов хранит локализованные поля рядом с доменными id.
- Текущая SQLite-схема и демо-каталог остаются совместимыми с русским MVP. Добавление локализации должно быть миграцией или отдельным импортным слоем, а не переименованием существующих id.

## UI в Godot

Позже UI-строки нужно выносить в Godot translation files: CSV или PO в каталоге `res://i18n/`, импортируемые Godot как `Translation` resources. Основной набор ключей должен иметь русские значения, а затем немецкие и английские варианты.

Формат ключей:

- `app.title`;
- `nav.map`;
- `nav.list`;
- `filter.transport_type`;
- `filter.visit_status`;
- `status.visit.not_visited`;
- `status.operational.active_seasonal`;
- `object_card.opened_year`;
- `empty.list_no_results`.

Новые UI-строки после введения translation files должны добавляться сразу как ключи и выводиться через `tr("key")`. До этого момента новые русские строки допустимы только для маленьких MVP-доработок, но рядом с ними не должно появляться новых русских id.

Строки, которые нужно вынести позже:

- название приложения и заголовки основных экранов;
- подписи кнопок, фильтров, вкладок и пунктов меню;
- empty states, ошибки, подтверждения и уведомления;
- labels карточки объекта: координаты, год открытия, оператор, производитель, статус посещения, эксплуатационный статус;
- display labels справочников `VisitStatus`, `OperationalStatus`, `TransportType`, `MediaAsset.kind`;
- форматируемые фразы с параметрами, например счетчики фото и даты проверки статуса.

Не нужно выносить в UI translations:

- стабильные id объектов и справочников;
- URL источников;
- пользовательские заметки;
- локализованные поля каталога объектов, которые хранятся как данные.

## Каталог объектов

`TransportObject.id` остается главным стабильным ключом объекта и не зависит от языка. Названия и описания объектов должны перейти на локализованные поля.

Рекомендуемый контракт для импортного каталога:

```json
{
  "id": "berlin-gaerten-der-welt",
  "transport_type_id": "cable_gondola",
  "country_code": "DE",
  "localized": {
    "ru": {
      "title": "Канатная дорога в садах мира Берлина",
      "description": "Гондольная канатная дорога над парком Gärten der Welt."
    },
    "de": {
      "title": "Seilbahn in den Gärten der Welt",
      "description": "Gondelbahn über den Gärten der Welt."
    },
    "en": {
      "title": "Gärten der Welt cable car",
      "description": "Gondola lift above Gärten der Welt."
    }
  }
}
```

Для MVP существующие поля `title`/`name`, `description`, `country`, `region`, `city`, `notes` остаются русскими display/content-полями. Будущая миграция может добавить таблицу `transport_object_localizations`:

```sql
CREATE TABLE transport_object_localizations (
    transport_object_id TEXT NOT NULL REFERENCES transport_objects(id) ON DELETE CASCADE,
    locale TEXT NOT NULL CHECK (locale IN ('ru', 'de', 'en')),
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    country TEXT NOT NULL DEFAULT '',
    region TEXT NOT NULL DEFAULT '',
    city TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (transport_object_id, locale)
);
```

Правила для каталога:

- `ru` обязателен для каждого объекта, потому что текущий продукт русский;
- `de` и `en` можно добавлять постепенно;
- если нужной локали нет, UI показывает `ru`;
- `operator`, `manufacturer`, `opened_year`, координаты, источники и технические id не переводятся как UI-строки;
- `status_note` может стать локализованным полем, если заметка пишется редакционно, но не если это пользовательская заметка или краткая цитата источника.

## Справочники и статусы

Справочники должны хранить id и display labels отдельно.

Для SQLite текущий контракт уже такой:

- `visit_statuses.id` - стабильный id, `visit_statuses.title` - русская подпись;
- `transport_types.id` - стабильный id, `transport_types.title` и `group_title` - русские подписи;
- `transport_objects.operational_status` - стабильный id, display label сейчас возвращается кодом.

Будущая локализация справочников может быть оформлена отдельными translation keys:

- `transport_type.cable_gondola`;
- `transport_type_group.cable`;
- `visit_status.not_visited`;
- `operational_status.active`.

Новый тип или статус считается корректным только если у него есть:

- стабильный ASCII id;
- русская display label для текущего UX;
- translation key или явное место, где этот label будет подключен к translation files;
- тест/контракт, который не дает использовать русскую строку как id.

## План внедрения

1. Зафиксировать эту стратегию и data-contract тесты для id/label.
2. При следующей крупной UI-итерации добавить `res://i18n/ru.csv` и подключить `tr()` для новых и изменяемых экранов.
3. При выносе каталога из GDScript в JSON или SQLite seed добавить структуру локализованных полей с обязательным `ru`.
4. После появления `de`/`en` добавить fallback-логику выбора языка: выбранная локаль, затем `ru`, затем стабильный id только как технический fallback.
