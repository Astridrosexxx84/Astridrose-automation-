#!/usr/bin/env python3
"""Edit only footage that a human has explicitly approved for reuse.
Input: footage-edit-plan.json. No publishing; sources and licence records travel with output.
"""
import json, os, re, subprocess, urllib.request
from pathlib import Path

OUT = Path("edited-footage-draft")
ASSETS = OUT / "assets"
OUT.mkdir(exist_ok=True)
ASSETS.mkdir(exist_ok=True)
UA = "AstridRoseFootageEditor/1.0 (GitHub Actions; review-only)"

def run(args):
    subprocess.run(args, check=True)

def main():
    plan_path = Path("footage-edit-plan.json")
    if not plan_path.exists():
        raise SystemExit("Missing footage-edit-plan.json. Add only clips you have reviewed and are allowed to reuse.")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    clips = plan.get("clips", [])
    if not clips:
        raise SystemExit("No clips supplied. Add reviewed clip entries to footage-edit-plan.json.")
    approved = []
    for c in clips:
        if c.get("approved_for_reuse") is not True:
            raise SystemExit("Blocked: every clip must have approved_for_reuse: true after human rights review.")
        for field in ("direct_url", "source_url", "license", "license_url", "start_seconds", "duration_seconds"):
            if c.get(field) in (None, ""):
                raise SystemExit("Blocked: missing required clip field: " + field)
        if float(c["start_seconds"]) < 0 or not (0 < float(c["duration_seconds"]) <= 30):
            raise SystemExit("Clip start must be >= 0 and duration must be > 0 and <= 30 seconds.")
        approved.append(c)
    records = []
    for i, c in enumerate(approved, 1):
        url = c["direct_url"]
        if not url.startswith("https://"):
            raise SystemExit("Only HTTPS direct media URLs are accepted.")
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                data = response.read(100 * 1024 * 1024 + 1)
        except Exception as e:
            raise SystemExit(f"Could not retrieve approved clip {i}: {type(e).__name__}: {e}")
        if len(data) > 100 * 1024 * 1024:
            raise SystemExit(f"Clip {i} exceeds 100 MB safety limit.")
        src = ASSETS / f"source-{i:02d}.mp4"
        src.write_bytes(data)
        out = OUT / f"segment-{i:02d}.mp4"
        # Reframe to vertical, standardize frame rate/codec, remove original audio so
        # third-party speech/music is not accidentally carried into the edit.
        vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=25,setsar=1,format=yuv420p"
        run(["ffmpeg","-y","-ss",str(float(c["start_seconds"])),"-i",str(src),
             "-t",str(float(c["duration_seconds"])),"-an","-vf",vf,"-c:v","libx264",
             "-preset","veryfast","-crf","25","-movflags","+faststart",str(out)])
        records.append({"segment": out.name, "source_url": c["source_url"],
                        "direct_url": url, "license": c["license"],
                        "license_url": c["license_url"], "creator": c.get("creator",""),
                        "attribution": c.get("attribution",""), "start_seconds": c["start_seconds"],
                        "duration_seconds": c["duration_seconds"],
                        "human_approval_recorded": True})
    concat = OUT / "concat.txt"
    concat.write_text("".join(f"file '{(OUT / r['segment']).resolve()}'\n" for r in records), encoding="utf-8")
    silent = OUT / "picture-track.mp4"
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),"-c","copy",str(silent)])
    narration = re.sub(r"\\s+"," ",str(plan.get("narration","")).strip())
    if narration:
        (OUT/"narration.txt").write_text(narration+"\n",encoding="utf-8")
        run(["espeak-ng","-s","145","-v","en-us","-w",str(OUT/"voice.wav"),narration])
        run(["ffmpeg","-y","-i",str(silent),"-i",str(OUT/"voice.wav"),"-map","0:v:0","-map","1:a:0",
             "-c:v","copy","-af","apad","-shortest","-c:a","aac","-b:a","128k","-movflags","+faststart",
             str(OUT/"edited-video-draft.mp4")])
    else:
        run(["ffmpeg","-y","-i",str(silent),"-f","lavfi","-i","anullsrc=channel_layout=stereo:sample_rate=44100",
             "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-shortest","-movflags","+faststart",
             str(OUT/"edited-video-draft.mp4")])
    (OUT/"source-and-rights.json").write_text(json.dumps({
        "topic":plan.get("topic",""),"clips":records,
        "notice":"Human approval was asserted in the input plan, not independently verified by this script. Check source terms, commercial use, adaptation rights, attribution, music, people and third-party rights before publishing. Editing does not itself grant rights. Nothing was published."
    },indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    (OUT/"REVIEW-FIRST.txt").write_text(
        "REVIEW BEFORE USE\nThis is a vertical edit of clips marked approved by a human in footage-edit-plan.json. "
        "The editor standardizes format, trims requested moments, removes source audio, concatenates the picture track and optionally adds synthetic narration. "
        "Check rights, factual context, pacing, and every attribution. Nothing was published.\n",encoding="utf-8")
    print(f"Rendered {len(records)} reviewed clip(s) to {OUT/'edited-video-draft.mp4'}. Not published.")

if __name__ == "__main__":
    main()
