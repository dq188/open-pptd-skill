#!/usr/bin/env python3
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import validate_pptx as MODULE


class ValidatePptxTests(unittest.TestCase):
    def test_leaked_tags_detection(self):
        regex = MODULE.LEAKED_TAG_REGEX
        self.assertIsNotNone(regex.search('Source: <a href="https://example.com">Link</a>'))
        self.assertIsNotNone(regex.search("Items: <ul><li>Item 1</li></ul>"))
        self.assertIsNotNone(regex.search("<ol><li>First</li></ol>"))
        self.assertIsNotNone(regex.search("Leaked raw tag <p> inside compiled text"))
        self.assertIsNone(regex.search("Plain text without any HTML tags"))

    def test_validation_report_properties(self):
        report = MODULE.ValidationReport(file_path="test.pptx", is_valid=True, slide_count=1)
        self.assertEqual(report.error_count, 0)
        self.assertEqual(report.warning_count, 0)

        report.issues.append(MODULE.SlideIssue(slide_index=1, severity="warning", category="test", message="warn"))
        self.assertEqual(report.error_count, 0)
        self.assertEqual(report.warning_count, 1)

        report.issues.append(MODULE.SlideIssue(slide_index=1, severity="error", category="test", message="err"))
        self.assertEqual(report.warning_count, 1)

    def test_validator_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            MODULE.PptxValidator(Path("/path/to/missing.pptx"))


if __name__ == "__main__":
    unittest.main()
