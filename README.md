# exam-review-skill

从课程 PDF/PPTX、作业和已提供的考试范例，生成有来源的讲义、练习、模拟卷，以及单文件离线互动 HTML。支持 Codex 和 Claude Code；可按需求只交付 Markdown、PDF 或 HTML。

当前默认入口采用维护者 ai-exam-review 的通用 JSON 构建器，合并本仓库的任务配置流程。它不依赖 Windows 盘符、某一门课的固定标题、题号或答案表。

## 按本次需求定制

先复用已明确的范围、题量、语言、阅读设备与格式，仅询问缺失的关键项。题量区分精确数量、上限与不出题，没有固定题数。详见 [启动配置](references/customization.md) 和 [配置模板](assets/review-config.example.yaml)。

review-config.yaml 是助手读取的任务契约，不是构建器自动消费全部选项的参数文件。实际 HTML 输入格式见 [JSON schema](references/data-schema.md)。题干、讲解与解析语言由内容决定；默认工具栏为中文。

## 功能

- 章节与细分讲解目录，双语解释、符号说明、来源页码，以及题目到讲解的链接。
- 选择、判断、计算/简答题；答案显式来自 JSON。支持 questions=[] 的纯讲义。
- 搜索、难度、错题、收藏和未作答筛选，简答草稿，本地进度与主题切换。
- 只有显式设置 exam_minutes 才启用计时闭卷自测。启动、结束和重置有确认提示；期限在刷新后保留。离线 HTML 中仍包含答案，不能用于正式防作弊考试。
- KaTeX 0.16.11、20个字体与图片可内嵌，无 CDN。题库变化默认切换进度标识，兼容布局更新可显式保留旧标识。
- 全部数值答案独立验算，材料范围与页码追踪，HTML/PDF需按实际环境做相应验收。

## 使用

将完整技能目录放到运行环境的技能目录，或通过该环境支持的技能安装功能安装。Codex 本地示例：

```sh
git clone https://github.com/Oldmonk-Ji/exam-review-skill.git ~/.codex/skills/exam-review-skill
```

Claude Code 可放在 ~/.claude/skills/exam-review-skill。云端安装必须包含完整 scripts/ 及离线资源，不要仅复制 SKILL.md 或引用本机路径。

构建 HTML 仅需 Python 3.9+ 标准库：

```sh
python /path/to/exam-review-skill/scripts/build_review.py input.json output.html
python /path/to/exam-review-skill/scripts/build_review.py --help
```

图片相对路径基于 input.json 所在目录。先创建输出目录；指定的 output.html 会被写入。用 tests/fixtures/mixed.json、reveal.json 或 notes.json 可运行不含课程私人资料的示例。

PDF 是可选工序，使用环境可用的排版工具及实际字体，见 [PDF 工作流](references/pdf-workflow.md)。PPTX 用适当解析器或先转换，不能直接当作 PDF 交给 PyMuPDF。

## 检查

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
node --check scripts/review.js
node tests/test_state.js
```

Python/Node测试不等于真实浏览器验收。还应检查页面的公式、导航、判分、筛选、草稿、刷新恢复、确认取消、计时和窄屏。页面提供 #selfcheck 和 window.reviewSelfcheck 诊断信息。构建结果从不代表课程内容或考试得分已获保证。

## 目录与兼容

- SKILL.md、agents/openai.yaml：技能入口与 Codex 元数据。
- scripts/：推荐的通用 JSON 构建器与完整离线资源。
- references/、assets/：任务配置、数据合同、学科检查及可选 PDF 指引。
- tests/：合成回归测试。
- tools/、examples/focus_paper/：保留旧 DASE7501 参考实现和已公开示例，以兼容原有工作；其中旧构建器有课程专用参数，不是新的通用入口。

请把课程原件、考试日期、个人作答和项目配置留在各自输出项目，勿自动提交到此技能仓库。

## 许可

[MIT](LICENSE) © 2026 Oldmonk-Ji。随附 KaTeX 的官方许可见 [KaTeX LICENSE](scripts/katex_assets/LICENSE)。
