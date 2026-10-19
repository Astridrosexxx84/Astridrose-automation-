#!/usr/bin/env python3
"""Render a basic text-led vertical video draft without uploading it anywhere."""
import os
import re
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
OUT = Path("output")
OUT.mkdir(exist_ok=True)

def run(cmd):
    subprocess.run(cmd, check=True)

def wrap(draw, text, font, max_width):
    lines, line = [], ""
    for word in text.split():
        test = (line + " " + word).strip()
        if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
            line = test
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines

def make_slide(path, kicker, headline, subline, index):
    palettes = [
        ((13, 18, 42), (48, 34, 92)), ((16, 36, 58), (20, 91, 112)),
        ((47, 23, 55), (121, 42, 86)), ((24, 43, 35), (38, 112, 82)),
        ((50, 34, 17), (145, 76, 28)), ((22, 26, 39), (65, 77, 110)),
    ]
    top, bottom = palettes[index % len(palettes)]
    im = Image.new("RGB", (W, H))
    pix = im.load()
    for y in range(H):
        t = y / (H - 1)
        c = tuple(int(top[i] * (1-t) + bottom[i] * t) for i in range(3))
        for x in range(W):
            pix[x, y] = c
    d = ImageDraw.Draw(im)
    regular = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    kicker_font = ImageFont.truetype(bold, 34)
    headline_font = ImageFont.truetype(bold, 76 if len(headline) < 34 else 62)
    sub_font = ImageFont.truetype(regular, 40)
    d.rounded_rectangle((70, 180, W-70, H-180), radius=42, outline=(255,255,255), width=3)
    d.text((110, 260), kicker.upper(), font=kicker_font, fill=(130, 235, 255))
    lines = wrap(d, headline, headline_font, W-220)
    line_h = 100 if headline_font.size > 65 else 84
    y = (H-len(lines)*line_h)//2 - 30
    for line in lines:
        box = d.textbbox((0,0), line, font=headline_font)
        d.text(((W-(box[2]-box[0]))//2, y), line, font=headline_font, fill="white")
        y += line_h
    sub_lines = wrap(d, subline, sub_font, W-220)
    sy = H-480
    for line in sub_lines:
        box = d.textbbox((0,0), line, font=sub_font)
        d.text(((W-(box[2]-box[0]))//2, sy), line, font=sub_font, fill=(232,238,248))
        sy += 58
    d.text((110, H-260), f"FIRST DRAFT  /  {index+1:02d}", font=kicker_font, fill=(210,220,235))
    im.save(path, quality=95)

def main():
    topic = re.sub(r"\s+", " ", os.getenv("DISCOVERY_TOPIC", "").strip())[:100]
    if not topic:
        raise RuntimeError("DISCOVERY_TOPIC is empty; provide a topic in the workflow input.")
    slides = [
        ("THE BIG QUESTION", topic, "What makes this worth talking about?"),
        ("THE CONTEXT", "What do we actually know?", "Separate confirmed facts from guesses"),
        ("THE SURPRISE", "Look for the unexpected detail", "Find a fact that changes the obvious story"),
        ("THE DEBATE", "Where do people disagree?", "Show more than one reasonable perspective"),
        ("THE PAYOFF", "What should viewers take away?", "Answer the question promised at the start"),
        ("YOUR TURN", "What's your take?", "Invite a specific, thoughtful response"),
    ]
    frames = []
    for i, (k, h, sub) in enumerate(slides):
        p = OUT / f"draft-slide-{i+1:02d}.png"
        make_slide(p, k, h, sub, i)
        frames.append(p)
    concat = OUT / "draft-slides.txt"
    with concat.open("w", encoding="utf-8") as f:
        for p in frames:
            f.write(f"file '{p.resolve()}'\n")
            f.write("duration 3.8\n")
        f.write(f"file '{frames[-1].resolve()}'\n")
    narration = (
        f"Today's topic is {topic}. First, what do we actually know? "
        "Next, look for the unexpected detail that changes the obvious story. "
        "Then consider where people reasonably disagree. "
        "The goal is to leave with a useful takeaway, not just a hot take. "
        "What's your take?"
    )
    run(["espeak-ng", "-s", "155", "-v", "en-us", "-w", str(OUT/"draft-voice.wav"), narration])
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
         "-i", str(OUT/"draft-voice.wav"), "-vf", "fps=30,scale=1080:1920,format=yuv420p",
         "-af", "apad=pad_dur=4", "-t", "23", "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "24", "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
         str(OUT/"content-draft.mp4")])
    Path("content-draft-result.txt").write_text(
        f"Draft rendered successfully\nTopic: {topic}\nFile: output/content-draft.mp4\n"
        "Status: DRAFT ONLY — not uploaded or published.\n"
        "Important: placeholder structure only; research facts and replace generic slides before publishing.\n",
        encoding="utf-8",
    )
    print("Created output/content-draft.mp4 (draft only; no upload attempted).")

if __name__ == "__main__":
    main()
