# Claude Code Adaptation Guide

This skill is adapted to run cleanly in Claude Code workflows.

## Execution Pattern
1. User provides `video_url` and optional subtitles/comments.
2. If subtitles are missing, run:
   ```bash
   py scripts/extract_video_text.py "<video_url>" --cookies-from-browser chrome
   ```
3. Feed generated `transcript.txt` into the skill analysis prompt.
4. Produce the fixed report structure from `SKILL.md` or `SKILL.en.md`.

## Recommended Defaults
- Keep subtitle priority: `zh-Hans,zh-CN,zh,zh-Hant,en`
- For English-heavy videos: `--langs en,zh`
- For no-subtitle videos: add `--enable-whisper`

## Language Controls
- Show supported language guidance:
  ```bash
  py scripts/extract_video_text.py --list-language-support
  ```
- Set whisper language hint explicitly when needed:
  ```bash
  --whisper-language zh
  ```
  or
  ```bash
  --whisper-language en
  ```

## Login-Restricted Content
- Reuse local browser session with `--cookies-from-browser`.
- If session expires, let user log in manually and rerun.
- Never ask for plaintext account passwords or OTP codes.

## Safety Boundaries
- Analyze only authorized content.
- No bypass of platform access controls.
- Investing outputs stay educational, with explicit risk boundaries.
