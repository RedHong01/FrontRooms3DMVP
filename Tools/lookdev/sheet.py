import sys, numpy as np
from PIL import Image, ImageDraw
T=sys.argv[1]; out=sys.argv[2]; names=sys.argv[3:]
cells=[]
for name in names:
    A=np.asarray(Image.open(f"{T}/{name}_A.png").convert("RGB")).astype(np.float32)/255
    try: N=np.asarray(Image.open(f"{T}/{name}_N.png").convert("RGB")).astype(np.float32)/255*2-1
    except: N=None
    h,w,_=A.shape
    tile=np.concatenate([np.concatenate([A,A],1)]*2,0)
    big=Image.fromarray((tile*255).astype(np.uint8)).resize((420,int(420*tile.shape[0]/tile.shape[1])))
    c=A[h//3:h//3+420, w//3:w//3+420]
    if N is not None:
        n=N[h//3:h//3+420, w//3:w//3+420]; L=np.array([-.6,.5,.62]); L/=np.linalg.norm(L)
        c=np.clip(c*(0.35+0.9*np.clip((n*L).sum(-1),0,1)[...,None]),0,1)
    crop=Image.fromarray((c*255).astype(np.uint8))
    cell=Image.new("RGB",(860,max(big.height,crop.height)+26),(24,24,24))
    cell.paste(big,(0,26)); cell.paste(crop,(440,26)); ImageDraw.Draw(cell).text((4,6),name,fill=(240,230,160))
    cells.append(cell)
H=sum(c.height for c in cells); sheet=Image.new("RGB",(860,H),(24,24,24)); y=0
for c in cells: sheet.paste(c,(0,y)); y+=c.height
sheet.save(out)
