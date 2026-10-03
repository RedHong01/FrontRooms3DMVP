import json, math, random, heapq
from collections import deque
from mapgen import Gen
CS=3.0
def f(v): return ('%.1f'%v).rstrip('0').rstrip('.')
def svg_open(W,H,bg='#141414'): 
    s=f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
    if bg: s+=f'<rect width="{W}" height="{H}" fill="{bg}"/>'
    return s
def dij(g,src,maxm,door=0.0,win=None):
    d={src:0.0}; h=[(0.0,src)]
    while h:
        c,p=heapq.heappop(h)
        if c>d.get(p,1e9): continue
        for s in ((1,0),(-1,0),(0,1),(0,-1)):
            nb=(p[0]+s[0],p[1]+s[1]); e=g.edge(p,nb)
            if e=='Wall': continue
            if e=='Window' and win is None: continue
            nc=c+CS+(door if e=='Door' else (win or 0) if e=='Window' else 0.0)
            if nc<=maxm and nc<d.get(nb,1e9): d[nb]=nc; heapq.heappush(h,(nc,nb))
    return d
# ================= RP05 zones map =================
seed=1032392419; P=(78,-20); g=Gen(seed)
W,H=864,560; px=26; nx,ny=31,20
x0,y0=P[0]-15,P[1]-10
ox=(W-nx*px)/2; oy=(H-ny*px)/2
def cxy(c): return (ox+(c[0]-x0+.5)*px, oy+(ny-(c[1]-y0)-.5)*px)
walk=dij(g,P,80)   # walking distance from player (doors passable, windows not)
st1=[c for c,d in walk.items() if d<=30 and 0<=c[0]-x0<nx and 0<=c[1]-y0<ny]
st2=[c for c,d in walk.items() if d<=15 and 0<=c[0]-x0<nx and 0<=c[1]-y0<ny]
# your room: BFS open edges only, depth<=2, <=9 cells
room=[P]; q=deque([(P,0)]); seen={P}
while q and len(room)<9:
    p,dd=q.popleft()
    if dd>=2: continue
    for s in ((1,0),(-1,0),(0,1),(0,-1)):
        nb=(p[0]+s[0],p[1]+s[1])
        if nb in seen or g.edge(p,nb)!='Open': continue
        seen.add(nb); room.append(nb); q.append((nb,dd+1))
        if len(room)>=9: break
# relay path: pick a cell at walking 40-48 m within window, path to player, stop at 9 m
cand=[c for c,d in walk.items() if 39<=d<=48 and 1<=c[0]-x0<nx-1 and 1<=c[1]-y0<ny-1]
cand.sort(key=lambda c:(-abs(c[0]-P[0]),c))
start=cand[0]
# path from start to P via parents of dijkstra from start
d2={start:0}; par={start:None}; q=deque([start])
while q:
    p=q.popleft()
    if p==P: break
    for s in ((1,0),(-1,0),(0,1),(0,-1)):
        nb=(p[0]+s[0],p[1]+s[1])
        if nb in par or g.edge(p,nb) in ('Wall','Window'): continue
        par[nb]=p; q.append(nb)
path=[]; c=P
while c is not None: path.append(c); c=par[c]
path=path[::-1]
# truncate where walking distance to player < 9 m
path=[c for c in path if walk.get(c,99)>=9] 
def sq(cells,inset=0):
    o=[]
    for c in cells:
        X=ox+(c[0]-x0)*px+inset; Y=oy+(ny-(c[1]-y0)-1)*px+inset; w=px-2*inset
        o.append(f'M{f(X)} {f(Y)}h{f(w)}v{f(w)}h{f(-w)}Z')
    return ''.join(o)
def edges():
    Wl=[];Dr=[];Wi=[]
    for i in range(nx):
        for j in range(ny):
            c=(x0+i,y0+j)
            for s in ((1,0),(0,1)):
                if (s==(1,0) and i==nx-1) or (s==(0,1) and j==ny-1): continue
                nb=(c[0]+s[0],c[1]+s[1]); e=g.edge(c,nb)
                if s==(1,0): X=ox+(i+1)*px; Y1=oy+(ny-j-1)*px; seg=f'M{f(X)} {f(Y1)}V{f(Y1+px)}'
                else: Y=oy+(ny-j-1)*px; X1=ox+i*px; seg=f'M{f(X1)} {f(Y)}H{f(X1+px)}'
                if e=='Wall': Wl.append(seg)
                elif e=='Door': Dr.append(seg)
                elif e=='Window': Wi.append(seg)
    return ''.join(Wl),''.join(Dr),''.join(Wi)
Wl,Dr,Wi=edges()
o=[svg_open(W,H)]
o.append(f'<path d="{sq(st1,1)}" fill="#ffffff" fill-opacity="0.10"/>')
o.append(f'<path d="{sq(st2,1)}" fill="#f4df3b" fill-opacity="0.30"/>')
# lamps: one lens per cell (0.6x1.2m at X1.2-1.8,Z1.2-2.4)
lw=0.6/CS*px; lh=1.2/CS*px
roomset=set(room)
rng=random.Random(3); lamps_dim=[]; lamps_room=[]
for i in range(nx):
    for j in range(ny):
        c=(x0+i,y0+j); X=ox+i*px+1.2/CS*px; Y=oy+(ny-j-1)*px+(CS-2.4)/CS*px
        r=f'M{f(X)} {f(Y)}h{f(lw)}v{f(lh)}h{f(-lw)}Z'
        (lamps_room if c in roomset else lamps_dim).append(r)
o.append(f'<path d="{"".join(lamps_dim)}" fill="#ffffff" fill-opacity="0.22"/>')
o.append(f'<path d="{sq(room,0)}" fill="none" stroke="#f4df3b" stroke-width="2"/>')
o.append(f'<path d="{"".join(lamps_room)}" fill="#f4df3b"/>')
o.append(f'<path d="{Wl}" stroke="#ffffff" stroke-width="3" stroke-linecap="square" fill="none"/>')
o.append(f'<path d="{Dr}" stroke="#f4df3b" stroke-width="4" fill="none"/>')
o.append(f'<path d="{Wi}" stroke="#8a8a8a" stroke-width="4" stroke-dasharray="3 3" fill="none"/>')
pts=' '.join(('M' if k==0 else 'L')+'%s %s'%tuple(map(f,cxy(c))) for k,c in enumerate(path))
o.append(f'<path d="{pts}" stroke="#ffffff" stroke-width="3" stroke-dasharray="8 6" fill="none"/>')
ex,ey=cxy(path[0]); rx,ry=cxy(path[-1]); px_,py_=cxy(P)
o.append(f'<circle cx="{f(ex)}" cy="{f(ey)}" r="11" fill="none" stroke="#ffffff" stroke-width="2" stroke-dasharray="4 4"/>')
o.append(f'<circle cx="{f(rx)}" cy="{f(ry)}" r="11" fill="#ffffff"/>')
o.append(f'<circle cx="{f(px_)}" cy="{f(py_)}" r="10" fill="#f4df3b" stroke="#141414" stroke-width="3"/>')
o.append('</svg>')
open('svg/rp05_zones.svg','w').write(''.join(o))
meta={'rp05':{'entry':[ex,ey],'relay':[rx,ry],'player':[px_,py_],'st1':len(st1),'st2':len(st2),'room':len(room),'pathcells':len(path),
   'cross30':[cxy(c) for c in path if walk[c]<=30][:1],'cross15':[cxy(c) for c in path if walk[c]<=15][:1]}}
# ================= RP05 approach timeline =================
TW,TH=888,500; T=17.0
def X(t): return t/T*TW
lanes={'dist':(0,170),'lamps':(214,300),'steps':(344,408),'cue':(452,484)}
o=[svg_open(TW,TH,None)]
# stage bands
t1=(45-30)/2.6; t2=(45-15)/2.6; tsee=(45-10)/2.6; tlock=tsee+0.25+0.035*10; tch=tlock+0.6
o.append(f'<rect x="{f(X(t1))}" y="0" width="{f(X(t2)-X(t1))}" height="{TH}" fill="#f4df3b" fill-opacity="0.10"/>')
o.append(f'<rect x="{f(X(t2))}" y="0" width="{f(X(tlock)-X(t2))}" height="{TH}" fill="#f4df3b" fill-opacity="0.24"/>')
o.append(f'<rect x="{f(X(tlock))}" y="0" width="{f(X(tch)-X(tlock))}" height="{TH}" fill="#f4df3b" fill-opacity="0.65"/>')
o.append(f'<rect x="{f(X(tch))}" y="0" width="{f(TW-X(tch))}" height="{TH}" fill="#0a0a0a" fill-opacity="0.06"/>')
# distance lane (0..50 m)
y0d,y1d=lanes['dist']
def Yd(d): return y1d-(d/50)*(y1d-y0d)
dpts=[]
for k in range(0,341):
    t=T*k/340; d=max(45-2.6*t,10) if t<tch else max(10-1.0*(t-tch),6)
    dpts.append(('M' if k==0 else 'L')+f'{f(X(t))} {f(Yd(d))}')
for dd in (30,15):
    o.append(f'<path d="M0 {f(Yd(dd))}H{TW}" stroke="#0a0a0a" stroke-width="1" stroke-dasharray="4 4"/>')
o.append(f'<path d="{" ".join(dpts)}" stroke="#0a0a0a" stroke-width="3" fill="none"/>')
o.append(f'<path d="M0 {y1d}H{TW}" stroke="#0a0a0a" stroke-width="1"/>')
# lamps lane: level of your room
y0l,y1l=lanes['lamps']
def Yl(v): return y1l-v*(y1l-y0l)
bursts=[t1+0.3, t1+0.3+5.2, t1+0.3+5.2+2.6]
dips=[]
rr=random.Random(9)
for b in bursts:
    n=3; 
    for i in range(n): dips.append((b+i*0.4+rr.uniform(-0.04,0.04), rr.uniform(0.3,0.6)))
def lamp(t):
    if t>=tlock: return 1.0
    v=1.0
    for (td,m) in dips:
        a,h,r=0.08,0.06,0.2
        u=t-td
        if 0<=u<a: e=u/a
        elif a<=u<a+h: e=1
        elif a+h<=u<a+h+r: e=1-(u-a-h)/r
        else: e=0
        v=min(v,1-(1-m)*e)
    return v
lp=[('M' if k==0 else 'L')+f'{f(X(T*k/1700))} {f(Yl(lamp(T*k/1700)))}' for k in range(0,1701)]
o.append(f'<path d="M0 {y1l}H{TW}" stroke="#0a0a0a" stroke-width="1"/>')
o.append(f'<path d="{" ".join(lp)}" stroke="#0a0a0a" stroke-width="2.5" fill="none"/>')
# steps lane
y0s,y1s=lanes['steps']
o.append(f'<path d="M0 {y1s}H{TW}" stroke="#0a0a0a" stroke-width="1"/>')
t=t2; tl=t2+1.6  # in line after turning the corner
ticks=[]
while t<tch:
    hgt=(y1s-y0s)*(0.35 if t<tl else 0.9)
    col='#8a8a8a' if t<tl else '#0a0a0a'
    ticks.append(f'<rect x="{f(X(t)-2)}" y="{f(y1s-hgt)}" width="4" height="{f(hgt)}" fill="{col}"/>')
    t+=0.44
while t<T:
    ticks.append(f'<rect x="{f(X(t)-2)}" y="{f(y0s)}" width="4" height="{f(y1s-y0s)}" fill="#0a0a0a"/>'); t+=0.29
o+=ticks
# cue lane
y0c,y1c=lanes['cue']
o.append(f'<rect x="{f(X(tlock))}" y="{y0c}" width="{f(X(tch)-X(tlock))}" height="{y1c-y0c}" fill="#0a0a0a"/>')
o.append(f'<path d="M{f(X(tch))} {f((y0c+y1c)/2)}H{TW}" stroke="#0a0a0a" stroke-width="3"/>')
o.append('</svg>')
open('svg/rp05_timeline.svg','w').write(''.join(o))
meta['rp05t']={'t1':t1,'t2':t2,'tsee':tsee,'tlock':tlock,'tch':tch,'X':{'t1':X(t1),'t2':X(t2),'tlock':X(tlock),'tch':X(tch)},'lanes':lanes,'Yd30':Yd(30),'Yd15':Yd(15)}
# ================= RP04 attention =================
D=json.load(open('figdata.json'))['rp04']
AW,AH=1776,330
o=[svg_open(AW,AH,None)]
sx=AW/D['w']; sy=AH/D['h']
import re
path=re.sub(r'([ML]) ([\d.]+) ([\d.]+)',lambda m:f"{m.group(1)}{f(float(m.group(2))*sx)} {f(float(m.group(3))*sy)}",D['path'])
def XA(t): return t/D['T']*AW
for a,b in D['sprints']:
    o.append(f'<rect x="{f(XA(a))}" y="0" width="{f(XA(b)-XA(a))}" height="{AH}" fill="#f4df3b" fill-opacity="0.35"/>')
thr=AH-60/100*AH
o.append(f'<path d="M0 {f(thr)}H{AW}" stroke="#0a0a0a" stroke-width="2" stroke-dasharray="8 6"/>')
o.append(f'<path d="M0 {AH}H{AW}" stroke="#0a0a0a" stroke-width="1"/>')
for (t,v) in D['doors']:
    o.append(f'<path d="M{f(XA(t))} {AH}V{AH-14}" stroke="#0a0a0a" stroke-width="3"/>')
o.append(f'<path d="{path}" stroke="#0a0a0a" stroke-width="3.5" fill="none"/>')
tc=D['called']
o.append(f'<circle cx="{f(XA(tc))}" cy="{f(thr)}" r="9" fill="#0a0a0a"/>')
o.append(f'<rect x="{f(XA(tc))}" y="{f(thr-6)}" width="{f(XA(tc+3)-XA(tc))}" height="12" fill="#0a0a0a"/>')
o.append('</svg>')
open('svg/rp04_attention.svg','w').write(''.join(o))
meta['rp04']={'called':tc,'X':{'called':XA(tc),'s1':XA(20),'s2':XA(41),'s3':XA(49)},'thrY':thr,'doors':[(t,XA(t),v) for t,v in D['doors']]}
# ================= RP06 cone =================
CW,CH=888,486; s=26  # px per m
o=[svg_open(CW,CH)]
for i in range(1,int(CW/(3*s))+1): o.append(f'<path d="M{f(i*3*s)} 0V{CH}" stroke="#2c2c2c" stroke-dasharray="3 5"/>')
for j in range(1,int(CH/(3*s))+1): o.append(f'<path d="M0 {f(j*3*s)}H{CW}" stroke="#2c2c2c" stroke-dasharray="3 5"/>')
cx,cy=150,CH/2; R=12*s
a1,a2=math.radians(-70),math.radians(70)
o.append(f'<path d="M{cx} {cy}L{f(cx+R*math.cos(a1))} {f(cy+R*math.sin(a1))}A{R} {R} 0 0 1 {f(cx+R*math.cos(a2))} {f(cy+R*math.sin(a2))}Z" fill="#ffffff" fill-opacity="0.12"/>')
o.append(f'<circle cx="{cx}" cy="{cy}" r="{2*s}" fill="none" stroke="#ffffff" stroke-width="2" stroke-dasharray="4 4"/>')
# wall
wx=cx+7*s
o.append(f'<path d="M{f(wx)} {f(cy-160)}V{f(cy-40)}" stroke="#ffffff" stroke-width="5"/>')
o.append(f'<circle cx="{cx}" cy="{cy}" r="12" fill="#ffffff"/>')
o.append(f'<path d="M{cx+12} {cy}L{cx+40} {cy}" stroke="#ffffff" stroke-width="3"/>')
p1=(cx+9*s*math.cos(math.radians(18)),cy+9*s*math.sin(math.radians(18)))
p2=(cx+9*s*math.cos(math.radians(-48)),cy+9*s*math.sin(math.radians(-48)))
p3=(cx-3.5*s,cy-2.5*s)
p4=(cx+4*s*math.cos(math.radians(-60)),cy+4*s*math.sin(math.radians(-60)))
for p in (p1,): o.append(f'<circle cx="{f(p[0])}" cy="{f(p[1])}" r="11" fill="#f4df3b"/>')
for p in (p2,p3): o.append(f'<circle cx="{f(p[0])}" cy="{f(p[1])}" r="11" fill="none" stroke="#f4df3b" stroke-width="2.5"/>')
o.append(f'<path d="M{cx} {cy}L{f(p1[0])} {f(p1[1])}" stroke="#f4df3b" stroke-width="2" stroke-dasharray="6 5"/>')
o.append('</svg>')
open('svg/rp06_cone.svg','w').write(''.join(o))
meta['rp06']={'relay':[cx,cy],'p1':p1,'p2':p2,'p3':p3,'R':R,'wallx':wx}
# ================= RP09 pacing =================
PW,PH=1776,250; Tm=300.0
def XP(t): return t/Tm*PW
o=[svg_open(PW,PH,None)]
# old row (y 0-70): released at 10s, on map to end
o.append(f'<rect x="0" y="0" width="{f(XP(10))}" height="70" fill="#d9d9d9"/>')
o.append(f'<rect x="{f(XP(10))}" y="0" width="{f(PW-XP(10))}" height="70" fill="#0a0a0a"/>')
# new row (y 150-220): designed cycles
cyc=[('away',0,62),('arrive',62,65),('on',65,80),('on',80,100),('withdraw',100,110),('away',110,150),('away',150,196),('arrive',196,199),('on',199,214),('chase',214,224),('on',224,238),('withdraw',238,248),('away',248,300)]
col={'away':'#d9d9d9','arrive':'#6b6b6b','on':'#0a0a0a','chase':'#f4df3b','withdraw':'#6b6b6b'}
for k,a,b in cyc:
    o.append(f'<rect x="{f(XP(a))}" y="150" width="{f(XP(b)-XP(a))}" height="70" fill="{col[k]}"/>')
# warning band under new row: stage1 intervals
for a,b in ((70,104),(204,242)):
    o.append(f'<rect x="{f(XP(a))}" y="228" width="{f(XP(b)-XP(a))}" height="8" fill="#f4df3b"/>')
o.append('</svg>')
open('svg/rp09_pacing.svg','w').write(''.join(o))
on_old=(300-10)/300; on_new=sum(b-a for k,a,b in cyc if k in('arrive','on','chase','withdraw'))/300
meta['rp09']={'old_on':on_old,'new_on':on_new,'X':{c:XP(c) for c in (10,62,110,196,248)}}
json.dump(meta,open('svgmeta.json','w'),default=float)
print(json.dumps(meta,default=lambda x:round(float(x),1))[:1500])
