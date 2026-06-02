import tempfile
import unittest
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from map_pipeline.sheet_slice_audit import audit_grid_cut_components, audit_nominal_cell_edges
from map_pipeline.slice_city_cluster_landmarks_hi_res import _component_crops


class SheetSliceAuditTest(unittest.TestCase):
    def test_slicers_keep_cut_audit_in_pipeline(self) -> None:
        root = Path(__file__).resolve().parent.parent
        city_slicer = (root / "map_pipeline" / "slice_city_cluster_landmarks_hi_res.py").read_text(encoding="utf-8")
        transport_slicer = (root / "map_pipeline" / "slice_transport_icons.py").read_text(encoding="utf-8")

        for text in (city_slicer, transport_slicer):
            self.assertIn("audit_grid_cut_components", text)
            self.assertIn("--edge-audit", text)
            self.assertIn("Grid-cut alpha components detected", text)

    def test_audit_reports_alpha_touching_nominal_cell_edge(self) -> None:
        sheet = Image.new("RGBA", (200, 100), (0, 0, 0, 0))
        draw = ImageDraw.Draw(sheet)
        draw.rectangle((35, 20, 100, 80), fill=(255, 255, 255, 255))
        draw.rectangle((135, 20, 165, 80), fill=(255, 255, 255, 255))

        issues = audit_nominal_cell_edges(sheet, ["left_city", "right_city"], columns=2, rows=1)

        self.assertEqual([issue.name for issue in issues], ["left_city", "right_city"])
        self.assertEqual(issues[0].edges, ("right",))
        self.assertEqual(issues[1].edges, ("left",))

    def test_cut_audit_reports_alpha_strip_with_alpha_on_both_sides(self) -> None:
        sheet = Image.new("RGBA", (200, 100), (0, 0, 0, 0))
        draw = ImageDraw.Draw(sheet)
        draw.rectangle((35, 20, 110, 80), fill=(255, 255, 255, 255))
        draw.rectangle((140, 20, 170, 80), fill=(255, 255, 255, 255))

        issues = audit_grid_cut_components(sheet, ["left_city", "right_city"], columns=2, rows=1)

        self.assertEqual([issue.name for issue in issues], ["left_city"])
        self.assertEqual(issues[0].grid_lines, ("x=100",))

    def test_cut_audit_does_not_report_when_alpha_only_touches_one_side(self) -> None:
        sheet = Image.new("RGBA", (200, 100), (0, 0, 0, 0))
        draw = ImageDraw.Draw(sheet)
        draw.rectangle((35, 20, 100, 80), fill=(255, 255, 255, 255))
        draw.rectangle((135, 20, 165, 80), fill=(255, 255, 255, 255))

        self.assertEqual(audit_grid_cut_components(sheet, ["left_city", "right_city"], columns=2, rows=1), [])

    def test_component_city_crop_keeps_object_that_crosses_grid_boundary(self) -> None:
        sheet = Image.new("RGBA", (200, 100), (0, 0, 0, 0))
        draw = ImageDraw.Draw(sheet)
        draw.rectangle((35, 20, 110, 80), fill=(255, 255, 255, 255))
        draw.rectangle((140, 20, 170, 80), fill=(255, 255, 255, 255))

        crops = _component_crops(sheet, ["left_city", "right_city"], columns=2)

        self.assertEqual(len(crops), 2)
        left_bbox = crops[0].getchannel("A").getbbox()
        self.assertIsNotNone(left_bbox)
        self.assertGreater(crops[0].size[0], 100)
        self.assertEqual(left_bbox[2], 100)

    def test_cli_exits_nonzero_for_cut_issue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            sheet_path = Path(tmp) / "sheet.png"
            sheet = Image.new("RGBA", (200, 100), (0, 0, 0, 0))
            ImageDraw.Draw(sheet).rectangle((35, 20, 110, 80), fill=(255, 255, 255, 255))
            sheet.save(sheet_path)

            import subprocess

            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "map_pipeline.sheet_slice_audit",
                    "--sheet",
                    str(sheet_path),
                    "--ids",
                    "left_city,right_city",
                    "--columns",
                    "2",
                ],
                cwd=Path(__file__).resolve().parent.parent,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("left_city", result.stdout)


if __name__ == "__main__":
    unittest.main()
