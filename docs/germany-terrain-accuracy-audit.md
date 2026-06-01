# Germany Terrain Accuracy Audit

Date: 2026-06-01

Scope: GitHub Issue #64, audit/contract only. This document does not approve the current map as `10/10` and does not change map art.

## Contract

The machine-readable audit lives in `map_pipeline/data/germany_terrain_accuracy_audit.json` and is enforced by `audit_germany_terrain_accuracy_contract()`.

It covers:

- Alps: must remain a strong cross-border massif system connected through Germany, Austria, Switzerland and northern Italy; current data is only pre-DEM guarded and cannot be production-approved until elevation-backed.
- Harz: must remain an isolated central massif around the Brocken region, readable but not spread into northern lowlands.
- Black Forest, Bavarian Forest, Erzgebirge, Saxon Switzerland / Elbe Sandstone and Eifel-Hunsrueck: must stay named source layers with ridge/spine metadata, not generic decorative mountains.
- North German Plain exclusions: Hamburg / Lower Elbe, Baltic-Mecklenburg lake plain and North Sea coastal plain reject large mountain glyphs, ridge bands and massif segments.
- Major water: Bodensee, Müritz, Chiemsee, Schweriner See, Plauer See, Schaalsee, Steinhuder Meer, Edersee, Ammersee, Starnberger See, Tegernsee and Berlin lakes/chains must stay explicit named outlines.
- Islands: Rügen must remain an audited Baltic island feature with a label and local island/sea details.
- Source requirements: final relief needs DEM-derived elevation/ridge masks or documented named massif geometry. Copernicus DEM GLO-30 is primary; EU-DEM and NASA SRTM 1 arc-second remain fallbacks.

## Automated Checks

Run:

```bash
python3 -m unittest tests.test_map_geography_audit
```

The tests cover:

- current underlay data passes the Germany terrain contract;
- a fake large mountain near Hamburg fails the North German Plain exclusion;
- removing Rügen or Müritz fails the island/water expectations;
- broader geography audits still cover named relief metadata, Alpine source extents, runtime coastal city placement and default clutter limits.

## Human Review Checklist

Future render passes for #62/#68/#69 must still inspect screenshots. Passing this audit only means the source data has guardrails.

- No large mountains near Hamburg, Lower Elbe, North Sea coast, Baltic coast or Mecklenburg lake lowlands.
- Alps read as the Alps: broad, strong, cross-border and connected to the German Alpine edge.
- Harz is visible as a central mountain region but remains geographically centered.
- Black Forest, Bavarian Forest, Erzgebirge and Saxon Switzerland read as smaller named massifs, not random rows.
- Lakes and islands match reality at atlas scale; Rügen and Müritz must not disappear into decorative noise.
- Relief source notes are present. Do not claim final terrain accuracy from placeholder glyph anchors alone.

## Remaining Work

This audit leaves visual and production terrain work open:

- #62: replace decorative relief with accurate reusable overlay layers.
- #68: improve the German Alpine edge so Bavaria/Zugspitze read as part of the real Alpine system.
- #69: replace placeholder massif art with per-massif source-backed glyph/layer assets.
