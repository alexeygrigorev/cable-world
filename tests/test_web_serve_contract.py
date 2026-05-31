from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class WebServeContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.script = (ROOT / "scripts" / "serve-web.sh").read_text(encoding="utf-8")

    def test_server_disables_browser_cache_for_web_payload(self) -> None:
        for expected in [
            '"Cache-Control", "no-store, no-cache, must-revalidate, max-age=0"',
            '"Pragma", "no-cache"',
            '"Expires", "0"',
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.script)

    def test_server_serves_gzip_for_godot_payload_and_map_pngs(self) -> None:
        for expected in [
            "-name '*.html'",
            "-name '*.js'",
            "-name '*.wasm'",
            "-name '*.pck'",
            "-name '*.png'",
            '"Content-Encoding", "gzip"',
            '"Vary", "Accept-Encoding"',
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.script)

    def test_server_stamps_index_and_exposes_build_metadata(self) -> None:
        for expected in [
            "cable-world-web-build",
            ".web-build.json",
            "WEB_BUILD_ID",
            "index\\.js\\?v=",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.script)

    def test_header_check_mode_covers_cache_gzip_and_build_stamp(self) -> None:
        for expected in [
            "--check-headers",
            "serve-web header check passed",
            "index.html index.js index.wasm index.pck map.png",
            "Content-Encoding: gzip",
            "Cache-Control: no-store, no-cache, must-revalidate, max-age=0",
            'name="cable-world-web-build"',
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.script)

    def test_busy_port_is_reported_without_killing_existing_server(self) -> None:
        for expected in [
            "Requested port",
            "is busy; leaving it untouched",
            "find_port(start_port)",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, self.script)


if __name__ == "__main__":
    unittest.main()
