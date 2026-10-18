#!/usr/bin/env python3
"""Validation and visual verification tool for compiled PPTX presentations.

Checks:
1. PPTX package integrity (OPC parts, presentation structure, slide parts).
2. Expected page/slide count.
3. Leaked unrendered HTML tags in DrawingML text nodes (<ul>, <li>, <a>, <p>, etc.).
4. Speaker notes presence, extraction, and validation.
5. Visual boundaries and potential text overflow.
6. Optional slide image rendering via headless LibreOffice, pdftoppm, or macOS QuickLook.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional, Sequence

# DrawingML and PresentationML namespaces
NAMESPACES = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}

# Regex for leaked HTML tags that should have been processed or stripped
LEAKED_TAG_REGEX = re.compile(
    r"</?(?:ul|ol|li|a|div|span|p|b|i|u|s|del|strike|font|code|h[1-6]|table|tr|td|th)(?:\s+[^>]*)?>|&(?:lt|gt|amp);",
    re.IGNORECASE,
)


@dataclass
class SlideIssue:
    slide_index: int
    severity: str  # "error" or "warning"
    category: str  # "leaked_tag", "overflow", "notes", "structure"
    message: str
    element_id: Optional[str] = None
    snippet: Optional[str] = None


@dataclass
class SlideInfo:
    index: int
    title: Optional[str] = None
    has_notes: bool = False
    notes_text: Optional[str] = None
    shapes_count: int = 0
    text_boxes_count: int = 0
    images_count: int = 0
    tables_count: int = 0


@dataclass
class ValidationReport:
    file_path: str
    is_valid: bool
    slide_count: int
    slides: list[SlideInfo] = field(default_factory=list)
    issues: list[SlideIssue] = field(default_factory=list)
    rendered_images: list[str] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "error")

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == "warning")


class PptxValidator:
    def __init__(self, pptx_path: Path):
        self.path = pptx_path.expanduser().resolve()
        if not self.path.is_file():
            raise FileNotFoundError(f"PPTX file not found: {self.path}")

    def validate(
        self,
        expected_pages: Optional[int] = None,
        check_notes: bool = False,
    ) -> ValidationReport:
        report = ValidationReport(
            file_path=str(self.path),
            is_valid=True,
            slide_count=0,
        )

        try:
            with zipfile.ZipFile(self.path, "r") as z:
                self._check_package_structure(z, report)
                if not report.is_valid:
                    return report

                slide_files = self._get_slide_files(z)
                report.slide_count = len(slide_files)

                if expected_pages is not None and report.slide_count != expected_pages:
                    report.issues.append(
                        SlideIssue(
                            slide_index=0,
                            severity="error",
                            category="structure",
                            message=f"Slide count mismatch: expected {expected_pages}, got {report.slide_count}",
                        )
                    )

                # Slide size in EMUs (1 pt = 12700 EMUs)
                slide_w, slide_h = self._get_slide_size(z)

                for idx, slide_path in enumerate(slide_files, start=1):
                    info = self._analyze_slide(z, idx, slide_path, slide_w, slide_h, report)
                    report.slides.append(info)

                    if check_notes and not info.has_notes:
                        report.issues.append(
                            SlideIssue(
                                slide_index=idx,
                                severity="warning",
                                category="notes",
                                message=f"Slide {idx} has no speaker notes",
                            )
                        )

        except zipfile.BadZipFile:
            report.is_valid = False
            report.issues.append(
                SlideIssue(
                    slide_index=0,
                    severity="error",
                    category="structure",
                    message="File is not a valid zip/PPTX archive",
                )
            )

        return report

    def _check_package_structure(self, z: zipfile.ZipFile, report: ValidationReport) -> None:
        required_parts = ["[Content_Types].xml", "ppt/presentation.xml"]
        for part in required_parts:
            if part not in z.namelist():
                report.is_valid = False
                report.issues.append(
                    SlideIssue(
                        slide_index=0,
                        severity="error",
                        category="structure",
                        message=f"Missing required OpenXML part: {part}",
                    )
                )

    def _get_slide_files(self, z: zipfile.ZipFile) -> list[str]:
        # Read ppt/presentation.xml to get slides in true sequence
        slides = []
        try:
            tree = ET.fromstring(z.read("ppt/presentation.xml"))
            sld_id_lst = tree.find("p:sldIdLst", NAMESPACES)
            if sld_id_lst is not None:
                # Read presentation rels to map r:id to filename
                rels_tree = ET.fromstring(z.read("ppt/_rels/presentation.xml.rels"))
                rel_map = {}
                for rel in rels_tree.findall("{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"):
                    r_id = rel.attrib.get("Id")
                    target = rel.attrib.get("Target")
                    if r_id and target:
                        # Normalize target
                        if target.startswith("/"):
                            target = target.lstrip("/")
                        elif not target.startswith("ppt/"):
                            target = f"ppt/{target}"
                        rel_map[r_id] = target

                for sld_id in sld_id_lst.findall("p:sldId", NAMESPACES):
                    r_id = sld_id.attrib.get(f"{{{NAMESPACES['r']}}}id")
                    if r_id and r_id in rel_map:
                        slides.append(rel_map[r_id])
        except Exception:
            pass

        if not slides:
            # Fallback: scan ppt/slides/slide*.xml and sort naturally
            candidates = [n for n in z.namelist() if re.match(r"^ppt/slides/slide\d+\.xml$", n)]
            candidates.sort(key=lambda s: int(re.search(r"\d+", s).group(0)))  # type: ignore
            slides = candidates

        return slides

    def _get_slide_size(self, z: zipfile.ZipFile) -> tuple[int, int]:
        try:
            tree = ET.fromstring(z.read("ppt/presentation.xml"))
            sld_sz = tree.find("p:sldSz", NAMESPACES)
            if sld_sz is not None:
                cx = int(sld_sz.attrib.get("cx", 12192000))
                cy = int(sld_sz.attrib.get("cy", 6858000))
                return cx, cy
        except Exception:
            pass
        return 12192000, 6858000  # Default 16:9 960x540 / 1920x1080

    def _analyze_slide(
        self,
        z: zipfile.ZipFile,
        slide_idx: int,
        slide_file: str,
        slide_w: int,
        slide_h: int,
        report: ValidationReport,
    ) -> SlideInfo:
        info = SlideInfo(index=slide_idx)

        try:
            content = z.read(slide_file)
            root = ET.fromstring(content)
        except Exception as e:
            report.issues.append(
                SlideIssue(
                    slide_index=slide_idx,
                    severity="error",
                    category="structure",
                    message=f"Corrupt slide XML in {slide_file}: {e}",
                )
            )
            return info

        # Check speaker notes
        notes_file = self._find_notes_slide(z, slide_file)
        if notes_file and notes_file in z.namelist():
            info.has_notes = True
            info.notes_text = self._extract_notes_text(z, notes_file)

        # Count elements & scan text for leaked HTML tags
        sp_tree = root.find(".//p:spTree", NAMESPACES)
        if sp_tree is not None:
            # Check shape bounds
            for sp in sp_tree.findall(".//p:sp", NAMESPACES):
                info.shapes_count += 1
                sp_name = ""
                nv_sp_pr = sp.find("p:nvSpPr", NAMESPACES)
                if nv_sp_pr is not None:
                    c_nv_pr = nv_sp_pr.find("p:cNvPr", NAMESPACES)
                    if c_nv_pr is not None:
                        sp_name = c_nv_pr.attrib.get("name", "")

                # Check transform bounds
                sp_pr = sp.find("p:spPr", NAMESPACES)
                if sp_pr is not None:
                    xfrm = sp_pr.find("a:xfrm", NAMESPACES)
                    if xfrm is not None:
                        off = xfrm.find("a:off", NAMESPACES)
                        ext = xfrm.find("a:ext", NAMESPACES)
                        if off is not None and ext is not None:
                            try:
                                x = int(off.attrib.get("x", 0))
                                y = int(off.attrib.get("y", 0))
                                cx = int(ext.attrib.get("cx", 0))
                                cy = int(ext.attrib.get("cy", 0))

                                # Margin buffer: 5% of slide bounds
                                if x + cx > int(slide_w * 1.05) or y + cy > int(slide_h * 1.05):
                                    report.issues.append(
                                        SlideIssue(
                                            slide_index=slide_idx,
                                            severity="warning",
                                            category="overflow",
                                            element_id=sp_name or None,
                                            message=f"Shape `{sp_name}` extends beyond slide boundaries: [x={x}, y={y}, w={cx}, h={cy}] vs slide [{slide_w}x{slide_h}]",
                                        )
                                    )
                            except ValueError:
                                pass

                # Check text body
                tx_body = sp.find("p:txBody", NAMESPACES)
                if tx_body is not None:
                    info.text_boxes_count += 1
                    full_text_parts = []
                    for t in tx_body.findall(".//a:t", NAMESPACES):
                        txt = t.text or ""
                        full_text_parts.append(txt)

                        # Leaked HTML tags check
                        match = LEAKED_TAG_REGEX.search(txt)
                        if match:
                            tag = match.group(0)
                            report.issues.append(
                                SlideIssue(
                                    slide_index=slide_idx,
                                    severity="error",
                                    category="leaked_tag",
                                    element_id=sp_name or None,
                                    message=f"Found leaked/unrendered HTML tag `{tag}` in slide {slide_idx}",
                                    snippet=txt.strip()[:100],
                                )
                            )

                    # Extract slide title
                    if not info.title and full_text_parts:
                        joined = " ".join(full_text_parts).strip()
                        if len(joined) > 0:
                            info.title = joined[:40]

            # Count picture elements
            for _ in sp_tree.findall(".//p:pic", NAMESPACES):
                info.images_count += 1

            # Count graphicFrames (tables, charts, media)
            for gf in sp_tree.findall(".//p:graphicFrame", NAMESPACES):
                info.shapes_count += 1
                if gf.find(".//a:tbl", NAMESPACES) is not None:
                    info.tables_count += 1

        return info

    def _find_notes_slide(self, z: zipfile.ZipFile, slide_file: str) -> Optional[str]:
        # slide_file is e.g. "ppt/slides/slide1.xml"
        slide_dir = Path(slide_file).parent
        slide_name = Path(slide_file).name
        rels_path = f"{slide_dir}/_rels/{slide_name}.rels"

        if rels_path in z.namelist():
            try:
                tree = ET.fromstring(z.read(rels_path))
                for rel in tree.findall("{http://schemas.openxmlformats.org/package/2006/relationships}Relationship"):
                    rel_type = rel.attrib.get("Type", "")
                    if "notesSlide" in rel_type:
                        target = rel.attrib.get("Target", "")
                        # Target is typically "../notesSlides/notesSlide1.xml"
                        resolved = os.path.normpath(os.path.join(str(slide_dir), target))
                        return resolved.replace("\\", "/")
            except Exception:
                pass
        return None

    def _extract_notes_text(self, z: zipfile.ZipFile, notes_file: str) -> str:
        try:
            tree = ET.fromstring(z.read(notes_file))
            texts = []
            # Only speaker notes text body, ignore slide thumbnail / slide number placeholders
            for sp in tree.findall(".//p:sp", NAMESPACES):
                nv_sp_pr = sp.find("p:nvSpPr", NAMESPACES)
                ph = nv_sp_pr.find(".//p:ph", NAMESPACES) if nv_sp_pr is not None else None
                ph_type = ph.attrib.get("type", "") if ph is not None else ""
                # ph type "body" is the notes text
                if ph_type == "body" or ph is None:
                    for t in sp.findall(".//a:t", NAMESPACES):
                        if t.text:
                            texts.append(t.text)
            return "\n".join(texts).strip()
        except Exception:
            return ""

    def render_thumbnails(self, output_dir: Path) -> list[Path]:
        """Attempt to render slides to PNG thumbnails via soffice or macOS QuickLook."""
        output_dir = output_dir.expanduser().resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        rendered: list[Path] = []

        # 1. Try LibreOffice / soffice
        soffice = shutil.which("soffice") or shutil.which("libreoffice")
        if not soffice and sys.platform == "darwin":
            mac_soffice = Path("/Applications/LibreOffice.app/Contents/MacOS/soffice")
            if mac_soffice.is_file():
                soffice = str(mac_soffice)

        if soffice:
            with tempfile.TemporaryDirectory() as tmp:
                tmp_dir = Path(tmp)
                # Convert PPTX -> PDF
                cmd = [soffice, "--headless", "--convert-to", "pdf", "--outdir", str(tmp_dir), str(self.path)]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                pdf_file = tmp_dir / f"{self.path.stem}.pdf"
                if pdf_file.is_file():
                    # Check pdftoppm
                    pdftoppm = shutil.which("pdftoppm")
                    if pdftoppm:
                        prefix = str(output_dir / "slide")
                        cmd2 = [pdftoppm, "-png", "-r", "150", str(pdf_file), prefix]
                        subprocess.run(cmd2, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        rendered = sorted(output_dir.glob("slide-*.png"))
                        if rendered:
                            return rendered

        # 2. Try macOS QuickLook
        if sys.platform == "darwin" and shutil.which("qlmanage"):
            with tempfile.TemporaryDirectory() as tmp:
                cmd = ["qlmanage", "-p", str(self.path), "-o", tmp]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                tmp_path = Path(tmp)
                for ql_img in tmp_path.glob("*.qlpreview/*.png"):
                    dest = output_dir / ql_img.name
                    shutil.copy2(ql_img, dest)
                    rendered.append(dest)
                if rendered:
                    return sorted(rendered)

        return rendered


def print_report(report: ValidationReport, verbose: bool = False) -> None:
    print("\n" + "=" * 65)
    print(f"PPTX VALIDATION REPORT: {Path(report.file_path).name}")
    print("=" * 65)
    status_str = "PASS" if report.error_count == 0 else "FAIL"
    print(f"Status:       [{status_str}]")
    print(f"Slides:       {report.slide_count}")
    print(f"Errors:       {report.error_count}")
    print(f"Warnings:     {report.warning_count}")
    print("-" * 65)

    if report.slides:
        print("Slide Overview:")
        for s in report.slides:
            title = f" - \"{s.title}\"" if s.title else ""
            notes_flag = "[Notes: Yes]" if s.has_notes else "[Notes: None]"
            elem_counts = f"({s.text_boxes_count} text, {s.images_count} img, {s.tables_count} tbl)"
            print(f"  Slide {s.index:2d}: {notes_flag:<14} {elem_counts:<25} {title}")
            if verbose and s.has_notes and s.notes_text:
                indented = "\n".join(f"      {line}" for line in s.notes_text.splitlines()[:3])
                print(f"    Notes:\n{indented}")

    if report.issues:
        print("\nDiagnostics:")
        for issue in report.issues:
            prefix = "[ERROR]" if issue.severity == "error" else "[WARN] "
            slide_tag = f"Slide {issue.slide_index:2d}:" if issue.slide_index > 0 else "Global:  "
            print(f"  {prefix} {slide_tag} {issue.message}")
            if issue.snippet:
                print(f"          Snippet: \"{issue.snippet}\"")
    else:
        print("\nAll checks passed cleanly! No leaked tags or boundary errors detected.")

    if report.rendered_images:
        print("\nRendered Slide Images:")
        for img in report.rendered_images:
            print(f"  - {img}")
    print("=" * 65 + "\n")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a compiled PPTX presentation file")
    parser.add_argument("pptx", type=Path, help="Path to input .pptx file")
    parser.add_argument("--expected-pages", type=int, default=None, help="Fail if page count does not match")
    parser.add_argument("--check-notes", action="store_true", help="Warn if any slide lacks speaker notes")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors (exit code != 0)")
    parser.add_argument("--render-images", type=Path, nargs="?", const=Path("./preview_slides"), help="Directory to export slide preview images")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print verbose slide notes and details")
    args = parser.parse_args(argv)

    try:
        validator = PptxValidator(args.pptx)
        report = validator.validate(
            expected_pages=args.expected_pages,
            check_notes=args.check_notes,
        )

        if args.render_images:
            out_dir = args.render_images
            imgs = validator.render_thumbnails(out_dir)
            report.rendered_images = [str(p) for p in imgs]

        if args.json:
            payload = {
                "filePath": report.file_path,
                "isValid": report.is_valid,
                "slideCount": report.slide_count,
                "errorCount": report.error_count,
                "warningCount": report.warning_count,
                "slides": [asdict(s) for s in report.slides],
                "issues": [asdict(i) for i in report.issues],
                "renderedImages": report.rendered_images,
            }
            print(json.dumps(payload, indent=2))
        else:
            print_report(report, verbose=args.verbose)

        if report.error_count > 0:
            return 1
        if args.strict and report.warning_count > 0:
            return 2
        return 0

    except Exception as err:
        print(f"[open-pptd-skill] Validation failed to run: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
