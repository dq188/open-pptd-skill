# open-pptd-skill

[简体中文](README.md) | [English](README_EN.md)

[![GitHub Release](https://img.shields.io/github/v/release/shiquda/slideforge?label=slideforge)](https://github.com/shiquda/slideforge/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An open-source full-stack presentation toolchain based on the **PPTD** (Declarative Presentation Language) specification and the high-performance native Rust compiler **slideforge**.

Designed for AI Coding Agents (Claude Code, Codex, Cursor, WorkBuddy, Multica, etc.), **completely removing any dependency on the legacy Kimi web frontend, headless browser sessions, cookies, or cloud authentication**. Compiles and reverse-decompiles native OpenXML `.pptx` presentations 100% offline with sub-second execution speeds.

---

## Key Features

- 🚀 **100% Offline & High-Speed Compilation**: Zero cloud requests, zero browser automation. Emits genuine OpenXML presentations in <0.5s for 20-slide decks.
- 📐 **DrawingML Vector Fidelity**: Renders native vector shapes, straight connector lines with directional arrowheads (`<a:tailEnd type="triangle"/>`), gradient fills, and precise line spacing.
- 🔢 **Native LaTeX Mathematics**: Full inline LaTeX support (`\( h(s_t) \ge 0 \)`), with automatic variable italics and baseline shifts for subscripts.
- 📊 **Bi-Directional Native Tables**: First-class support for PowerPoint `<a:tbl>` elements with cell merging (`rowSpan`/`colSpan`), borders, and background fills; seamlessly decompiles existing tables back to PPTD.
- 🔤 **Cross-Platform Safe Font Fallbacks**: Maps fonts to safe system-installed typefaces across macOS and Windows (e.g. Source Han Serif maps safely to `SimSun` + `Georgia`), eliminating cursive handwriting fallback artifacts.
- 📦 **Automated Binary Installation**: Downloads prebuilt binaries for macOS (Apple Silicon / Intel), Linux (x86_64 / arm64), and Windows on demand.

---

## Quick Installation

### Option 1: Automatic Binary Download (Recommended)

```bash
# One-line curl installer for macOS and Linux:
curl -fsSL https://raw.githubusercontent.com/shiquda/open-pptd-skill/main/skills/open-pptd/scripts/install_binary.sh | bash

# Or via Python script:
python3 skills/open-pptd/scripts/install_binary.py
```

### Option 2: Register Skill for AI Agents

```bash
# Non-interactive install to shared skills directory:
npx open-pptd-skill install -y

# Or install to a specific agent directory:
npx open-pptd-skill install --target ~/.claude/skills
```

### Option 3: Compile from Source via Cargo

```bash
cargo install --git https://github.com/shiquda/slideforge.git
```

---

## CLI & Workflow

### 1. Compile PPTD to Native PPTX (`build`)

```bash
# Direct slideforge CLI:
slideforge build deck.pptd -o output.pptx

# Or via Python wrapper:
python3 skills/open-pptd/scripts/export_pptx.py deck.pptd -o output.pptx [--pdf]
```

### 2. Decompile Existing PPTX to PPTD (`convert`)

```bash
# Decompile presentation into a modular project directory:
slideforge convert input.pptx -o ./project_dir/

# Or via Python wrapper:
python3 skills/open-pptd/scripts/convert_pptx.py input.pptx -o ./project_dir/
```

### 3. Image Slices & Overview Montage (`export_images`)

```bash
python3 skills/open-pptd/scripts/export_images.py deck.pptd -o qa-images/
```

---

## Documentation References

Detailed specifications are available under `skills/open-pptd/reference/`:
- [pptd.md](skills/open-pptd/reference/pptd.md): Core PPTD v2 DSL AST and element definitions
- [shapes.md](skills/open-pptd/reference/shapes.md): Vector shape library and parameter specifications
- [fonts.md](skills/open-pptd/reference/fonts.md): Cross-platform typography and font fallback mapping
- [tables.md](skills/open-pptd/reference/tables.md): Native PowerPoint table structure and styling
- [math.md](skills/open-pptd/reference/math.md): LaTeX mathematical formula formatting
- [cli.md](skills/open-pptd/reference/cli.md): CLI command reference and options

---

## License

This project is licensed under the [MIT License](LICENSE).
