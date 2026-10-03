import math, random, statistics as st, heapq
from mapgen import Gen
CS=3.0
def dijkstra(g,src,maxm,door_pen=9.0,window_pen=9.0):
    d={src:0.0}; h=[(0.0,src)]
    while h:
        c,p=heapq.heappop(h)
        if c>d.get(p,1e9): continue
        for s in ((1,0),(-1,0),(0,1),(0,-1)):
            nb=(p[0]+s[0],p[1]+s[1]); e=g.edge(p,nb)
            if e=='Wall': continue
            nc=c+CS+(door_pen if e=='Door' else window_pen if e=='Window' else 0.0)
            if nc<=maxm and nc<d.get(nb,1e9): d[nb]=nc; heapq.heappush(h,(nc,nb))
    return d
random.seed(11)
res={15:[],12:[],20:[],60:[]}; old=[]
for t in range(200):
    g=Gen(random.randint(1,2**31-2)); p=(random.randint(-200,200),random.randint(-200,200))
    for L in res: res[L].append(len(dijkstra(g,p,L)))
    R=36.4; rad=int(R//CS)+1
    old.append(sum(1 for dx in range(-rad,rad+1) for dy in range(-rad,rad+1) if math.hypot(dx*CS,dy*CS)<=R))
print('old straight-line sprint 36.4 m cells', st.median(old))
for L,v in res.items(): print('path-propagated',L,'m: median cells',st.median(v),'p90',sorted(v)[int(.9*len(v))])
