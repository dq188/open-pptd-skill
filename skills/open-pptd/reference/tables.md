# Native Tables in PPTD & slideforge

`open-pptd-skill` supports full native PowerPoint tables (`<a:tbl>`), with bi-directional support:
1. **Forward compilation**: `slideforge build` compiles PPTD `elementType: table` into a native OpenXML table `graphicFrame`.
2. **Reverse decompilation**: `slideforge convert` extracts PPTX tables back into clean PPTD YAML.

---

## AST Structure

A table is an element on a page with `elementType: table`:

```yaml
- elementId: comparison-tbl
  elementType: table
  bounds: [56, 170, 848, 230]       # [x, y, width, height]
  columnWidths: [0.18, 0.26, 0.26, 0.30] # Proportions or EMU normalized
  rowHeights: [0.18, 0.20, 0.20, 0.20, 0.22]
  style: "$tblStyle"               # Optional theme reference
  rows:
    - - text: "<p><strong>模型</strong></p>"
        align: [center, middle]
        fill: { type: solid, color: "$greenDeep" }
        color: "$white"
      - text: "<p><strong>动作表示</strong></p>"
        align: [center, middle]
        fill: { type: solid, color: "$greenDeep" }
        color: "$white"
      - text: "<p><strong>动作头融合</strong></p>"
        align: [center, middle]
        fill: { type: solid, color: "$greenDeep" }
        color: "$white"
      - text: "<p><strong>训练数据</strong></p>"
        align: [center, middle]
        fill: { type: solid, color: "$greenDeep" }
        color: "$white"
    - - text: "<p><strong>RT-2</strong></p>"
        align: [center, middle]
      - text: "<p>离散分词 256 桶</p>"
      - text: "<p>共享词表自回归</p>"
      - text: "<p>轨迹 + 图文联合微调</p>"
```

---

## Cell Attributes

| Attribute | Type | Description |
|---|---|---|
| `text` | string | Rich text content (`<p>`, `<span>`, `<strong>`, `<em>`) |
| `align` | `[hAlign, vAlign]` | Horizontal (`left`, `center`, `right`) and vertical (`top`, `middle`, `bottom`) alignment |
| `fill` | object | Cell fill (`{ type: solid, color: "#..." }`) |
| `color` | string | Text color override |
| `fontSize` | number | Font size in points |
| `bold` | bool | Bold font weight |
| `italic` | bool | Italic font style |
| `rowSpan` | number | Vertical cell merge count |
| `colSpan` | number | Horizontal cell merge count |
| `border` | object | Cell border styles (`style`, `width`, `color`) |
