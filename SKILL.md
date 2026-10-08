---
name: exam-review-skill
description: 一站式复习资料流水线:从课件(PPT/PDF)、作业(docx)等材料提炼考点,生成复习全书/试卷(Markdown + PDF),并构建单文件离线互动复习网页(点击判题、解析展开、进度记录、深浅色主题)。当用户要求根据讲义/PPT/作业整理复习资料、出模拟卷、生成互动复习网页时使用。
---

# Exam Review Skill(复习资料流水线)

从课件与作业到复习全书、试卷、互动复习网页的完整流程。本仓库同时是可安装的 Claude Code skill(SKILL.md 即技能定义)。

## 何时使用 / 何时不用

**使用**:用户提供课件/作业等材料,要求复习全书、练习卷、模拟卷、互动复习网页(如"根据 PPT 出题""生成复习资料""做一份互动练习")。

**不用**:只要纯文本列表(不需要 PDF/网页);用户给的是 `.tex` 且只需小改;要做联网线上考试平台(本 skill 产出本地离线单文件网页)。

## 工作流总览

1. 探索材料 → 2. 提炼考点 → 3. 设计文档结构 → 4. 写 Markdown(抽象概念按 §4.5 配图)→ 5. 质量检查 → 6. 编译 PDF → 7. 构建互动 HTML → 8. 验证输出

每个数值答案都要独立重算核对后再写入。

## 1. 探索材料

- **PPT 文本**:用 PyMuPDF(`fitz`)逐页 `get_text()` 提取,集中存到 `ppt_text/` 目录便于 grep。
- **矢量绘制的符号陷阱**:公式里的根号、分数线等可能是矢量绘制,文本提取看不到。用 `page.get_drawings()` 定位图形后人工核对公式结构(曾因此把"每点距离取平均"误写成 RMS,见[关键教训](#关键教训来自真实使用))。
- **手写批注 PDF**(如 GoodNotes):批注是独立文本层,`get_text()` 可直接提取,常含老师补充例题。
- **docx 作业**:`pandoc 作业.docx -o 作业.md`;图片用 OCR 或人眼识别后转述成文字题。
- 所有源材料的例题数字都值得记录——考试常改编原例换数字。

## 2. 提炼考点

- 逐章列出考点、公式、例题;按"考过什么"排优先级:往年题/作业题 > 讲义例题 > 概念。
- 记录易混概念(如精度 accuracy vs 重复性 repeatability)、单位换算、边界条件。
- 用讲义表格核对参数(如各类机器人的负载/重复性/速度范围),出选项时避免歧义。

## 3. 文档结构(类型 A–E)

| 类型 | 用途 | 版式要点 |
|---|---|---|
| A 试卷 | 模拟真实考试 | 10.5–11pt、2.0–2.5cm 边距、答案置末 |
| B 讲义 | 系统学习材料 | 知识梳理 + 例题 + 举一反三 |
| C 复习全书 | 期末复习参考 | 多章、理论 + 例题 + 详解 |
| D 纯题 | 最大题量刷题 | 8.5–9pt、1.2–1.5cm 边距 |
| E 英文文档 | 英文考试材料 | article + Times New Roman |

frontmatter 模板(中文文档,ctexart):

```yaml
---
title: "标题"
subtitle: "副标题"
fontsize: 10.5pt
documentclass: ctexart
geometry: margin=2.1cm
colorlinks: true
header-includes: |
  \setlength{\emergencystretch}{3em}
  \linespread{1.2}
  \widowpenalty=10000
  \clubpenalty=10000
  \brokenpenalty=10000
  \usepackage{amsmath}
  \usepackage{amssymb}
  \usepackage{booktabs}
  \usepackage{graphicx}
  \setkeys{Gin}{width=\linewidth}
  \usepackage{float}
  \floatplacement{figure}{H}
  \usepackage{enumitem}
  \setlist[enumerate]{nosep}
  \usepackage{tcolorbox}
  \tcbuselibrary{skins,breakable}
  \renewenvironment{quote}{\begin{tcolorbox}[colback=blue!3!white,colframe=blue!40!black,boxrule=0.4pt,arc=1.5mm,breakable,left=2mm,right=2mm,top=1mm,bottom=1mm]}{\end{tcolorbox}}
  \setCJKmainfont{SimSun}
  \setCJKsansfont{Microsoft YaHei}
mainfont: "Times New Roman"
sansfont: "Microsoft YaHei"
monofont: "Consolas"
---
```

(引文块被重定义为蓝色例题框;Windows 下 SimSun/YaHei 可用,Linux 换 Noto Serif CJK SC。所有文档必须带 widow/club/broken penalty = 10000 防孤行。)

## 4. Markdown 规则(要点)

- **正文禁用独立成行的 `---`**(会被渲染成横线/分页),仅 YAML frontmatter 例外;行内破折号用 `--`。
- 中文引号用 “ ”,破折号 ——,省略号 ……。
- 公式一律 `$...$`/`$$...$$`;中文进公式用 `\text{}`;不用 Unicode 逻辑符号(→ ∧ ∨ 等)。
- 表格每个含公式的格子必须完整包在 `$...$` 内。
- **英文考试材料约定:题目/题干纯英文、零中文;解析与讲解可带中文括号标注;UI 标签可双语**。写完用脚本逐块校验题目区无 CJK 字符。

## 4.5 配图管线(抽象概念必配图)

抽象内容(坐标系、D-H 参数、变换矩阵、控制框图等)必须配图,否则学生无法建立几何直觉。管线:

1. **手写 SVG**(参考 `tools/make_figures.py`):双语标注(英文术语 + 中文解释)、粗箭头、坐标轴红/绿/蓝三色区分、统一配色与字号。用脚本拼 SVG 字符串,保证可复现。
2. **渲染**:Edge headless `--headless=new --disable-gpu --user-data-dir=<临时空目录> --screenshot=png --window-size=W,H --force-device-scale-factor=1 --default-background-color=FFFFFFFF file:///xxx.svg`。`--user-data-dir` 必须指向独立临时目录(浏览器子进程会锁 dump 文件,清理用 `mkdtemp` + `shutil.rmtree(ignore_errors=True)`)。
3. **程序化验证(不可肉眼)**:PIL 像素抽样——输出尺寸与 SVG 画布一致、四角为背景色、墨量占比在 1–75% 区间、各主色(红/蓝/绿)像素计数超过阈值。阈值是抽样伪影,不是渲染缺陷:细线(如 2px 十字)按 3px 步长抽样会漏采,把阈值降到实际命中数以下即可。
4. **嵌入 md**:`![中文图注(可含 $公式$)](figures/name.png)`;引用块内的图写成 `> ![...](...)` 保持在题框内。
5. **HTML**:构建器 `figure_html()` 把 PNG base64 内联为 data URI(`<figure class="fig">`),保持单文件离线;图注中的直引号同样要用全角 “ ”(quality_check 会查)。
6. **PDF**:frontmatter 必须带 `\usepackage{float}` + `\floatplacement{figure}{H}`——tcolorbox(quote 例题框)内的浮动体会报 `Not in outer par mode`;`[H]` 使图就地放置,`\setkeys{Gin}{width=\linewidth}` 使图自适应框宽。

## 5. 质量检查

```bash
python tools/quality_check.py 输出.md
```

0 error 才能继续(检查横线、直引号、公式内中文、Unicode 逻辑符号、未闭合数学模式等)。

## 6. 编译 PDF

```bash
pandoc 输出.md -o 输出.pdf --pdf-engine=xelatex
```

(Windows + MiKTeX xelatex;字体配置已在 frontmatter 里。)检查输出无 `Missing character` / `Undefined control sequence`。

## 7. 构建互动 HTML(核心)

参考实现:`tools/build_focus_paper.py`(单卷模板,较简单)与 `tools/build_interactive_review.py`(全书 + 多卷,较完整)。架构:

1. **解析**:把 Markdown 解析成题目模型 `{n, sec, text, opts, sol}`——选择题/判断题带选项与答案,计算题/简答题为"点击显示解析"型;答案速查表与逐题详解从 Part 2 提取。
2. **数学**:`stash_math` 先把 `$...$`/`$$...$$` 替换成 `<span class="mi">`/`<div class="mb">` 占位符,再 HTML 转义,最后还原占位符;页面加载后由 `renderMathInElement` 统一渲染(避免转义破坏公式)。
3. **图片**:`![caption](path.png)`(含引用块内 `> ![...]`)被 `figure_html()` 转成 base64 data URI 的 `<figure class="fig">`,缺文件时输出 `fig-missing` 占位并计入 WARNINGS;`![` 行不参与段落合并。
4. **离线**:katex.min.css 里所有字体 url 内联 base64;katex.min.js + auto-render.min.js 整体内联进单文件——无任何 CDN 依赖,双击即用。
5. **交互**(原生 JS,无框架):
   - 选择/判断:点击选项 → 答对绿、答错红(正确项同时标绿)+ 锁定 + 自动展开解析;
   - 计算/简答:按钮「点击显示答案解析」展开/收起;
   - localStorage 记录作答与正确率;顶部进度条;成绩单;深浅色主题切换;重置按钮;
   - 页面内放一个 `#selfcheck` 隐藏 div,load 后写入自检 JSON(题数、KaTeX 节点数、渲染错误数、缺答案题号)——供无头验证使用。
6. 题目区保持纯英文(与真实考试一致),UI 标签与解析可中文。

## 8. 验证

- **PDF**:PyMuPDF 全文检索关键数值与答案;题目区 CJK 字符数为 0;配图文档再核对 `page.get_images()` 计数与图注文本存在。
- **HTML**:一键运行

```bash
python tools/verify_html.py 输出.html
```

内部用 Edge/Chrome headless(`--headless=new --user-data-dir=<隔离临时目录> --virtual-time-budget=9000 --dump-dom`),解析 `#selfcheck` JSON,要求 `katexLoaded=true`、`katexErrors=0`、`missingAnswers=[]`。
- **注意**:`--user-data-dir` 必须指向隔离空目录,否则会被正在运行的浏览器实例抢占导致拿不到输出。
- **假阳性**:统计 `katex-error` 前先剥掉 `<script>` 块(katex.min.js 源码里含该字符串)。

## 关键教训(来自真实使用)

- PPT 公式的根号是矢量绘制、文本提取缺失 → 必须用 `get_drawings()` 复核;曾因此把"每点误差距离取平均"的精度/重复性公式误写成 RMS,导致全部数值答案错误。
- 出题前先核对讲义表格数字(如机器人类型参数表),否则选项会出现歧义(如"龙门机 vs 关节型"负载上限重叠,应改用应用场景措辞)。
- 每个生成的数值答案都独立重算一遍再入库(曾出现 RMS 之外还带算术错的情况)。
- 互动页验证用无头浏览器 dump-dom + selfcheck,比肉眼查更可靠;浏览器更新/本地缓存导致的假错误要用剥 script 法排除。
- 图放不进例题框:quote 被重定义为 tcolorbox,其内的 pandoc 图默认是浮动体,编译报 `Not in outer par mode`——加 `\usepackage{float}` + `\floatplacement{figure}{H}` 解决。
- 图注里的中文直引号会被 quality_check 报 warning——图注同样遵守全角引号规则。
- 无法直接查看图片(Read 工具不支持该会话)时,配图验证必须全程程序化:PIL 像素抽样代替肉眼。
- 画坐标系必须验证右手性:屏幕坐标(y 向下)里 Z 轴垂直纸面向外时,Y 轴屏幕角 = X 轴屏幕角 − 90°(曾把 D-H 建系图的远端两个坐标系画成左手系被用户纠正)。验证三法:SVG 文本解析确认每帧 Y 角 = X 角 − 90°、按线段中点坐标做像素抽样(应命中对应颜色)、旧方向坐标抽样应返回 False。屏幕角 −135° 是"左上"不是"左下"(y 轴向下,atan2 直觉会骗人)。

## 出题原则

基础题 → 变式题(同考点换场景/数字)→ 综合题 → 开放题;真题风格优先(仿作业题与往年题)。每题解析讲清"为什么"而不只给答案。
