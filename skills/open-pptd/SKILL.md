---
name: open-pptd-skill
description: Create, edit, reverse-decompile, and export presentations using the open PPTD format and native slideforge compiler. For every PPT task, default deliverables are BOTH (1) a self-contained PPTD project folder (deck.pptd manifest + pages/*.page) and (2) a locally compiled native .pptx with vector shapes, connector arrows, LaTeX math formulas, and native tables. Completely offline — zero dependency on Kimi web frontend, browser automation, or cloud logins.
---

# open-pptd-skill: Native Declarative Presentation Engine

`open-pptd-skill` is an open-source presentation toolchain built around the **PPTD** (Declarative Presentation Language) specification and the high-performance **slideforge** native Rust compiler. It provides AI coding agents with a clean, modular YAML abstraction over OOXML and produces real, fully editable `.pptx` presentations offline in milliseconds.

## Key Capabilities

1. **100% Offline & Private**: Zero external network or browser dependencies during compilation. No Chromium, Playwright, or cloud logins required.
2. **Native OpenXML Fidelity**: Emits real DrawingML shapes, linear connectors with arrowheads, native PowerPoint tables (`<a:tbl>`), and LaTeX math formatting with precise baseline shifts and italics.
3. **Bi-directional Pipeline**:
   - **Build**: Compiles `deck.pptd` into native `.pptx` via `slideforge build`.
   - **Convert**: Decompiles existing `.pptx` files into clean, editable `.pptd` projects via `slideforge convert`.
4. **Automated Binary Provisioning**: Built-in installer (`scripts/install_binary.py` / `install_binary.sh`) automatically downloads pre-compiled native binaries for macOS (Apple Silicon & Intel), Linux, and Windows from GitHub Releases.

---

## Deliverables Contract

Unless the user explicitly opts out, every presentation task MUST deliver:
1. **The editable PPTD project folder**: `deck.pptd` manifest plus `pages/*.page` and local assets.
2. **The compiled native `.pptx` file**: Generated via `slideforge build`.
3. *(Optional)* A PDF copy and visual preview images if LibreOffice / pdftoppm are installed in the local environment.

---

## PPTD Format Overview

A PPTD project is structured as:
```text
project_dir/
├── deck.pptd            # Manifest: size, theme, global textStyles, page list
├── pages/
│   ├── 01_cover.page    # Individual slide YAML AST
│   ├── 02_intro.page
│   └── ...
└── assets/              # Local images/media referenced by pages
```

### Manifest (`deck.pptd`) Example
```yaml
version: v2
title: "Project Title"
size: [960, 540]         # 16:9 standard canvas (scaled by viewer/compiler)
theme:
  colors:
    ink: "#1A1A1A"
    paper: "#F7F5EE"
    accent: "#1F4E38"
  textStyles:
    title:
      fontFamily: "思源宋体"
      fontSize: 28
      bold: true
      color: "$ink"
    body:
      fontFamily: "思源宋体"
      fontSize: 15
      lineHeight: 1.45
      color: "$ink"
pages:
  - pages/01_cover.page
  - pages/02_intro.page
```

### Page File (`pages/01_cover.page`) Example
```yaml
pageType: cover
background: { type: solid, color: "$paper" }
elements:
  - elementId: heading
    elementType: text
    bounds: [60, 120, 840, 80]
    content:
      style: "$title"
      text: "从语义先验到物理动作"
  - elementId: line-sep
    elementType: line
    bounds: [60, 220, 120, 2]
    points: "0,0 120,0"
    border: { style: solid, width: 2, color: "$accent" }
```

---

## Toolchain & Commands

### 1. Ensure `slideforge` Compiler
Run the automated binary installer if `slideforge` is not yet on your `PATH`:
```bash
python3 scripts/install_binary.py
# Or one-line shell installation:
curl -fsSL https://raw.githubusercontent.com/shiquda/open-pptd-skill/main/skills/open-pptd/scripts/install_binary.sh | bash
```

### 2. Compile PPTD to PPTX
```bash
# Using slideforge CLI directly:
slideforge build deck.pptd -o output.pptx

# Or via Python script wrapper:
python3 scripts/export_pptx.py deck.pptd -o output.pptx [--pdf]
```

### 3. Decompile PPTX to PPTD
```bash
# Reverse-engineer an existing presentation:
slideforge convert input.pptx -o project_dir/

# Or via Python script wrapper:
python3 scripts/convert_pptx.py input.pptx -o project_dir/
```

### 4. Image Export & Multi-Page Visual QA
```bash
python3 scripts/export_images.py deck.pptd -o qa-images/
```

---

## Best Practices for Slide Production

1. **Typography & Font Fallback**:
   - For academic / book aesthetics: set primary font to `思源宋体` (automatically mapped to safe `SimSun` on East Asian systems and `Georgia` for Latin).
   - For business / tech aesthetics: set primary font to `Microsoft YaHei` / `PingFang SC` (automatically mapped to safe `Arial` for Latin).
2. **Formula Syntax**:
   - Inline math formulas are written as `\( h(s_t) \ge 0 \)`.
   - Variables are rendered in italics, while subscripts (`_t`) apply baseline shifts automatically.
3. **Connectors and Arrows**:
   - Use two-point straight lines `points: "0,0 dx,dy"` with `arrow: [null, "arrow"]` or `arrow: ["stealth", null]`.
   - Avoid manual multi-segment lines that confuse office software layout engines.
4. **Tables**:
   - Use `elementType: table` with explicit `columnWidths` and `rowHeights`.
   - Cell contents support rich text `text: "<p>Content</p>"`, cell merging (`rowSpan`/`colSpan`), borders, and background fills.
