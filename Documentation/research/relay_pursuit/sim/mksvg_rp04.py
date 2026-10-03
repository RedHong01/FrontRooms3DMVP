import json
def f(v): return ('%.1f'%v).rstrip('0').rstrip('.')
W,H=1776,300; T=135.0
def X(t): return t/T*W
def Y(a): return H-a/100*H
doors=[(8,6),(9.5,6),(33,6),(34.2,6)]
sprints=[(20,23),(41,46)]
dt=0.05; t=0; A=0; last=-99; pts=[]; call=None
steps=set()
for a,b in sprints:
    k=0
    while a+k*0.3<b: steps.add(round(a+k*0.3,2)); k+=1
while t<=60:
    g=0
    for td,v in doors:
        if abs(t-td)<dt/2: g+=v
    if round(t,2) in steps: g+=3
    if g: A+=g; last=t
    elif t-last>4: A=max(0,A-2*dt)
    pts.append((t,A))
    if A>=60 and call is None: call=t; break
    t=round(t+dt,2)
d=' '.join(('M' if i==0 else 'L')+f'{f(X(tt))} {f(Y(a))}' for i,(tt,a) in enumerate(pts))
onmap=(call,call+52)  # arrive 3 + walk ~15 + investigate/search ~22 + withdraw ~12
grace=(onmap[1],onmap[1]+40)
# after withdraw: attention reset to 20 then decays (halved gains during grace)
post=f'M{f(X(grace[0]))} {f(Y(20))}L{f(X(grace[0]+4))} {f(Y(20))}L{f(X(grace[0]+14))} {f(Y(0))}L{f(X(T))} {f(Y(0))}'
o=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">']
for a,b in sprints: o.append(f'<rect x="{f(X(a))}" y="0" width="{f(X(b)-X(a))}" height="{H}" fill="#f4df3b" fill-opacity="0.35"/>')
o.append(f'<rect x="{f(X(onmap[0]))}" y="0" width="{f(X(onmap[1])-X(onmap[0]))}" height="{H}" fill="#0a0a0a"/>')
o.append(f'<rect x="{f(X(grace[0]))}" y="0" width="{f(X(grace[1])-X(grace[0]))}" height="{H}" fill="#0a0a0a" fill-opacity="0.07"/>')
o.append(f'<path d="M0 {f(Y(60))}H{f(X(onmap[0]))}M{f(X(onmap[1]))} {f(Y(60))}H{W}" stroke="#0a0a0a" stroke-width="2" stroke-dasharray="8 6"/>')
o.append(f'<path d="M0 {H}H{W}" stroke="#0a0a0a" stroke-width="1.5"/>')
for td,v in doors: o.append(f'<path d="M{f(X(td))} {H}V{H-16}" stroke="#0a0a0a" stroke-width="3"/>')
o.append(f'<path d="{d}" stroke="#0a0a0a" stroke-width="3.5" fill="none"/>')
o.append(f'<path d="{post}" stroke="#0a0a0a" stroke-width="3.5" fill="none"/>')
o.append(f'<circle cx="{f(X(call))}" cy="{f(Y(60))}" r="10" fill="#f4df3b" stroke="#0a0a0a" stroke-width="3"/>')
o.append('</svg>')
open('svg/rp04_attention2.svg','w').write(''.join(o))
print(json.dumps({'call':call,'Xcall':X(call),'onmap':[X(onmap[0]),X(onmap[1])],'grace':[X(grace[0]),X(grace[1])],'Y60':Y(60),'Y20':Y(20),'doors':[X(t) for t,_ in doors],'sprints':[[X(a),X(b)] for a,b in sprints],'Xs':{str(s):X(s) for s in (0,30,60,90,120,135)}}))
