# exam-review-skill

一站式复习资料流水线:**课件(PPT/PDF)+ 作业(docx) → 复习全书 / 试卷(Markdown + PDF)→ 单文件离线互动复习网页(HTML)**。

本仓库同时是 Claude Code 可安装的 skill(见 [SKILL.md](SKILL.md)),也可以把 `tools/` 下的脚本独立使用。

## 功能

- **材料解析**:PPT/讲义 PDF 文本提取(含矢量绘制符号的 `get_drawings()` 复核、GoodNotes 手写批注层)、docx 作业经 pandoc 转换。
- **考点提炼与出题**:选择 / 判断 / 计算 / 简答,基础题 → 变式题 → 综合题,真题风格优先。
- **PDF 输出**:pandoc + xelatex(MiKTeX),中文 ctexart(SimSun / Microsoft YaHei)+ Times New Roman,例题框、表格、公式排版。
- **互动复习网页**:单文件 HTML,KaTeX 全部内联(base64 字体 + 内联 JS,离线可用、无 CDN);选择题/判断题点击判分(绿对红错 + 自动展开解析),计算/简答题点击显示解析;localStorage 记录进度与正确率、成绩单、深浅色主题。
- **自动验证**:`quality_check.py` 检查 Markdown 常见错误;`verify_html.py` 用无头浏览器跑页面,解析页面自检 JSON(KaTeX 加载状态、渲染错误、缺答案题号)。

## 目录结构

```
exam-review-skill/
├── SKILL.md                     # Claude Code skill 定义(完整工作流)
├── tools/
│   ├── quality_check.py         # Markdown 质量检查(横线/引号/公式/Unicode 符号)
│   ├── build_focus_paper.py     # 互动页构建器(单卷模板,推荐从这里上手改)
│   ├── build_interactive_review.py  # 互动页构建器(全书+多卷参考实现)
│   ├── verify_html.py           # 无头浏览器冒烟测试 + 页面自检
│   └── katex_assets/            # KaTeX 0.16.x 离线资源(MIT / SIL OFL)
└── examples/
    └── focus_paper/             # 完整示例:DASE7501 聚焦卷(L1/L2/L4)
        ├── DASE7501_Focus_Paper_L1L2L4.md    # 试卷源文件(Part 1 纯英文题目 + Part 2 双语解析)
        ├── DASE7501_Focus_Paper_L1L2L4.pdf   # 编译出的 PDF
        └── DASE7501_Focus_Interactive.html   # 构建出的互动网页(双击即用)
```

## 快速开始

### 作为 Claude Code skill 使用

```bash
# 克隆到 Claude Code 技能目录
git clone https://github.com/<你的账号>/exam-review-skill.git ~/.claude/skills/exam-review-skill
```

之后在会话中直接说"根据这些 PPT 帮我生成复习资料/模拟卷/互动练习网页"即可触发。

### 独立使用工具链

```bash
# 1. 生成互动网页(以示例为例)
cd examples/focus_paper
python ../../tools/build_focus_paper.py
# 2. 编译 PDF(需要 pandoc + MiKTeX/xelatex)
pandoc DASE7501_Focus_Paper_L1L2L4.md -o DASE7501_Focus_Paper_L1L2L4.pdf --pdf-engine=xelatex
# 3. 验证互动页(需要 Edge 或 Chrome)
python ../../tools/verify_html.py DASE7501_Focus_Interactive.html
```

自己写新材料时:照 `examples/focus_paper/*.md` 的结构写题目(Part 1 题目 / Part 2 解析 + 答案速查),把 `build_focus_paper.py` 顶部的 `SRC`/`OUT` 改成你的文件名即可。

## 示例(Examples)

`examples/focus_paper/` 是香港大学 DASE7501 机器人课程的一份 20 题聚焦卷(范围 Lecture 1/2/4,题型仿作业与往年考试:机器人应用、自由度、选型、精度/重复性、灵敏度、PWM),以教学演示目的发布。

## 依赖

- Python 3.8+(PyMuPDF 用于 PDF 验证;构建器本身仅用标准库)
- pandoc + xelatex(MiKTeX 或 TeX Live)用于编译 PDF
- Microsoft Edge 或 Google Chrome 用于 HTML 无头验证
- KaTeX 0.16.x 已随仓库分发(MIT License;字体 SIL OFL 1.1)

## License

[MIT](LICENSE) © 2026 Oldmonk-Ji
