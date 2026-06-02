# Мир Троссов

«Мир Троссов» — семейное приложение о канатных дорогах, фуникулерах, лифтах, подвесном транспорте и необычных инженерных сооружениях.

Цель MVP: дать семье простой способ находить объекты на карте, смотреть список и карточку объекта, отмечать посещения, хранить фото или билеты и вести локальный журнал поездок.

## MVP

- карта объектов на базе OpenStreetMap/MapLibre;
- список объектов с фильтрами по типу и региону;
- карточка объекта с описанием, координатами и семейными заметками;
- отметка «посещено»;
- прикрепление фото и билетов;
- журнал посещений;
- локальное хранение данных.

## Технологии

- Godot 4.6.x как основной клиент;
- typed GDScript без C# на первом этапе;
- SQLite для первого локального хранилища;
- PocketBase позже, когда появится синхронизация между устройствами;
- MapLibre/OpenStreetMap для карты, после проверки Godot-интеграции;
- Python `unittest` для быстрых контрактных проверок проекта;
- позже GdUnit4 для сценариев внутри Godot.

## Текущий каркас

Сейчас проект содержит стартовую сцену Godot 4 с локальным SQLite-хранилищем на Linux desktop:

- слева показан список объектов;
- справа открывается карточка выбранного объекта;
- при запуске создается и мигрируется `user://mir-trossov.sqlite3`;
- SQL seed добавляет демо-объекты без перезаписи пользовательских статусов;
- кнопка в карточке переключает отметку посещения и сохраняет ее в SQLite;
- ниже ведется простой журнал действий за сессию.

Если SQLite runtime недоступен, например в Web export, приложение честно деградирует к встроенному `DemoCatalog` без сохранения изменений между запусками.

Документация начинается с [docs/README.md](docs/README.md). Доменная модель MVP и SQLite-схема описаны в [docs/data-model.md](docs/data-model.md).
SQL migrations и demo seed закреплены в `scripts/storage/`; быстрый SQLite-контракт проверяется стандартным Python `sqlite3`, а runtime-контракт проверяется Godot headless через vendored GDExtension `addons/godot-sqlite`.

## Проверки

Быстрая проверка без установленного Godot:

```bash
python3 -m unittest discover -s tests
```

Пайплайны генерации glyph-ассетов описаны в [docs/pipelines/glyph-generation.md](docs/pipelines/glyph-generation.md). Городские glyphs отдельно: [docs/pipelines/city-glyphs.md](docs/pipelines/city-glyphs.md).

Проверка нарезки glyph sheets перед добавлением ассетов в карту:

```bash
python3 -m map_pipeline.sheet_slice_audit \
  --sheet tmp/<sheet>.png \
  --ids id_1,id_2,id_3,id_4 \
  --columns 4
```

Этот чек смотрит на пиксельную полоску вдоль линий разреза и ловит случаи, когда alpha-компонент реально пересекает grid cut. Он включен в городской и транспортный слайсеры через `--edge-audit`.

Если Godot установлен, этот же набор дополнительно запускает движок в headless-режиме:

```bash
godot --headless --path . --import --quit
godot --headless --path . --quit-after 1
python3 -m unittest discover -s tests
```

Так мы ловим не только ошибки структуры файлов, но и реальные ошибки компиляции GDScript, загрузки главной сцены и работы SQLite-адаптера внутри Godot. Позже добавим GdUnit4 для сценариев Godot и оставим Python-проверки как быстрый контракт структуры проекта в CI.

## Web-сборка локально

Для локального Web export нужен установленный `godot`. Штатный скрипт пересобирает проект в `build/web`, добавляет cache busting и поднимает сервер на `http://127.0.0.1:9000/`:

```bash
PORT=9000 scripts/serve-web.sh
```

Если нужно отдать уже существующую сборку без нового export:

```bash
PORT=9000 scripts/serve-web.sh --no-export
```

Скрипт сохраняет PID сервера в `build/web/.serve-web.pid`. Остановить управляемый сервер можно так:

```bash
scripts/stop-web.sh
```

Проверить текущий локальный сервер и build stamp можно так:

```bash
PORT=9000 scripts/web-status.sh
```

## Android APK

APK для установки на телефон публикуется в GitHub Releases вместе с Web/Linux-архивами. В релизе нужно скачать файл вида `mir-trossov-android-<version>.apk` и установить его вручную как sideload APK.

Перед семейной установкой пройти ручной [release smoke test](docs/releases.md): запуск, ориентация, карта, карточка объекта, фото, статусы и объекты Германии.

Android package id закреплен как `com.mirtrossov.app`, имя приложения на устройстве — «Мир Троссов». APK подписывается стабильным `android/debug.keystore` из репозитория со стандартными debug credentials. Это dev/sideload подпись для семейных сборок, не production key для Google Play.

Будущие APK должны ставиться поверх старой установки, если не менять package id и keystore, а `version/code` в Android export preset монотонно увеличивать перед каждым релизом.

## Процесс

Процесс работы описан в [process.md](process.md), роли агентов — в [agents.md](agents.md).
