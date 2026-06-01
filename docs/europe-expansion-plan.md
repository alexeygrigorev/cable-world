# Europe Expansion Plan

Дата: 2026-05-31.

Статус: planning/data contract для #75, дочерняя работа к #63.

## Europe-Wide #63 Contract

Общий region/layer contract для #63 теперь зафиксирован в `map_pipeline/data/europe_expansion_regions.json`. Он не является render manifest и не меняет визуальную карту; это проверяемый список регионов, стран, detail tiers, source strategy и cross-border relief правил для следующих implementers.

Контракт покрывает обязательный scope #63:

- high-detail блоки: France, Spain, Italy, Switzerland, Austria;
- Germany neighbors: Denmark, Netherlands, Belgium, Luxembourg, France, Switzerland, Austria, Czechia, Poland;
- Nordics + отдельная Finland;
- Baltics: Estonia, Latvia, Lithuania;
- Russia, Belarus и Ukraine до Ukrainian Carpathians / Crimean Mountains;
- Turkey как medium-detail bridge region;
- lower-detail remaining countries как admin/coastline/water/broad-relief context.

Cross-border relief rule является обязательным data contract: Alps cannot stop at Germany; Po Valley, Vienna Basin и Swiss Plateau должны быть lowland exclusions; mountain placement должен идти от DEM-derived ridges, elevation bands или documented named massif geometry, а не от decorative anchors. Child issues #74/#76/#77 остаются открытыми и не закрываются этим контрактом.

## France And Spain #76 Contract

Дочерний non-render contract для France/Spain зафиксирован в `map_pipeline/data/france_spain_map_block.json`.

Этот файл не является render manifest. Он нужен, чтобы будущий pass по Франции и Испании не рисовал рельеф и города наугад:

- France mainland и Spain mainland/Balearic context получают явные bounds и high-detail статус;
- relief layers разделены на Western Alps, French/Spanish Pyrenees, Massif Central, Vosges/Jura, Cantabrian Mountains, Sistema Central, Iberian System, Sierra Nevada, Corsica and Balearic context;
- Pyrenees и Alps имеют cross-border continuity refs, а Ebro Basin, Aquitaine Basin, Rhone Valley, Rhine Plain and coastal plains зафиксированы как lowland exclusions;
- city landmark coverage включает Paris, Lyon, Marseille, Toulouse, Bordeaux, Grenoble, Chamonix, Madrid, Barcelona, Valencia, Seville, Bilbao, Zaragoza and Granada;
- transport candidate buckets остаются `staging_review_only`, без production import.

Acceptance для #76: `tests/test_france_spain_map_block_contract.py` должен проходить вместе с общим `tests/test_europe_expansion_regions_contract.py`; render assets, terrain glyph art, runtime UI and release files не меняются.

## Nordics, Baltics And Northern Seas #77 Contract

Дочерний non-render contract для Nordics/Baltics зафиксирован в `map_pipeline/data/nordics_baltics_map_block.json`.

Главное правило #77: северная широта сама по себе не означает ни "горы", ни "равнина". Контракт поэтому разделяет:

- Norway/Sweden mountain spine and fjord coast как DEM-backed relief;
- Denmark как explicit lowland exclusion plus North Sea/Baltic island context;
- Finland как low-relief lakeland context with Saimaa, Paijanne, Inari and Aland Islands, без копирования Scandinavian mountain glyphs;
- Baltics как lowland/coast/island context with Saaremaa, Hiiumaa, Curonian Spit, Gulf of Riga and Gulf of Finland;
- Iceland как broad volcanic highland context, отдельно от Scandinavia.

Acceptance для #77: `tests/test_nordics_baltics_map_block_contract.py` должен проходить вместе с общим `tests/test_europe_expansion_regions_contract.py`; render assets, terrain glyph art, runtime UI and release files не меняются.

## Eastern Europe, Balkans And Turkey #74 Contract

Дочерний non-render contract для Eastern Europe/Balkans/Turkey зафиксирован в `map_pipeline/data/eastern_europe_turkey_map_block.json`.

Контракт покрывает Poland/Czechia/Slovakia/Hungary, Romania/Balkans, Belarus/Ukraine до Ukrainian mountain cutoff, western Russia lower-detail context и Turkey bridge region. Основные guardrails:

- Carpathians разделены на Western, Eastern, Southern and Ukrainian cutoff layers; Sudetes, Dinaric Alps, Balkan Mountains/Stara Planina, Rhodope/Pindus context, Crimean Mountains, Pontic/Taurus Mountains, Anatolian Plateau and Caucasus/Armenian Highlands context требуют DEM-backed geometry;
- North European Plain, Pannonian Basin, Danube lowlands, Ukrainian steppe, Belarus lowlands, Russian Plain and Anatolian central basins зафиксированы как lowland exclusions, чтобы будущий render pass не ставил mountain glyphs на равнины;
- water context включает Baltic coast, Black Sea, Sea of Azov, Danube Delta, Dnieper/Dniester, Bosporus/Marmara, Turkey Aegean/Mediterranean coasts, Lake Van and Lake Tuz;
- city landmark coverage включает Warsaw, Krakow, Prague, Brno, Bratislava, Budapest, Bucharest, Cluj-Napoca, Sofia, Belgrade, Zagreb, Sarajevo, Ljubljana, Skopje, Tirana, Kyiv, Lviv, Odesa, Minsk, Moscow/St Petersburg as lower-detail context, Istanbul, Ankara, Izmir, Antalya, Bursa and Trabzon;
- transport candidate buckets остаются `staging_review_only`, без production import.

Acceptance для #74: `tests/test_eastern_europe_turkey_map_block_contract.py` должен проходить вместе с общим `tests/test_europe_expansion_regions_contract.py`; render assets, terrain glyph art, runtime UI and release files не меняются.

## Цель блока #75

DACH + Northern Italy expansion должен подготовить основу для расширения карты Европы на юг от Германии без визуального render pass. Эта задача не должна "дорисовывать красивые Альпы" случайными anchors. Результат должен быть проверяемым контрактом данных, по которому следующий implementer сможет добавить новые bounds, relief layers, city landmarks и transport-object candidates.

## Sub-blocks

### Switzerland

- Страна: Switzerland.
- Обязательные city landmarks: Zürich, Bern, Geneva.
- Дополнительные cableway/funicular cities для candidate coverage: Lucerne, Interlaken, Zermatt, St. Moritz, Davos, Lugano, Lausanne, Neuchatel.
- Relief scope: Swiss Plateau, Jura, Swiss Alps, named Alpine sectors вокруг Valais/Bernese Oberland/Graubünden/Ticino.
- Acceptance data: city coordinates, landmark icon mapping or missing-icon placeholder, canton/region label, relation to Alpine relief polygon.

### Austria

- Страна: Austria.
- Обязательные city landmarks: Vienna, Innsbruck, Salzburg.
- Дополнительные cableway/funicular cities для candidate coverage: Graz, Linz, Bregenz, Zell am See, Kitzbühel, St. Anton am Arlberg, Kaprun, Bad Gastein.
- Relief scope: Northern Limestone Alps, Central Eastern Alps, Tyrol/Salzburg/Styria continuations, Danube lowland around Vienna.
- Acceptance data: city coordinates, Alpine/non-Alpine classification, object candidate source links for urban funiculars and mountain lifts.

### Northern Italy

- Страна: Italy, северный блок.
- Обязательные city landmarks: Milan, Turin, Venice, Verona, Bolzano.
- Дополнительные cableway/funicular cities для candidate coverage: Como, Bergamo, Brescia, Trento, Merano, Aosta, Cortina d'Ampezzo, Sondrio, Bormio.
- Relief scope: Western Alps, Aosta/Piedmont Alps, Lombardy Alps, Dolomites, South Tyrol, Venetian Prealps, Po Valley as explicit lowland.
- Acceptance data: city coordinates, Alpine vs Po Valley placement, northern-Italy map bounds that leave room for the Adriatic/Venice and Alpine ridges.

### Alpine Relief Source And Elevation Validation

- Use real elevation sources before drawing any new Alpine relief:
  - Copernicus DEM GLO-30 or EU-DEM for high-detail European elevation where licensing and attribution are acceptable.
  - NASA SRTM 1 arc-second as fallback where GLO-30/EU-DEM is unavailable.
  - Natural Earth terrain/hypsometric layers only as low-detail fallback for broad relief silhouettes, not final Alpine validation.
  - OpenStreetMap/Natural Earth admin and water/coastline data for borders, lakes, rivers and city context, not for elevation.
- Derive data products before art:
  - raster elevation clip for the expanded map bounds;
  - normalized hillshade/relief intensity mask;
  - elevation-band polygons, for example `500m`, `1000m`, `1500m`, `2000m+`;
  - named massif/sector polygons sampled from the elevation mask and checked against real geography;
  - lowland exclusion polygons for Swiss Plateau, Po Valley and Vienna Basin.
- Validation rules:
  - Alpine ridge anchors must be derived from elevation ridges or documented named massif centroids, not random decorative positions.
  - Relief intensity must increase through Switzerland, Austria and northern Italy, not stop at the German edge.
  - Po Valley and Vienna Basin must not receive mountain glyphs.
  - German Alpine edge must be a continuation of the same Alps layer, not a separate sticker.
  - Every source dataset must record source name, URL, license/attribution note, download date and processing command.

### City Landmark Coverage

Required first-pass landmarks:

- Switzerland: Zürich, Bern, Geneva.
- Austria: Vienna, Innsbruck, Salzburg.
- Northern Italy: Milan, Turin, Venice, Verona, Bolzano.

Coverage contract:

- Each city entry needs stable id, display name, country, lon/lat, priority, landmark sprite id or explicit `missing_landmark_icon`, and reviewer note.
- Zürich, Vienna, Milan, Venice and Geneva should be priority `major`.
- Bern, Innsbruck, Salzburg, Turin, Verona and Bolzano should be at least priority `regional` because they anchor Alpine/cableway navigation.
- City labels must be runtime overlays, not baked into the composed underlay.
- City coordinates must be reviewed against real geography after map bounds/projection change.

### Cableway And Funicular Object Candidate Data

Candidate data is not production import yet. It should be a staging/review contract for later catalog expansion.

Candidate groups:

- Urban funicular/cable systems: Zürich Polybahn, Geneva/Lausanne funicular-adjacent candidates if applicable, Vienna/Hietzing or Kahlenberg-related historic candidates only if source-backed, Innsbruck Hungerburgbahn, Salzburg Festungsbahn, Bergamo funiculars, Como-Brunate funicular, Turin Sassi-Superga rack railway.
- Alpine resort/city anchors: Zermatt, St. Moritz, Davos, Interlaken, Lucerne/Pilatus/Rigi, Innsbruck/Nordkette, Kitzbühel, Zell am See/Kaprun, St. Anton, Bolzano/Renon and San Genesio cableways, Merano cableways, Aosta/Pila, Cortina d'Ampezzo, Bormio.
- Transport types to preserve: `cable_gondola`, `cable_aerial_tram`, `cable_urban`, `cable_tourist`, `funicular_classic`, `rail_cog`, `special_transport_system`.

Each candidate needs source URLs, operating status, coordinates, city/region/country, transport type, confidence and reviewer note. OSM/Wikidata can seed the list, but production data must stay reviewed before it appears in the app.

## Data Contract For Next Implementation

Recommended non-render files for a later implementation:

- `map_pipeline/data/europe_expansion_regions.json`
- `map_pipeline/data/elevation_sources.json`
- `map_pipeline/data/city_landmark_coverage.json`
- `examples/staging/dach_northern_italy_candidates.json`

Minimum schema expectations:

- Region records: `id`, `label`, `countries`, `bounds`, `kind`, `source`, `review_status`.
- Relief records: `id`, `region_id`, `source_dataset`, `source_url`, `license_note`, `elevation_band_m`, `geometry_source`, `review_status`.
- City records: `id`, `display_name`, `country`, `lon`, `lat`, `priority`, `landmark_icon_id`, `review_status`.
- Candidate records: same import staging shape as the OSM/Wikidata candidate pipeline, with `review.state` not equal to production approval until sources are checked.

## Acceptance Checks

- The plan is linked from `docs/active-map-backlog.md` and consistent with `docs/map-production-direction.md`.
- Automated contract test confirms the document still names the required sub-blocks, cities, source strategy and reviewer evidence.
- No render assets are changed in this planning pass.
- If data JSON files are added later, tests must validate schema, bounds, source metadata and required city coverage.
- Full unittest discovery must pass, or any environment-only failure must be recorded with command output.

## Reviewer Evidence

Reviewer must receive:

- Command output for the relevant docs/contract tests.
- A diff showing only docs/tests or non-render metadata/data files.
- A checklist mapping every required city to a planned city landmark entry.
- Source notes for the selected elevation dataset before relief art is implemented.
- For the later render pass only: screenshots showing the Alps continuous through Switzerland, Austria and northern Italy, with Po Valley/Vienna Basin lowland exclusions visible.
