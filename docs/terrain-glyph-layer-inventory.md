# Terrain Glyph Layer Inventory

Date: 2026-05-31

Scope: issue #69 first integrable slice for named massif glyph/layer production.

## Rule

Production terrain is composed from named reusable layers, not from one generated map bitmap and not from hash-random mountain stamps.

The machine-readable contract is `map_pipeline/data/terrain_massif_layers.json`. It defines source extent ids, placement policy, required ridge bands, allowed placeholder glyphs and replacement status for every exported relief source layer.

## Reference Use

Allowed references:

- `/home/alexey/tmp/file_000000000d5c71f4b60ecae32dd4240b.png`
- `tmp/map-underlay-source/germany_atlas_underlay_2026-05-31_v2.png`

These may be used only to inventory reusable motifs: alpine wall shape, isolated Harz shape, forested Black Forest/Bavarian Forest massing, Erzgebirge border ridge, Saxon Switzerland sandstone rim, lakes, ports, ships, bridges and readable forest clusters.

They must not be shipped as full-map production underlays.

## Current Named Layers

- `alps`: composite cross-border layer, backed by Alpine child segments and `map_pipeline/data/alpine_relief_extents.json`; still pre-DEM and not production-approved.
- `harz`: isolated central massif layer with `harz_brocken_spine` and `harz_south_spur`; first production-candidate custom renderer `harz_production_v1` replaces the generic ridge-band rectangle with one reusable transparent source layer composed from larger forest/mountain glyphs.
- `black_forest`: named forested highland spine; needs custom forested massif glyph.
- `bavarian_forest`: named forested highland spine; needs custom forested massif glyph.
- `erzgebirge`: named border ridge; needs custom Erzgebirge asset.
- `saxon_switzerland`: named Elbe Sandstone rim; needs custom sandstone asset.
- `eifel_hunsrueck`: named low highland layer; needs custom low-highland asset.

## Audit Gate

`audit_terrain_massif_layer_contract()` rejects:

- exported relief layers missing a source extent contract;
- forbidden placement policies such as random/decorative/full-map bitmap placement;
- legacy generic `mountains` lists on named source layers;
- glyph anchors outside the allowed placeholder glyphs for that layer;
- source layer manifest metadata that no longer matches the contract.

This is guardrail work. It does not make the map `10/10` visually by itself.
