# Cross-Domain Video Learning Assistant

Turn Douyin / Bilibili / YouTube / TikTok videos into actionable learning playbooks in minutes.

[![GitHub stars](https://img.shields.io/github/stars/Irkalla0/cross-domain-video-learning-assistant?style=social)](https://github.com/Irkalla0/cross-domain-video-learning-assistant/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/Irkalla0/cross-domain-video-learning-assistant?style=social)](https://github.com/Irkalla0/cross-domain-video-learning-assistant/network/members)
[![License](https://img.shields.io/github/license/Irkalla0/cross-domain-video-learning-assistant)](https://github.com/Irkalla0/cross-domain-video-learning-assistant/blob/main/LICENSE)
[![Issues](https://img.shields.io/github/issues/Irkalla0/cross-domain-video-learning-assistant)](https://github.com/Irkalla0/cross-domain-video-learning-assistant/issues)

If this helps your workflow, star the repo so you can find it faster later.

## 30-Second Quick Start

Extract transcript first:

```bash
py scripts/extract_video_text.py "<video_url>" --cookies-from-browser chrome
```

If subtitle tracks are missing:

```bash
py scripts/extract_video_text.py "<video_url>" --cookies-from-browser chrome --enable-whisper --whisper-model small --whisper-language en
```

Feed `transcript_artifacts/run-*/transcript.txt` into the skill as `subtitle_text`.

## Why This Project

Most subtitle tools stop at text dumping. This project goes further:
- Login-session aware extraction for restricted videos (authorized access only)
- Cross-platform support: Douyin, Bilibili, YouTube, TikTok
- Structured learning output: evidence index, action checklist, domain-specific guidance
- Claude Code-ready workflow with predictable input/output shape

## Dictation / Transcription Language Support

Two layers:
1. `yt-dlp` subtitle layer: any language exposed by the source subtitle tracks
2. `whisper` fallback layer: multilingual STT (common codes: `zh`, `en`, `ja`, `ko`, `es`, `fr`, `de`, `ru`, `ar`, `hi`)

Show live language support details:

```bash
py scripts/extract_video_text.py --list-language-support
```

## Safety Boundaries

- Analyze authorized content only
- No bypass of platform access control
- No plaintext password/OTP collection
- Investing output stays educational and risk-bounded

## Key Links

- Chinese skill spec: [SKILL.md](SKILL.md)
- English skill spec: [SKILL.en.md](SKILL.en.md)
- Claude Code adaptation: [CLAUDE_CODE.md](CLAUDE_CODE.md)
- Transcript script: [scripts/extract_video_text.py](scripts/extract_video_text.py)
- Eval set: [evals/evals.json](evals/evals.json)

---

## 中文完整说明

把抖音 / B站 / YouTube / TikTok 视频转成可执行学习方案。

### 能力

- 输入：`video_url` + 字幕（推荐）+ 高赞评论（可选）+ 学习目标（可选）
- 输出：结构化深度报告（证据索引、执行清单、领域模块、风险边界、复盘问题）
- 领域：投资、科技工具、学科考试、旅游美食
- 受限内容：优先复用本机登录会话；字幕缺失时自动转写兜底

### 听写语言支持

分两层：
1. `yt-dlp` 字幕层：支持视频源实际提供的官方/自动字幕语言
2. `whisper` 转写层：支持多语言听写（常见：`zh` `en` `ja` `ko` `es` `fr` `de` `ru` `ar` `hi`）

查看当前语言支持说明：

```bash
py scripts/extract_video_text.py --list-language-support
```

### 快速使用

1. 有字幕时直接走 skill 分析
2. 无字幕时先转写：

```bash
py scripts/extract_video_text.py "<video_url>" --cookies-from-browser chrome
```

3. 如果没有可用字幕轨道，启用 whisper：

```bash
py scripts/extract_video_text.py "<video_url>" --cookies-from-browser chrome --enable-whisper --whisper-model small --whisper-language zh
```

4. 将 `transcript_artifacts/run-*/transcript.txt` 作为 `subtitle_text` 输入 skill

### 依赖

- 必需：`yt-dlp`
- 可选：`whisper` CLI + `ffmpeg`（用于音频转写兜底）

### Claude Code 适配

- 已适配 Claude Code 工作流：先登录会话复用，再转写，再结构化分析
- 详细说明见 [CLAUDE_CODE.md](CLAUDE_CODE.md)
