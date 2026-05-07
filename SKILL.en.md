---
name: cross-domain-video-learning-assistant
description: Convert Douyin/Bilibili/YouTube/TikTok videos into actionable learning outputs. Trigger this skill when users ask to learn from videos, break down subtitles, synthesize comments, handle login-restricted videos, or apply video methods to investing, tech tutorials, exams, or travel/food tasks.
---

# Cross-Domain Video Learning Assistant

## Goal
Transform user-provided video materials into actionable, evidence-backed reports.

## Input Contract
```json
{
  "video_url": "https://...",
  "subtitle_text": "optional but recommended",
  "subtitle_file": "optional local subtitle/transcript file",
  "top_comments": [{"text": "optional", "likes": 123}],
  "user_goal": "optional"
}
```

Rules:
- Required: `video_url`
- Recommended: `subtitle_text` or `subtitle_file`
- Optional: `top_comments`, `user_goal`

## Auto Transcript (Script)
If users do not provide subtitles, run:
```bash
py scripts/extract_video_text.py "<video_url>" --cookies-from-browser chrome
```

If subtitles are missing, use whisper fallback:
```bash
py scripts/extract_video_text.py "<video_url>" --cookies-from-browser chrome --enable-whisper --whisper-model small
```

If subtitle + whisper both fail, enable visible-page fallback (Selenium):
```bash
py scripts/extract_video_text.py "<video_url>" --cookies-from-browser chrome --enable-whisper --enable-visible-text-fallback
```

Check language support:
```bash
py scripts/extract_video_text.py --list-language-support
```

## Access and Login Handling
1. Reuse existing local login session first.
2. If session is invalid, ask user to log in once in browser and continue.
3. Never request or store plaintext passwords, OTPs, or bypass access control.

## Extraction Priority
1. User-provided subtitles/transcripts
2. `scripts/extract_video_text.py` output (`transcript.txt`)
3. Visible page text fallback
4. If still insufficient: provide a missing-input checklist and stop guessing

## Domain Add-on Modules
- Investing: teaching + simulated case + explicit risk boundaries; no buy/sell timing instructions.
- Tech: reproducible steps + troubleshooting checklist.
- Exams: key points + practice questions + common error patterns.
- Travel/Food: route/spot checklist + budget/time guidance + pitfalls.

## Fixed Output Structure
1. Core conclusions
2. Evidence index (timestamps/source snippets)
3. Top-comment insights (if available)
4. Action checklist (prep, steps, checkpoints, failure recovery)
5. Domain module
6. Risk and boundaries
7. Reflection questions

## Claude Code Notes
- This skill works in Claude Code and Codex-style environments.
- Use the script first when subtitles are not provided.
- If Browser Use backend is unavailable, keep going with `--enable-visible-text-fallback` instead of blocking.
- Keep outputs deterministic with explicit evidence references.

## Optional Skill Chaining
- `browser-use`: for interactive page navigation when backend is healthy.
- `transcribe`: for audio-first pipelines when you intentionally prioritize speech recognition.
- `qa`: to validate report consistency (evidence index completeness, risk boundary presence).
