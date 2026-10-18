---
name: open-pptd-skill
description: Create, edit, reverse-decompile, and export presentations using the open PPTD format and native slideforge compiler. For every PPT task, default deliverables are BOTH (1) a self-contained PPTD project folder (deck.pptd manifest + pages/*.page) and (2) a locally compiled native .pptx with vector shapes, connector arrows, LaTeX math formulas, speaker notes, and native tables. Completely offline — zero dependency on browser automation or cloud logins.
---

# open-pptd-skill: Native Declarative Presentation Engine

`open-pptd-skill` is an open-source presentation toolchain built around the **PPTD** (Declarative Presentation Language) specification and the high-performance **slideforge** native Rust compiler. It provides AI coding agents with a clean, modular YAML abstraction over OOXML and produces real, fully editable `.pptx` presentations offline in milliseconds.

---

## ⚡ Agent Quickstart (3 步极速开工)

Agent 接到任何 PPT 创建或修改任务后，直接按以下标准 3 步闭环执行：

```bash
# 1. 确保 slideforge 本地编译器就绪 (已安装即刻返回，未安装则自动下载或编译)
python3 skills/open-pptd/scripts/install_binary.py

# 2. 编写或修改 PPTD 源码后，运行严格语义校验 (检查字段、颜色、$token、图片存在性、溢出)
slideforge check <project_dir>/deck.pptd

# 3. 编译并使用质检脚本验收 (检查页数、无遗漏HTML标签、备注完整性、溢出检测)
slideforge build <project_dir>/deck.pptd -o <output.pptx>
python3 skills/open-pptd/scripts/validate_pptx.py <output.pptx> --expected-pages <N>
```

---

## 📋 功能支持矩阵 (Supported Feature Matrix)

在生成 PPTD 时，**严格遵守以下能力边界**。不支持的标签和元素会在 `check` 和 `build` 时被拦截报错，切勿猜测或硬套 Web HTML 语法：

| 功能类别 | 支持状态 | 规范与说明 / 替代指引 |
|---|---|---|
| **文本与排版** | ✅ 完全支持 | `fontSize`, `color`, `bold`, `italic`, `lineHeight`, `align`, `valign`, `letterSpacing`, `shape`, `padding` |
| **富文本标签** | ✅ 支持 | `<p>`, `<span>`, `<b>`/`<strong>`, `<i>`/`<em>`, `<u>` (下划线), `<s>`/`<del>`/`<strike>` (删除线), `<code>`, `<latex>` / `\( ... \)` (原生公式) |
| **列表与超链接标签** | ❌ **严禁使用** | `<ul>`, `<ol>`, `<li>`, `<a>` **不受支持**！编译器与校验器会**直接拦截报错**。列表必须写成常规段落并手写序号（如 `1. 第一点` 或 `• 第一点`） |
| **演讲者备注 (Notes)** | ✅ 完全支持 | 页面根级属性 `notes: "备注内容..."`，自动生成原生 PowerPoint 演讲者备注 (`notesSlide`) |
| **图表 / Charts** | ❌ **编译器尚未支持** | `elementType: chart` 会在 `check` 和 `build` 时被**直接报错拦截**。替代方案：使用原生表格 (`elementType: table`) 呈现数据，或使用脚本将图表导出为图片 (`elementType: image`) |
| **矢量形状 / Shapes** | ✅ 完全支持 | `rect`, `roundRect`, `ellipse`, `triangle`, `diamond`, `rightArrow`, `pentagon`, `hexagon`, `callout` 等 DrawingML 预设形状 |
| **线条与箭头** | ✅ 完全支持 | `elementType: line`，支持相对坐标 `points: "0,0 dx,dy"`，以及两端箭头 `arrow: [start, end]` (可选: `triangle`, `stealth`, `arrow`, `diamond`, `oval`, `none`) |
| **表格 / Tables** | ✅ 完全支持 | 原生 PowerPoint 表格 (`<a:tbl>`)，支持 `columnWidths`、`rowHeights`、单元格跨行跨列、边框样式、底色填充 |
| **图片与媒体** | ✅ 完全支持 | 统一存放在 `assets/` 目录；支持透明通道、裁切 `crop`、填充模式 `fit: {mode: cover/contain}`、边框与阴影 |
| **主题色彩与继承** | ✅ 完全支持 | `theme.colors` 统一声明命名色，元素中通过 `"$colorKey"` 引用；引用未定义颜色会在 `check` 阶段拦截 |
| **静态质检与校验** | ✅ 严格校验 | `slideforge check` 自动拦截拼写错误、非法形状名、无效色彩引用、缺失的媒体文件以及潜在文字溢出 |

---

## 🔒 `.sync.hash` 机制与双向同步注意

`slideforge` 在项目根目录使用旁车文件 `.sync.hash` 记录项目合法写入时各文件的 SHA-256 哈希：

1. **防覆盖守卫 (Overwrite Guard)**：
   - 执行 `slideforge build deck.pptd -o presentation.pptx` 时，若输出文件 `presentation.pptx` 已存在，编译器会比对当前文件的实时哈希与 `.sync.hash` 的记录。
   - **若文件被外部程序或人类手工编辑过**，编译器会**拒绝覆写**（退出码 2，提示 `changed after its last recorded sync point`），防止破坏未知修改。
   - **如何解决**：若确认需要以 PPTD 代码强制覆写，删除已有 `.pptx` 文件后再运行 `build` 即可。
2. **跳过未变更的 Convert**：
   - 执行 `slideforge convert presentation.pptx output_dir/` 时，若源 PPTX 的 SHA-256 与上次记录一致，编译器将自动输出 `unchanged → skipped convert` 并跳过，保护本地已有的 PPTD 源码不被重复覆写。

---

## 交付规范 (Deliverables Contract)

除非用户明确声明不需要，每个 PPT 制作或修改任务必须交付：
1. **可编辑的 PPTD 源码工程**：包含 `deck.pptd` 清单文件、`pages/*.page` 页面描述、以及 `assets/` 资源目录。
2. **编译出的原生 `.pptx` 成品**：通过 `slideforge build` 生成。
3. **质检通过报告**：通过 `validate_pptx.py` 验证无遗漏标签和结构异常。

---

## PPTD 工程目录结构

```text
my_presentation/
├── deck.pptd            # 演示文稿清单：画幅比例、主题色、全局文本样式、页面清单
├── pages/
│   ├── 01_cover.page    # 单页声明式 AST (YAML 格式)
│   ├── 02_intro.page
│   └── ...
└── assets/              # 本地引用的图片/多媒体文件 (统一命名为 assets/，禁止使用 media/)
```

### 1. 清单文件 (`deck.pptd`) 示例
```yaml
version: v2
title: "Emby 家庭影音库搭建与调优"
size: [960, 540]         # 16:9 标准画布尺寸 (像素坐标体系)
theme:
  colors:
    ink: "#1A1A1A"
    paper: "#F7F5EE"
    primary: "#2563EB"
    accent: "#52B788"
  textStyles:
    title:
      fontFamily: "思源宋体"
      fontSize: 28
      bold: true
      color: "$ink"
    body:
      fontFamily: "思源黑体"
      fontSize: 15
      lineHeight: 1.45
      color: "$ink"
pages:
  - pages/01_cover.page
  - pages/02_intro.page
```

### 2. 单页文件 (`pages/01_cover.page`) 示例
```yaml
pageType: cover
background: { type: solid, color: "$paper" }
notes: |
  各位好，今天为大家分享家庭影音库的搭建方案，核心关注网络直连与硬件转码。
elements:
  - elementId: heading
    elementType: text
    bounds: [60, 120, 840, 80]
    content:
      style: "$title"
      text: "Emby 家庭影音库搭建与调优"
  - elementId: sep-line
    elementType: line
    bounds: [60, 210, 180, 2]
    points: "0,0 180,0"
    arrow: [null, "triangle"]
    border: { style: solid, width: 2, color: "$primary" }
```

---

## 常用工具链命令

### 1. 安装 / 确保编译器就绪
```bash
python3 skills/open-pptd/scripts/install_binary.py
# 如需强制重新下载: python3 skills/open-pptd/scripts/install_binary.py --force
```

### 2. 严格语义检查 (Check)
```bash
slideforge check deck.pptd
```

### 3. 编译工程为 PPTX (Build)
```bash
# 推荐直接使用 slideforge:
slideforge build deck.pptd -o output.pptx

# 或通过 Python 包装脚本:
python3 skills/open-pptd/scripts/export_pptx.py deck.pptd -o output.pptx [--pdf]
```

### 4. 逆向反编译 PPTX 为 PPTD 工程 (Convert)
注意：`slideforge convert` 接收两个位置参数，**不要加 `-o` 参数**：
```bash
# 原生命令格式: slideforge convert <INPUT.pptx> <OUTPUT_DIR>
slideforge convert input.pptx my_project_dir/

# 或通过 Python 包装脚本:
python3 skills/open-pptd/scripts/convert_pptx.py input.pptx -o my_project_dir/
```

### 5. 成品全面验证与视觉质检 (Validate)
```bash
python3 skills/open-pptd/scripts/validate_pptx.py output.pptx --expected-pages 8 --check-notes
```

---

## 排版与设计最佳实践

1. **字体与跨平台回退**：
   - 严谨/学术/出版风格：主标题采用 `思源宋体` (自动映射西文 `Georgia` / 东亚 `SimSun`)。
   - 商业/现代科技风格：采用 `PingFang SC` / `Microsoft YaHei` (自动映射西文 `Arial`)。
2. **连接线与箭头 (Line & Arrow)**：
   - 线条使用相对坐标定义 `points: "0,0 dx,dy"`，起点通常为 `0,0`。
   - 箭头使用二元数组 `arrow: [startArrow, endArrow]`，例如 `arrow: [null, "triangle"]` 或 `arrow: ["stealth", null]`。
3. **表格 (Table)**：
   - 必须提供 `columnWidths` (各列相对占比，和必须为 1.0) 和 `rowHeights`。
   - 单元格内文字使用 `text: "内容"`，支持多行文本与底色。
4. **多媒体与图片 (Assets)**：
   - 所有图片均应放置在工程的 `assets/` 文件夹下，禁止直接散落在根目录。
   - 严禁在页面文件中将图片路径写为绝对路径，统一写为相对工程根目录的路径（如 `assets/banner.png`）。
