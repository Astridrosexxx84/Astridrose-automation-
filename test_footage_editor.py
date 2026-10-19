#!/usr/bin/env python3
"""Create a tiny synthetic test clip, then run the same vertical edit operations.
No third-party footage, no publishing, and no AI credits.
"""
import subprocess
from pathlib import Path
out=Path("editor-self-test"); out.mkdir(exist_ok=True)
src=out/"synthetic-source.mp4"
segment=out/"vertical-trimmed-segment.mp4"
final=out/"editor-self-test.mp4"
def run(args): subprocess.run(args,check=True)
run(["ffmpeg","-y","-f","lavfi","-i","testsrc2=size=640x360:rate=25","-f","lavfi","-i","sine=frequency=440:duration=8","-t","8","-c:v","libx264","-pix_fmt","yuv420p","-c:a","aac",str(src)])
run(["ffmpeg","-y","-ss","1","-i",str(src),"-t","4","-an","-vf","scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=25,setsar=1,format=yuv420p","-c:v","libx264","-preset","veryfast","-crf","25",str(segment)])
run(["ffmpeg","-y","-f","lavfi","-i","sine=frequency=660:duration=4","-i",str(segment),"-map","1:v:0","-map","0:a:0","-c:v","copy","-c:a","aac","-shortest","-movflags","+faststart",str(final)])
run(["ffprobe","-v","error","-show_entries","format=duration:stream=codec_type,codec_name,width,height","-of","json",str(final)])
(out/"SELF-TEST.txt").write_text("PASS if workflow completed: generated synthetic footage, trimmed 1-5 seconds, reframed to 1080x1920, removed source audio, added test tone, and verified MP4 metadata. Synthetic footage only; this does not prove external clip rights or production source downloads. Nothing published.\n",encoding="utf-8")
print("SELF-TEST PASS: "+str(final))
