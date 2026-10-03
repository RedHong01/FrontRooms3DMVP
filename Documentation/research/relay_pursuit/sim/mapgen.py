# Python port of FrontRoomsMap.cs generator (no modules/columns/keys) to test
# whether the entry cell behind door D stays connected once the start area R is walled.
import math, random, sys
from collections import deque
M=0xffffffff
def mix(h):
    h^=h>>16; h=(h*0x7feb352d)&M; h^=h>>15; h=(h*0x846ca68b)&M; h^=h>>16; return h
def H(seed,a,b,salt,rev=0):
    h=mix((seed&M)^0x9e3779b9)
    h=mix(h^((a&M)*0x85ebca6b&M))
    h=mix(h^((b&M)*0xc2b2ae35&M))
    h=mix(h^((salt&M)*0x27d4eb2f&M))
    h=mix(h^((rev&M)*0x165667b1&M))
    return h
def unit(h): return (h>>8)*(1.0/16777216.0)
def nxt(s):
    s^=(s<<13)&M; s^=s>>17; s^=(s<<5)&M; return s&M
SiteX,SiteZ,Height,EdgeEast,EdgeNorth,GateEast,GateNorth,Tree,Rooms_,Theme=11,13,17,23,29,31,37,41,53,59
N=8; CS=3.0; CH=24.0
LOW,STD,TALL=0,1,2
S=dict(low=.35,std=.55,tall=.10,lowDoorway=.25,stdDoorway=.30,tallDoorway=.10,lowWall=.5,lowArch=.2,stdWall=.82,stdArch=.10,tallWall=.3,tallArch=.1,
       rooms={LOW:(2,2,3),STD:(2,2,4),TALL:(1,5,7)},border=.15,office=.3)
def fdiv(a,b): return a//b
class Gen:
    def __init__(s,seed): s.seed=seed; s.zones={}; s.cz={}; s.chunks={}
    def zone(s,c):
        if c in s.zones: return s.zones[c]
        sd=s.seed
        sx=(c[0]+.15+.7*unit(H(sd,c[0],c[1],SiteX)))*CH
        sz=(c[1]+.15+.7*unit(H(sd,c[0],c[1],SiteZ)))*CH
        roll=unit(H(sd,c[0],c[1],Height))*(S['low']+S['std']+S['tall'])
        h=LOW if roll<S['low'] else STD if roll<S['low']+S['std'] else TALL
        th=1 if (h==STD and unit(H(sd,c[0],c[1],Theme))<S['office']) else 0
        z=(c,h,th,sx,sz); s.zones[c]=z; return z
    def zoneof(s,cell):
        if cell in s.cz: return s.zone(s.cz[cell])
        ch=(fdiv(cell[0],N),fdiv(cell[1],N)); cx=(cell[0]+.5)*CS; cz=(cell[1]+.5)*CS
        best=1e30; bid=ch
        for dy in range(-2,3):
            for dx in range(-2,3):
                cand=s.zone((ch[0]+dx,ch[1]+dy)); d=(cand[3]-cx)**2+(cand[4]-cz)**2
                if d<best-1e-4 or (abs(d-best)<=1e-4 and (cand[0][0]<bid[0] or (cand[0][0]==bid[0] and cand[0][1]<bid[1]))):
                    best=d; bid=cand[0]
        s.cz[cell]=bid; return s.zone(bid)
    def height(s,cell): return s.zoneof(cell)[1]
    def resolve(s,a,b,req,inroom,roll):
        ha=s.height(a); hb=s.height(b)
        if ha!=hb:
            ex='Window' if (ha==TALL or hb==TALL) else 'Door'
            return ex if (req or roll<S['border']) else 'Wall'
        if inroom: return 'Open'
        if ha==LOW: dw,w,ar=S['lowDoorway'],S['lowWall'],S['lowArch']
        elif ha==TALL: dw,w,ar=S['tallDoorway'],S['tallWall'],S['tallArch']
        else: dw,w,ar=S['stdDoorway'],S['stdWall'],S['stdArch']
        if req: return 'Arch' if roll<dw else 'Open'
        return 'Wall' if roll<w else 'Arch' if roll<w+ar else 'Open'
    def border(s,cell,east):
        ch=(fdiv(cell[0],N),fdiv(cell[1],N))
        local=cell[1]-ch[1]*N if east else cell[0]-ch[0]*N
        gate=H(s.seed,ch[0],ch[1],GateEast if east else GateNorth)%N
        other=(cell[0]+1,cell[1]) if east else (cell[0],cell[1]+1)
        roll=unit(H(s.seed,cell[0],cell[1],EdgeEast if east else EdgeNorth))
        return s.resolve(cell,other,local==gate,False,roll)
    def chunk(s,c):
        if c in s.chunks: return s.chunks[c]
        sd=s.seed; n=N
        te=[False]*64; tn=[False]*64; vis=[False]*64
        rng=H(sd,c[0],c[1],Tree)|1
        rng=nxt(rng); start=rng%64; st=[start]; vis[start]=True
        while st:
            cur=st[-1]; ci=cur%n; cj=cur//n; ch=[]
            if ci+1<n and not vis[cur+1]: ch.append(cur+1)
            if ci>0 and not vis[cur-1]: ch.append(cur-1)
            if cj+1<n and not vis[cur+n]: ch.append(cur+n)
            if cj>0 and not vis[cur-n]: ch.append(cur-n)
            if not ch: st.pop(); continue
            rng=nxt(rng); nx=ch[rng%len(ch)]
            if nx==cur+1: te[cur]=True
            elif nx==cur-1: te[nx]=True
            elif nx==cur+n: tn[cur]=True
            else: tn[nx]=True
            vis[nx]=True; st.append(nx)
        room=[0]*64
        own=s.zone(c)[1]; cnt,mn,mx=S['rooms'][own]
        rr=H(sd,c[0],c[1],Rooms_)|1
        for r in range(1,cnt+1):
            rr=nxt(rr); w=mn+rr%(mx-mn+1)
            rr=nxt(rr); h=mn+rr%(mx-mn+1)
            rr=nxt(rr); x0=rr%(n-w+1)
            rr=nxt(rr); y0=rr%(n-h+1)
            for y in range(y0,y0+h):
                for x in range(x0,x0+w): room[x+y*n]=r
        E=[None]*64; NO=[None]*64
        for j in range(n):
            for i in range(n):
                k=i+j*n; cell=(c[0]*n+i,c[1]*n+j)
                E[k]=s.resolve(cell,(cell[0]+1,cell[1]),te[k],room[k]!=0 and room[k]==room[k+1],unit(H(sd,cell[0],cell[1],EdgeEast))) if i<n-1 else s.border(cell,True)
                NO[k]=s.resolve(cell,(cell[0],cell[1]+1),tn[k],room[k]!=0 and room[k]==room[k+n],unit(H(sd,cell[0],cell[1],EdgeNorth))) if j<n-1 else s.border(cell,False)
        s.chunks[c]=(E,NO); return s.chunks[c]
    def edge(s,a,b):
        if b[0]<a[0] or b[1]<a[1]: a,b=b,a
        east=b[0]==a[0]+1
        c=(fdiv(a[0],N),fdiv(a[1],N)); E,NO=s.chunk(c)
        k=(a[0]-c[0]*N)+(a[1]-c[1]*N)*N
        return E[k] if east else NO[k]

def spiral(r):
    out=[(0,0)]
    for ring in range(1,r+1):
        for dy in range(-ring,ring+1):
            for dx in range(-ring,ring+1):
                if max(abs(dx),abs(dy))==ring: out.append((dx,dy))
    return out
SP=spiral(8)
def trial(seed,camz):
    g=Gen(seed)
    c=math.floor((camz+6)/12); endc=-6+12*(c+1)
    K=c+1 if endc-camz<4 else c
    D=-6+12*(K+1)
    oldest=c-2 if camz< (-6+12*c)+4 else c-1
    oldest=max(oldest, K-4, 0) if True else oldest
    Sz=-6+12*oldest
    X0,X1=83,88  # world cells x 249..264
    Yd=D//3; Ys=Sz//3
    root=None
    for (a,b) in SP:
        ok=True
        for X in range(X0,X1):
            z=g.zoneof((X-64*a,Yd-64*b))
            if z[1]!=STD or z[2]!=0: ok=False;break
        if ok: root=(a,b);break
    if root is None: return None
    a,b=root
    R=set((X-64*a,Y-64*b) for X in range(X0,X1) for Y in range(Ys,Yd))
    start=(85-64*a,Yd-64*b)
    seen={start}; q=deque([start]); far=0
    while q:
        p=q.popleft()
        far=max(far,abs(p[0]-start[0]),abs(p[1]-start[1]))
        if far>=24 or len(seen)>400: return (True,len(seen),far)
        for d in ((1,0),(-1,0),(0,1),(0,-1)):
            nb=(p[0]+d[0],p[1]+d[1])
            if nb in seen or nb in R: continue
            if g.edge(p,nb)=='Wall': continue
            seen.add(nb); q.append(nb)
    return (False,len(seen),far)

if __name__=="__main__":
  random.seed(1)
  T=int(sys.argv[1]) if len(sys.argv)>1 else 300
  trapped=0; total=0; sizes=[]
  for t in range(T):
      seed=random.randint(1,2**31-2); camz=random.uniform(0,150)
      r=trial(seed,camz)
      if r is None: continue
      total+=1
      if not r[0]: trapped+=1; sizes.append(r[1])
  print("trials",total,"trapped",trapped,"rate",trapped/max(1,total),"pocket sizes",sorted(sizes)[:40])
