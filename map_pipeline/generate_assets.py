import sys


MESSAGE = """This project no longer generates individual map assets.

Use one generated 4x2 transport icon sheet, remove the chroma key, then slice it:

  python "${CODEX_HOME:-$HOME/.codex}/skills/.system/imagegen/scripts/remove_chroma_key.py" \\
    --input <generated-magenta-sheet.png> \\
    --out tmp/map-icon-source/transport_icon_sheet.png \\
    --auto-key border --soft-matte --transparent-threshold 12 \\
    --opaque-threshold 220 --despill

  uv run python -m map_pipeline.slice_transport_icons \\
    --sheet tmp/map-icon-source/transport_icon_sheet.png \\
    --out-dir assets/sprites

Reusable glyph workflows are documented in docs/pipelines/glyph-generation.md.
"""


def main() -> int:
    print(MESSAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
