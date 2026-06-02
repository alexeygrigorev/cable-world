import argparse
import math
from collections import deque
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass(frozen=True)
class SheetEdgeIssue:
    name: str
    index: int
    edges: tuple[str, ...]
    cell_bounds: tuple[int, int, int, int]
    alpha_bbox: tuple[int, int, int, int]


@dataclass(frozen=True)
class SheetCutIssue:
    name: str
    index: int
    grid_lines: tuple[str, ...]
    component_bbox: tuple[int, int, int, int]


def cell_bounds(width: int, height: int, index: int, columns: int, rows: int) -> tuple[int, int, int, int]:
    col = index % columns
    row = index // columns
    return (
        round(width * col / columns),
        round(height * row / rows),
        round(width * (col + 1) / columns),
        round(height * (row + 1) / rows),
    )


def audit_nominal_cell_edges(
    image: Image.Image,
    names: list[str],
    columns: int,
    rows: int | None = None,
    edge_tolerance: int = 2,
) -> list[SheetEdgeIssue]:
    rows = rows or max(1, math.ceil(len(names) / columns))
    alpha = image.convert("RGBA").getchannel("A")
    issues: list[SheetEdgeIssue] = []

    for index, name in enumerate(names):
        bounds = cell_bounds(alpha.width, alpha.height, index, columns, rows)
        cell_alpha = alpha.crop(bounds)
        bbox = cell_alpha.getbbox()
        if bbox is None:
            continue

        left, top, right, bottom = bbox
        edges: list[str] = []
        if left <= edge_tolerance:
            edges.append("left")
        if top <= edge_tolerance:
            edges.append("top")
        if cell_alpha.width - right <= edge_tolerance:
            edges.append("right")
        if cell_alpha.height - bottom <= edge_tolerance:
            edges.append("bottom")
        if edges:
            issues.append(SheetEdgeIssue(name, index, tuple(edges), bounds, bbox))

    return issues


def _alpha_components(
    image: Image.Image,
    min_pixels: int = 1200,
) -> list[tuple[int, tuple[int, int, int, int], set[int] | None]]:
    alpha = image.convert("RGBA").getchannel("A")
    width, height = alpha.size
    alpha_data = alpha.load()
    visited = bytearray(width * height)
    components: list[tuple[int, tuple[int, int, int, int], set[int] | None]] = []

    for start_y in range(height):
        for start_x in range(width):
            start_index = start_y * width + start_x
            if visited[start_index] or alpha_data[start_x, start_y] == 0:
                continue

            count = 0
            min_x = max_x = start_x
            min_y = max_y = start_y
            pixels: set[int] = set()
            queue: deque[tuple[int, int]] = deque([(start_x, start_y)])
            visited[start_index] = 1
            while queue:
                x, y = queue.popleft()
                count += 1
                pixels.add(y * width + x)
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)
                for next_x, next_y in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if next_x < 0 or next_y < 0 or next_x >= width or next_y >= height:
                        continue
                    next_index = next_y * width + next_x
                    if visited[next_index] or alpha_data[next_x, next_y] == 0:
                        continue
                    visited[next_index] = 1
                    queue.append((next_x, next_y))

            if count >= min_pixels:
                components.append((count, (min_x, min_y, max_x + 1, max_y + 1), pixels))

    return components


def _slot_index_for_bbox(
    bbox: tuple[int, int, int, int],
    width: int,
    height: int,
    count: int,
    columns: int,
    rows: int,
) -> int:
    cx = (bbox[0] + bbox[2]) / 2
    cy = (bbox[1] + bbox[3]) / 2
    best_index = 0
    best_distance = float("inf")
    for index in range(count):
        left, top, right, bottom = cell_bounds(width, height, index, columns, rows)
        slot_cx = (left + right) / 2
        slot_cy = (top + bottom) / 2
        distance = (slot_cx - cx) ** 2 + (slot_cy - cy) ** 2
        if distance < best_distance:
            best_index = index
            best_distance = distance
    return best_index


def audit_grid_cut_components(
    image: Image.Image,
    names: list[str],
    columns: int,
    rows: int | None = None,
    min_pixels: int = 1200,
    strip_radius: int = 1,
    neighbor_radius: int = 4,
) -> list[SheetCutIssue]:
    rows = rows or max(1, math.ceil(len(names) / columns))
    rgba = image.convert("RGBA")
    vertical_lines = [round(rgba.width * col / columns) for col in range(1, columns)]
    horizontal_lines = [round(rgba.height * row / rows) for row in range(1, rows)]
    issues: list[SheetCutIssue] = []

    for _count, bbox, pixels in _alpha_components(rgba, min_pixels):
        if pixels is None:
            continue
        crossed: list[str] = []
        for line in vertical_lines:
            strip_left = max(0, line - strip_radius)
            strip_right = min(rgba.width, line + strip_radius + 1)
            has_strip_alpha = any(
                y * rgba.width + x in pixels
                for y in range(bbox[1], bbox[3])
                for x in range(strip_left, strip_right)
            )
            left_probe = range(max(0, strip_left - neighbor_radius), strip_left)
            right_probe = range(strip_right, min(rgba.width, strip_right + neighbor_radius))
            has_left_alpha = any(
                y * rgba.width + x in pixels
                for y in range(bbox[1], bbox[3])
                for x in left_probe
            )
            has_right_alpha = any(
                y * rgba.width + x in pixels
                for y in range(bbox[1], bbox[3])
                for x in right_probe
            )
            if has_strip_alpha and has_left_alpha and has_right_alpha:
                crossed.append(f"x={line}")
        for line in horizontal_lines:
            strip_top = max(0, line - strip_radius)
            strip_bottom = min(rgba.height, line + strip_radius + 1)
            has_strip_alpha = any(
                y * rgba.width + x in pixels
                for y in range(strip_top, strip_bottom)
                for x in range(bbox[0], bbox[2])
            )
            top_probe = range(max(0, strip_top - neighbor_radius), strip_top)
            bottom_probe = range(strip_bottom, min(rgba.height, strip_bottom + neighbor_radius))
            has_top_alpha = any(
                y * rgba.width + x in pixels
                for y in top_probe
                for x in range(bbox[0], bbox[2])
            )
            has_bottom_alpha = any(
                y * rgba.width + x in pixels
                for y in bottom_probe
                for x in range(bbox[0], bbox[2])
            )
            if has_strip_alpha and has_top_alpha and has_bottom_alpha:
                crossed.append(f"y={line}")
        if not crossed:
            continue

        index = _slot_index_for_bbox(bbox, rgba.width, rgba.height, len(names), columns, rows)
        issues.append(SheetCutIssue(names[index], index, tuple(crossed), bbox))

    return issues


def format_edge_issues(issues: list[SheetEdgeIssue]) -> str:
    return "\n".join(
        f"{issue.name}: touches {','.join(issue.edges)} "
        f"cell={issue.cell_bounds} alpha_bbox={issue.alpha_bbox}"
        for issue in issues
    )


def format_cut_issues(issues: list[SheetCutIssue]) -> str:
    return "\n".join(
        f"{issue.name}: component crosses {','.join(issue.grid_lines)} "
        f"component_bbox={issue.component_bbox}"
        for issue in issues
    )


def _parse_ids(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit generated glyph sheets for alpha touching nominal grid cell edges."
    )
    parser.add_argument("--sheet", type=Path, required=True)
    parser.add_argument("--ids", required=True, help="Comma-separated glyph ids in sheet order.")
    parser.add_argument("--columns", type=int, required=True)
    parser.add_argument("--rows", type=int)
    parser.add_argument("--edge-tolerance", type=int, default=2)
    parser.add_argument("--mode", choices=["cuts", "edges"], default="cuts")
    parser.add_argument("--warn-only", action="store_true")
    args = parser.parse_args()

    names = _parse_ids(args.ids)
    image = Image.open(args.sheet).convert("RGBA")
    if args.mode == "edges":
        issues = audit_nominal_cell_edges(image, names, args.columns, args.rows, args.edge_tolerance)
        formatted = format_edge_issues(issues)
        ok_message = "no nominal cell edge alpha"
    else:
        issues = audit_grid_cut_components(image, names, args.columns, args.rows)
        formatted = format_cut_issues(issues)
        ok_message = "no alpha components crossing grid cuts"
    if not issues:
        print(f"OK {args.sheet}: {ok_message}")
        return 0

    print(formatted)
    return 0 if args.warn_only else 1


if __name__ == "__main__":
    raise SystemExit(main())
