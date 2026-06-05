#!/usr/bin/env python3
"""
Unit and Integration Tests for ORCID Publication Extractor.
Uses unittest and unittest.mock to test logic without making real API calls.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import functions from orcid_extractor
from orcid_extractor import (
    get_access_token,
    fetch_orcid_works,
    parse_works,
    save_to_csv
)

class TestORCIDExtractor(unittest.TestCase):

    def setUp(self):
        self.mock_client_id = "APP-1234567890ABCDEF"
        self.mock_client_secret = "abcdef12-3456-7890-abcd-ef1234567890"
        self.mock_orcid_id = "0000-0002-1825-0097"
        
        # Standard ORCID works JSON snippet
        self.sample_works_json = {
            "group": [
                {
                    "last-modified-date": {"value": 1620000000000},
                    "external-ids": {
                        "external-id": [
                            {
                                "external-id-type": "doi",
                                "external-id-value": "10.1002/xyz.789",
                                "external-id-relationship": "self"
                            }
                        ]
                    },
                    "work-summary": [
                        {
                            "put-code": 1001,
                            "title": {
                                "title": {"value": "First Publication Title"}
                            },
                            "journal-title": {"value": "Journal of Machine Learning"},
                            "publication-date": {
                                "year": {"value": "2021"}
                            },
                            "external-ids": {
                                "external-id": [
                                    {
                                        "external-id-type": "doi",
                                        "external-id-value": "10.1002/xyz.789",
                                        "external-id-relationship": "self"
                                    }
                                ]
                            }
                        }
                    ]
                },
                {
                    # A work with missing publication date and missing journal
                    "last-modified-date": {"value": 1620000000000},
                    "work-summary": [
                        {
                            "put-code": 1002,
                            "title": {
                                "title": {"value": "Second Publication with Missing Fields"}
                            }
                            # journal-title and publication-date are omitted to test fallback
                        }
                    ]
                },
                {
                    # A work in 2023 to test sorting
                    "last-modified-date": {"value": 1620000000000},
                    "external-ids": {
                        "external-id": [
                            {
                                "external-id-type": "doi",
                                "external-id-value": "10.1002/abc.123"
                            },
                            {
                                "external-id-type": "isbn",
                                "external-id-value": "978-3-16-148410-0"
                            }
                        ]
                    },
                    "work-summary": [
                        {
                            "put-code": 1003,
                            "title": {
                                "title": {"value": "Third Publication Title"}
                            },
                            "journal-title": {"value": "Advanced AI Journal"},
                            "publication-date": {
                                "year": {"value": "2023"}
                            }
                        }
                    ]
                }
            ]
        }

    @patch("requests.post")
    def test_get_access_token_success(self, mock_post):
        # Set up mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"access_token": "mock-access-token-9876"}
        mock_post.return_value = mock_response
        
        token = get_access_token(self.mock_client_id, self.mock_client_secret)
        
        self.assertEqual(token, "mock-access-token-9876")
        mock_post.assert_called_once()
        # Verify post payload
        called_args, called_kwargs = mock_post.call_args
        self.assertEqual(called_kwargs['data']['client_id'], self.mock_client_id)
        self.assertEqual(called_kwargs['data']['grant_type'], 'client_credentials')

    @patch("requests.post")
    def test_get_access_token_failure(self, mock_post):
        # Set up mock failure response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Unauthorized")
        mock_post.return_value = mock_response
        
        with self.assertRaises(requests.exceptions.HTTPError):
            get_access_token(self.mock_client_id, self.mock_client_secret)

    @patch("requests.get")
    def test_fetch_orcid_works_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.sample_works_json
        mock_get.return_value = mock_response
        
        response_json = fetch_orcid_works(self.mock_orcid_id, "mock-token")
        
        self.assertEqual(response_json, self.sample_works_json)
        mock_get.assert_called_once()
        # Check that authorization header and accept header are correct
        called_args, called_kwargs = mock_get.call_args
        self.assertEqual(called_kwargs['headers']['Authorization'], "Bearer mock-token")
        self.assertEqual(called_kwargs['headers']['Accept'], "application/vnd.orcid+json")

    def test_parse_works(self):
        parsed = parse_works(self.sample_works_json)
        
        self.assertEqual(len(parsed), 3)
        
        # Test work 1
        self.assertEqual(parsed[0]["title"], "First Publication Title")
        self.assertEqual(parsed[0]["publication_year"], "2021")
        self.assertEqual(parsed[0]["journal_venue"], "Journal of Machine Learning")
        self.assertEqual(parsed[0]["doi"], "10.1002/xyz.789")
        self.assertEqual(parsed[0]["all_external_ids"], "DOI:10.1002/xyz.789")
        
        # Test work 2 (missing fields)
        self.assertEqual(parsed[1]["title"], "Second Publication with Missing Fields")
        self.assertEqual(parsed[1]["publication_year"], "")
        self.assertEqual(parsed[1]["journal_venue"], "")
        self.assertEqual(parsed[1]["doi"], "")
        self.assertEqual(parsed[1]["all_external_ids"], "")
        
        # Test work 3 (multiple external IDs)
        self.assertEqual(parsed[2]["title"], "Third Publication Title")
        self.assertEqual(parsed[2]["publication_year"], "2023")
        self.assertEqual(parsed[2]["journal_venue"], "Advanced AI Journal")
        self.assertEqual(parsed[2]["doi"], "10.1002/abc.123")
        # Assert other ID type was added in all_external_ids
        self.assertIn("ISBN:978-3-16-148410-0", parsed[2]["all_external_ids"])

    def test_save_to_csv_sorting_and_content(self):
        parsed_works = parse_works(self.sample_works_json)
        
        # Create a temporary file to save the CSV
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_csv_path = os.path.join(temp_dir, "test_orcid_publications.csv")
            
            # Save to CSV (which should sort by year in descending order)
            save_to_csv(parsed_works, temp_csv_path)
            
            # Verify file exists and read it back
            self.assertTrue(os.path.exists(temp_csv_path))
            
            with open(temp_csv_path, mode='r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Headers + 3 rows = 4 lines
            self.assertEqual(len(lines), 4)
            
            # Verify header row
            self.assertIn("Title,Publication Year,Journal/Venue,DOI,External IDs", lines[0])
            
            # Since sorted in descending order:
            # 1st data row should be the 2023 paper (Third Publication Title)
            self.assertIn("Third Publication Title", lines[1])
            self.assertIn("2023", lines[1])
            
            # 2nd data row should be the 2021 paper (First Publication Title)
            self.assertIn("First Publication Title", lines[2])
            self.assertIn("2021", lines[2])
            
            # 3rd data row should be the paper with missing year (Second Publication... sorted to the bottom)
            self.assertIn("Second Publication with Missing Fields", lines[3])
            self.assertIn("N/A", lines[3]) # missing year replaced by N/A

if __name__ == "__main__":
    unittest.main()
