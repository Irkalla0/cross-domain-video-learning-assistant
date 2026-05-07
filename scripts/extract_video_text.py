#!/usr/bin/env python3
"""
Extract transcript text from a video URL for the cross-domain-video-learning-assistant skill.

Workflow:
1) Try subtitles first with yt-dlp (--write-subs / --write-auto-subs).
2) If no subtitles are found and --enable-whisper is set, download best audio and run whisper CLI.

This script is intended for authorized content only.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional


SUBTITLE_EXTS = {".vtt", ".srt"}
AUDIO_EXTS = {".m4a", ".mp3", ".webm", ".wav", ".aac", ".ogg", ".flac", ".opus"}
COMMON_WHISPER_LANG_CODES = [
    "af", "am", "ar", "az", "be", "bg", "bn", "bs", "ca", "cs",
    "cy", "da", "de", "el", "en", "es", "et", "fa", "fi", "fr",
    "ga", "gu", "he", "hi", "hr", "hu", "hy", "id", "is", "it",
    "ja", "ka", "kk", "km", "kn", "ko", "la", "lt", "lv", "mk",
    "ml", "mn", "mr", "ms", "my", "ne", "nl", "no", "pa", "pl",
    "pt", "ro", "ru", "si", "sk", "sl", "sq", "sr", "sv", "sw",
    "ta", "te", "th", "tl", "tr", "uk", "ur", "uz", "vi", "zh",
]


@dataclass
class Segment:
    timestamp: str
    text: str


def run_cmd(cmd: List[str], cwd: Path, timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
    )


def ensure_tool(tool: str) -> None:
    if shutil.which(tool) is None:
        raise RuntimeError(f"Required tool not found in PATH: {tool}")


def yt_dlp_invocation() -> List[str]:
    if shutil.which("yt-dlp") is not None:
        return ["yt-dlp"]
    try:
        import yt_dlp  # type: ignore # noqa: F401
    except Exception as exc:
        raise RuntimeError(
            "yt-dlp is required but not found. Install with: py -m pip install --user yt-dlp"
        ) from exc
    return [sys.executable, "-m", "yt_dlp"]


def make_run_dir(base_output_dir: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = base_output_dir / f"run-{stamp}"
    run_dir.mkdir(parents=True, exist_ok=False)
    return run_dir


def yt_dlp_auth_args(browser: Optional[str], cookies_file: Optional[Path]) -> List[str]:
    args: List[str] = []
    if browser:
        args.extend(["--cookies-from-browser", browser])
    if cookies_file:
        args.extend(["--cookies", str(cookies_file)])
    return args


def list_files_with_ext(root: Path, exts: Iterable[str]) -> List[Path]:
    ext_set = {e.lower() for e in exts}
    return sorted(
        [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in ext_set],
        key=lambda p: p.stat().st_mtime,
    )


def choose_best_subtitle_file(files: List[Path], lang_order: List[str]) -> Path:
    if len(files) == 1:
        return files[0]

    def score(path: Path) -> int:
        name = path.name.lower()
        for idx, lang in enumerate(lang_order):
            if lang.lower() in name:
                return idx
        return len(lang_order) + 1

    ranked = sorted(files, key=lambda p: (score(p), p.name.lower()))
    return ranked[0]


def parse_timestamped_subtitle(path: Path) -> List[Segment]:
    raw = path.read_text(encoding="utf-8", errors="replace").splitlines()
    segments: List[Segment] = []
    current_ts: Optional[str] = None
    current_lines: List[str] = []

    def flush() -> None:
        nonlocal current_ts, current_lines
        if current_ts and current_lines:
            text = " ".join(x.strip() for x in current_lines if x.strip())
            if text:
                segments.append(Segment(timestamp=current_ts, text=text))
        current_ts = None
        current_lines = []

    for line in raw:
        stripped = line.strip()
        if not stripped:
            flush()
            continue

        upper = stripped.upper()
        if upper.startswith("WEBVTT") or upper.startswith("NOTE") or upper.startswith("STYLE"):
            continue

        if "-->" in stripped:
            flush()
            parts = stripped.split("-->", 1)
            current_ts = parts[0].strip().replace(",", ".")
            continue

        if stripped.isdigit():
            continue

        # ignore HTML-like tags often present in subtitles
        cleaned = stripped.replace("<i>", "").replace("</i>", "").replace("<b>", "").replace("</b>", "")
        current_lines.append(cleaned)

    flush()
    return segments


def parse_plain_text(path: Path) -> List[Segment]:
    lines = [x.strip() for x in path.read_text(encoding="utf-8", errors="replace").splitlines() if x.strip()]
    return [Segment(timestamp=f"line-{idx+1}", text=line) for idx, line in enumerate(lines)]


def dedupe_lines(lines: List[str]) -> List[str]:
    seen: set[str] = set()
    out: List[str] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line in seen:
            continue
        seen.add(line)
        out.append(line)
    return out


def extract_comment_lines(lines: List[str]) -> List[str]:
    start_markers = {"全部评论"}
    end_markers = {"登录后可查看更多评论", "推荐视频", "广告投放"}
    in_block = False
    comment_lines: List[str] = []

    for line in lines:
        if line in start_markers:
            in_block = True
            comment_lines.append(line)
            continue
        if not in_block:
            continue
        comment_lines.append(line)
        if line in end_markers:
            break
    return comment_lines


def language_support_payload(default_sub_langs: str) -> dict:
    return {
        "subtitle_mode": {
            "how_it_works": "Uses subtitle tracks provided by the source platform via yt-dlp.",
            "supported_languages": "Any language that the source video exposes as official/auto subtitles.",
            "default_priority": default_sub_langs.split(","),
            "how_to_override": "Use --langs, e.g. --langs zh,en,ja",
        },
        "whisper_mode": {
            "how_it_works": "Fallback speech-to-text from audio when subtitle tracks are unavailable.",
            "language_detection": "Auto-detect when --whisper-language is not set.",
            "common_language_codes": COMMON_WHISPER_LANG_CODES,
            "how_to_set": "Use --whisper-language <code>, e.g. zh, en, ja, ko, es, fr",
            "note": "Whisper supports multilingual transcription; accuracy varies by language and audio quality.",
        },
    }


def write_outputs(
    run_dir: Path,
    url: str,
    method: str,
    source_files: List[Path],
    segments: List[Segment],
    note: str,
) -> None:
    transcript_txt = run_dir / "transcript.txt"
    transcript_md = run_dir / "transcript.md"
    metadata_json = run_dir / "metadata.json"

    transcript_txt.write_text("\n".join(f"[{s.timestamp}] {s.text}" for s in segments), encoding="utf-8")

    md_lines = [
        "# Extracted Transcript",
        "",
        f"- URL: {url}",
        f"- Method: {method}",
        f"- Segment count: {len(segments)}",
        "",
        "## Notes",
        f"- {note}",
        "",
        "## Segments",
        "",
    ]
    for s in segments:
        md_lines.append(f"- [{s.timestamp}] {s.text}")
    transcript_md.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    metadata = {
        "url": url,
        "method": method,
        "segment_count": len(segments),
        "source_files": [str(p.name) for p in source_files],
        "generated_at": datetime.now().isoformat(),
        "note": note,
    }
    metadata_json.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def try_subtitles(
    url: str,
    run_dir: Path,
    auth_args: List[str],
    lang_order: List[str],
    timeout: int,
) -> tuple[Optional[List[Segment]], Optional[Path], Optional[str], Optional[str]]:
    outtmpl = str(run_dir / "%(id)s.%(ext)s")
    cmd = [
        *yt_dlp_invocation(),
        "--skip-download",
        "--no-playlist",
        "--write-subs",
        "--write-auto-subs",
        "--sub-langs",
        ",".join(lang_order),
        "--sub-format",
        "srt/vtt/best",
        "-o",
        outtmpl,
        *auth_args,
        url,
    ]
    proc = run_cmd(cmd, cwd=run_dir, timeout=timeout)
    if proc.returncode != 0:
        return None, None, proc.stdout, proc.stderr

    subtitle_files = list_files_with_ext(run_dir, SUBTITLE_EXTS)
    if not subtitle_files:
        return None, None, proc.stdout, proc.stderr

    chosen = choose_best_subtitle_file(subtitle_files, lang_order)
    segments = parse_timestamped_subtitle(chosen)
    if not segments:
        return None, chosen, proc.stdout, proc.stderr
    return segments, chosen, proc.stdout, proc.stderr


def whisper_fallback(
    url: str,
    run_dir: Path,
    auth_args: List[str],
    whisper_cmd: str,
    whisper_model: str,
    whisper_language: Optional[str],
    timeout: int,
) -> tuple[List[Segment], Path]:
    if shutil.which(whisper_cmd) is None:
        raise RuntimeError(
            f"Whisper fallback requested, but command not found: {whisper_cmd}. "
            "Install whisper CLI first."
        )

    outtmpl = str(run_dir / "audio.%(ext)s")
    dl_cmd = [
        *yt_dlp_invocation(),
        "--no-playlist",
        "-f",
        "bestaudio/best",
        "-o",
        outtmpl,
        *auth_args,
        url,
    ]
    dl_proc = run_cmd(dl_cmd, cwd=run_dir, timeout=timeout)
    if dl_proc.returncode != 0:
        raise RuntimeError(
            "Failed to download audio for whisper fallback.\n"
            f"stdout:\n{dl_proc.stdout}\n\nstderr:\n{dl_proc.stderr}"
        )

    audio_files = list_files_with_ext(run_dir, AUDIO_EXTS)
    if not audio_files:
        raise RuntimeError("Audio download reported success but no audio file was found.")
    audio_path = audio_files[-1]

    whisper_out_dir = run_dir / "whisper"
    whisper_out_dir.mkdir(parents=True, exist_ok=True)
    w_cmd = [
        whisper_cmd,
        str(audio_path),
        "--model",
        whisper_model,
        "--output_format",
        "txt",
        "--output_dir",
        str(whisper_out_dir),
    ]
    if whisper_language:
        w_cmd.extend(["--language", whisper_language])

    w_proc = run_cmd(w_cmd, cwd=run_dir, timeout=timeout)
    if w_proc.returncode != 0:
        raise RuntimeError(
            "Whisper transcription failed.\n"
            f"stdout:\n{w_proc.stdout}\n\nstderr:\n{w_proc.stderr}"
        )

    txt_files = sorted(whisper_out_dir.glob("*.txt"), key=lambda p: p.stat().st_mtime)
    if not txt_files:
        raise RuntimeError("Whisper command completed but no txt transcript file was produced.")
    txt_path = txt_files[-1]
    return parse_plain_text(txt_path), txt_path


def visible_text_fallback(
    url: str,
    run_dir: Path,
    wait_seconds: int,
    scroll_steps: int,
    scroll_pixels: int,
) -> tuple[List[Segment], List[Path], str]:
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.edge.options import Options
    except Exception as exc:
        raise RuntimeError(
            "Visible-text fallback requires selenium and Edge WebDriver support. "
            "Install with: py -m pip install --user selenium. "
            f"Original import error: {exc}"
        ) from exc

    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1600,1200")

    snapshots: List[str] = []
    final_url = ""
    title = ""

    with webdriver.Edge(options=opts) as driver:
        driver.set_page_load_timeout(60)
        driver.get(url)
        time.sleep(max(wait_seconds, 1))

        for _ in range(max(scroll_steps, 1)):
            body_text = driver.find_element(By.TAG_NAME, "body").text
            snapshots.append(body_text)
            driver.execute_script(f"window.scrollBy(0, {scroll_pixels});")
            time.sleep(1.5)

        final_url = driver.current_url
        title = driver.title or ""

    raw_lines: List[str] = []
    for snap in snapshots:
        raw_lines.extend(snap.splitlines())
    merged_lines = dedupe_lines(raw_lines)

    comment_candidates: List[List[str]] = []
    for snap in snapshots:
        snap_lines = [x.strip() for x in snap.splitlines() if x.strip()]
        comment_block = extract_comment_lines(snap_lines)
        if comment_block:
            comment_candidates.append(comment_block)

    if comment_candidates:
        comment_lines = max(comment_candidates, key=len)
    else:
        comment_lines = extract_comment_lines(merged_lines)

    raw_path = run_dir / "visible_page_raw.txt"
    merged_path = run_dir / "visible_page_merged.txt"
    comments_path = run_dir / "visible_page_comments.txt"

    raw_path.write_text(
        "\n\n".join(
            [f"===== SNAP {i} =====\n{snap}" for i, snap in enumerate(snapshots)]
        ) + "\n",
        encoding="utf-8",
    )
    merged_path.write_text("\n".join(merged_lines) + "\n", encoding="utf-8")
    comments_path.write_text("\n".join(comment_lines) + "\n", encoding="utf-8")

    segments = [Segment(timestamp=f"line-{idx+1}", text=line) for idx, line in enumerate(merged_lines)]
    note = (
        "Used Selenium visible-page fallback. "
        f"final_url={final_url}; page_title={title if title else '(empty)'}; "
        "confidence is lower than subtitle/transcript mode."
    )
    return segments, [raw_path, merged_path, comments_path], note


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract subtitle/transcript text from video links (Douyin/Bilibili/YouTube/TikTok)."
    )
    parser.add_argument("video_url", nargs="?", help="Video URL")
    parser.add_argument(
        "--list-language-support",
        action="store_true",
        help="Print language support details for subtitle mode and whisper mode, then exit.",
    )
    parser.add_argument(
        "--output-dir",
        default="transcript_artifacts",
        help="Directory where run outputs will be written (default: transcript_artifacts)",
    )
    parser.add_argument(
        "--cookies-from-browser",
        default="",
        help="Browser name for yt-dlp cookie reuse, e.g. chrome, edge, firefox",
    )
    parser.add_argument(
        "--cookies-file",
        default="",
        help="Path to Netscape cookies.txt (optional alternative to --cookies-from-browser)",
    )
    parser.add_argument(
        "--langs",
        default="zh-Hans,zh-CN,zh,zh-Hant,en",
        help="Subtitle language priority for yt-dlp, comma separated",
    )
    parser.add_argument(
        "--enable-whisper",
        action="store_true",
        help="If subtitles are unavailable, fallback to whisper transcription.",
    )
    parser.add_argument(
        "--enable-visible-text-fallback",
        action="store_true",
        help="If subtitle/whisper are unavailable, fallback to Selenium visible-page text extraction.",
    )
    parser.add_argument(
        "--visible-fallback-wait-seconds",
        type=int,
        default=5,
        help="Initial wait seconds before capturing visible text (default: 5).",
    )
    parser.add_argument(
        "--visible-fallback-scroll-steps",
        type=int,
        default=6,
        help="How many scroll snapshots to capture in visible fallback (default: 6).",
    )
    parser.add_argument(
        "--visible-fallback-scroll-pixels",
        type=int,
        default=900,
        help="Scroll pixels per step in visible fallback (default: 900).",
    )
    parser.add_argument(
        "--whisper-cmd",
        default="whisper",
        help="Whisper command name/path for fallback mode (default: whisper)",
    )
    parser.add_argument(
        "--whisper-model",
        default="small",
        help="Whisper model name used in fallback mode (default: small)",
    )
    parser.add_argument(
        "--whisper-language",
        default="",
        help="Whisper language hint, e.g. zh or en (optional)",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=1200,
        help="Timeout for each external command in seconds (default: 1200)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.list_language_support:
        print(json.dumps(language_support_payload(args.langs), ensure_ascii=False, indent=2))
        return 0

    if not args.video_url:
        print(json.dumps({"status": "error", "error": "video_url is required unless --list-language-support is used."}, ensure_ascii=False))
        return 1

    output_dir = Path(args.output_dir).resolve()
    run_dir = make_run_dir(output_dir)
    lang_order = [x.strip() for x in args.langs.split(",") if x.strip()]
    cookies_file = Path(args.cookies_file).resolve() if args.cookies_file else None
    auth_args = yt_dlp_auth_args(
        args.cookies_from_browser.strip() or None,
        cookies_file,
    )

    try:
        segments, sub_file, _, _ = try_subtitles(
            url=args.video_url,
            run_dir=run_dir,
            auth_args=auth_args,
            lang_order=lang_order,
            timeout=args.timeout_seconds,
        )

        if segments:
            write_outputs(
                run_dir=run_dir,
                url=args.video_url,
                method="subtitle",
                source_files=[sub_file] if sub_file else [],
                segments=segments,
                note="Used subtitle track extracted by yt-dlp.",
            )
            print(json.dumps({"status": "ok", "method": "subtitle", "run_dir": str(run_dir)}, ensure_ascii=False))
            return 0

        if args.enable_whisper:
            whisper_language = args.whisper_language.strip() or None
            try:
                w_segments, txt_path = whisper_fallback(
                    url=args.video_url,
                    run_dir=run_dir,
                    auth_args=auth_args,
                    whisper_cmd=args.whisper_cmd,
                    whisper_model=args.whisper_model,
                    whisper_language=whisper_language,
                    timeout=args.timeout_seconds,
                )
                write_outputs(
                    run_dir=run_dir,
                    url=args.video_url,
                    method="whisper",
                    source_files=[txt_path],
                    segments=w_segments,
                    note="Subtitle unavailable; used whisper fallback from downloaded audio.",
                )
                print(json.dumps({"status": "ok", "method": "whisper", "run_dir": str(run_dir)}, ensure_ascii=False))
                return 0
            except Exception as whisper_exc:
                if not args.enable_visible_text_fallback:
                    raise whisper_exc

        if args.enable_visible_text_fallback:
            v_segments, v_files, v_note = visible_text_fallback(
                url=args.video_url,
                run_dir=run_dir,
                wait_seconds=args.visible_fallback_wait_seconds,
                scroll_steps=args.visible_fallback_scroll_steps,
                scroll_pixels=args.visible_fallback_scroll_pixels,
            )
            if not v_segments:
                print(
                    json.dumps(
                        {
                            "status": "error",
                            "method": "visible_text",
                            "run_dir": str(run_dir),
                            "error": "Visible-text fallback produced no text.",
                        },
                        ensure_ascii=False,
                    )
                )
                return 1

            write_outputs(
                run_dir=run_dir,
                url=args.video_url,
                method="visible_text",
                source_files=v_files,
                segments=v_segments,
                note=v_note,
            )
            print(
                json.dumps(
                    {
                        "status": "ok",
                        "method": "visible_text",
                        "run_dir": str(run_dir),
                        "hint": "Used lower-confidence visible page fallback.",
                    },
                    ensure_ascii=False,
                )
            )
            return 0

        print(
            json.dumps(
                {
                    "status": "no_subtitle",
                    "method": "none",
                    "run_dir": str(run_dir),
                    "hint": "No subtitle track found. Re-run with --enable-whisper or --enable-visible-text-fallback.",
                },
                ensure_ascii=False,
            )
        )
        return 2

    except subprocess.TimeoutExpired:
        print(json.dumps({"status": "error", "error": "Command timed out", "run_dir": str(run_dir)}, ensure_ascii=False))
        return 3
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc), "run_dir": str(run_dir)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(main())
