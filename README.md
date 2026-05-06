# Cross-Domain Video Learning Assistant Skill

把抖音 / B站 / YouTube / TikTok 视频内容转成可执行学习方案的 Codex Skill。

## What It Does
- 输入：视频链接（抖音/B站/YouTube/TikTok）+ 字幕（推荐）+ 高赞评论（可选）+ 学习目标（可选）
- 输出：中文专业版深度报告（证据索引、执行清单、领域附加模块、风险边界、复盘问题）
- 领域覆盖：投资、科技工具、学科考试、旅游美食
- 受限内容：优先复用本机登录会话；字幕缺失时支持页面可见文本兜底

## Why This Version Is Stronger
本技能吸收了高星 AI 学习/提示词仓库的共性做法：
- 强触发描述 + 明确输入契约
- 固定输出模板，保证结果稳定
- 示例驱动（让模型更容易命中预期）
- 失败场景兜底与安全边界

参考仓库（2026-05-06 采样）：
- [f/prompts.chat](https://github.com/f/prompts.chat)（Stars: 162,406）
- [microsoft/generative-ai-for-beginners](https://github.com/microsoft/generative-ai-for-beginners)（Stars: 92,997）
- [dair-ai/Prompt-Engineering-Guide](https://github.com/dair-ai/Prompt-Engineering-Guide)（Stars: 74,236）
- [openai/openai-cookbook](https://github.com/openai/openai-cookbook)（Stars: 66,366）
- [microsoft/ai-for-beginners](https://github.com/microsoft/ai-for-beginners)（Stars: 47,699）

## Files
- `SKILL.md`: 核心技能定义
- `evals/evals.json`: 8 个评测用例
- `evals/assertion-checklist.json`: 关键断言清单
- `evals/RUN_EVALS.md`: 评测运行说明

## Quick Usage
1. 提供 `video_url` 与字幕文本（建议带时间戳）。
2. 可选附上 `top_comments` 和 `user_goal`。
3. 使用 skill 生成深度报告与执行清单。
4. 用 `evals` 目录内容进行 with/without skill 对比评测。

## Safety
- 只处理用户授权访问内容，不绕过平台权限。
- 不接收明文账号密码。
- 投资类仅教学与模拟案例，不给个股买卖指令。

## License
MIT
