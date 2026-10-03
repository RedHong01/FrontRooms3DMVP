# Hearing/spawn statistics on the generated Level 0 map (Python port of FrontRoomsMap.cs edges; modules ignored).
import math, random, statistics as st
from collections import deque
from mapgen import Gen
CS=3.0
PASS={'Open','Arch','Door'}           # Relay hunt path: doors passable (it breaks them), windows/walls not
def bfs(g,start,maxd,through_doors=True):
    d={start:0}; q=deque([start])
    while q:
        p=q.popleft()
        if d[p]>=maxd: continue
        for s in ((1,0),(-1,0),(0,1),(0,-1)):
            nb=(p[0]+s[0],p[1]+s[1])
            if nb in d: continue
            e=g.edge(p,nb)
            if e in ('Wall','Window'): continue
            if e=='Door' and not through_doors: continue
            d[nb]=d[p]+1; q.append(nb)
    return d
def eu(a,b): return math.hypot((a[0]-b[0])*CS,(a[1]-b[1])*CS)
random.seed(7)
R_SPRINT=26*1.4; R_DOOR=14*1.4; R_GLASS=40*1.4
rows=[]; spawn_heard=[]; spawn_eu=[]; ratio=[]; unreach_frac=[]; far_frac=[]
for t in range(400):
    g=Gen(random.randint(1,2**31-2))
    p=(random.randint(-200,200),random.randint(-200,200))
    D=bfs(g,p,60)
    # cells within straight-line sprint radius (any cell, built or not; a Relay can stand in any reachable cell)
    rad=int(R_SPRINT//CS)+1
    inr=[(p[0]+dx,p[1]+dy) for dx in range(-rad,rad+1) for dy in range(-rad,rad+1) if eu(p,(p[0]+dx,p[1]+dy))<=R_SPRINT]
    reach=[c for c in inr if c in D]
    if len(D)<200: continue
    pd=[D[c]*CS for c in reach]
    rows.append((len(inr),len(reach),st.median(pd),sorted(pd)[int(.9*len(pd))]))
    unreach_frac.append(1-len(reach)/len(inr))
    far_frac.append(sum(1 for c in reach if D[c]*CS>2*R_SPRINT/1.0*0.5*2 and False)/len(reach))
    # spawn ring 9-15 cells of walking
    ring=[c for c,d in D.items() if 9<=d<=15]
    if ring:
        spawn_heard.append(sum(1 for c in ring if eu(p,c)<=R_SPRINT)/len(ring))
        spawn_eu+= [eu(p,c) for c in ring]
    for c in reach: ratio.append(D[c]*CS/max(eu(p,c),1e-6))
print("trials",len(rows))
print("cells inside straight-line sprint radius (36.4 m): median",st.median(r[0] for r in rows))
print("  of which reachable by walking:",round(1-st.mean(unreach_frac),3))
print("  walking distance to those cells: median of medians %.1f m, median p90 %.1f m"%(st.median(r[2] for r in rows),st.median(r[3] for r in rows)))
print("  walking / straight ratio: median %.2f, p90 %.2f"%(st.median(ratio),sorted(ratio)[int(.9*len(ratio))]))
print("spawn ring (9-15 cells walking): share of ring cells inside sprint hearing: mean %.3f, min %.3f"%(st.mean(spawn_heard),min(spawn_heard)))
print("spawn ring straight-line distance: median %.1f m, p10 %.1f, p90 %.1f"%(st.median(spawn_eu),sorted(spawn_eu)[int(.1*len(spawn_eu))],sorted(spawn_eu)[int(.9*len(spawn_eu))]))
