# open-pptd-skill

[简体中文](README.md) | [English](README_EN.md)

[![GitHub Release](https://img.shields.io/github/v/release/shiquda/slideforge?label=slideforge)](https://github.com/shiquda/slideforge/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

基于开放声明式演示文稿规范 **PPTD**（Declarative Presentation Language）与 Rust 原生高性能编译器 **slideforge** 的开源演示文稿全栈工具链。

专为 AI Coding Agent（Claude Code、Codex、Cursor、WorkBuddy、Multica 等）打造，**彻底剔除对原版 Kimi 网页端、无头浏览器、Cookie 登录凭证与网络拦截的脆弱依赖**，在本地实现 100% 离线、毫秒级响应、高度私密的原生 `.pptx` 编译与双向反编译。

---

## 核心特性

- 🚀 **100% 离线与极速编译**：零云端请求、零浏览器自动化。使用 Rust 原生编译器直接输出标准 OpenXML，单份 20 页演示文稿构建耗时 <0.5 秒。
- 📐 **工业级 DrawingML 矢量保真**：完整渲染原生矢量形状、直线连接器与方向箭头（`<a:tailEnd type="triangle"/>`）、渐变填充与精准字号间距。
- 🔢 **LaTeX 数学公式原生排版**：支持 `\( h(s_t) \ge 0 \)` 行内数学公式，变量自动斜体，上下标自动基线偏移与缩放。
- 📊 **原生双向表格支持**：支持 PowerPoint `<a:tbl>` 表格结构，支持单元格合并（`rowSpan`/`colSpan`）、背景填充与边框定制；支持将现有 PPTX 逆向反编译回 PPTD 表格代码。
- 🔤 **跨平台安全字体回退**：自动将中文字体映射到 Windows / macOS 原生预装字体（如思源宋体回退为标准学术宋体 `SimSun` + `Georgia`），彻底避免系统级字体降级导致的草书手写体（翩翩体）崩溃。
- 📦 **免 Rust 环境一键安装**：支持直接下载预编译二进制（macOS Apple Silicon / Intel、Linux x86_64 / arm64、Windows），开箱即用。

---

## 快速安装

### 方式一：一键下载编译器二进制（推荐）

通过内置脚本自动检测系统与架构，从 GitHub Releases 自动下载并配置 `slideforge`：

```bash
# 使用 curl 一键安装到 ~/.local/bin/slideforge
curl -fsSL https://raw.githubusercontent.com/shiquda/open-pptd-skill/main/skills/open-pptd/scripts/install_binary.sh | bash

# 或通过 Python 脚本安装
python3 skills/open-pptd/scripts/install_binary.py
```

### 方式二：安装 Skill 到 AI Agent

将 `open-pptd-skill` 注册到本地 Agent 的 Skills 目录下（如 `~/.agents/skills`、`~/.claude/skills` 等）：

```bash
# 通过 npx 快速分发安装
npx open-pptd-skill install -y

# 或在特定目录下安装
npx open-pptd-skill install --target ~/.claude/skills
```

### 方式三：通过 Cargo 源码编译

```bash
cargo install --git https://github.com/shiquda/slideforge.git
```

---

## 命令行与工作流

### 1. 编译 PPTD 生成原生 PPTX (`build`)

```bash
# 使用 slideforge CLI 直接构建
slideforge build deck.pptd -o output.pptx

# 或使用 Python 脚本包装器（支持自动获取二进制）
python3 skills/open-pptd/scripts/export_pptx.py deck.pptd -o output.pptx [--pdf]
```

### 2. 逆向反编译现有 PPTX 为 PPTD (`convert`)

将现有的 `.pptx` 解构为可继续编程编辑的声明式 PPTD 项目目录（含 `deck.pptd` 及每页 `.page` YAML 文件）：

```bash
# 使用 slideforge convert
slideforge convert existing_deck.pptx -o ./project_dir/

# 或通过 Python 脚本
python3 skills/open-pptd/scripts/convert_pptx.py existing_deck.pptx -o ./project_dir/
```

### 3. 多页切片与全景总览图导出 (`export_images`)

```bash
python3 skills/open-pptd/scripts/export_images.py deck.pptd -o qa-images/
```

---

## 项目结构与规范参考

一个完整的 PPTD 工程结构如下：
```text
my_presentation/
├── deck.pptd            # 演示文稿清单：画幅尺寸、调色盘、全局文本样式、页面清单
├── pages/
│   ├── 01_cover.page    # 单页声明式 AST（背景、形状、文本、线条、表格）
│   ├── 02_why.page
│   └── ...
└── assets/              # 页面引用的本地图片与媒体
```

详细规范请查阅 `skills/open-pptd/reference/`：
- [pptd.md](skills/open-pptd/reference/pptd.md)：PPTD v2 核心 AST 语法与属性字典
- [shapes.md](skills/open-pptd/reference/shapes.md)：内置矢量形状与参数库
- [fonts.md](skills/open-pptd/reference/fonts.md)：跨平台安全排版与字体回退机制
- [tables.md](skills/open-pptd/reference/tables.md)：原生 PPT 表格定义与合并属性
- [math.md](skills/open-pptd/reference/math.md)：LaTeX 数学公式排版规范
- [cli.md](skills/open-pptd/reference/cli.md)：CLI 工具命令行参数手册

---

## 开源协议

本项目采用 [MIT 许可证](LICENSE)。
