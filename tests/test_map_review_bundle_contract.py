from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class MapReviewBundleContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bundle_script = (ROOT / "scripts" / "create-map-review-bundle.sh").read_text(encoding="utf-8")
        cls.verify_script = (ROOT / "scripts" / "verify-web-map.mjs").read_text(encoding="utf-8")
        cls.gate_doc = (ROOT / "docs" / "map-reviewer-gate.md").read_text(encoding="utf-8")

    def test_bundle_script_is_single_reproducible_review_command(self) -> None:
        for expected in [
            "scripts/serve-web.sh",
            "node scripts/verify-web-map.mjs",
            "screenshots_dir",
            "web-build.json",
            "review-report.md",
            "reviewed-commit.txt",
            "git-status.txt",
            "header-check.log",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.bundle_script)

    def test_bundle_checks_gzip_no_cache_and_build_metadata(self) -> None:
        for expected in [
            "Content-Encoding: gzip",
            "Cache-Control: no-store, no-cache, must-revalidate, max-age=0",
            "Pragma: no-cache",
            "Expires: 0",
            ".web-build.json",
            'name="cable-world-web-build"',
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.bundle_script)

    def test_screenshot_capture_covers_required_map_review_scenarios(self) -> None:
        for expected in [
            "mobile-390x844",
            "desktop-1280x800",
            "zoom-150",
            "zoom-200",
            "after-marker-click",
            "after-drag",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.verify_script)
                self.assertIn(expected, self.bundle_script)

    def test_report_template_forces_strict_accept_or_reject_decision(self) -> None:
        for expected in [
            "Decision: REJECT",
            "Only valid final decisions are ACCEPT or REJECT.",
            "ACCEPT is allowed only when Score is 10/10",
            "Any visual regression",
            "send back to implementer/fix-worker before integration",
            "Blockers if REJECT",
            "Screenshots Checked",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.bundle_script)

    def test_gate_document_names_bundle_command_and_strict_rejection(self) -> None:
        for expected in [
            "scripts/create-map-review-bundle.sh",
            "mobile-390x844-zoom-150.png",
            "mobile-390x844-zoom-200.png",
            "review-report.md",
            "fix-worker",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.gate_doc)


if __name__ == "__main__":
    unittest.main()
