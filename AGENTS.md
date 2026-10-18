# AGENTS.md: open-pptd-skill Agent 指南

欢迎来到 `open-pptd-skill` 仓库。对于任何 PPT 创建、编辑与交付任务，请严格遵守以下操作守则与标准流程。

---

## ⚡ Agent Quickstart (极速闭环)

接到 PPT 任务后，直接运行以下标准化流程：

```bash
# 1. 确保编译器已就绪
python3 skills/open-pptd/scripts/install_binary.py

# 2. 严格语义与结构校验
slideforge check <project_dir>/deck.pptd

# 3. 极速编译为原生 PPTX
slideforge build <project_dir>/deck.pptd -o <output.pptx>

# 4. 成品质量与合规性验收 (无泄漏标签、页数与备注检查)
python3 skills/open-pptd/scripts/validate_pptx.py <output.pptx> --expected-pages <N> --check-notes
```

---

## 📚 建议阅读顺序 (Reading Order)

在编写 PPTD 源码前，请按序查阅：
1. `skills/open-pptd/reference/slides_categories.md` ➔ 确定 PPT 业务场景与受众
2. `skills/open-pptd/reference/slides_categories/<scenario>.md` ➔ 掌握版式结构与密度红线
3. `theme.md` (或 `theme_EN.md`) ➔ 选用预设 30+ 种专业主题配色方案
4. `skills/open-pptd/reference/fonts.md` ➔ 查阅跨平台字体映射与回退机制
5. `skills/open-pptd/SKILL.md` 与 `skills/open-pptd/reference/pptd.md` ➔ 语法规范（严禁使用暂不支持的元素）

---

## ⚠️ 严禁使用的非支持特性 (Feature Boundaries)

以下语法目前在 `slideforge` 编译器中**不受支持**，编译器与质检脚本会**直接拦截报错**：
- ❌ **严禁使用 HTML 列表与超链接标签**：`<ul>`, `<ol>`, `<li>`, `<a>`。
  - 列表写法：使用常规段落配合文字符号（如 `• 第一点` 或 `1. 第一点`）。
  - 超链接写法：使用纯文本 URL 或在页脚使用普通文本标注来源（如 `来源: IDC (2026)`）。
- ❌ **严禁使用图表元素**：`elementType: chart`。
  - 替代方案：使用原生表格 `elementType: table`，或使用外部脚本渲染为图片后以 `elementType: image` 引入。
- ❌ **严禁使用上标/下标 HTML 标签**：`<sup>`, `<sub>`。
  - 替代方案：使用原生 LaTeX 公式 `\( x^2 \)`、`\( H_2O \)`。

---

## 🛠️ 异常分支与恢复指引 (Failure Branches)

1. **下载或网络受限**：
   - `install_binary.py` 会自动回退至本地 `cargo install --git`。
   - 若本地无 Rust 工具链，可从 Release 页面手动下载解压至 `~/.local/bin/slideforge`。
2. **`slideforge check` 报错**：
   - 检查 `shapeName` 是否拼写错误（必须为 DrawingML 预设形状如 `roundRect`, `rect`, `ellipse`, `diamond` 等）。
   - 检查 `$color` 引用是否已在 `theme.colors` 中声明。
   - 检查图片路径是否存在（统一放置于 `assets/` 目录）。
3. **`slideforge build` 退出码 2 (.sync.hash 覆盖保护)**：
   - 说明目标 `.pptx` 在上次编译后被外部程序编辑过。若确认以 PPTD 源码为准，先 `rm <output.pptx>` 再重新 build。
4. **`validate_pptx.py` 报错**：
   - 若报 `Leaked HTML tags`，排查源码并移除 `<ul>`/`<li>`/`<a>` 标签。
   - 若页数不符，排查 `deck.pptd` 中的 `pages` 列表。
