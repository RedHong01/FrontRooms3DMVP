import json
D=json.load(open('figdata.json'))['rp02']
W,H=864,560; n=D['n']; px=D['px']; size=n*px
ox=W-size-18; oy=(H-size)//2
def grid():
    s=[]
    for i in range(1,n):
        s.append(f'<line x1="{i*px}" y1="0" x2="{i*px}" y2="{size}"/>'); s.append(f'<line x1="0" y1="{i*px}" x2="{size}" y2="{i*px}"/>')
    return '<g stroke="#2c2c2c" stroke-width="1" stroke-dasharray="3 5" fill="none">'+''.join(s)+'</g>'
def panel(kind):
    o=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
       f'<rect width="{W}" height="{H}" fill="#141414"/>', f'<g transform="translate({ox},{oy})">', grid()]
    if kind=='old':
        o.append(f'<path d="{D["oldNear"]}" fill="#ffffff" fill-opacity="0.14"/>')
        o.append(f'<path d="{D["oldFar"]}" fill="#f4df3b" fill-opacity="0.42"/>')
    else:
        o.append(f'<path d="{D["new"]}" fill="#f4df3b" fill-opacity="0.55"/>')
    o.append(f'<path d="{D["walls"]}" stroke="#ffffff" stroke-width="3" stroke-linecap="square" fill="none"/>')
    o.append(f'<path d="{D["doors"]}" stroke="#f4df3b" stroke-width="4" fill="none"/>')
    o.append(f'<path d="{D["windows"]}" stroke="#8a8a8a" stroke-width="4" stroke-dasharray="3 3" fill="none"/>')
    x,y=D['player']
    if kind=='old':
        o.append(f'<circle cx="{x}" cy="{y}" r="{D["circleR"]:.1f}" stroke="#f4df3b" stroke-width="2.5" fill="none"/>')
    o.append(f'<circle cx="{x}" cy="{y}" r="9" fill="#f4df3b" stroke="#141414" stroke-width="3"/>')
    o.append('</g></svg>')
    return '\n'.join(o)
open('svg/rp02_old.svg','w').write(panel('old')); open('svg/rp02_new.svg','w').write(panel('new'))
print(ox,oy,size, len(open('svg/rp02_old.svg').read()))
