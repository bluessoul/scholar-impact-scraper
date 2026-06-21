import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from intake.author_resolver import resolve_author


class TestAuthorResolver(unittest.TestCase):
    def test_scholar_id_is_ready(self):
        profile = {"name": "Xiaolu Li", "scholar_user_id": "abcDEF1AAAAJ", "scholar_url": "", "orcid": ""}
        result = resolve_author(profile)
        self.assertEqual(result["status"], "ready")
        self.assertEqual(result["accepted_candidate"]["source"], "google_scholar")

    def test_openalex_high_confidence_without_runnable_id(self):
        profile = {
            "name": "Xiaolu Li",
            "affiliation": "IMDEA Materials Institute",
            "publication_titles": ["Fire behavior of polymer composites"],
            "orcid": "",
        }
        results = [{
            "id": "https://openalex.org/A123",
            "display_name": "Xiaolu Li",
            "last_known_institutions": [{"display_name": "IMDEA Materials Institute"}],
            "works": [{"title": "Fire behavior of polymer composites"}],
            "works_count": 42,
        }]
        resolved = resolve_author(profile, search_func=lambda name: results)
        self.assertEqual(resolved["status"], "identity_found_no_runnable_id")
        self.assertTrue(resolved["needs_confirmation"])

    def test_low_confidence_needs_confirmation(self):
        profile = {"name": "Xiaolu Li", "affiliation": "IMDEA Materials Institute", "publication_titles": []}
        results = [{"id": "https://openalex.org/A999", "display_name": "X Li", "last_known_institutions": []}]
        resolved = resolve_author(profile, search_func=lambda name: results)
        self.assertEqual(resolved["status"], "needs_user_confirmation")
        self.assertIsNone(resolved["accepted_candidate"])

    def test_close_candidates_need_confirmation(self):
        profile = {"name": "Xiaolu Li", "affiliation": "", "publication_titles": [], "orcid": ""}
        results = [
            {"id": "https://openalex.org/A1", "display_name": "Xiaolu Li", "last_known_institutions": [], "works_count": 1},
            {"id": "https://openalex.org/A2", "display_name": "Xiaolu Li", "last_known_institutions": [], "works_count": 1},
        ]
        resolved = resolve_author(profile, search_func=lambda name: results, min_confidence=0.3)
        self.assertEqual(resolved["status"], "needs_user_confirmation")


if __name__ == "__main__":
    unittest.main()
