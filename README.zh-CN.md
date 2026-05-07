# 跨领域视频学习助教 Skill

把抖音 / B站 / YouTube / TikTok 视频内容转成可执行学习方案。

## 能力
- 输入：视频链接 + 字幕（推荐）+ 高赞评论（可选）+ 学习目标（可选）
- 输出：深度报告（证据索引、执行清单、领域模块、风险边界、复盘问题）
- 领域：投资、科技工具、学科考试、旅游美食
- 受限内容：优先复用本机登录会话；字幕缺失时可自动转写

## 听写支持语言
分两层：
1. `yt-dlp` 字幕层：支持视频本身提供的官方/自动字幕语言（可用 `--langs` 指定优先级）。
2. `whisper` 转写层：支持多语言语音识别（常用如 `zh`, `en`, `ja`, `ko`, `es`, `fr`, `de`, `ru`, `ar`, `hi` 等）。

查看语言说明：
```bash
py scripts/extract_video_text.py --list-language-support
```

## 自动转写脚本
- 脚本：`scripts/extract_video_text.py`
- 必需依赖：`yt-dlp`
- 可选依赖（无字幕时）：`whisper` CLI + `ffmpeg`

常规提取：
```bash
py scripts/extract_video_text.py "<video_url>" --cookies-from-browser chrome
```

无字幕时音频转写：
```bash
py scripts/extract_video_text.py "<video_url>" --cookies-from-browser chrome --enable-whisper --whisper-model small --whisper-language zh
```

输出目录：`transcript_artifacts/run-时间戳/`
- `transcript.txt`
- `transcript.md`
- `metadata.json`

## Claude Code 适配
见 [CLAUDE_CODE.md](CLAUDE_CODE.md)。

## 主要文件
- 中文技能定义：`SKILL.md`
- 英文技能定义：`SKILL.en.md`
- 评测用例：`evals/evals.json`
