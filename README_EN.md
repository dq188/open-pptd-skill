# Open PPTD (`open-pptd`)

[简体中文](README.md) | [English](README_EN.md)

[![GitHub Release](https://img.shields.io/github/v/release/shiquda/open-pptd-skill?label=release)](https://github.com/shiquda/open-pptd-skill/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

An open-source full-stack presentation suite based on the **PPTD** (Declarative Presentation Language) specification and a high-performance native Rust compiler. Integrates both the **native compiler engine (`open-pptd` / `slideforge` CLI)** and an **out-of-the-box AI Coding Agent skill (Agent Skill)** in a unified repository.

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
# Install to local Agent environment via npm / npx:
npx github:shiquda/open-pptd-skill install -y

# Or install to a specific agent directory:
npx github:shiquda/open-pptd-skill install --target ~/.claude/skills
```
### Option 3: Compile from Source via Cargo

The repository contains the complete Rust source code. You can compile and install both `open-pptd` and `slideforge` CLI tools directly:

```bash
cargo install --git https://github.com/shiquda/open-pptd-skill.git
```

---

## CLI & Workflow

After installation, `open-pptd` and `slideforge` commands are identical and can be used interchangeably:

### 1. Static Syntax & Semantic Validation (`check`)

```bash
open-pptd check deck.pptd
```

### 2. Compile PPTD to Native PPTX (`build`)

```bash
# Direct CLI build:
open-pptd build deck.pptd -o output.pptx

# Or via Python script wrapper:
python3 skills/open-pptd/scripts/export_pptx.py deck.pptd -o output.pptx [--pdf]
```

### 3. Decompile Existing PPTX to PPTD (`convert`)

```bash
# Direct CLI convert:
open-pptd convert existing_deck.pptx ./project_dir/

# Or via Python wrapper:
python3 skills/open-pptd/scripts/convert_pptx.py existing_deck.pptx -o ./project_dir/
```
### 3. Image Slices & Overview Montage (`export_images`)

```bash
python3 skills/open-pptd/scripts/export_images.py deck.pptd -o qa-images/
```

### 4. Comprehensive Validation & QA (`validate_pptx`)

```bash
python3 skills/open-pptd/scripts/validate_pptx.py output.pptx --expected-pages 8 --check-notes
```

---

## 🔒 `.sync.hash` Overwrite Guard & Bi-directional Sync

`slideforge` maintains a `.sync.hash` ledger in every project directory:
- **Overwrite Guard**: `build` verifies the live SHA-256 of an existing target `.pptx`. If it was altered externally, `build` refuses to overwrite (exit code 2) to protect uncommitted manual work.
- **Smart Skip**: `convert` verifies the source `.pptx` hash and skips re-conversion (`unchanged → skipped convert`) if it has not changed.

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

## License & Attribution

This project is licensed under the [MIT License](LICENSE).

### Acknowledgments & Upstream Attributions:
1. **`open-kimi-ppt-skill`**:
   Originally conceived and authored by Binaryify Zhuang under the MIT License ([GitHub](https://github.com/acnlie/open-kimi-ppt-skill)). We gratefully acknowledge the pioneering work on PPTD declarative slide concepts and Agent skills.
2. **`slideforge`**:
   The underlying native Rust compiler engine was originally created by **meatRoll** ([`meatRoll/slideforge`](https://github.com/meatRoll/slideforge), MIT License). Further secondary development by shiquda and contributors added rich text formatting (`<u>`, `<s>`), tokenized academic LaTeX math rendering, PowerPoint speaker notes (`notesSlide`), expanded Font Awesome icon datasets, and strict semantic validation, before being fully integrated into Open PPTD. We gratefully acknowledge meatRoll's foundational work.
3. **Font Awesome 6 (Solid Icons)**:
   Vector icons embedded in the compiler are from Font Awesome 6.7.2 under CC BY 4.0 ([License](https://fontawesome.com/license/free)).
