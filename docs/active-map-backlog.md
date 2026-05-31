# Active Map Backlog

Дата: 2026-05-31.

Цель остается `10/10`: карта должна быть fullscreen-first, узнаваемой, читаемой за 1-2 секунды, с реальными координатами, нормальным pan/zoom и стилистически цельным atlas UI.

## Open Items

- [ ] Проверить и откалибровать координаты city landmarks относительно реальной географии: Росток должен быть у моря, Дрезден не должен визуально уезжать в Чехию, города должны совпадать с реальной картой настолько, насколько позволяет художественная подложка.
- [ ] Исправить pan sensitivity: drag пальцем и мышью должен ощущаться примерно 1:1, без ускорения, где 1 см движения пальца сдвигает карту на несколько сантиметров.
- [ ] Разобраться с тем, почему пользователь может видеть старую версию с точками вместо city landmark icons: web rebuild, Godot import, browser cache, service worker/PWA/cache busting.
- [ ] Довести city landmark layer: сделать иконки достаточно крупными, не перекрывать labels/markers, использовать правильные немецкие названия с умляутами.
- [ ] Заменить cluster count badges на более нативные atlas group markers: сейчас они функциональны, но все еще выглядят как UI-счетчики.
- [x] #60 Убрать залитые фоновые плашки под транспортными пиктограммами: оставить естественный outline/glow, чтобы объекты читались лучше городов и выглядели частью карты.
- [x] #61 Масштабировать транспортные и городские иконки вместе с zoom, но с максимальным порогом размера, чтобы пиксель-арт не раздувался.
- [x] Добавить outline-only runtime sprites для транспортных и city landmark иконок: объекты должны читаться поверх детальной карты без кругов, плашек и фоновых подложек.
- [x] Снизить clutter на default zoom: второстепенные подписи городов появляются после zoom `1.20`, а названия под иконками стали ближе к пиктограммам.
- [ ] #62 Перевести рельеф из декоративных гор в точные переиспользуемые overlay-слои: Alps, Harz, Black Forest, Erzgebirge, Bavarian Forest и другие реальные массивы. Германия начата; нужно расширить и проверить слой по Европе.
- [x] Начать настройку масштаба/якорей terrain glyphs через явные `mountain_glyphs`: Альпы, Harz, Erzgebirge, Black Forest и Bavarian Forest больше не выбираются hash-ом.
- [ ] Проверить и откалибровать `mountain_glyphs` по реальным relief extents: Альпы должны начинаться/заканчиваться по настоящему массиву, Harz/Erzgebirge/Black Forest/Bavarian Forest не должны расползаться за свои области.
- [ ] #64 Провести terrain accuracy audit текущей Германии: убрать ложные большие горы у Hamburg/севера и проверить, что все видимые горы соответствуют реальности.
- [ ] #63 Спроектировать Europe map pipeline для следующих стран и регионов: France, Spain, Italy, Switzerland, Austria, Germany neighbors, Scandinavia, Finland, Baltics, Russia, Belarus, Ukraine до украинских гор, Turkey; рельефные слои должны продолжаться через границы.
- [ ] #63 Позже разбить большую Europe pipeline issue на маленькие блоки по странам/регионам/слоям, но пока держать общий список в одной issue, чтобы ничего не потерять.
- [ ] Оформить list mode отдельной задачей: список при переключении с карты должен соответствовать стилю карты, а не выглядеть как чужой UI.
- [ ] Интегрировать themed splash/loading и Android app icon после завершения parallel subagent.
- [ ] #65 Разобрать Godot headless shutdown warnings/RID leaks: сейчас `godot --headless --path . --quit-after 1` выходит с кодом 0, но печатает CanvasItem/ObjectDB/DummyTexture/ShapedText/Font leak warnings.
- [ ] Обновлять GitHub issue #54 после каждой проверяемой итерации и регулярно коммитить.

## Current Known State

- Карта на `http://127.0.0.1:9000/` пересобрана из `main`.
- Последний map commit на момент обновления backlog: pending outline readability commit after current review.
- Текущий рельеф Германии перешел на reusable sprite glyphs для гор, лесов и озер; главные горные массивы уже имеют явные placements. Иконки транспорта и городов теперь грузятся из outlined runtime variants. Blocker для `8/10+` теперь проверка этих placements по реальным relief extent, list/cluster styling и дальнейшая Европа без country-only clipping.
