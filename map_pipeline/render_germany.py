import os

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.collections import PatchCollection
from shapely.geometry import box

from map_pipeline.projection import MapProjection

GERMANY_BOUNDS = (4.5, 46.5, 15.5, 55.5)
IMAGE_SIZE = (1024, 1024)
OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "map", "germany_base.png")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "natural_earth")

OCEAN_COLOR = "#c8dce8"
LAND_COLOR = "#e8dcc8"
BORDER_COLOR = "#b0a090"
LAKE_COLOR = "#a8c4d8"
BG_COLOR = "#c8dce8"


def load_shapefile(name):
    path = os.path.join(DATA_DIR, name)
    shp_files = [f for f in os.listdir(path) if f.endswith(".shp")]
    if not shp_files:
        raise FileNotFoundError(f"No .shp file in {path}")
    return gpd.read_file(os.path.join(path, shp_files[0]))


def clip_to_bounds(gdf, bounds):
    minx, miny, maxx, maxy = bounds
    clip_box = box(minx - 1, miny - 1, maxx + 1, maxy + 1)
    clipped = gdf[gdf.geometry.intersects(clip_box)].copy()
    clipped["geometry"] = clipped.geometry.intersection(box(minx - 0.5, miny - 0.5, maxx + 0.5, maxy + 0.5))
    clipped = clipped[~clipped.is_empty]
    return clipped


def geometry_to_patches(geom, proj):
    patches = []
    if geom.geom_type == "Polygon":
        coords = list(geom.exterior.coords)
        projected = [proj.project(c[0], c[1]) for c in coords]
        if len(projected) >= 3:
            patches.append(MplPolygon(projected, closed=True))
        for interior in geom.interiors:
            coords = list(interior.coords)
            projected = [proj.project(c[0], c[1]) for c in coords]
            if len(projected) >= 3:
                patches.append(MplPolygon(projected, closed=True))
    elif geom.geom_type == "MultiPolygon":
        for poly in geom.geoms:
            patches.extend(geometry_to_patches(poly, proj))
    return patches


def render():
    proj = MapProjection(GERMANY_BOUNDS, IMAGE_SIZE)

    print("Loading Natural Earth data...")
    land_50 = load_shapefile("ne_50m_land")
    countries = load_shapefile("ne_110m_admin_0_countries")
    lakes_110 = load_shapefile("ne_110m_lakes")

    print("Clipping to Germany bounds...")
    land_50 = clip_to_bounds(land_50, GERMANY_BOUNDS)
    countries = clip_to_bounds(countries, GERMANY_BOUNDS)
    lakes_110 = clip_to_bounds(lakes_110, GERMANY_BOUNDS)

    fig, ax = plt.subplots(1, 1, figsize=(10.24, 10.24), dpi=100)
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    ax.set_xlim(0, IMAGE_SIZE[0])
    ax.set_ylim(IMAGE_SIZE[1], 0)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.patch.set_facecolor(OCEAN_COLOR)
    ax.set_facecolor(OCEAN_COLOR)

    print("Rendering land (50m)...")
    land_patches = []
    for _, row in land_50.iterrows():
        land_patches.extend(geometry_to_patches(row.geometry, proj))
    if land_patches:
        pc = PatchCollection(land_patches, facecolor=LAND_COLOR, edgecolor="none", linewidths=0)
        ax.add_collection(pc)

    print("Rendering country borders...")
    border_lines = []
    for _, row in countries.iterrows():
        geom = row.geometry
        if geom.is_empty:
            continue
        if geom.geom_type == "Polygon":
            coords = list(geom.exterior.coords)
            projected = [proj.project(c[0], c[1]) for c in coords]
            if len(projected) >= 2:
                border_lines.append(projected)
        elif geom.geom_type == "MultiPolygon":
            for poly in geom.geoms:
                coords = list(poly.exterior.coords)
                projected = [proj.project(c[0], c[1]) for c in coords]
                if len(projected) >= 2:
                    border_lines.append(projected)

    for line_coords in border_lines:
        xs, ys = zip(*line_coords)
        ax.plot(xs, ys, color=BORDER_COLOR, linewidth=0.6, alpha=0.7)

    print("Rendering lakes...")
    lake_patches = []
    for _, row in lakes_110.iterrows():
        geom = row.geometry
        if geom.is_empty:
            continue
        lake_patches.extend(geometry_to_patches(geom, proj))
    if lake_patches:
        pc = PatchCollection(lake_patches, facecolor=LAKE_COLOR, edgecolor="none", linewidths=0)
        ax.add_collection(pc)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    print(f"Saving to {OUTPUT_PATH}...")
    fig.savefig(OUTPUT_PATH, dpi=100, bbox_inches="tight", pad_inches=0,
                facecolor=OCEAN_COLOR, edgecolor="none")
    plt.close(fig)

    from PIL import Image
    img = Image.open(OUTPUT_PATH)
    if img.size != IMAGE_SIZE:
        img = img.resize(IMAGE_SIZE, Image.LANCZOS)
        img.save(OUTPUT_PATH)
        print(f"Resized to {IMAGE_SIZE}")

    file_size = os.path.getsize(OUTPUT_PATH)
    print(f"Output: {OUTPUT_PATH}")
    print(f"Size: {img.size[0]}x{img.size[1]}, {file_size:,} bytes")
    return OUTPUT_PATH


if __name__ == "__main__":
    render()
