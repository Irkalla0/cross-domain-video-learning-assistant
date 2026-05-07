# Cross-Domain Video Learning Assistant Skill

Turn videos from Douyin / Bilibili / YouTube / TikTok into actionable learning plans.

## What It Does
- Input: video URL + subtitles (recommended) + top comments (optional) + user goal (optional)
- Output: structured report (evidence index, action checklist, domain module, risk boundaries, review prompts)
- Domains: investing, tech tutorials, exam study, travel/food
- Restricted videos: reuse local login session first; fallback to transcript extraction when subtitles are missing

## Dictation / Transcription Language Support
There are two layers:
1. `yt-dlp` subtitle layer: any language provided by the source video subtitle tracks.
2. `whisper` fallback layer: multilingual speech-to-text (common codes include `zh`, `en`, `ja`, `ko`, `es`, `fr`, `de`, `ru`, `ar`, `hi`).

Show language support details:
```bash
py scripts/extract_video_text.py --list-language-support
```

## Auto Transcript Script
- Script: `scripts/extract_video_text.py`
- Required: `yt-dlp`
- Optional fallback: `whisper` CLI + `ffmpeg`
- Optional visible-page fallback: `selenium`

Subtitle-first extraction:
```bash
py scripts/extract_video_text.py "<video_url>" --cookies-from-browser chrome
```

Whisper fallback if no subtitles:
```bash
py scripts/extract_video_text.py "<video_url>" --cookies-from-browser chrome --enable-whisper --whisper-model small --whisper-language en
```

Visible-page fallback if subtitle + whisper both fail:
```bash
py scripts/extract_video_text.py "<video_url>" --cookies-from-browser edge --enable-whisper --enable-visible-text-fallback
```

Output directory: `transcript_artifacts/run-<timestamp>/`
- `transcript.txt`
- `transcript.md`
- `metadata.json`

## Claude Code Adaptation
See [CLAUDE_CODE.md](CLAUDE_CODE.md).

## Main Files
- Chinese skill spec: `SKILL.md`
- English skill spec: `SKILL.en.md`
- Eval prompts: `evals/evals.json`
