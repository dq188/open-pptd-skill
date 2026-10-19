#!/usr/bin/env python3
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import export_pptx as MODULE


class ExportPptxTests(unittest.TestCase):
    def test_find_manifest_direct_file(self):
        with tempfile.NamedTemporaryFile(suffix=".pptd", delete=False) as tf:
            tf.write(b"theme: {}\n")
            path = Path(tf.name)
        try:
            self.assertEqual(MODULE.find_manifest(path), path.resolve())
        finally:
            path.unlink(missing_ok=True)

    def test_find_manifest_wrong_extension(self):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tf:
            path = Path(tf.name)
        try:
            with self.assertRaises(ValueError):
                MODULE.find_manifest(path)
        finally:
            path.unlink(missing_ok=True)

    def test_find_manifest_directory_single(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            manifest = d / "presentation.pptd"
            manifest.write_text("theme: {}\n")
            self.assertEqual(MODULE.find_manifest(d), manifest.resolve())

    def test_find_manifest_directory_prefers_deck_pptd(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            (d / "a.pptd").write_text("theme: {}\n")
            deck = d / "deck.pptd"
            deck.write_text("theme: {}\n")
            self.assertEqual(MODULE.find_manifest(d), deck.resolve())

    def test_find_manifest_directory_empty(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(FileNotFoundError):
                MODULE.find_manifest(Path(td))

    def test_find_manifest_directory_multiple_ambiguous(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            (d / "a.pptd").write_text("theme: {}\n")
            (d / "b.pptd").write_text("theme: {}\n")
            with self.assertRaises(ValueError):
                MODULE.find_manifest(d)

    @patch.object(MODULE, "ensure_pptd", return_value=Path(__file__))
    @patch("subprocess.run")
    def test_export_pptx_builds_successfully(self, mock_run, mock_ensure):
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="wrote presentation.pptx\n", stderr="")
        with tempfile.TemporaryDirectory() as td:
            manifest = Path(td) / "deck.pptd"
            manifest.write_text("theme: {}\n")
            out_file = Path(td) / "out.pptx"

            result = MODULE.export_pptx(manifest, output=out_file)
            self.assertEqual(result, out_file.resolve())
            mock_ensure.assert_called_once()
            mock_run.assert_called_once()
            call_args = mock_run.call_args[0][0]
            self.assertEqual(call_args[:4], [str(Path(__file__)), "build", str(manifest.resolve()), "-o"])
            self.assertNotIn("--force", call_args)

    @patch.object(MODULE, "ensure_pptd", return_value=Path(__file__))
    @patch("subprocess.run")
    def test_export_pptx_passes_force_flag(self, mock_run, mock_ensure):
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout="wrote presentation.pptx\n", stderr="")
        with tempfile.TemporaryDirectory() as td:
            manifest = Path(td) / "deck.pptd"
            manifest.write_text("theme: {}\n")
            out_file = Path(td) / "out.pptx"

            MODULE.export_pptx(manifest, output=out_file, force=True)
            self.assertIn("--force", mock_run.call_args[0][0])

    @patch.object(MODULE, "ensure_pptd", return_value=Path(__file__))
    @patch("subprocess.run")
    def test_export_pptx_raises_on_compiler_error(self, mock_run, mock_ensure):
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=2, stdout="", stderr="error: changed after sync point")
        with tempfile.TemporaryDirectory() as td:
            manifest = Path(td) / "deck.pptd"
            manifest.write_text("theme: {}\n")
            with self.assertRaises(RuntimeError):
                MODULE.export_pptx(manifest)


if __name__ == "__main__":
    unittest.main()
