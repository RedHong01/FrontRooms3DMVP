import math, random, heapq
from mapgen import Gen
from collections import deque
CS=3.0
def dij(g,src,maxm,door_pen=9.0,win_pen=9.0):
    d={src:0.0}; h=[(0.0,src)]
    while h:
        c,p=heapq.heappop(h)
        if c>d.get(p,1e9): continue
        for s in ((1,0),(-1,0),(0,1),(0,-1)):
            nb=(p[0]+s[0],p[1]+s[1]); e=g.edge(p,nb)
            if e=='Wall': continue
            nc=c+CS+(door_pen if e=='Door' else win_pen if e=='Window' else 0.0)
            if nc<=maxm and nc<d.get(nb,1e9): d[nb]=nc; heapq.heappush(h,(nc,nb))
    return d
best=None
random.seed(5)
for t in range(60):
    seed=random.randint(1,2**31-2); g=Gen(seed); p=(random.randint(-100,100),random.randint(-100,100))
    walk=dij(g,p,120,0,1e9)   # plain walking, no door penalty, windows impassable
    new=dij(g,p,15)
    R=36.4; rad=12
    old=[(p[0]+dx,p[1]+dy) for dx in range(-rad,rad+1) for dy in range(-rad,rad+1) if math.hypot(dx*CS,dy*CS)<=R]
    far=[c for c in old if walk.get(c,1e9)>R]
    doors=sum(1 for dx in range(-6,7) for dy in range(-6,7) for s in((1,0),(0,1)) if g.edge((p[0]+dx,p[1]+dy),(p[0]+dx+s[0],p[1]+dy+s[1]))=='Door')
    score=len(far)/len(old)
    if 22<=len(new)<=40 and doors>=2:
        if best is None or abs(score-0.45)<abs(best[0]-0.45): best=(score,seed,p,len(old),len(far),len(new),doors)
print(best)
