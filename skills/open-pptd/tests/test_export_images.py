#!/usr/bin/env python3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import export_images as MODULE


class ExportImagesTests(unittest.TestCase):
    def test_build_montage_empty_list(self):
        with tempfile.TemporaryDirectory() as td:
            out_file = Path(td) / "overview.jpg"
            MODULE.build_montage([], out_file)
            self.assertFalse(out_file.exists())

    def test_build_montage_creates_grid(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow not installed")

        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            img1 = d / "slide_1.png"
            img2 = d / "slide_2.png"
            im = Image.new("RGB", (800, 600), color="white")
            im.save(img1)
            im.save(img2)

            out_file = d / "overview.jpg"
            MODULE.build_montage([img1, img2], out_file, cols=2)
            self.assertTrue(out_file.exists())
            with Image.open(out_file) as res:
                self.assertGreater(res.width, 0)
                self.assertGreater(res.height, 0)

    def test_export_images_missing_source(self):
        with self.assertRaises(FileNotFoundError):
            MODULE.export_images(Path("/path/to/nonexistent/deck.pptd"))


if __name__ == "__main__":
    unittest.main()
