#!/usr/bin/env python3
"""Create a short, image-led video draft from verifiable Wikimedia Commons leads.
No publishing. Every downloaded asset keeps its source/licence/attribution record.
"""
import html, json, os, re, subprocess, time, urllib.parse, urllib.request
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
W,H=1080,1920
OUT=Path("video-draft"); ASSETS=OUT/"assets"; OUT.mkdir(exist_ok=True); ASSETS.mkdir(exist_ok=True)
UA="AstridRoseFreeVideoDraft/1.0 (GitHub Actions; research prototype)"
def get(url,timeout=15):
    req=urllib.request.Request(url,headers={"User-Agent":UA})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req,timeout=timeout) as r:return r.read()
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 2: raise
            time.sleep(3 * (attempt + 1))
def tokens(s): return {x for x in re.findall(r"[a-z0-9]{3,}",s.casefold())}
def wrap(draw,text,font,width):
    lines=[]; cur=""
    for word in text.split():
        test=(cur+" "+word).strip()
        if draw.textbbox((0,0),test,font=font)[2] <= width:cur=test
        else:
            if cur:lines.append(cur)
            cur=word
    if cur:lines.append(cur)
    return lines
def main():
    topic=re.sub(r"\s+"," ",os.getenv("VIDEO_TOPIC","").strip())[:100]
    if not topic: raise SystemExit("VIDEO_TOPIC is required")
    topic_words=tokens(topic)-{"the","and","for","with","from","into"}
    queries=[topic] + (topic.split() if " " in topic else [])
    candidates=[]; seen=set()
    for query in queries:
        api="https://commons.wikimedia.org/w/api.php?"+urllib.parse.urlencode({
          "action":"query","format":"json","generator":"search","gsrsearch":query,
          "gsrnamespace":"6","gsrlimit":"50","prop":"imageinfo","iiprop":"url|mime|extmetadata"})
        data=json.loads(get(api))
        for p in data.get("query",{}).get("pages",{}).values():
            info=(p.get("imageinfo") or [{}])[0]; meta=info.get("extmetadata",{})
            title=p.get("title",""); overlap=topic_words & tokens(title)
            def val(k): return re.sub(r"<[^>]*>","",str(meta.get(k,{}).get("value",""))).strip()
            lic=val("LicenseShortName"); licurl=val("LicenseUrl")
            if not overlap or not info.get("url") or not info.get("mime","").startswith("image/"): continue
            ll=lic.casefold().replace("creative commons","cc").replace("attribution-sharealike","by-sa").replace("attribution-share-alike","by-sa").replace("attribution","by")
            allowed=(ll in {"cc0","public domain","pd","cc by","cc by 2.0","cc by 3.0","cc by 4.0","cc by-sa","cc by-sa 2.0","cc by-sa 3.0","cc by-sa 4.0"} or ll.startswith("cc by ") or ll.startswith("cc by-sa "))
            if not allowed or not licurl: continue
            if info["url"] in seen: continue
            seen.add(info["url"])
            candidates.append({"title":title,"url":info["url"],"page_url":info.get("descriptionurl",""),
              "creator":val("Artist") or val("Credit") or "Creator not stated",
              "license":lic,"license_url":licurl,"overlap":sorted(overlap)})
        if len(candidates)>=5: break
    candidates.sort(key=lambda a:(-len(a["overlap"]),a["title"].casefold()))
    candidates=candidates[:5]
    if not candidates: raise SystemExit("No relevant Commons images with explicit reusable licence metadata. No video generated; inspect another topic or review media manually.")
    # Use the encyclopedia intro as a research starting point, not as an automatically verified script.
    q="https://en.wikipedia.org/w/api.php?"+urllib.parse.urlencode({"action":"query","format":"json","prop":"extracts|info","exintro":"1","explaintext":"1","inprop":"url","redirects":"1","titles":topic})
    wd=json.loads(get(q)); pages=wd.get("query",{}).get("pages",{}); page=next((v for v in pages.values() if "missing" not in v),{})
    research=re.sub(r"\s+"," ",page.get("extract","")).strip()
    if len(research)<120: raise SystemExit("Not enough encyclopedia research returned; refusing to invent narration.")
    research_url=page.get("fullurl","https://en.wikipedia.org/w/index.php?"+urllib.parse.urlencode({"search":topic}))
    # A short intro only; it is explicitly a review draft.
    narration=research[:900]
    # End on a complete sentence so the synthetic voice never trails off mid-thought.
    sentence_ends=[m.end() for m in re.finditer(r"[.!?](?:\s|$)",narration)]
    if sentence_ends: narration=narration[:sentence_ends[-1]].strip()
    else: narration=research[:650].rsplit(" ",1)[0].strip()+ "."
    narration += " This is a first research draft: check every detail and the image credits before use."
    (OUT/"narration.txt").write_text(narration+"\n",encoding="utf-8")
    (OUT/"source-and-rights.json").write_text(json.dumps({"topic":topic,"research_url":research_url,"research_status":"UNVERIFIED DRAFT","assets":candidates,"notice":"No asset is legally cleared by this script. Confirm source page, licence version, attribution, adaptation/share-alike requirements and third-party rights."},indent=2,ensure_ascii=False),encoding="utf-8")
    font="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"; bold="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    frames=[]
    for i,a in enumerate(candidates):
        try:
            raw=get(a["url"],timeout=25)
            import io
            from PIL import ImageOps
            im=ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert("RGB")
            im.thumbnail((W,1100))
        except Exception as e:
            print("Skipping unavailable or unreadable image",a["title"],repr(e))
            continue
        p=ASSETS/f"image-{i+1}.bin"; p.write_bytes(raw)
        canvas=Image.new("RGB",(W,H),(12,18,34))
        # Fill top visual area with a blurred-ish dark solid backdrop and fit original image without cropping.
        im.thumbnail((W-60,1050))
        canvas.paste(im,((W-im.width)//2,110))
        d=ImageDraw.Draw(canvas); hf=ImageFont.truetype(bold,54); bf=ImageFont.truetype(font,31)
        d.text((60,1240),topic[:70],font=hf,fill="white")
        d.text((60,1320),f"IMAGE {i+1} · {a['license']}",font=bf,fill=(130,225,255))
        title=a["title"].replace("File:","")
        for j,line in enumerate(wrap(d,title,bf,W-120)[:3]): d.text((60,1400+j*43),line,font=bf,fill=(230,235,245))
        d.text((60,1630),"Research draft · verify facts and credits",font=bf,fill=(210,210,220))
        fp=OUT/f"frame-{i+1:02d}.png"; canvas.save(fp); frames.append(fp)
    if not frames: raise SystemExit("All candidate images failed to decode.")
    wav=OUT/"voice.wav"; subprocess.run(["espeak-ng","-s","145","-v","en-us","-w",str(wav),narration],check=True)
    # Each still gets equal time, with a final still repeated for concat demuxer.
    concat=OUT/"frames.txt"
    duration=max(4.0, min(9.0, 30.0/len(frames)))
    with concat.open("w") as f:
        for fp in frames: f.write(f"file '{fp.resolve()}'\nduration {duration}\n")
        f.write(f"file '{frames[-1].resolve()}'\n")
    subprocess.run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),"-i",str(wav),
      "-vf","fps=25,format=yuv420p","-af","apad","-shortest","-c:v","libx264","-preset","veryfast","-crf","25",
      "-c:a","aac","-b:a","128k","-movflags","+faststart",str(OUT/"video-draft.mp4")],check=True)
    (OUT/"REVIEW-FIRST.txt").write_text(
      f"TOPIC: {topic}\nDraft video: video-draft.mp4\nResearch starting point: {research_url}\n\n"
      "NOT READY TO PUBLISH. This is a proof of concept made from relevant Wikimedia Commons still images, synthetic narration and a research excerpt. "
      "Verify factual accuracy, each original file page, attribution and exact licence conditions. This is not footage-heavy yet. Nothing was uploaded or published.\n",
      encoding="utf-8")
    print(f"Created {OUT/'video-draft.mp4'} using {len(frames)} candidate still images. Not published.")
if __name__=="__main__": main()
