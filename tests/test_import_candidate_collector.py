from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "import_candidates"
SCRIPT = ROOT / "scripts" / "import_candidate_collector.py"
sys.path.insert(0, str(ROOT))

from scripts import import_candidate_collector as collector  # noqa: E402


class ImportCandidateCollectorTest(unittest.TestCase):
    def test_queries_cover_required_osm_and_wikidata_fields(self) -> None:
        for expected in [
            '"aerialway"',
            '"railway"="funicular"',
            '"railway"="rail"]["rack"="yes"',
            '"railway"="monorail"',
        ]:
            self.assertIn(expected, collector.OVERPASS_QUERY)

        for expected in ["P31", "P625", "P17", "P137", "P856", "P402", "P10689", "P11693"]:
            self.assertIn(expected, collector.WIKIDATA_SPARQL_QUERY)

    def test_offline_collection_merges_by_wikidata_and_osm_ids(self) -> None:
        payload = collector.collect_candidates(
            collector.load_json(FIXTURES / "osm_overpass_sample.json"),
            collector.load_json(FIXTURES / "wikidata_sparql_sample.json"),
        )
        candidates = payload["candidates"]
        by_wikidata = {
            candidate["source_ids"].get("wikidata"): candidate
            for candidate in candidates
            if candidate["source_ids"].get("wikidata")
        }

        self.assertEqual(len(candidates), 5)
        berlin = by_wikidata["Q1001"]
        self.assertEqual(berlin["transport_type_id"], "cable_gondola")
        self.assertEqual(berlin["operational_status"], "unknown")
        self.assertIn("ручная проверка", berlin["review"]["notes"])
        self.assertIn("way/1001", berlin["source_ids"]["osm"])
        self.assertEqual(berlin["source_ids"]["wikidata_osm_way"], "1001")
        self.assertIn("https://www.openstreetmap.org/way/1001", berlin["source_urls"])
        self.assertIn("https://www.wikidata.org/wiki/Q1001", berlin["source_urls"])

    def test_draft_types_and_manual_status_note_are_present(self) -> None:
        payload = collector.collect_candidates(
            collector.load_json(FIXTURES / "osm_overpass_sample.json"),
            collector.load_json(FIXTURES / "wikidata_sparql_sample.json"),
        )
        types_by_osm = {
            candidate["source_ids"]["osm"][0]: candidate["transport_type_id"]
            for candidate in payload["candidates"]
            if candidate["source_ids"].get("osm")
        }

        self.assertEqual(types_by_osm["relation/2002"], "rail_cog")
        self.assertEqual(types_by_osm["node/3003"], "suspended_train")
        self.assertEqual(types_by_osm["way/4004"], "funicular_classic")

        for candidate in payload["candidates"]:
            self.assertEqual(candidate["visit_status_id"], "not_visited")
            self.assertEqual(candidate["operational_status"], "unknown")
            self.assertIn("Черновой статус", candidate["status_note"])
            self.assertIn("ru", candidate["localized"])
            self.assertTrue(candidate["localized"]["ru"]["title"])
            self.assertTrue(candidate["localized"]["ru"]["description"])

    def test_cli_writes_only_requested_staging_json_in_offline_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            output = Path(tmp_dir) / "candidates.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--osm-json",
                    str(FIXTURES / "osm_overpass_sample.json"),
                    "--wikidata-json",
                    str(FIXTURES / "wikidata_sparql_sample.json"),
                    "--output",
                    str(output),
                    "--no-validate",
                ],
                cwd=ROOT,
                check=False,
                text=True,
                capture_output=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output.exists())
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema_version"], "import-candidates-v1")
            self.assertEqual(len(payload["candidates"]), 5)


if __name__ == "__main__":
    unittest.main()
