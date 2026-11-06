---
name: exam-review-skill
description: 根据课程讲义、PDF、PPTX、作业和考试范例创建或更新可追溯的复习讲义、练习与互动 HTML，可按要求交付 PDF 或 Markdown。适用于课程复习与模拟练习，不用于预测未提供的考试范围。
---

# Exam Review

## 工作流

1. **确定本次契约。** 读取 [customization](references/customization.md)，提取已有范围、题量、语言、阅读设备与交付格式，只问缺失的关键项。题量区分精确、上限及不出题，不默认固定题数、语言或两小时。可将 [配置示例](assets/review-config.example.yaml) 复制到输出项目作为 `review-config.yaml`；它是助手任务契约，不是构建器自动读取的配置文件。只有用户选择历史预设时才读取 [review-preferences](references/review-preferences.md)。
2. **盘点证据。** 记录材料名、版本、原始页码或幻灯片号与覆盖章节。PDF 可用 PyMuPDF；PPTX 使用适当的 PPTX 解析器或转换器，不直接交给 PyMuPDF。文字提取后回看公式、图表、图注和考试范例页面；无法辨认或缺失的材料明确标记。区分课程原文、推导及外部补充，不推测未提供的考试范围。
3. **编写共同内容源。** 按确认顺序组织章节讲解、条件、例题与练习。独立验算全部数值答案，检查推导的维度、边界与假设。题目记录独立训练目的，除非明确要求重复训练，不以换数字充题量。AI、机器学习或机器人材料实际涉及相关主题时，读取 [ai-course-checks](references/ai-course-checks.md)，不把这些主题强加给其他课程。
4. **生成选定格式。** HTML 仅需 Python 3.9+ 与随技能提供的离线资源。将 `<skill-dir>` 解析为本技能目录，在输出项目中运行 `python "<skill-dir>/scripts/build_review.py" input.json output.html`；产物和私有材料不写入技能目录。读取 [JSON 数据格式](references/data-schema.md)，答案显式写入 JSON。章节可含 notes 与 sections（id/title/body），题目通过 lesson_id 关联讲解；题型为 mcq、tf、reveal，questions 为空生成纯讲义。只有明确指定 exam_minutes 才启用计时自测，它不保护 HTML 内含答案，也不适用于正式防作弊考试。不要臆造字段或声称所有契约选项均已实现。需要未支持的布局或功能时明确适配，或使用合适工具。Markdown 和 PDF 不要求附带 HTML；仅在选择 PDF 时读取 [pdf-workflow](references/pdf-workflow.md)。
5. **验证交付。** 核对章节、唯一题目、答案与来源数量和内容，检查题量/语言/格式符合契约。HTML 在当前环境允许的浏览器工具中测试目录、章节关联、搜索、难度、错题、收藏、简答草稿和进度隔离；无题讲义也需检查。查看答案不是答对，简答草稿不是自动评分。纯排版更新尽量保留稳定 ID；题意、答案或数据集改变时验证旧进度不会错误复用。回看真实渲染的数学、表格和窄屏页面，不能仅以像素阈值或源码关键词判断公式质量。报告实际完成的检查及无法验证的边界。

## 云端与材料边界

使用技能内相对路径与当前环境工具，不依赖原作者本机盘符、浏览器配置或课程目录。不另起独立浏览器绕过当前访问限制。只有独立资源实际随交付包含并验证时才声称离线可用。个人讲义、考试日期、作答、输出项目配置不打包进技能。

本技能保留上游 MIT 许可与版权，见 [attribution](references/attribution.md)。
