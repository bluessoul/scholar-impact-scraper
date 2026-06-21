import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import scholar_intake


class Completed:
    returncode = 0


class TestScholarIntakeCli(unittest.TestCase):
    def test_cli_generates_plan_but_waits_for_confirmation_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            cv = Path(tmp) / "cv.txt"
            out = Path(tmp) / "out"
            cv.write_text(
                "Name: Xiaolu Li\nAffiliation: IMDEA Materials Institute\n"
                "Google Scholar: https://scholar.google.com/citations?user=abcDEF1AAAAJ\n",
                encoding="utf-8",
            )
            argv = ["scholar_intake.py", "--input", str(cv), "--output-dir", str(out)]
            with patch.object(sys, "argv", argv), patch("scholar_intake.subprocess.run", return_value=Completed()) as run:
                self.assertEqual(scholar_intake.main(), 0)
                run.assert_not_called()
            plan = json.loads((out / "scrape_plan.json").read_text(encoding="utf-8"))
            self.assertEqual(plan["commands"][0]["kind"], "scholar")
            self.assertEqual(plan["commands"][0]["status"], "planned")
            self.assertEqual(plan["status"], "needs_confirmation")
            self.assertTrue((out / "final_summary.md").exists())

    def test_cli_runs_with_yes_when_required_fields_are_complete(self):
        with tempfile.TemporaryDirectory() as tmp:
            cv = Path(tmp) / "cv.txt"
            template = Path(tmp) / "template.txt"
            out = Path(tmp) / "out"
            cv.write_text(
                "Name: Xiaolu Li\nAffiliation: IMDEA Materials Institute\n"
                "Google Scholar: https://scholar.google.com/citations?user=abcDEF1AAAAJ\n",
                encoding="utf-8",
            )
            template.write_text("Please provide publications, total citations, H-index, DOI, and APA format.", encoding="utf-8")
            argv = ["scholar_intake.py", "--input", str(cv), "--template", str(template), "--output-dir", str(out), "--yes", "--all-years"]
            with patch.object(sys, "argv", argv), patch("scholar_intake.subprocess.run", return_value=Completed()) as run:
                self.assertEqual(scholar_intake.main(), 0)
                run.assert_called()
            plan = json.loads((out / "scrape_plan.json").read_text(encoding="utf-8"))
            self.assertEqual(plan["status"], "ready")
            self.assertEqual(plan["commands"][0]["status"], "completed")

    def test_cli_yes_does_not_run_when_year_scope_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            cv = Path(tmp) / "cv.txt"
            template = Path(tmp) / "template.txt"
            out = Path(tmp) / "out"
            cv.write_text(
                "Name: Xiaolu Li\nAffiliation: IMDEA Materials Institute\n"
                "Google Scholar: https://scholar.google.com/citations?user=abcDEF1AAAAJ\n",
                encoding="utf-8",
            )
            template.write_text("Please provide publications, total citations, H-index, DOI, and APA format.", encoding="utf-8")
            argv = ["scholar_intake.py", "--input", str(cv), "--template", str(template), "--output-dir", str(out), "--yes"]
            with patch.object(sys, "argv", argv), patch("scholar_intake.subprocess.run", return_value=Completed()) as run:
                self.assertEqual(scholar_intake.main(), 0)
                run.assert_not_called()
            plan = json.loads((out / "scrape_plan.json").read_text(encoding="utf-8"))
            self.assertEqual(plan["status"], "needs_confirmation")
            self.assertIn("No publication year range was specified. Confirm all years with --all-years, or pass --year / --year-from and --year-to.", plan["confirmation"]["blocking_reasons"])

    def test_cli_infers_year_range_from_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            cv = Path(tmp) / "cv.txt"
            template = Path(tmp) / "template.txt"
            out = Path(tmp) / "out"
            cv.write_text(
                "Name: Xiaolu Li\nAffiliation: IMDEA Materials Institute\n"
                "Google Scholar: https://scholar.google.com/citations?user=abcDEF1AAAAJ\n",
                encoding="utf-8",
            )
            template.write_text("Please provide publications from 2020-2024, total citations, H-index, DOI, and APA format.", encoding="utf-8")
            argv = ["scholar_intake.py", "--input", str(cv), "--template", str(template), "--output-dir", str(out), "--yes"]
            with patch.object(sys, "argv", argv), patch("scholar_intake.subprocess.run", return_value=Completed()) as run:
                self.assertEqual(scholar_intake.main(), 0)
                run.assert_called()
            plan = json.loads((out / "scrape_plan.json").read_text(encoding="utf-8"))
            self.assertEqual(plan["year_scope"]["description"], "2020-2024")

    def test_cli_yes_does_not_run_when_affiliation_is_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            cv = Path(tmp) / "cv.txt"
            template = Path(tmp) / "template.txt"
            out = Path(tmp) / "out"
            cv.write_text("Name: Xiaolu Li\nGoogle Scholar: https://scholar.google.com/citations?user=abcDEF1AAAAJ\n", encoding="utf-8")
            template.write_text("Please provide publications, total citations, H-index, DOI, and APA format.", encoding="utf-8")
            argv = ["scholar_intake.py", "--input", str(cv), "--template", str(template), "--output-dir", str(out), "--yes", "--all-years"]
            with patch.object(sys, "argv", argv), patch("scholar_intake.subprocess.run", return_value=Completed()) as run:
                self.assertEqual(scholar_intake.main(), 0)
                run.assert_not_called()
            plan = json.loads((out / "scrape_plan.json").read_text(encoding="utf-8"))
            self.assertEqual(plan["status"], "needs_confirmation")
            self.assertIn("No affiliation or organization was detected.", plan["confirmation"]["blocking_reasons"])

    def test_cli_yes_does_not_run_when_template_requirements_are_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            cv = Path(tmp) / "cv.txt"
            out = Path(tmp) / "out"
            cv.write_text(
                "Name: Xiaolu Li\nAffiliation: IMDEA Materials Institute\n"
                "Google Scholar: https://scholar.google.com/citations?user=abcDEF1AAAAJ\n",
                encoding="utf-8",
            )
            argv = ["scholar_intake.py", "--input", str(cv), "--output-dir", str(out), "--yes"]
            with patch.object(sys, "argv", argv), patch("scholar_intake.subprocess.run", return_value=Completed()) as run:
                self.assertEqual(scholar_intake.main(), 0)
                run.assert_not_called()
            plan = json.loads((out / "scrape_plan.json").read_text(encoding="utf-8"))
            self.assertEqual(plan["status"], "needs_confirmation")
            self.assertIn("No explicit output format or template requirements were detected.", plan["confirmation"]["blocking_reasons"])

    def test_cli_low_confidence_does_not_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            argv = [
                "scholar_intake.py",
                "--name",
                "Ambiguous Scholar",
                "--affiliation",
                "Unknown Institute",
                "--output-dir",
                str(out),
                "--no-run",
            ]
            with patch.object(sys, "argv", argv), patch("scholar_intake.subprocess.run") as run, patch(
                "intake.author_resolver.requests.get"
            ) as get:
                get.return_value.json.return_value = {"results": []}
                get.return_value.raise_for_status.return_value = None
                self.assertEqual(scholar_intake.main(), 0)
                run.assert_not_called()
            candidates = json.loads((out / "author_candidates.json").read_text(encoding="utf-8"))
            self.assertTrue(candidates["needs_confirmation"])


if __name__ == "__main__":
    unittest.main()
