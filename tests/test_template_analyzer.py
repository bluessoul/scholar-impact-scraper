import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from intake.template_analyzer import analyze_template, default_requirements


class TestTemplateAnalyzer(unittest.TestCase):
    def test_detects_requested_fields_and_format(self):
        template = """
        请填写代表作、总引用、H-index、中科院分区、第一作者/通讯作者信息。
        参考文献格式使用 GB/T 7714-2025，并列出 DOI。
        """
        result = analyze_template(template)
        self.assertIn("representative_works", result["requested_fields"])
        self.assertIn("total_citations", result["requested_fields"])
        self.assertIn("h_index", result["requested_fields"])
        self.assertIn("cas_partition", result["requested_fields"])
        self.assertEqual(result["citation_format"], "gbt2025")
        self.assertTrue(result["requires_cas_partition"])

    def test_default_requirements(self):
        result = default_requirements()
        self.assertEqual(result["output_style"], "CV-ready publication list + impact summary")
        self.assertEqual(result["citation_format"], "gbt2025")


if __name__ == "__main__":
    unittest.main()

