import sys, numpy as np
from PIL import Image
T=sys.argv[1]; name=sys.argv[2]; out=sys.argv[3]
A=np.asarray(Image.open(f"{T}/{name}_A.png").convert("RGB")).astype(np.float32)/255
try: N=np.asarray(Image.open(f"{T}/{name}_N.png").convert("RGB")).astype(np.float32)/255*2-1
except: N=None
h,w,_=A.shape
# tile 2x2 downscaled to show seams/repetition
tile=np.concatenate([np.concatenate([A,A],1)]*2,0)
im=Image.fromarray((tile*255).astype(np.uint8)).resize((900,int(900*tile.shape[0]/tile.shape[1])))
# 1:1 crop with grazing light shading
c=A[h//3:h//3+700, w//3:w//3+700]
if N is not None:
    n=N[h//3:h//3+700, w//3:w//3+700]
    L=np.array([-.6,.5,.62]); L/=np.linalg.norm(L)
    sh=np.clip((n*L).sum(-1),0,1)[...,None]
    c=np.clip(c*(0.35+0.9*sh),0,1)
crop=Image.fromarray((c*255).astype(np.uint8))
H=max(im.height,crop.height)
sheet=Image.new("RGB",(im.width+crop.width+20,H),(20,20,20))
sheet.paste(im,(0,0)); sheet.paste(crop,(im.width+20,0))
sheet.save(out)
