import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import topic_shortlist_audit as shortlist


def asset(source, title="Zelda game", license_name=None, license_url=None, file_url=None, mime=""):
    return {
        "source": source,
        "title": title,
        "description": "Zelda game historical media",
        "creator": "Test",
        "license": license_name,
        "license_url": license_url,
        "file_url": file_url,
        "mime": mime,
        "file_name": "clip.mp4" if file_url else "",
    }


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.out = Path(self.tempdir.name) / "topic-audit"
        self.candidate = {
            "topic": "Zelda game",
            "trend_rank": 2,
            "markets": ["US", "GB", "NZ", "AU"],
            "trend_raw_score": 99,
        }
        self.research = {"status": "found", "extract": "Zelda " + ("research " * 80)}

    def run_audit(self, commons, nasa=None, openverse=None, loc=None, archive=None, research=None):
        patches = [
            patch.object(shortlist.audit, "wikipedia_research", return_value=research or self.research),
            patch.object(shortlist.audit, "commons_media", return_value=(commons, None)),
            patch.object(shortlist.audit, "nasa_media", return_value=(nasa or [], None)),
            patch.object(shortlist.audit, "openverse_media", return_value=(openverse or [], None)),
            patch.object(shortlist.audit, "loc_media", return_value=(loc or [], None)),
            patch.object(shortlist.audit, "internet_archive_media", return_value=(archive or [], None)),
            patch.object(shortlist.audit, "search_links", return_value={}),
            patch.object(shortlist, "OUT", self.out),
        ]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)
        return shortlist.audit_candidate(self.candidate)

    def test_multiple_source_types_improve_media_and_feasibility_scores(self):
        result = self.run_audit(
            [asset("Wikimedia Commons"), asset("Wikimedia Commons")],
            nasa=[asset("NASA")],
        )
        scores = result["score_components_0_to_5"]
        self.assertEqual(scores["media_inventory"], 2)
        self.assertEqual(scores["production_feasibility"], 3)
        self.assertEqual(result["media_counts"]["distinct_sources_with_keyword_matches"], 2)

    def test_missing_licence_metadata_never_counts_as_rights_ready(self):
        result = self.run_audit([asset("Wikimedia Commons"), asset("NASA"), asset("LOC")])
        self.assertEqual(result["score_components_0_to_5"]["rights_readiness"], 0)
        self.assertEqual(result["media_counts"]["automatically_cleared_assets"], 0)

    def test_insufficient_research_holds_topic(self):
        result = self.run_audit(
            [asset("Wikimedia Commons")],
            research={"status": "found", "extract": "short"},
        )
        self.assertEqual(result["decision"], "HOLD_OR_RESELECT")
        self.assertEqual(result["score_components_0_to_5"]["research_depth"], 1)

    def test_video_candidate_is_counted_but_not_auto_cleared(self):
        result = self.run_audit([
            asset("Wikimedia Commons", file_url="https://example.test/clip.mp4", mime="video/mp4")
        ])
        self.assertEqual(result["media_counts"]["keyword_matched_video_file_candidates"], 1)
        self.assertEqual(result["media_counts"]["automatically_cleared_assets"], 0)

    def test_placeholder_archive_rights_text_does_not_count_as_licence(self):
        result = self.run_audit([
            asset("Internet Archive", license_name="See item metadata",
                  license_url="https://archive.org/details/example")
        ])
        self.assertEqual(result["score_components_0_to_5"]["rights_readiness"], 0)
        self.assertEqual(result["media_counts"]["automatically_cleared_assets"], 0)


if __name__ == "__main__":
    unittest.main()
