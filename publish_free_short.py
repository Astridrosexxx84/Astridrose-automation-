#!/usr/bin/env python3
"""Render and upload one original, text-led YouTube Short using free runner tools."""
import json, os, re, subprocess, sys, time, urllib.parse, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
OUT = Path("output")
OUT.mkdir(exist_ok=True)

def run(cmd):
    subprocess.run(cmd, check=True)

def wrap(draw, text, font, max_width):
    words, lines, line = text.split(), [], ""
    for word in words:
        test = (line + " " + word).strip()
        if draw.textbbox((0, 0), test, font=font)[2] <= max_width:
            line = test
        else:
            if line: lines.append(line)
            line = word
    if line: lines.append(line)
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
    total_h = len(lines) * line_h
    y = (H-total_h)//2 - 30
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
    d.text((110, H-260), f"RABBIT HOLE  /  {index+1:02d}", font=kicker_font, fill=(210,220,235))
    im.save(path, quality=95)

def get_access_token():
    form = urllib.parse.urlencode({
        "client_id": os.environ["YOUTUBE_CLIENT_ID"],
        "client_secret": os.environ["YOUTUBE_CLIENT_SECRET"],
        "refresh_token": os.environ["YOUTUBE_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=form,
        headers={"Content-Type":"application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read().decode())
    if not data.get("access_token"):
        raise RuntimeError("OAuth refresh returned no access token")
    return data["access_token"]

def upload_video(video_path, title, description, token):
    size = video_path.stat().st_size
    metadata = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": ["internet rabbit hole", "discussion", "shorts", "trending topics"],
            "categoryId": "24",
        },
        "status": {"privacyStatus":"public", "selfDeclaredMadeForKids":False},
    }
    start = urllib.request.Request(
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        data=json.dumps(metadata).encode(),
        headers={
            "Authorization":"Bearer "+token,
            "Content-Type":"application/json; charset=UTF-8",
            "X-Upload-Content-Type":"video/mp4",
            "X-Upload-Content-Length":str(size),
        }, method="POST")
    with urllib.request.urlopen(start, timeout=60) as r:
        location = r.headers.get("Location")
    if not location:
        raise RuntimeError("YouTube did not return a resumable upload URL")
    req = urllib.request.Request(location, data=video_path.read_bytes(),
        headers={"Content-Type":"video/mp4","Content-Length":str(size)}, method="PUT")
    with urllib.request.urlopen(req, timeout=180) as r:
        result = json.loads(r.read().decode())
    return result

def main():
    topic = os.getenv("DISCOVERY_TOPIC", "").strip()
    if not topic:
        raise RuntimeError("DISCOVERY_TOPIC is empty")
    topic = re.sub(r"\\s+", " ", topic).strip()[:100]
    safe = re.sub(r"[^A-Za-z0-9 ]+", "", topic).strip()
    title = ("The Internet Rabbit Hole: " + safe)[:95]
    slides = [
        ("THIS WEEK'S RABBIT HOLE", topic, "A quick original conversation starter"),
        ("QUESTION 1", "Why does this grab people's attention?", "Think beyond the obvious answer"),
        ("QUESTION 2", "What's the biggest misconception?", "Share a take, not just a hot take"),
        ("QUESTION 3", "What would you tell a beginner?", "One useful tip can start a great thread"),
        ("YOUR TURN", "Agree, disagree, or add context", "Make the comments more interesting"),
        ("NEXT RABBIT HOLE", "What should we explore next?", "Comment below and follow for the next topic"),
    ]
    frames = []
    for i, (k,h,s) in enumerate(slides):
        p = OUT / f"slide{i:02d}.png"
        make_slide(p,k,h,s,i)
        frames.append(p)
    concat = OUT / "slides.txt"
    with concat.open("w", encoding="utf-8") as f:
        for p in frames:
            f.write(f"file '{p.resolve()}'\n")
            f.write("duration 3.8\n")
        f.write(f"file '{frames[-1].resolve()}'\n")
    narration = (
        f"Today's internet rabbit hole is {topic}. "
        "Question one: why does this grab people's attention? "
        "Question two: what's the biggest misconception? "
        "Question three: what would you tell a beginner? "
        "Share your take in the comments, and follow for the next rabbit hole."
    )
    run(["espeak-ng", "-s", "155", "-v", "en-us", "-w", str(OUT/"voice.wav"), narration])
    run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),"-i",str(OUT/"voice.wav"),
         "-vf","fps=30,scale=1080:1920,format=yuv420p","-af","apad=pad_dur=4",
         "-t","23","-c:v","libx264","-preset","veryfast","-crf","24",
         "-c:a","aac","-b:a","128k","-movflags","+faststart",str(OUT/"free-original-short.mp4")])
    video = OUT/"free-original-short.mp4"
    description = (
        f"An original discussion starter about {topic}. No borrowed video clips or music. "
        "What do you think? Add a thoughtful answer below.\n\n"
        "#Shorts #Discussion #InternetRabbitHole"
    )
    token = get_access_token()
    result = upload_video(video, title, description, token)
    video_id = result.get("id")
    status = result.get("status", {}).get("privacyStatus", "unknown")
    with open("published-video-result.txt","w",encoding="utf-8") as f:
        f.write(f"Title: {title}\nVideo ID: {video_id}\nRequested visibility: public\nReturned visibility: {status}\n")
        if video_id: f.write(f"URL: https://www.youtube.com/watch?v={video_id}\n")
    print(f"Uploaded video {video_id}; returned visibility={status}")
    if not video_id:
        raise RuntimeError("YouTube upload response contained no video ID")
    if status != "public":
        print("WARNING: YouTube did not confirm public visibility; check API project verification and YouTube Studio.", file=sys.stderr)

if __name__ == "__main__":
    main()
