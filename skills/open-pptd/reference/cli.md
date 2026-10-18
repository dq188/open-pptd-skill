# slideforge CLI Reference

`slideforge` is the native compiler toolchain for PPTD presentations.

---

## Installation

### Automatic Binary Download
```bash
python3 scripts/install_binary.py
# Or curl one-liner:
curl -fsSL https://raw.githubusercontent.com/shiquda/open-pptd-skill/main/skills/open-pptd/scripts/install_binary.sh | bash
```

### From Source (via Cargo)
```bash
cargo install --git https://github.com/shiquda/slideforge.git
```

---
### `slideforge check`
Performs strict semantic and structural validation of a PPTD project without building.

```bash
slideforge check <MANIFEST>
```

Checks for:
- Unknown or misspelled YAML fields on page and element definitions
- Invalid DrawingML preset shape names with automatic suggestions
- Undefined theme color `$colorKey` references
- Missing local image or media files
- Unsupported rich text tags (such as `<ul>`, `<ol>`, `<li>`, `<a>`)
- Unsupported element types (such as `chart`)
- Potential vertical or horizontal text box overflows

---


## Commands

### `slideforge build`
Compiles a PPTD manifest into a native OpenXML `.pptx` presentation.

```bash
slideforge build <MANIFEST> [OPTIONS]
```

**Arguments:**
- `<MANIFEST>`: Path to `deck.pptd` manifest.

**Options:**
- `-o, --output <PATH>`: Output `.pptx` file path (default: `<title>.pptx` or `presentation.pptx`).

**Example:**
```bash
slideforge build deck.pptd -o my_slides.pptx
```

---

### `slideforge convert`
Decompiles an existing PowerPoint `.pptx` file into a clean, editable PPTD project.

```bash
slideforge convert <INPUT_PPTX> <OUTPUT_DIR>
```

**Arguments:**
- `<INPUT_PPTX>`: Path to input PowerPoint presentation.
- `<OUTPUT_DIR>`: Output directory for the generated PPTD project.

**Example:**
```bash
slideforge convert input.pptx ./project_dir
```

---

### `slideforge dump`
Dumps a diagnostic summary of the parsed project structure and element counts to stdout.

```bash
slideforge dump <MANIFEST>
```
