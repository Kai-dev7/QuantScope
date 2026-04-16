# PDF 导出功能使用指南

## 📋 概述

QuantScope 支持将分析报告导出为多种格式：
- **Markdown** - 纯文本格式，易于编辑
- **Word (DOCX)** - 适合进一步编辑和格式化
- **PDF** - 适合打印和分享

本指南重点介绍 **PDF 导出功能**的使用和配置。

---

## 🚀 快速开始

### 1. 安装依赖

运行自动安装脚本（推荐）：

```bash
python scripts/setup/install_pdf_tools.py
```

或手动安装：

```bash
# 方案 1: WeasyPrint（推荐）
pip install weasyprint

# 方案 2: pdfkit（需要额外安装 wkhtmltopdf）
pip install pdfkit

# 方案 3: Pandoc（回退方案）
pip install pypandoc
```

### 2. 导出 PDF

在前端界面：
1. 打开分析报告详情页
2. 点击"导出"按钮
3. 选择"PDF"格式
4. 等待生成并下载

---

## 🔧 PDF 生成工具对比

系统支持三种 PDF 生成工具，按优先级自动选择：

### 1. WeasyPrint（推荐）⭐

**优点**：
- ✅ 纯 Python 实现，跨平台
- ✅ 无需外部依赖（Windows 除外）
- ✅ 中文支持良好
- ✅ CSS 样式支持完善
- ✅ 表格分页处理好
- ✅ **文本方向控制准确，不会出现竖排问题**

**缺点**：
- ❌ Windows 需要安装 GTK3 运行时

**安装方法**：

```bash
# Linux/macOS
pip install weasyprint

# Windows
# 1. 先安装 GTK3 运行时
#    下载: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases
# 2. 再安装 WeasyPrint
pip install weasyprint
```

**适用场景**：
- 所有场景（推荐）
- 特别适合需要精确控制样式的报告

---

### 2. pdfkit + wkhtmltopdf

**优点**：
- ✅ 渲染效果好
- ✅ 支持复杂的 HTML/CSS
- ✅ 中文支持良好

**缺点**：
- ❌ 需要安装外部工具 wkhtmltopdf
- ❌ 配置相对复杂

**安装方法**：

```bash
# 1. 安装 pdfkit
pip install pdfkit

# 2. 安装 wkhtmltopdf
# Windows: https://wkhtmltopdf.org/downloads.html
# macOS: brew install wkhtmltopdf
# Ubuntu/Debian: sudo apt-get install wkhtmltopdf
# CentOS/RHEL: sudo yum install wkhtmltopdf
```

**适用场景**：
- 需要高质量渲染的报告
- 已经安装了 wkhtmltopdf 的环境

---

### 3. Pandoc（回退方案）

**优点**：
- ✅ 通用的文档转换工具
- ✅ 支持多种格式互转

**缺点**：
- ❌ 需要安装外部工具 pandoc
- ❌ 中文竖排问题难以解决
- ❌ 表格分页控制不佳
- ❌ **不推荐用于中文报告**

**安装方法**：

```bash
# 1. 安装 pypandoc
pip install pypandoc

# 2. 安装 pandoc
# Windows: https://pandoc.org/installing.html
# macOS: brew install pandoc
# Ubuntu/Debian: sudo apt-get install pandoc
# CentOS/RHEL: sudo yum install pandoc
```

**适用场景**：
- 仅作为回退方案
- 其他工具都不可用时使用

---

## 📊 工作原理

### PDF 生成流程

```
分析报告数据
    ↓
生成 Markdown 内容
    ↓
转换为 HTML（添加样式）
    ↓
选择 PDF 生成工具
    ↓
┌─────────────────────────────────┐
│ 1. WeasyPrint（优先）            │
│    - 直接从 HTML 生成 PDF        │
│    - 应用自定义 CSS 样式         │
│    - 强制横排显示                │
├─────────────────────────────────┤
│ 2. pdfkit（备选）                │
│    - 使用 wkhtmltopdf 渲染       │
│    - 应用自定义 CSS 样式         │
│    - 强制横排显示                │
├─────────────────────────────────┤
│ 3. Pandoc（回退）                │
│    - 从 Markdown 转换            │
│    - 尝试修复文本方向            │
│    - 可能出现竖排问题            │
└─────────────────────────────────┘
    ↓
生成 PDF 文件
```

### 关键技术点

#### 1. 强制横排显示

在 HTML 模板中添加 CSS 样式：

```css
* {
    writing-mode: horizontal-tb !important;
    text-orientation: mixed !important;
    direction: ltr !important;
}
```

#### 2. 表格分页控制

```css
table {
    page-break-inside: auto;  /* 允许表格跨页 */
}

tr {
    page-break-inside: avoid;  /* 避免行中间分页 */
}

thead {
    display: table-header-group;  /* 表头在每页重复 */
}
```

#### 3. 中文字体支持

```css
body {
    font-family: "Microsoft YaHei", "SimHei", "Arial", sans-serif;
}
```

---

## 🐛 常见问题

### 问题 1: 中文文本竖排显示

**现象**：PDF 中的中文文本从上到下显示，而不是从左到右。

**原因**：Pandoc 在处理中文时可能错误地应用竖排样式。

**解决方案**：
1. **推荐**：安装并使用 WeasyPrint
   ```bash
   pip install weasyprint
   ```

2. 或者安装 pdfkit
   ```bash
   pip install pdfkit
   # 并安装 wkhtmltopdf
   ```

3. 系统会自动优先使用 WeasyPrint/pdfkit，避免 Pandoc 的问题

---

### 问题 2: 表格跨页被截断

**现象**：表格在页面边界被切成两半。

**原因**：PDF 生成工具没有正确处理表格分页。

**解决方案**：
- WeasyPrint 和 pdfkit 都已经配置了正确的表格分页样式
- 系统会自动应用 CSS 样式控制分页

---

### 问题 3: WeasyPrint 安装失败（Windows）

**现象**：
```
OSError: cannot load library 'gobject-2.0-0'
```

**原因**：Windows 需要 GTK3 运行时。

**解决方案**：
1. 下载 GTK3 运行时：
   https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases

2. 安装 `gtk3-runtime-x.x.x-x-x-x-ts-win64.exe`

3. 重新安装 WeasyPrint：
   ```bash
   pip install weasyprint
   ```

---

### 问题 4: pdfkit 找不到 wkhtmltopdf

**现象**：
```
OSError: No wkhtmltopdf executable found
```

**原因**：wkhtmltopdf 未安装或不在 PATH 中。

**解决方案**：

**Windows**：
1. 下载：https://wkhtmltopdf.org/downloads.html
2. 安装到默认路径
3. 或者在代码中指定路径：
   ```python
   config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
   ```

**macOS**：
```bash
brew install wkhtmltopdf
```

**Linux**：
```bash
# Ubuntu/Debian
sudo apt-get install wkhtmltopdf

# CentOS/RHEL
sudo yum install wkhtmltopdf
```

---

## 📈 性能对比

| 工具 | 生成速度 | 文件大小 | 中文支持 | 样式控制 | 推荐度 |
|------|---------|---------|---------|---------|--------|
| WeasyPrint | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| pdfkit | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Pandoc | ⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ | ⭐⭐ |

---

## 🔍 检查当前可用的工具

在 Python 中运行：

```python
from app.utils.report_exporter import ReportExporter

exporter = ReportExporter()
print(f"WeasyPrint: {exporter.weasyprint_available}")
print(f"pdfkit: {exporter.pdfkit_available}")
print(f"Pandoc: {exporter.pandoc_available}")
```

或查看日志输出：

```
✅ WeasyPrint 可用（推荐的 PDF 生成工具）
✅ pdfkit + wkhtmltopdf 可用
✅ Pandoc 可用
```

---

## 📚 相关文档

- [故障排查指南](../troubleshooting/pdf_word_export_issues.md)
- [安装脚本](../../scripts/setup/install_pdf_tools.py)
- [WeasyPrint 官方文档](https://doc.courtbouillon.org/weasyprint/)
- [pdfkit 官方文档](https://github.com/JazzCore/python-pdfkit)
- [Pandoc 官方文档](https://pandoc.org/)

---

## 💡 最佳实践

1. **优先使用 WeasyPrint**
   - 最可靠，中文支持最好
   - 无需外部依赖（Linux/macOS）

2. **备选 pdfkit**
   - 如果 WeasyPrint 不可用
   - 渲染效果好

3. **避免使用 Pandoc**
   - 仅作为最后的回退方案
   - 中文竖排问题难以解决

4. **测试导出功能**
   - 安装后立即测试
   - 检查中文显示是否正常
   - 检查表格分页是否正确

---

## 🆘 获取帮助

如果遇到问题：

1. 查看日志输出，确认使用了哪个 PDF 生成工具
2. 参考[故障排查指南](../troubleshooting/pdf_word_export_issues.md)
3. 运行安装脚本检查依赖：
   ```bash
   python scripts/setup/install_pdf_tools.py
   ```
4. 在 GitHub 提交 Issue

