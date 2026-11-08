import subprocess,sys
from pathlib import Path
import imageio_ffmpeg
from PIL import Image
f=imageio_ffmpeg.get_ffmpeg_exe(); src=sys.argv[1]; times=[float(x) for x in sys.argv[2].split(",")]; out=sys.argv[3]
ims=[]
for i,t in enumerate(times):
    p=f"/tmp/_f{i}.png"; subprocess.run([f,"-y","-ss",str(t),"-i",src,"-frames:v","1","-vf","scale=800:-1",p],capture_output=True); ims.append(Image.open(p))
cols=2; rows=(len(ims)+1)//2; W=Image.new("RGB",(800*cols,450*rows))
for i,im in enumerate(ims): W.paste(im,((i%cols)*800,(i//cols)*450))
W.save(out)
