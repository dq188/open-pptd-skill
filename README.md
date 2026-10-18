# Open PPTD (`open-pptd`)

[简体中文](README.md) | [English](README_EN.md)

[![GitHub Release](https://img.shields.io/github/v/release/shiquda/open-pptd-skill?label=release)](https://github.com/shiquda/open-pptd-skill/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![CI](https://github.com/shiquda/open-pptd-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/shiquda/open-pptd-skill/actions/workflows/ci.yml)
[![Node >= 18](https://img.shields.io/badge/node-%3E%3D18-brightgreen)](https://nodejs.org)
[![Rust >= 1.85](https://img.shields.io/badge/rust-%3E%3D1.85-orange)](https://www.rust-lang.org)

**Open PPTD** 是面向 AI Coding Agent（Claude Code、Cursor、Codex、WorkBuddy、Multica 等）与开发者的开源声明式幻灯片套件。基于开放的 **PPTD**（Declarative Presentation Language）YAML 规范，提供 **100% 本地离线、毫秒级响应** 的原生 Rust 编译器（`pptd` CLI）与开箱即用的 Agent 技能。

彻底剔除对网页端会话、无头浏览器、Cookie 凭证与云端接口的脆弱依赖，在本地毫秒级生成真实可编辑、带矢量图形与数学公式的原生 `.pptx` 成品及双向工程。

---

## 🖼️ 作品展示 (Showcase)

Open PPTD 坚持 **「PPTD 源码工程 + 原生可编辑 PPTX」** 双交付路线。无论是商业路演、前沿技术汇报还是学术研讨，均能稳定产出大师级排版：

| 小米 YU7 商业级发布会演示（图文排版） | DJI Pocket 4 产品发布演示（全景视觉） |
| :---: | :---: |
| [![小米 YU7 导出效果](docs/images/example-yu7-pptx.png)](docs/images/example-yu7-pptx.png) | [![DJI Pocket 4 导出效果](docs/images/example-dji-pocket4-pptx.png)](docs/images/example-dji-pocket4-pptx.png) |

| DeepSeek Liquid Glass 风格演示 | 极简 Starter 标杆模版（表格/连线/备注） |
| :---: | :---: |
| [![DeepSeek Liquid Glass 风格](docs/images/example-deepseek-liquid-glass.png)](docs/images/example-deepseek-liquid-glass.png) | [![Starter 标杆模版](example/starter/starter_expected.png)](example/starter/starter_expected.png) |

---

## 💡 为什么选择 Open PPTD？

目前常见的 AI 幻灯片方案大多存在明显痛点：直接调用代码库拼接坐标容易错位，整页画图模式文字无法二次编辑，而网页 HTML 幻灯片则非正式商务与学术通用的 PPTX。

| 评估维度 | **Open PPTD** | 代码直接拼写（如 pptxgenjs） | 整页出图型 PPT | 网页 HTML 幻灯片 |
|---|---|---|---|---|
| **默认交付物** | **PPTD 源码工程 + 原生 PPTX** | 通常仅 PPTX 文件 | 单张位图嵌入 PPTX | 单文件 HTML |
| **Agent 编写体验** | **YAML 声明式描述**，语义清晰 | 坐标与细节繁杂，极易翻车 | 依赖提示词与文生图模型 | HTML/CSS 标签约束重 |
| **PowerPoint 二次编辑** | **100% 矢量无损**，文字图形可改 | 结构脆弱，二次调整易错位 | 整页图片，无法改字 | 并非真实 PPTX 文件 |
| **构建性能与依赖** | **<0.05 秒**（Rust 原生离线执行） | 1 ~ 5 秒（Node 运行时） | 10 ~ 30 秒（出图排队） | 需浏览器环境播放 |
| **数学公式与排版** | **原生 LaTeX 数学排版**（变量斜体/字号缩放） | 不支持或需外部插件 | 依赖图片生成 | MathJax / KaTeX 渲染 |
| **安全与隐私** | **零网络调用**，内网离线沙箱安全 | 本地执行 | 需将文本上传云端大模型出图 | 通常依赖 Web 渲染 |

---

## ⚡ 极速开始 (Quick Start)

### 1. 一键安装编译器 CLI (`pptd`)

支持 macOS（Apple Silicon / Intel）、Linux（x86_64 / arm64）以及 Windows（x86_64）：

```bash
# 方式 A：通过 curl 脚本一键下载预编译包到 ~/.local/bin/pptd（推荐）
curl -fsSL https://raw.githubusercontent.com/shiquda/open-pptd/main/skills/open-pptd/scripts/install_binary.sh | bash

# 方式 B：通过 Python 跨平台安装脚本
python3 skills/open-pptd/scripts/install_binary.py

# 方式 C：通过 Rust / Cargo 从源码极速编译安装
cargo install --git https://github.com/shiquda/open-pptd.git
```

验证安装：
```bash
pptd --version
# 输出: pptd 1.0.4
```

### 2. 注册 Agent Skill（可选）

将技能无缝挂载至当前 Coding Agent 环境（如 Codex、Claude Code、Cursor 等）：

```bash
# 通过 npx 自动分发至全局技能目录 ~/.agents/skills/open-pptd
npx github:shiquda/open-pptd install -y

# 或显式指定目标 Agent 路径
npx github:shiquda/open-pptd install --target ~/.claude/skills
```

---

## 🚀 核心工作流与 CLI 命令

### 1. 语义与结构静态质检 (`pptd check`)
在编译前全面扫描语法、非法字段、未定义色彩 `$token`、缺失资源与文字溢出风险：
```bash
pptd check my_project/deck.pptd
```

### 2. 毫秒级编译为原生 PPTX (`pptd build`)
将声明式工程直接编译为真矢量、带演讲者备注的 OpenXML `.pptx` 文件：
```bash
pptd build my_project/deck.pptd -o presentation.pptx
```

### 3. 反向反编译已有 PPTX 为 PPTD 工程 (`pptd convert`)
解构现有演示文稿，提取页面、文本、颜色与表格，生成可继续用代码维护的 PPTD 项目：
```bash
pptd convert presentation.pptx ./decompiled_project/
```

### 4. 自动化深度质检套件 (`validate_pptx.py`)
全面核验成品的页数完整性、未解析 HTML 泄漏标签检索、溢出预警与备注覆盖度：
```bash
python3 skills/open-pptd/scripts/validate_pptx.py presentation.pptx --expected-pages 8 --check-notes
```

---

## 📋 功能特性矩阵

- 📐 **工业级 DrawingML 矢量形状**：原生支持 `rect`, `roundRect`, `ellipse`, `triangle`, `diamond` 等形状，支持精确描边与阴影。
- 🔗 **直线连接器与箭头系统**：支持相对矢量坐标 `points: "0,0 dx,dy"` 及双向箭头定义（`triangle`, `stealth` 等）。
- 🔢 **学术级 LaTeX 数学公式**：行内公式 `\( h(s_t) \ge 0 \)` 原生转义，变量自动西文斜体，上下标自动基线偏移与字号缩放。
- 📊 **原生双向表格支持**：支持单元格合并（`rowSpan`/`colSpan`）、列宽比例定制、斑马纹与边框，支持反编译回 PPTD 代码。
- 🗣️ **PowerPoint 演讲者备注**：页面级 `notes: "..."` 属性自动关联生成标准 OOXML `notesSlide` 关系链。
- 🎨 **1422 款矢量图标内置**：内嵌 Font Awesome 6.7.2 Solid 图标库，支持 `fa-` 自动前缀容错与静态校验。
- 🔒 **`.sync.hash` 双向同步防覆写**：编译器维护校验哈希，防止外部编辑与代码构建相互意外覆盖。
- 🔤 **跨平台安全字体回退**：中文字体智能安全映射至预装字体（如思源宋体安全映射 `SimSun` + `Georgia`），杜绝草书翩翩体降级。

---

## 📁 PPTD 项目结构标准

一个标准、完全自包含的 PPTD 项目结构如下：

```text
my_presentation/
├── deck.pptd             # 主清单：尺寸比例、主题配色、全局字体、页面引用
├── pages/
│   ├── 01_cover.page     # 单页 AST（背景、形状、文本、表格、连线）
│   ├── 02_problem.page
│   └── 03_solution.page
└── assets/               # 页面引用的图片与媒体资产
```

详细 DSL 语法与设计规范请查阅：
- [快速上手指南 (SKILL.md)](skills/open-pptd/SKILL.md)
- [PPTD v2 核心语法规范 (pptd.md)](skills/open-pptd/reference/pptd.md)
- [30+ 款精选主题配色表 (theme.md)](theme.md)
- [CLI 命令参考手册 (cli.md)](skills/open-pptd/reference/cli.md)
- [跨平台安全排版与字体指南 (fonts.md)](skills/open-pptd/reference/fonts.md)

---

## 📄 开源协议与致谢 (License & Attribution)

本项目采用 [MIT 许可证](LICENSE)。

### 鸣谢与上游开源项目致谢：
1. **`open-kimi-ppt-skill`**：
   本项目源于并基于 Binaryify Zhuang 开发的 `open-kimi-ppt-skill`（MIT 许可证，[GitHub](https://github.com/acnlie/open-kimi-ppt-skill)）演进重构。特别致谢原作者对 PPTD 声明式幻灯片设计哲学与 Agent 技能形态的奠基性贡献。
2. **`slideforge` (原生 Rust 编译器核心)**：
   底层核心 Rust 编译器引擎源自原作者 **meatRoll** 创建的开源项目 [`meatRoll/slideforge`](https://github.com/meatRoll/slideforge)（MIT 许可证）。由 shiquda 及其贡献者进行了深度二次开发（丰富富文本排版、增强学术 LaTeX 数学公式渲染、实现完整演讲者备注 notesSlide 关系链、扩充 1422 个矢量图标库并强化 check 严格静态校验诊断），现正式合并并入 Open PPTD 单体代码库以 `pptd` CLI 统一维护。在此向原作者 meatRoll 致以诚挚感谢。
3. **Font Awesome Free 6 (Solid Icons)**：
   项目内嵌的矢量图标集合来源于 Font Awesome 6.7.2（CC BY 4.0 许可证，[License](https://fontawesome.com/license/free)）。
