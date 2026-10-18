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
slideforge convert <INPUT_PPTX> [OPTIONS]
```

**Arguments:**
- `<INPUT_PPTX>`: Path to input PowerPoint presentation.

**Options:**
- `-o, --output <DIR>`: Output directory for the generated PPTD project.

**Example:**
```bash
slideforge convert input.pptx -o ./project_dir
```

---

### `slideforge inspect`
Prints structured metadata and AST statistics about a PPTD project or PPTX file.

```bash
slideforge inspect <PATH>
```
