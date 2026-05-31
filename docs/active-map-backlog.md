# Active Map Backlog

Дата: 2026-05-31.

Цель остается `10/10`: карта должна быть fullscreen-first, узнаваемой, читаемой за 1-2 секунды, с реальными координатами, нормальным pan/zoom и стилистически цельным atlas UI.

## Direction Lock

- Production direction is documented in `docs/map-production-direction.md`.
- Stop polishing monolithic generated map bitmaps as if they are the final approach.
- Generated full-map images are reference material only; production rendering must be clean base + reusable glyph layers + explicit real-coordinate placement.

## Open Items

- [ ] Перевести текущую карту в glyph-based production pipeline: чистая база без baked городов + отдельные переиспользуемые glyph layers для гор, лесов, озер, кораблей и atlas details.
- [x] #66 Добавить базовую reproducible текстуру земли и воды: land/water больше не являются плоскими заливками; текстура маскируется отдельно по land/water и не должна конкурировать с маркерами и подписями.
- [ ] #66 Follow-up: water texture direction is acceptable, but land texture is still too flat/boring. Re-open the old reference image `/home/alexey/tmp/file_000000000d5c71f4b60ecae32dd4240b.png` and the generated donor map `tmp/map-underlay-source/germany_atlas_underlay_2026-05-31_v2.png`; extract the land pattern direction into reusable procedural/glyph layers instead of returning to a monolithic bitmap.
- [ ] Восстановить исходную задачу donor-map decomposition: найти удачную цельную карту-донора, сравнить ее trees/land/relief/details с текущим `assets/map/germany_styled.png`, нарезать/перерисовать крупные trees/forest/detail glyphs из этого visual language и заменить текущие мелкие деревья, которые всё ещё выглядят не как в reference.
- [x] Первый donor-derived terrain/forest glyph pass: сгенерирован один `terrain_forest_sheet.png`, нарезан в 16 `atlas_forest_*` / `atlas_land_*` glyphs через `map_pipeline.slice_terrain_forest_glyphs`, подключен в `ATLAS_FOREST_MASSES` и новый `ATLAS_LAND_DETAIL_PATCHES`.
- [x] #66/#67 Follow-up после первого donor-derived pass: grass/meadow patches стали заметнее, но часть из них выглядит отдельными желтыми пятнами; compositor теперь уменьшает land detail scale/alpha, feather-ит alpha и tint-ит glyphs в сторону базовой земли.
- [ ] #66 Follow-up: текущие land detail patches уже не выглядят как яркие наклейки, но они стали довольно слабым secondary texture. Для `8/10+` нужен следующий hand-authored/pass: больше мелкого warm terrain pattern без отдельных blob-силуэтов.
- [x] Первый production cut: `map_pipeline.compose_map` больше не рисует baked town/city pictograms в underlay; runtime city landmarks остаются единственным городским слоем.
- [x] Добавить первый atlas detail layer: reproducible glyphs для ships/ports/bridges/castles/tower + explicit `ATLAS_DETAILS` placement по координатам.
- [x] Расширить runtime map bounds южнее Германии: можно панорамировать вниз к München/Alps и видеть соседние страны как контурную основу без ручных overlay-глифов.
- [x] Ограничить zoom диапазоном `50%..200%`, чтобы пользователь мог оценить читаемый максимум, а карта не уходила в прежний `400%` pixel mush.
- [x] Отключить finger pinch/magnify zoom: touch gestures больше не меняют масштаб; масштаб меняется только кнопками `+/-` и mouse wheel.
- [x] Сделать шаг zoom controls предсказуемым: `+/-` и wheel меняют масштаб на `25` процентных пунктов, а не множителем.
- [x] Добавить второй atlas detail pass из монолитной карты-донора: деревни, часовни, руины, мельницы, маяки, водяные мельницы и более плотные маршруты как отдельные glyph placements.
- [x] Исправить аспект и физическое разрешение runtime map texture после расширения bounds: `germany_styled.png` теперь `1932x3072`, близко к Mercator aspect `0.629`, чтобы не растягивать карту и не апскейлить подложку выше источника на `150%`.
- [x] Убрать artificial half-size/nearest upscale finish из renderer: карта больше не создаёт крупные пиксельные блоки до runtime zoom; финал остается `1932x3072` через `LANCZOS` + full-resolution palette pass.
- [x] Оптимизировать payload после full-resolution finish: source-only glyph/city/transport assets исключены из export, `index.pck.gz` снизился примерно с `8.4 MB` до `5.4 MB` без возврата к `NEAREST`-пикселизации.
- [ ] Перестать считать текущую procedural/GIS underlay улучшаемой до 8/10 мелкими правками: пользовательская оценка 2026-05-31 — около 4/10. Следующий крупный шаг должен заменить или радикально переработать сам визуальный слой карты.
- [x] Заменить текущую procedural/GIS underlay на цельную generated RPG-atlas подложку для проверки направления. Текущая самооценка после screenshot review: 6/10, не 8/10.
- [ ] Провести geography audit новой generated подложки: декоративные AI-города/реки/озера не должны конфликтовать с реальными city/object координатами.
- [x] Переделать generated/underlay слой так, чтобы в нем не было случайных baked городов/городских пиктограмм, которые потом дублируются runtime city landmark layer сверху.
- [x] Исправить clipping подписей на краях viewport после новой подложки: Hamburg/Rostock/Berlin/Dresden/Köln не должны резаться или прятаться под zoom controls.
- [x] Масштабировать runtime icons при resize карты/viewport: транспортные маркеры и city landmarks должны меняться вместе с визуальным масштабом карты, с верхним пределом для пиксель-арта.
- [x] Отдать интерактивным объектам приоритет над второстепенными подписями: terrain/town labels не должны налезать на кластеры и транспортные иконки.
- [x] Исправить city landmarks, которые визуально "бегут" за viewport при pan: city icons/labels должны оставаться привязанными к географической точке, без clamp к экрану.
- [x] Добавить видимый zoom percent на карту, чтобы пользователь мог назвать порог максимального приближения.
- [x] Поднять city labels/icons в отдельный overlay над transport markers, чтобы названия городов не пропадали под канатками/кластерами.
- [x] Сжать `assets/branding/splash_loading.png`: Godot boot splash поддерживает только PNG, поэтому asset оставлен PNG, но уменьшен с 3.3 MB до ~125 KB.
- [x] Первый payload cut для map asset: `assets/map/germany_styled.png` уменьшен примерно с 5.1 MB до 272 KB, `index.pck` gzip примерно с 9.1 MB до 7.1 MB после удаления монолитной heavy подложки.
- [x] Задокументировать verification protocol: команды, скриншоты, gzip/payload checks, screenshot checklist и критерии `3/10`, `6/10`, `8/10`, `10/10`.
- [x] Заменить generic lake glyph placement для ключевых озёр на named coordinate outlines: Bodensee, Müritz, Chiemsee, Schweriner See, Plauer See, Schaalsee, Steinhuder Meer, Edersee, Ammersee, Starnberger See, Tegernsee, Berlin lakes.
- [x] Настроить visual hierarchy для named lakes: точные озёра приглушены, получили shoreline underpaint и softer highlights, поэтому меньше похожи на overlay markers и лучше сидят в atlas map.
- [ ] Доработать форму named lakes: текущий слой полезен для ориентира, но часть озёр на mobile всё ещё выглядит как маленькие round blobs; нужно сделать силуэты более узнаваемыми и менее похожими на маркеры.
- [ ] Проверить и откалибровать координаты city landmarks относительно реальной географии: Росток должен быть у моря, Дрезден не должен визуально уезжать в Чехию, города должны совпадать с реальной картой настолько, насколько позволяет художественная подложка.
- [x] #70 Первый pass: исправить placement Rostock city landmark. Иконка получила data-driven `icon_offset`, поэтому больше не висит в открытом море и визуально сидит ближе к суше/портовой зоне; подпись остаётся рядом.
- [x] #70 Второй pass: усилить Rostock `icon_offset` до `Vector2(0.0, 52.0)`, потому что меньший offset всё ещё воспринимался как "висит на море" на runtime screenshot.
- [x] #70 Третий pass: стартовый camera focus для Germany сдвинут на `Vector2(10.70, 52.00)`, чтобы Rostock/Hamburg не резались на desktop initial screenshot без viewport-clamp, который заставляет города визуально "бежать" за экраном.
- [x] Исправить pan sensitivity: drag пальцем и мышью теперь использует viewport-local `event.relative` и `PAN_DRAG_SCALE := 1.0`, чтобы движение было 1:1 в координатах карты, без `screen_relative` acceleration.
- [x] Touch-pan regression follow-up: после повторного feedback "1 см пальцем -> 3 см карты" touch drag отделен от mouse drag, использует сохраненную предыдущую позицию касания и `TOUCH_PAN_DRAG_SCALE := 0.34`. Нужно проверить руками на телефоне; если всё ещё быстро, менять один этот коэффициент.
- [ ] Разобраться с тем, почему пользователь может видеть старую версию с точками вместо city landmark icons: web rebuild, Godot import, browser cache, service worker/PWA/cache busting.
- [ ] Довести city landmark layer: сделать иконки достаточно крупными, не перекрывать labels/markers, использовать правильные немецкие названия с умляутами.
- [x] Заменить cluster count badges на более нативные atlas group markers: clusters теперь показываются как stack из реальных транспортных sprites без count text/circles/station badge.
- [x] #60 Убрать залитые фоновые плашки под транспортными пиктограммами: оставить естественный outline/glow, чтобы объекты читались лучше городов и выглядели частью карты.
- [x] #61 Масштабировать транспортные и городские иконки вместе с zoom и resize viewport, но с максимальным порогом размера, чтобы пиксель-арт не раздувался.
- [x] Усилить visual hierarchy интерактивных объектов: transport markers теперь крупнее city landmarks на default/mobile и имеют больший cap (`60..96`) против более сдержанных city landmarks (`42..76`).
- [x] Добавить outline-only runtime sprites для транспортных и city landmark иконок: объекты должны читаться поверх детальной карты без кругов, плашек и фоновых подложек.
- [ ] REGRESSION: убрать jitter у runtime объектов при pan/zoom. Пользователь повторно видит дрожание объектов на `:9000`; предыдущая галочка была преждевременной. Первый fix: не пересоздавать marker/cluster style и cluster stack sprites на каждом pan frame, только при изменении style key.
- [ ] REGRESSION: домики/малые atlas details всё ещё заметны пользователю как проблема. Предыдущий pass убрал `village/chapel/ruins/watermill/windmill` из default render, но нужно проверить фактический screenshot и убрать/заменить оставшиеся glyphs, которые читаются как домики.
- [x] #67 Первый pass: убрать именно мелкие домики и мелкие деревья из default render. Поселковые detail kinds (`village`, `chapel`, `ruins`, `watermill`, `windmill`) больше не рендерятся по умолчанию, россыпь мелких одиночных tree clusters убрана; оставшиеся дома/леса должны быть крупными landmark-глифами.
- [x] #68 Первый pass: добавить отдельный `german_alpine_edge_massif`, чтобы Альпы были видны внутри южной Германии, а не только южнее границы.
- [x] #69 Первый architecture pass: Alpine massif segments теперь сохраняются как отдельные source PNG layers в `assets/map/massifs/` и исключены из Godot export; итоговая карта собирается из того же per-massif render path.
- [x] Добавить non-render audit до screenshots: `audit_geography_layers()` проверяет, что немецкий Alpine-edge massif пересекает Germany geometry, а runtime landmark audit проверяет top/center/bottom samples Ростока по реальному полигону Германии.
- [x] #69 Добавить metadata для massif source layers: общий `assets/map/massifs/manifest.json` и per-layer JSON sidecars фиксируют image file, crop bbox, geo bounds, arc/shadow/glyph anchors и overlap requirements; `audit_massif_source_manifest()` сверяет manifest с PNG без визуального рендера.
- [x] #69 Расширить source-layer pipeline за пределы Альп: `black_forest`, `bavarian_forest`, `harz`, `erzgebirge`, `saxon_switzerland`, `eifel_hunsrueck` и полный `alps` region теперь тоже сохраняются как отдельные проверяемые relief source layers; `northern_lowlands` намеренно не экспортируется как mountain layer.
- [x] #69 Убрать дублирующий generic mountain-glyph ряд из полного `alps` relief layer: Альпы теперь рисуются через ridge bands + named massif source layers, без второй повторной полосы случайных `alps_range_*` поверх того же места.
- [ ] #69 Follow-up: заменить текущий Alpine art на более узнаваемые отдельные massif glyphs/segments. Текущая правка убирает дубль, но еще не делает Альпы качеством `8/10`.
- [ ] REGRESSION / #69/#64: Альпы сейчас географически неправильные и слишком условные. Следующий relief pass должен строиться от реальных elevation/relief maps/data, а не от декоративных anchors: Альпы должны быть сильнее и шире через Austria/Switzerland/northern Italy, а немецкая кромка должна быть частью настоящего массива, не отдельной наклейкой.
- [x] #69 Первый characteristic relief pass для малых массивов: Black Forest, Bavarian Forest, Harz, Erzgebirge, Saxon Switzerland и Eifel/Hunsrück получили отдельные короткие ridge-spines с layer metadata вместо одиночной наклейки-глифа.
- [x] Снизить видимость технических Alpine shadow bands: широкие полупрозрачные полосы вокруг Alpine ridge/massif layers стали слабее, чтобы не читаться как артефакты.
- [ ] #67 Follow-up: проверить mobile руками и убрать/укрупнить оставшиеся дома/лесные glyphs, если пользователь всё ещё воспринимает их как мелкий шум.
- [x] Добавить первый explicit forest mass layer: `ATLAS_FOREST_MASSES` покрывает Lüneburger Heide, Mecklenburg lake forests, Spreewald/Lausitz, Teutoburg/Weser, Sauerland/Rothaar, Eifel, Spessart/Odenwald, Thuringian Forest, Franconian/Swabian uplands и Upper Bavaria foothills.
- [x] Убрать странные декоративные полоски из текущего рендера: route overlay и слишком прямые procedural waterways больше не вызываются, field hatch/field patch заменены на более спокойные tufts/hill marks.
- [x] Вернуть journey-map структуру без технических полос: добавлен controlled `ATLAS_ROUTE_SEGMENTS` layer с короткими dotted atlas trails, без continuous `draw.line` и без blue procedural waterways.
- [x] Снизить clutter на default zoom: второстепенные подписи городов появляются после zoom `1.20`, а названия под иконками стали ближе к пиктограммам.
- [x] City-label proximity follow-up: подписи городов подтянуты ближе к pictogram baseline через `CITY_ICON_LABEL_BASELINE_OVERLAP := 9.0`; следующий review должен проверить, что текст визуально прикреплен к пиктограмме и не уехал вниз.
- [x] Сделать стартовый zoom адаптивным: portrait остается крупным, landscape/desktop не получает дополнительный `1.10` zoom и меньше режет ориентиры у краев.
- [x] Перевести map labels в atlas-style: vendored `LiberationSerif-BoldItalic.ttf`, runtime city labels и baked terrain labels используют один serif italic стиль; terrain labels больше не дублируются runtime-слоем.
- [x] Вернуть шрифт runtime city labels по user feedback: города снова используют theme/default font; atlas serif оставлен для terrain/map labels.
- [ ] #62 Перевести рельеф из декоративных гор в точные переиспользуемые overlay-слои: Alps, Harz, Black Forest, Erzgebirge, Bavarian Forest и другие реальные массивы. Германия начата; Альпы переведены в составной Alpine massif layer, но нужно расширить и проверить слой по Европе.
- [ ] #69 Сделать отдельные glyph/sprite layers для каждого горного массива: Alps, Harz, Black Forest, Erzgebirge, Saxon Switzerland / Elbe Sandstone, Bavarian Forest; не использовать generic random mountains как финальный подход.
- [ ] #68 Исправить немецкую часть Альп: сейчас Альпы визуально слишком “не в Германии”; южная кромка Германии/Bavaria/Zugspitze должна явно читаться как Alpine edge, при этом массив должен продолжаться в Austria/Switzerland/Italy.
- [x] Начать настройку масштаба/якорей terrain glyphs через явные `mountain_glyphs`: Альпы, Harz, Erzgebirge, Black Forest и Bavarian Forest больше не выбираются hash-ом.
- [x] Сделать первый непрерывный cross-border pass для Альп: explicit `main_alpine_wall` и `northern_alpine_foothills` ridge bands плюс перераспределенные `alps_range_*` glyphs вместо короткого обрубленного массива только у юга Германии.
- [x] Добавить automated geography guardrails: `audit_geography_layers()` проверяет relief polygons, northern lowlands без гор, anchors mountain/ridge/massif внутри named regions, water/detail/forest bounds и glyph types.
- [ ] Визуально откалибровать `mountain_glyphs` по реальным relief extents: automated audit теперь ловит грубые ошибки placement, но scale/edge/art still need human screenshot/geography review; Harz/Erzgebirge/Black Forest/Bavarian Forest не должны расползаться за свои области.
- [ ] REGRESSION / Harz readability: Harz сейчас слишком маленький и незаметный среди налепленных деталей. Для readability его можно сделать визуально крупнее/сильнее, чем буквальный масштаб, но центр должен оставаться географически правильным, чтобы было быстро понятно: "здесь Harz, здесь есть канатные дороги".
- [ ] Унифицировать размер подписей городов: кроме Berlin как столицы, остальные city labels должны быть примерно одного визуального ранга. Если подпись слишком длинная или перегружает карту, лучше скрыть/убрать второстепенный label, чем делать случайно мелкий текст.
- [ ] Проверить видимость Müritz/Jüritz и других озёр: если озеро/подпись почти не видны или превращаются в шум, укрупнить форму/подпись или убрать второстепенную подпись до следующего zoom threshold.
- [ ] #64 Провести terrain accuracy audit текущей Германии по скриншотам/карте высот: automated guardrails есть, но нужно визуально проверить, что нет ложных больших гор у Hamburg/севера и что все видимые горы выглядят соразмерно реальности.
- [ ] #63 Спроектировать Europe map pipeline для следующих стран и регионов: France, Spain, Italy, Switzerland, Austria, Germany neighbors, Scandinavia, Finland, Baltics, Russia, Belarus, Ukraine до украинских гор, Turkey; рельефные слои должны продолжаться через границы.
- [ ] #63 Позже разбить большую Europe pipeline issue на маленькие блоки по странам/регионам/слоям, но пока держать общий список в одной issue, чтобы ничего не потерять.
- [ ] Перегенерировать/переразмерить glyph source assets под рабочий максимум `200%`, чтобы atlas details и terrain glyphs были четкими на максимальном приближении без лишней пиксельности.
- [ ] Оформить list mode отдельной задачей: список при переключении с карты должен соответствовать стилю карты, а не выглядеть как чужой UI.
- [ ] Интегрировать themed splash/loading и Android app icon после завершения parallel subagent.
- [ ] #65 Разобрать Godot headless shutdown warnings/RID leaks: сейчас `godot --headless --path . --quit-after 1` выходит с кодом 0, но печатает CanvasItem/ObjectDB/DummyTexture/ShapedText/Font leak warnings.
- [ ] Обновлять GitHub issue #54 после каждой проверяемой итерации и регулярно коммитить.

## Current Known State

- Карта на `http://127.0.0.1:9000/` пересобрана из `main`; Web build отдает gzip и `Cache-Control: no-store`.
- Последний map commit на момент обновления backlog: pending characteristic relief + initial focus pass.
- Non-render checks now cover координаты, geography bounds, source-layer metadata, PNG dimensions/non-blank state, export payload contract and runtime draw contracts. Screenshots/manual review still required for contrast, clutter, visual hierarchy and "does this feel like a real atlas map".
- Текущая карта технически рабочая и архитектурно движется в glyph-based direction. Честная оценка после screenshots: около `6.9/10`, но нельзя оценивать ее как `8/10`: Alpine art still too generic, relief/lake recognizability and marker composition still need work.
