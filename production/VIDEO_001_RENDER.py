import asyncio, subprocess, urllib.request
from pathlib import Path
import edge_tts

OUT=Path("output"); MEDIA=OUT/"media"
MEDIA.mkdir(parents=True, exist_ok=True)
SCENES=[
("https://svs.gsfc.nasa.gov/vis/a010000/a011100/a011157/G2012-129_Earth_At_Night-720x480.webmhd.webm","night.webm","Earth after dark","From the ground, Earth feels familiar. From orbit, it becomes a living planet marked by light, weather, and a thin glowing edge.","NASA Goddard Space Flight Center — https://svs.gsfc.nasa.gov/11157/"),
("https://svs.gsfc.nasa.gov/vis/a010000/a012900/a012963/Airglow_africa_iss_20111006HD_web.webm","cities.webm","1. Lights make a map","City lights trace where people live, build, travel, and use energy. But darkness does not mean emptiness: it can mean forests, deserts, oceans, or simply fewer lights.","NASA — https://svs.gsfc.nasa.gov/12963/"),
("https://svs.gsfc.nasa.gov/vis/a010000/a012900/a012963/Airglow_lightning_iss_20150914HD.webm","lightning.webm","2. Storms flash from within","From space, lightning can illuminate cloud systems that look featureless from below. These brief pulses remind us that the atmosphere constantly moves energy around the planet.","NASA — https://svs.gsfc.nasa.gov/12963/"),
("https://svs.gsfc.nasa.gov/vis/a010000/a012900/a012963/Airglow_ISS_Airglow1-1280viz-MASTER.webm","airglow.webm","3. The atmosphere glows","The edge of Earth is not a hard line. Gases high above the clouds emit faint light called airglow. Unlike auroras, airglow is driven by ordinary solar energy and chemistry.","NASA Goddard Space Flight Center — https://svs.gsfc.nasa.gov/12963/"),
("https://svs.gsfc.nasa.gov/vis/a010000/a011600/a011615/Landsat_Global_Persp-MASTER_720x480.webmhd.webm","landsat.webm","4. Colour can be data","Some satellite views are not natural-colour photographs. Satellites measure wavelengths our eyes cannot see, including infrared, helping reveal patterns in vegetation, water, heat, and land change.","NASA Goddard Space Flight Center — https://svs.gsfc.nasa.gov/11615/"),
("https://svs.gsfc.nasa.gov/vis/a000000/a005500/a005570/Earth_wAtmos_spin_02_1080p60.mp4","earth.mp4","5. The blue edge is thin","The atmosphere that makes our world breathable is astonishingly thin compared with the planet beneath it. That layer helps regulate temperature, moves water through weather, and shields life.","NASA Scientific Visualization Studio — https://svs.gsfc.nasa.gov/5570/"),
("https://svs.gsfc.nasa.gov/vis/a010000/a012900/a012963/Airglow_europeindia_iss_20111019.webm","orbit.webm","One planet, many signals","Earth is not a still blue marble. It is a system of connected signals: lights, clouds, lightning, chemistry, land, and air. Which would you most want to see from orbit?","NASA — https://svs.gsfc.nasa.gov/12963/")
]
def run(args):
 subprocess.run(args,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
def probe(p):
 return float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(p)],text=True).strip())
def stamp(x):
 ms=int(x*1000); h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); s,ms=divmod(ms,1000); return f"{h:02}:{m:02}:{s:02},{ms:03}"
async def voice(text,path):
 await edge_tts.Communicate(text,"en-US-AriaNeural").save(str(path))
def main():
 segs=[]; caps=[]; credits=[]; clock=0
 for i,(url,fn,title,narr,credit) in enumerate(SCENES,1):
  src=MEDIA/fn
  if not src.exists():
   req=urllib.request.Request(url,headers={"User-Agent":"NASA-SVS-source-first-video"})
   with urllib.request.urlopen(req,timeout=120) as r,open(src,"wb") as f:
    while True:
     chunk=r.read(1024*1024)
     if not chunk: break
     f.write(chunk)
  audio=MEDIA/f"voice{i}.mp3"; asyncio.run(voice(narr,audio)); d=probe(audio)
  title=title.replace("'","\\'")
  vf=f"scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:black,fps=30,drawbox=x=0:y=0:w=iw:h=100:color=black@0.6:t=fill,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='{title}':fontcolor=white:fontsize=36:x=48:y=28"
  seg=MEDIA/f"scene{i}.mp4"
  run(["ffmpeg","-y","-stream_loop","-1","-i",str(src),"-i",str(audio),"-t",str(d),"-vf",vf,"-map","0:v:0","-map","1:a:0","-c:v","libx264","-preset","veryfast","-crf","21","-pix_fmt","yuv420p","-c:a","aac","-b:a","160k","-af","loudnorm=I=-16:TP=-1.5:LRA=11","-shortest",str(seg)])
  segs.append(seg); caps.append(f"{i}\n{stamp(clock)} --> {stamp(clock+d)}\n{narr}\n"); clock+=d; credits.append("- "+credit)
 concat=MEDIA/"concat.txt"; concat.write_text("".join(f"file '{p.resolve()}'\n" for p in segs))
 final=OUT/"VIDEO_001_Earth_From_Space.mp4"
 run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),"-c","copy","-movflags","+faststart",str(final)])
 (OUT/"VIDEO_001_captions.srt").write_text("\n".join(caps))
 (OUT/"VIDEO_001_credits.txt").write_text("Visual credits; source audio excluded:\n"+"\n".join(credits)+"\n\nConfirm item-specific restrictions and complete visual/audio review before publication.\n")
 (OUT/"VIDEO_001_render_report.txt").write_text(f"Draft rendered: {final.name}\nDuration: {probe(final):.1f} seconds\n1280x720, 30fps, H.264/AAC\nHuman review required. Not uploaded.\n")
 print("Draft rendered:",final)
if __name__=="__main__": main()
