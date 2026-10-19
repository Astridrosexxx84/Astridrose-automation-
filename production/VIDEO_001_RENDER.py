import asyncio, subprocess, urllib.request
from pathlib import Path
import edge_tts

OUT=Path("output"); MEDIA=OUT/"media"
MEDIA.mkdir(parents=True, exist_ok=True)
SCENES=[
("https://svs.gsfc.nasa.gov/vis/a010000/a011100/a011157/G2012-129_Earth_At_Night-720x480.webmhd.webm","night.webm","Earth after dark","From the ground, Earth feels solid and familiar. We see a horizon, a skyline, or the weather passing overhead. But pull back far enough and familiar views become patterns. Night lights trace human activity. Lightning flashes inside enormous storms. A faint glow outlines the atmosphere. Satellites reveal colours and changes our eyes could never see on their own. These are five things that become easier to notice when we look at Earth from space.","NASA Goddard Space Flight Center — https://svs.gsfc.nasa.gov/11157/"),
("https://svs.gsfc.nasa.gov/vis/a010000/a012900/a012963/Airglow_africa_iss_20111006HD_web.webm","cities.webm","1. Lights make a map","At night, towns and cities draw bright lines across the dark surface. Roads connect clusters of light, while coastlines can appear as necklaces of settlements. But brightness is not a simple map of population or activity. Fires and gas flares can shine too. The global night view is assembled from satellite observations taken over time, not one exposure at one instant. It is a powerful picture, but also a data visualization. And the dark spaces matter just as much: ocean, desert, forest, and places where artificial light is sparse.","NASA — https://svs.gsfc.nasa.gov/12963/"),
("https://svs.gsfc.nasa.gov/vis/a010000/a012900/a012963/Airglow_lightning_iss_20150914HD.webm","lightning.webm","2. Storms flash from within","Storms look different from orbit. A cloud deck that seems like a flat grey ceiling from the ground can reveal structure and motion from above. Lightning appears in brief flashes, exposing energy moving through a storm system. A single frame captures one moment, but repeated observations help scientists track how weather develops. Satellites do not make the atmosphere simple; they give us another angle on a system that is always changing.","NASA — https://svs.gsfc.nasa.gov/12963/"),
("https://svs.gsfc.nasa.gov/vis/a010000/a012900/a012963/Airglow_ISS_Airglow1-1280viz-MASTER.webm","airglow.webm","3. The atmosphere glows","Look toward the curved edge of Earth and you may notice a thin band of colour above the clouds. The atmosphere does not end at a neat visible boundary. High in the sky, gases can emit faint light in a phenomenon called airglow. It can resemble a glowing ribbon along the horizon, but it is not a solid shell or a painted line. It is light produced by processes in the upper atmosphere. From the ground, the scale is difficult to appreciate; from orbit, the delicate edge becomes visible against space.","NASA Goddard Space Flight Center — https://svs.gsfc.nasa.gov/12963/"),
("https://svs.gsfc.nasa.gov/vis/a010000/a011600/a011615/Landsat_Global_Persp-MASTER_720x480.webmhd.webm","landsat.webm","4. Colour can be data","Some colourful views of Earth are not photographs in the ordinary sense. Satellite instruments measure different wavelengths of light, including parts of the spectrum human eyes cannot see. Scientists can assign visible colours to those measurements to make patterns easier to interpret. A bright red or electric blue region may represent a measurement channel rather than the colour you would see standing there. These images can reveal vegetation, water, ice, and changes across the land. The key is to understand what the colours represent before deciding what the image is telling us.","NASA Goddard Space Flight Center — https://svs.gsfc.nasa.gov/11615/"),
("https://svs.gsfc.nasa.gov/vis/a000000/a005500/a005570/Earth_wAtmos_spin_02_1080p60.mp4","earth.mp4","5. The blue edge is thin","The atmosphere looks vast when we watch clouds roll over a landscape, yet against the size of the planet its life-supporting layers are remarkably thin. The air around us carries water, redistributes heat, and helps protect life at the surface. Visualizations may exaggerate the thickness of the boundary so it is visible on screen. The important point is not a perfectly scaled glowing line. It is that the conditions we depend on occupy a narrow envelope around a much larger world.","NASA Scientific Visualization Studio — https://svs.gsfc.nasa.gov/5570/"),
("https://svs.gsfc.nasa.gov/vis/a010000/a012900/a012963/Airglow_europeindia_iss_20111019.webm","orbit.webm","One planet, many signals","From orbit, Earth is never just a still blue marble. It is a changing system: cities illuminate the night, storms move energy through the atmosphere, high-altitude gases glow, and satellite instruments turn invisible measurements into visible patterns. Each view answers a different question, and each comes with limits that matter. The next time you see a dramatic image of our planet, ask what the instrument actually measured and how the image was made. Which view would you most want to see: the night lights, the storms, or the glowing edge of the atmosphere?","NASA — https://svs.gsfc.nasa.gov/12963/")
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
  base_filter="crop=iw:ih*0.62:0:ih*0.38,scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:black" if i==5 else "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2:black"
  vf=f"{base_filter},fps=30,drawbox=x=0:y=0:w=iw:h=100:color=black@0.6:t=fill,drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:text='{title}':fontcolor=white:fontsize=36:x=48:y=28"
  seg=MEDIA/f"scene{i}.mp4"
  run(["ffmpeg","-y","-stream_loop","-1","-i",str(src),"-i",str(audio),"-t",str(d),"-vf",vf,"-map","0:v:0","-map","1:a:0","-c:v","libx264","-preset","veryfast","-crf","21","-pix_fmt","yuv420p","-c:a","aac","-b:a","160k","-af","loudnorm=I=-16:TP=-1.5:LRA=11","-shortest",str(seg)])
  segs.append(seg); caps.append(f"{i}\n{stamp(clock)} --> {stamp(clock+d)}\n{narr}\n"); clock+=d; credits.append("- "+credit)
 concat=MEDIA/"concat.txt"; concat.write_text("".join(f"file '{p.resolve()}'\n" for p in segs))
 final=OUT/"VIDEO_001_Earth_From_Space.mp4"
 run(["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),"-c","copy","-movflags","+faststart",str(final)])
 (OUT/"VIDEO_001_captions.srt").write_text("\n".join(caps))
 (OUT/"VIDEO_001_credits.txt").write_text("Visual credits; source audio excluded:\n"+"\n".join(credits)+"\n\nConfirm item-specific restrictions and complete visual/audio review before publication.\n")
 duration=probe(final)
 info=subprocess.check_output(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height,r_frame_rate","-of","default=noprint_wrappers=1",str(final)],text=True).strip()
 black=subprocess.run(["ffmpeg","-hide_banner","-i",str(final),"-vf","blackdetect=d=1.0:pix_th=0.10","-an","-f","null","-"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 black_hits=[line.strip() for line in black.stderr.splitlines() if "black_start:" in line]
 if duration < 120: raise RuntimeError(f"Quality gate failed: duration only {duration:.1f}s; expected at least 120s.")
 if "width=1280" not in info or "height=720" not in info: raise RuntimeError("Quality gate failed: output is not 1280x720.")
 if len(segs)!=7 or len(caps)!=7 or len(credits)!=7: raise RuntimeError("Quality gate failed: scene, caption, or credit count mismatch.")
 scan_note=("Blackdetect flagged possible dark intervals for human review: "+"; ".join(black_hits[:5])) if black_hits else "Blackdetect: no intervals flagged"\n (OUT/"VIDEO_001_render_report.txt").write_text(f"TECHNICAL QC: PASS\nFile: {final.name}\nDuration: {duration:.1f} seconds\n{info}\nScenes: {len(segs)}\nCaptions: {len(caps)}\nCredits: {len(credits)}\n{scan_note}\nStatus: candidate for final human review; not uploaded.\n")
 print("Draft rendered:",final)
if __name__=="__main__": main()
