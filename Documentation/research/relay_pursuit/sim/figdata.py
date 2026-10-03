import json, math, random, heapq, glob, os
from mapgen import Gen
from collections import deque
CS=3.0
OUT={}
def f(v): return ('%.1f'%v).rstrip('0').rstrip('.')
# ---------- RP01 autopilot rows ----------
files=sorted(glob.glob('/private/tmp/claude-501/**/main-autopilot*/report.json',recursive=True),key=os.path.getmtime)
seen=set(); rows=[]
for fn in files:
    r=json.load(open(fn)); st=r.get('relayStates',[])
    key=(r.get('seed'),round(r.get('playSeconds',0),1),tuple(st))
    if key in seen or 'Wander' not in ' '.join(st): continue
    seen.add(key)
    s=[(float(x.split(' s ')[0]),x.split(' s ')[1]) for x in st]
    segs=[[t, s[i+1][0] if i+1<len(s) else r['playSeconds'], n] for i,(t,n) in enumerate(s)]
    rows.append({'segs':segs,'caught':r['caught'],'end':r['playSeconds']})
OUT['rp01']=rows
# ---------- map helpers ----------
def dij(g,src,maxm,door=9.0,win=9.0,wall=None):
    d={src:0.0}; h=[(0.0,src)]
    while h:
        c,p=heapq.heappop(h)
        if c>d.get(p,1e9): continue
        for s in ((1,0),(-1,0),(0,1),(0,-1)):
            nb=(p[0]+s[0],p[1]+s[1]); e=g.edge(p,nb)
            if e=='Wall': continue
            if e=='Window' and win is None: continue
            nc=c+CS+(door if e=='Door' else (win if e=='Window' else 0.0))
            if nc<=maxm and nc<d.get(nb,1e9): d[nb]=nc; heapq.heappush(h,(nc,nb))
    return d
def edges_paths(g,x0,y0,nx,ny,px,flipy=True):
    W=[];D=[];Wi=[];A=[]
    def P(cx,cy):  # cell corner (cx,cy) world-cell coords -> px, y up flipped
        X=(cx-x0)*px; Y=(ny-(cy-y0))*px if flipy else (cy-y0)*px
        return X,Y
    for i in range(nx):
        for j in range(ny):
            c=(x0+i,y0+j)
            for s,(a,b) in (((1,0),((c[0]+1,c[1]),(c[0]+1,c[1]+1))),((0,1),((c[0],c[1]+1),(c[0]+1,c[1]+1)))):
                nb=(c[0]+s[0],c[1]+s[1])
                if (s==(1,0) and i==nx-1) or (s==(0,1) and j==ny-1): continue
                e=g.edge(c,nb)
                (X1,Y1)=P(*a);(X2,Y2)=P(*b)
                seg='M %s %s L %s %s'%(f(X1),f(Y1),f(X2),f(Y2))
                if e=='Wall': W.append(seg)
                elif e=='Door': D.append(seg)
                elif e=='Window': Wi.append(seg)
    # outer frame not drawn
    return ' '.join(W),' '.join(D),' '.join(Wi)
def squares(cells,x0,y0,ny,px,inset=1.0):
    out=[]
    for (cx,cy) in cells:
        X=(cx-x0)*px+inset; Y=(ny-(cy-y0)-1)*px+inset; w=px-2*inset
        out.append('M %s %s L %s %s L %s %s L %s %s Z'%(f(X),f(Y),f(X+w),f(Y),f(X+w),f(Y+w),f(X),f(Y+w)))
    return ' '.join(out)
# ---------- RP02 hearing region ----------
seed=1032392419; P=(78,-20); g=Gen(seed); R=12; px=21
x0,y0=P[0]-R,P[1]-R; n=2*R+1
walk=dij(g,P,200,0.0,None)
old=[(P[0]+dx,P[1]+dy) for dx in range(-R,R+1) for dy in range(-R,R+1) if math.hypot(dx*CS,dy*CS)<=36.4]
old_near=[c for c in old if walk.get(c,1e9)<=36.4]
old_far=[c for c in old if walk.get(c,1e9)>36.4]
new=dij(g,P,15.0,9.0,9.0)
newc=[c for c in new if abs(c[0]-P[0])<=R and abs(c[1]-P[1])<=R]
W,D,Wi=edges_paths(g,x0,y0,n,n,px)
OUT['rp02']={'px':px,'n':n,'walls':W,'doors':D,'windows':Wi,'oldNear':squares(old_near,x0,y0,n,px),'oldFar':squares(old_far,x0,y0,n,px),
  'new':squares(newc,x0,y0,n,px),'player':[(P[0]-x0+.5)*px,(n-(P[1]-y0)-.5)*px],'circleR':36.4/CS*px,
  'counts':{'old':len(old),'oldFar':len(old_far),'new':len(new)}}
# ---------- RP05 lamp field ----------
seed5=seed; g5=g
nx,ny=17,9; px5=40
# choose relay cell and path: BFS within region from an entry-like dead end toward player
Pp=(P[0]+5,P[1]); # player
best=None
for dx in range(-7,-1):
    for dy in range(-3,4):
        c=(P[0]+dx,P[1]+dy)
        d=dij(g,c,60,0.0,None)
        if Pp in d and 15<=d[Pp]<=30: best=c; break
    if best: break
relay=best or (P[0]-4,P[1])
# path from relay back 6 cells (where it came from) : BFS away from player
dd=dij(g,relay,40,0.0,None)
far=[c for c in dd if abs(c[0]-P[0]+0.5)<=8 and abs(c[1]-P[1])<=4 and dd[c]>=12]
start=min(far,key=lambda c:(-dd[c]+abs(c[0]-relay[0])*0)) if far else relay
# reconstruct path start->relay by BFS parents
par={start:None}; q=deque([start])
while q:
    p=q.popleft()
    if p==relay: break
    for s in ((1,0),(-1,0),(0,1),(0,-1)):
        nb=(p[0]+s[0],p[1]+s[1])
        if nb in par or g.edge(p,nb) in ('Wall','Window'): continue
        par[nb]=p; q.append(nb)
path=[]; c=relay
while c is not None and c in par: path.append(c); c=par[c]
path=path[::-1]
x05,y05=P[0]-8,P[1]-4
W5,D5,Wi5=edges_paths(g,x05,y05,nx,ny,px5)
rng=random.Random(4)
lamps=[]
rx,ry=relay[0]+.5,relay[1]+.5
for i in range(nx):
    for j in range(ny):
        c=(x05+i,y05+j)
        lx=(c[0]+0.5)*CS; lz=(c[1]+0.6)*CS  # lens centre ~ (1.5,1.8) in cell
        d=math.hypot(lx-rx*CS,lz-ry*CS)
        roll=rng.random(); mode='steady' if roll<.62 else 'stutter' if roll<.82 else 'failing' if roll<.92 else 'dead' if roll<.97 else 'dim'
        amb={'steady':1.0,'stutter':0.95,'failing':0.5,'dead':0.0,'dim':0.42}[mode]
        omen=0.15 if d<=3 else 0.45 if d<=7.5 else 1.0
        lvl=min(amb,omen) if True else amb
        band='core' if d<=3 else 'mid' if d<=7.5 else 'far' if d<=12 else 'none'
        X=(i)*px5+1.2/CS*px5; Y=(ny-j-1)*px5+(CS-2.4)/CS*px5
        lamps.append({'x':round(X,1),'y':round(Y,1),'w':round(0.6/CS*px5,1),'h':round(1.2/CS*px5,1),'lvl':lvl,'mode':mode,'band':band})
OUT['rp05map']={'px':px5,'nx':nx,'ny':ny,'walls':W5,'doors':D5,'windows':Wi5,'lamps':lamps,
  'relay':[(rx-x05)*px5,(ny-(ry-y05))*px5],'player':[(Pp[0]+.5-x05)*px5,(ny-(Pp[1]+.5-y05))*px5],
  'path':' '.join(('M' if k==0 else 'L')+' %s %s'%(f((c[0]+.5-x05)*px5),f((ny-(c[1]+.5-y05))*px5)) for k,c in enumerate(path)),
  'r3':3/CS*px5,'r75':7.5/CS*px5,'r12':12/CS*px5}
# ---------- RP05 timelines (6 s, width 760, height 90 per lane) ----------
TW,TH=760.0,90.0; Tm=8.0
def lane(fn):
    pts=[]
    for k in range(0,801):
        t=Tm*k/800; v=max(0,min(1.3,fn(t)))
        pts.append(('M' if k==0 else 'L')+' %s %s'%(f(t/Tm*TW),f(TH-v/1.3*TH)))
    return ' '.join(pts)
def failing(t):
    ph=17.0; tt=t+ph
    wave=.5+.5*math.sin(tt*3.1)*(.7+.3*math.sin(tt*1.27))
    # perlin-ish dropout
    drop=0.05 if (math.sin(tt*1.4*2.1)+math.sin(tt*0.9*1.7))>1.35 else 1.0
    return (.25+.45*wave)*drop
def env(t,a,h,r):
    if t<0: return 0
    if t<a: return t/a
    if t<a+h: return 1
    if t<a+h+r: return 1-(t-a-h)/r
    return 0
step=0.44; pattern=[1,0,0,1,0,0,1,0]
def omen(t):
    # relay approaches: sink starts at 1.0 s (attack .25 to .45), dips on footfalls
    base=1.0
    if t>=1.0: base=1.0-0.55*min(1,(t-1.0)/0.25)
    if t>6.0: base=0.45+0.55*min(1,(t-6.0)/0.6)  # it moves on
    m=base
    if 1.0<=t<6.0:
        k=int((t-1.0)/step)
        for kk in range(max(0,k-1),k+1):
            if pattern[kk%8]:
                e=env(t-(1.0+kk*step),.12,.10,.30)
                m=min(m, base*(1-0.85*e))
    return m
def restrike(t):
    # lamp in core (0.15) until 2.0s, then restrike: 2 blinks at 2Hz then ramp 1.5s
    if t<2.0: return 0.15
    u=t-2.0
    if u<1.0:
        return 0.9 if (u%0.5)<0.12 else 0.1
    return min(1.0,0.1+0.9*(u-1.0)/1.5)
OUT['rp05lanes']={'w':TW,'h':TH,'T':Tm,'failing':lane(failing),'omen':lane(omen),'restrike':lane(restrike),
  'dips':[1.0+k*step for k in range(12) if pattern[k%8] and 1.0+k*step<6.0]}
# ---------- RP04 attention (90 s, width 1100, height 300) ----------
AW,AH,AT=1100.0,300.0,90.0
ev=[]  # (t, gain)
A=0.0; pts=[]; quiet=0.0; t=0.0; dt=0.05; called=None
events=[(8,'door',6),(9.5,'door',6)]
for k in range(int(22/0.3)): pass
sprints=[(20,23.0),(41,46.0),(49,52)]
doorev=[(8,6),(9.5,6),(33,6),(34.2,6),(47,15)]
series=[]
last_gain=-99
sp_next={}
while t<=AT:
    g_=0
    for (ta,v) in doorev:
        if abs(t-ta)<dt/2: g_+=v
    for (a,b) in sprints:
        if a<=t<b and abs(((t-a)/0.3)-round((t-a)/0.3))<1e-6*0+dt/0.3/2: g_+=3
    if g_>0: A+=g_; last_gain=t
    elif t-last_gain>4: A=max(0,A-2*dt)
    if called is None and A>=60: called=t
    if called is not None and t>called: A=max(A,60) if t<called+3 else A
    series.append((t,min(100,A)))
    t=round(t+dt,4)
OUT['rp04']={'w':AW,'h':AH,'T':AT,'path':' '.join(('M' if i==0 else 'L')+' %s %s'%(f(tt/AT*AW),f(AH-a/100*AH)) for i,(tt,a) in enumerate(series)),
  'called':called,'thr':60,'sprints':sprints,'doors':doorev}
# ---------- RP06 spotting curve (2..12 m) ----------
SW,SH=700.0,260.0
OUT['rp06']={'w':SW,'h':SH,'path':' '.join(('M' if i==0 else 'L')+' %s %s'%(f((d-0)/12*SW),f(SH-(0.25+0.035*d)/0.8*SH)) for i,d in enumerate([x/10 for x in range(20,121)]))}
json.dump(OUT,open('figdata.json','w'))
print({k:(len(json.dumps(v))) for k,v in OUT.items()})
print('rp02 counts',OUT['rp02']['counts'],'relay',relay,'path len',len(path),'called',called)
