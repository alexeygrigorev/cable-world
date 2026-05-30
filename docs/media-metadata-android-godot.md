# EXIF/GPS metadata на Android и Godot

Документ фиксирует research/data contract для issue #19 «Подтягивать координаты фото и видео из metadata». Это не спецификация native plugin и не изменение схемы хранения.

## Вывод

Надежный импорт координат из metadata на Android требует доступа к Android API. В Godot 4 штатный `Image` умеет загружать пиксели JPEG/PNG/WebP/TGA/EXR из файла или буфера, но публичный API Godot не дает готового чтения EXIF/GPS-тегов и не дает общего API для location metadata видео. Поэтому для production-импорта координат из выбранных пользователем фото и видео нужен Android plugin на Java/Kotlin или другой нативный слой.

Сейчас native plugin не нужен. Для текущего MVP стартуем с ручной привязки медиа к станции, направлению, отрезку маршрута или точке объекта. Координаты медиа остаются локальными в пользовательской SQLite-базе и не отправляются наружу. Если координата задана вручную, `MediaAsset.coordinate_source = 'manual'`; если координата когда-нибудь будет надежно прочитана из EXIF/GPS metadata, `coordinate_source = 'exif'`; если координаты нет или источник неизвестен, `coordinate_source = 'unknown'`.

## Что реально доступно

### Android

Android дает нативные API для чтения metadata:

- `androidx.exifinterface.media.ExifInterface` читает EXIF у изображений и умеет работать с GPS latitude/longitude; Android documentation рекомендует AndroidX ExifInterface как более обновляемый superset платформенного класса.
- `android.media.MediaMetadataRetriever` содержит ключ `METADATA_KEY_LOCATION` для location metadata видео, если контейнер и камера ее записали.
- Начиная с Android 10/API 29, EXIF location считается чувствительной metadata. Для unredacted EXIF location у фото нужно объявить `ACCESS_MEDIA_LOCATION` и запросить это runtime permission; даже после запроса доступ не гарантирован, потому что требуется явное согласие пользователя.
- При работе через `MediaStore` может понадобиться `MediaStore.setRequireOriginal(uri)`, чтобы получить оригинальные байты без EXIF redaction. Без нужного доступа Android может вернуть redacted-копию или отказать.
- Для доступа к чужим медиа применяются ограничения scoped storage, Photo Picker, Storage Access Framework и runtime permissions. Набор разрешений зависит от версии Android, target SDK и способа выбора файла.

### Godot

В Godot 4 без нативного расширения доступны только базовые операции с файлами и изображениями:

- `Image.load_from_file()`, `Image.load_jpg_from_buffer()` и похожие методы загружают пиксели изображения во время выполнения.
- `FileAccess` может читать файлы, к которым приложение реально имеет доступ.
- `OS.request_permission()` и `OS.request_permissions()` на Android могут запросить опасные permissions, если они отмечены в export preset.
- Android plugins в Godot позволяют подключить Java/Kotlin API Android и вызвать их из GDScript.

Этого достаточно для показа выбранного файла и копирования его в `user://`, но недостаточно для надежного чтения GPS из EXIF и location metadata видео. Теоретически можно написать узкий JPEG EXIF parser на GDScript, но он не решит Android redaction, `content://` URI, HEIC/WebP/MP4 и разные контейнеры видео. Такой parser не является целевым решением для #19.

## Решение для MVP

Решение на сейчас:

- native plugin не делаем;
- schema storage не меняем;
- пользователь или seed-данные могут вручную привязать медиа к `ObjectStation`, `RouteDirection`, `RouteSegment` или координате объекта;
- ручная координата сохраняется как `coordinate_source = 'manual'` и сопровождается русским `geo_note`;
- файл без координат или с недоступной metadata сохраняется как `coordinate_source = 'unknown'`;
- `coordinate_source = 'exif'` зарезервирован только для будущего импортера, который действительно прочитал GPS/location metadata из исходного файла;
- приватность координат локальная: координаты медиа хранятся в локальной SQLite-базе приложения и не синхронизируются наружу в рамках MVP.

Native plugin стоит делать позже, когда появится отдельная задача на импорт metadata. Минимальный контракт такого плагина: получить выбранный пользователем media URI/path, прочитать координаты фото через AndroidX ExifInterface или координаты видео через MediaMetadataRetriever, явно обработать redacted/permission-denied/no-metadata cases и вернуть в Godot результат без изменения storage schema.

## Связь с `MediaAsset.coordinate_source`

`MediaAsset.coordinate_source` уже покрывает нужные состояния:

- `exif` - координаты прочитаны из EXIF/GPS или location metadata исходного файла автоматическим импортером;
- `manual` - координаты или привязка к станции/точке/отрезку заданы пользователем, seed-данными или будущим UI;
- `unknown` - координаты отсутствуют, metadata не содержит location, metadata недоступна из-за permission/privacy или источник координат не установлен.

Важно: `exif` не должен выставляться просто потому, что файл является фото или видео. Это значение означает успешное чтение координат из metadata.

## Тестовые файлы и кейсы для будущей проверки

Для будущей реализации импортера нужны fixtures, которые можно хранить отдельно от production-данных:

- `photo_with_gps.jpg` - JPEG с валидными GPSLatitude/GPSLongitude и ожидаемыми decimal coordinates;
- `photo_without_gps.jpg` - JPEG с EXIF без GPS или без EXIF, ожидаемый результат `coordinate_source = 'unknown'`;
- `video_with_location.mp4` - MP4/3GPP с location metadata, ожидаемый результат `coordinate_source = 'exif'`;
- `file_without_metadata.bin` или `image_plain.png` - файл без metadata, ожидаемый результат `coordinate_source = 'unknown'`;
- `photo_redacted_by_android.jpg` или Android instrumentation case - выбранное фото, у которого Android вернул redacted EXIF без `ACCESS_MEDIA_LOCATION`, ожидаемый результат `unknown` и русская причина в диагностике;
- `permission_denied_access_media_location` - пользователь отказал в media location permission, импорт не падает и не выставляет `exif`;
- `selected_media_read_grant_only` - файл выбран через Photo Picker/SAF, приложение имеет read grant только на выбранный URI, импорт не требует доступа ко всей медиатеке;
- `local_app_copy_preserves_privacy` - после копирования в `user://` координаты остаются только в локальной базе приложения, а наружная синхронизация отсутствует.

## Источники

- Godot documentation: `Image` и runtime file loading описывают загрузку пикселей из файлов/буферов, но не EXIF/GPS API: https://docs.godotengine.org/en/stable/classes/class_image.html и https://docs.godotengine.org/en/stable/tutorials/io/runtime_file_loading_and_saving.html
- Godot documentation: Android plugins являются штатным способом подключить Java/Kotlin Android API: https://docs.godotengine.org/en/stable/tutorials/platform/android/javaclasswrapper_and_androidruntimeplugin.html
- Android Developers: AndroidX `ExifInterface` для EXIF/GPS изображений: https://developer.android.com/reference/androidx/exifinterface/media/ExifInterface
- Android Developers: `MediaMetadataRetriever.METADATA_KEY_LOCATION` для media location metadata: https://developer.android.com/reference/android/media/MediaMetadataRetriever
- Android Developers: `ACCESS_MEDIA_LOCATION`, scoped storage и media location privacy: https://developer.android.com/training/data-storage/shared/media
