# Math & LaTeX Formulas in PPTD

`open-pptd-skill` and `pptd` support inline LaTeX mathematics. Formulas are parsed into structured DrawingML text runs with authentic typographical formatting.

---

## Syntax

Inline formulas are delimited by `\( ... \)` inside paragraph text:

```yaml
- elementId: formula-box
  elementType: text
  bounds: [56, 300, 848, 40]
  content:
    text: "<p>安全前向不变集　\\(h(s_t) \\ge 0\\)　严格定义安全集合</p>"
```

### Complex Formula Example
```yaml
- elementId: policy-box
  elementType: text
  bounds: [572, 244, 332, 44]
  content:
    text: "<p>策略输出：\\(A_t \\sim \\pi_\\theta(A_t \\mid o_{\\le t}, \\ell, q_t)\\)</p>"
```

---

## Typography Rules Applied by pptd

1. **Variables**: Single-letter variables (like $s, t, A, \ell, q, h$) are automatically formatted in mathematical italics (`<a:rPr i="1">`).
2. **Subscripts**: Subscript expressions (`_t`, `_{t+1}`, `_{\le t}`) automatically have their baseline lowered by 25% (`baseline="-25000"`) and font size scaled to 70%, preserving correct typographical proportions.
3. **Symbols**: Standard TeX symbols like `\ge` ($\ge$), `\le` ($\le$), `\sim` ($\sim$), `\mid` ($\mid$), `\theta` ($\theta$), `\pi` ($\pi$) are converted to their standard Unicode mathematical counterparts with proper surrounding spacing.
