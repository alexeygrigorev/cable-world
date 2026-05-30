# Real map tiles follow-up

Текущая карта остается offline-first: объекты проецируются по координатам на локальный картографический слой без сетевых запросов. Это закрывает выбор объектов на карте в MVP, но не заменяет настоящие тайлы OpenStreetMap.

## Цель

Добавить реальную карту для Android и desktop без нарушения offline UX:

- основной слой: OSM-compatible raster/vector tiles;
- маркеры объектов из локального каталога;
- сохранение текущих возможностей `MapPanel`: pan, zoom, фильтр посещений, выделение выбранного объекта;
- graceful fallback на текущий realistic offline map style, если сеть или tile cache недоступны.

## Варианты интеграции

1. **Godot WebView/native Android map wrapper**
   - Android: открыть native `MapView`/MapLibre поверх Godot или в отдельном Activity.
   - Плюсы: зрелый MapLibre SDK, gestures и tile cache уже решены.
   - Минусы: сложнее синхронизировать Godot UI, маркеры, lifecycle и back navigation.

2. **Godot plugin для MapLibre Native**
   - Создать GDExtension/Android plugin, который отдает Godot Control-like surface.
   - Плюсы: ближе к текущему `MapPanel`, меньше разрыв между UI и картой.
   - Минусы: самая дорогая реализация, нужно поддерживать сборку Android ABI.

3. **Raster tiles внутри Godot**
   - Загружать XYZ tiles (`z/x/y.png`) через `HTTPRequest`, рисовать TextureRect tiles в `MapPanel`.
   - Плюсы: быстро прототипируется в GDScript, маркеры остаются текущими.
   - Минусы: нужно аккуратно сделать attribution, rate limiting, cache, retina tiles и offline fallback.

## Рекомендуемый первый шаг

Сделать вариант 3 как прототип за feature flag:

- добавить `TileMapLayer` рядом с `OfflineMapLayer`;
- реализовать Web Mercator tile math: lon/lat -> z/x/y -> screen;
- держать visible tile window только вокруг viewport;
- добавить disk cache в `user://tile_cache/{provider}/{z}/{x}/{y}.png`;
- показывать обязательную attribution строку `© OpenStreetMap contributors`;
- оставить `OfflineMapLayer` как fallback при ошибках сети, пустом cache или отключенном флаге;
- покрыть контрактом: сетевые URL не захардкожены в UI, provider настраивается, fallback не ломает выбор marker.

## Android/Godot checks

- Проверить `INTERNET` permission в Android export preset только при включенном tile layer.
- Ограничить параллельные запросы tiles, чтобы не блокировать мобильный UI.
- Учитывать suspend/resume: отменять активные запросы при закрытии карты.
- Не хранить OSM tiles бессрочно без политики cache expiry.

## Открытые решения

- Выбрать provider: публичные OSM tiles подходят только для dev/test; для production нужен свой tile server или провайдер с понятными лимитами.
- Решить, нужна ли полностью offline карта регионов через MBTiles. Для Android это может быть лучше, чем live tiles, если каталог в основном туристический и заранее известен.
- Определить UX переключения: авто-fallback или явный toggle "реальная карта / офлайн-карта".
