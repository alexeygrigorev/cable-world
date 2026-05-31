# Active Map Backlog

Дата: 2026-05-31.

Цель остается `10/10`: карта должна быть fullscreen-first, узнаваемой, читаемой за 1-2 секунды, с реальными координатами, нормальным pan/zoom и стилистически цельным atlas UI.

## Direction Lock

- Production direction is documented in `docs/map-production-direction.md`.
- Stop polishing monolithic generated map bitmaps as if they are the final approach.
- Generated full-map images are reference material only; production rendering must be clean base + reusable glyph layers + explicit real-coordinate placement.

## Open Items

- [ ] Перевести текущую карту в glyph-based production pipeline: чистая база без baked городов + отдельные переиспользуемые glyph layers для гор, лесов, озер, кораблей и atlas details.
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
- [x] Исправить pan sensitivity: drag пальцем и мышью теперь использует viewport-local `event.relative` и `PAN_DRAG_SCALE := 1.0`, чтобы движение было 1:1 в координатах карты, без `screen_relative` acceleration.
- [ ] Разобраться с тем, почему пользователь может видеть старую версию с точками вместо city landmark icons: web rebuild, Godot import, browser cache, service worker/PWA/cache busting.
- [ ] Довести city landmark layer: сделать иконки достаточно крупными, не перекрывать labels/markers, использовать правильные немецкие названия с умляутами.
- [x] Заменить cluster count badges на более нативные atlas group markers: clusters теперь показываются как stack из реальных транспортных sprites без count text/circles/station badge.
- [x] #60 Убрать залитые фоновые плашки под транспортными пиктограммами: оставить естественный outline/glow, чтобы объекты читались лучше городов и выглядели частью карты.
- [x] #61 Масштабировать транспортные и городские иконки вместе с zoom и resize viewport, но с максимальным порогом размера, чтобы пиксель-арт не раздувался.
- [x] Усилить visual hierarchy интерактивных объектов: transport markers теперь крупнее city landmarks на default/mobile и имеют больший cap (`60..96`) против более сдержанных city landmarks (`42..76`).
- [x] Добавить outline-only runtime sprites для транспортных и city landmark иконок: объекты должны читаться поверх детальной карты без кругов, плашек и фоновых подложек.
- [x] Убрать jitter у runtime объектов при pan/zoom: транспортные маркеры, city landmarks и размеры иконок snap-аются к целым пикселям по тому же принципу, что и подписи.
- [x] Увеличить мелкие atlas details: домики/часовни/мельницы/руины/водяные мельницы имеют `MIN_ATLAS_DETAIL_WIDTH = 78`, чтобы не превращаться в шум.
- [x] Добавить первый explicit forest mass layer: `ATLAS_FOREST_MASSES` покрывает Lüneburger Heide, Mecklenburg lake forests, Spreewald/Lausitz, Teutoburg/Weser, Sauerland/Rothaar, Eifel, Spessart/Odenwald, Thuringian Forest, Franconian/Swabian uplands и Upper Bavaria foothills.
- [x] Убрать странные декоративные полоски из текущего рендера: route overlay и слишком прямые procedural waterways больше не вызываются, field hatch/field patch заменены на более спокойные tufts/hill marks.
- [x] Вернуть journey-map структуру без технических полос: добавлен controlled `ATLAS_ROUTE_SEGMENTS` layer с короткими dotted atlas trails, без continuous `draw.line` и без blue procedural waterways.
- [x] Снизить clutter на default zoom: второстепенные подписи городов появляются после zoom `1.20`, а названия под иконками стали ближе к пиктограммам.
- [x] Сделать стартовый zoom адаптивным: portrait остается крупным, landscape/desktop не получает дополнительный `1.10` zoom и меньше режет ориентиры у краев.
- [x] Перевести map labels в atlas-style: vendored `LiberationSerif-BoldItalic.ttf`, runtime city labels и baked terrain labels используют один serif italic стиль; terrain labels больше не дублируются runtime-слоем.
- [x] Вернуть шрифт runtime city labels по user feedback: города снова используют theme/default font; atlas serif оставлен для terrain/map labels.
- [ ] #62 Перевести рельеф из декоративных гор в точные переиспользуемые overlay-слои: Alps, Harz, Black Forest, Erzgebirge, Bavarian Forest и другие реальные массивы. Германия начата; Альпы переведены в составной Alpine massif layer, но нужно расширить и проверить слой по Европе.
- [x] Начать настройку масштаба/якорей terrain glyphs через явные `mountain_glyphs`: Альпы, Harz, Erzgebirge, Black Forest и Bavarian Forest больше не выбираются hash-ом.
- [x] Сделать первый непрерывный cross-border pass для Альп: explicit `main_alpine_wall` и `northern_alpine_foothills` ridge bands плюс перераспределенные `alps_range_*` glyphs вместо короткого обрубленного массива только у юга Германии.
- [x] Добавить automated geography guardrails: `audit_geography_layers()` проверяет relief polygons, northern lowlands без гор, anchors mountain/ridge/massif внутри named regions, water/detail/forest bounds и glyph types.
- [ ] Визуально откалибровать `mountain_glyphs` по реальным relief extents: automated audit теперь ловит грубые ошибки placement, но scale/edge/art still need human screenshot/geography review; Harz/Erzgebirge/Black Forest/Bavarian Forest не должны расползаться за свои области.
- [ ] #64 Провести terrain accuracy audit текущей Германии по скриншотам/карте высот: automated guardrails есть, но нужно визуально проверить, что нет ложных больших гор у Hamburg/севера и что все видимые горы выглядят соразмерно реальности.
- [ ] #63 Спроектировать Europe map pipeline для следующих стран и регионов: France, Spain, Italy, Switzerland, Austria, Germany neighbors, Scandinavia, Finland, Baltics, Russia, Belarus, Ukraine до украинских гор, Turkey; рельефные слои должны продолжаться через границы.
- [ ] #63 Позже разбить большую Europe pipeline issue на маленькие блоки по странам/регионам/слоям, но пока держать общий список в одной issue, чтобы ничего не потерять.
- [ ] Перегенерировать/переразмерить glyph source assets под рабочий максимум `200%`, чтобы atlas details и terrain glyphs были четкими на максимальном приближении без лишней пиксельности.
- [ ] Оформить list mode отдельной задачей: список при переключении с карты должен соответствовать стилю карты, а не выглядеть как чужой UI.
- [ ] Интегрировать themed splash/loading и Android app icon после завершения parallel subagent.
- [ ] #65 Разобрать Godot headless shutdown warnings/RID leaks: сейчас `godot --headless --path . --quit-after 1` выходит с кодом 0, но печатает CanvasItem/ObjectDB/DummyTexture/ShapedText/Font leak warnings.
- [ ] Обновлять GitHub issue #54 после каждой проверяемой итерации и регулярно коммитить.

## Current Known State

- Карта на `http://127.0.0.1:9000/` пересобрана из `main`.
- Последний map commit на момент обновления backlog: pending named water/detail readability pass.
- Текущая карта технически рабочая и архитектурно движется в glyph-based direction. Честная оценка после screenshots: около `6.5/10` по плотности и читаемости, но нельзя оценивать ее как `8/10`: некоторые water blobs и forest+village clusters тяжеловаты, marker composition в городах всё еще плотная, нужна более сильная художественная плотность, visual audit рельефа/озер/координат, finer high-quality mountain glyphs and broader Europe explicit layers.
