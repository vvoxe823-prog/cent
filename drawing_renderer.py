import html

CSS = '''
*{box-sizing:border-box}body{margin:0;font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif;color:#25324a;background:linear-gradient(135deg,#eef7ff,#f8f1ff)}.wrap{width:min(1280px,94vw);margin:28px auto 50px}.top{display:flex;justify-content:space-between;align-items:center;gap:20px;margin-bottom:22px}.brand{font-size:1.25rem;font-weight:900}.sub{color:#71809a;font-size:.82rem;margin-top:4px}.actions{display:flex;gap:10px}.btn{display:inline-block;border:1px solid #d9dfeb;background:#fff;color:#25324a;padding:11px 15px;border-radius:12px;text-decoration:none;font-weight:800;font-size:.82rem}.card{background:rgba(255,255,255,.84);border:1px solid #fff;border-radius:24px;box-shadow:0 24px 70px rgba(70,82,120,.13);padding:20px;margin-bottom:22px;overflow:auto}.plan-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:10px}.badge{padding:7px 11px;border-radius:999px;background:#eef3ff;color:#5367a8;font-size:.72rem;font-weight:900}.badge.bad{background:#fff0f0;color:#a34d4d}.warn{padding:11px 13px;border-radius:12px;background:#fff8e8;color:#806a39;font-size:.78rem;margin:10px 0}.plan-svg{display:block;width:100%;height:auto;min-width:760px;background:#fff}.outer-wall{fill:#fff;stroke:#27364e;stroke-width:5}.room-name{font-size:11px;font-weight:800;fill:#26324a}.room-size{font-size:9px;fill:#71809a;font-weight:700}.window{stroke:#3e9db0;stroke-width:3}.stair{stroke:#7a6fb2;stroke-width:1}.dim{stroke:#7c8799;stroke-width:.8}.dimension{font-size:10px;font-weight:800;fill:#53627a}.north{font-size:13px;font-weight:900;fill:#53627a}.sheet-title{font-size:15px;font-weight:900}.sheet-sub{font-size:10px;font-weight:800;fill:#667eea}.meta{font-size:9px;fill:#71809a}.disclaimer{font-size:7.5px;fill:#8b95a7}@media(max-width:700px){.top{align-items:flex-start;flex-direction:column}.actions{width:100%}.btn{flex:1;text-align:center}}@media print{body{background:#fff}.wrap{width:100%;margin:0}.top{display:none}.card{box-shadow:none;border:0;padding:0;margin:0 0 15px}.card:not(:first-of-type){page-break-before:always}.plan-svg{min-width:0;width:100%}.btn{display:none}}
'''

def safe(v): return html.escape(str(v), quote=True)
def fmt(v):
    v=float(v); return str(int(round(v))) if abs(v-round(v))<.01 else f'{v:.1f}'
def fill(k): return {'living':'#eef4ff','master_bedroom':'#f5efff','bedroom':'#f8f2ff','kitchen':'#fff5e9','dining':'#effbf7','bathroom':'#eaf9fb','pooja':'#fff8e8','utility':'#f2f5f8','store':'#f4f4f4','study':'#eef7f1','staircase':'#f1edff','lift':'#edf1f7','parking':'#f3f5f8'}.get(k,'#f5f7fb')

def svg(plan,data,n):
    env=plan.get('buildable_area') or data['buildable_area_preliminary']; width=float(env['width']); depth=float(env['depth'])
    scale=min(900/max(width,1),650/max(depth,1)); W=width*scale; H=depth*scale; ml=105; mt=90; tw=W+ml+85; th=H+mt+105
    X=lambda v:ml+float(v)*scale; Y=lambda v:mt+H-float(v)*scale
    p=[f'<svg class="plan-svg" viewBox="0 0 {tw:.0f} {th:.0f}" role="img"><defs><pattern id="g{n}" width="20" height="20" patternUnits="userSpaceOnUse"><path d="M20 0L0 0 0 20" fill="none" stroke="#d9dfeb" stroke-width=".45"/></pattern></defs><rect width="100%" height="100%" fill="#fff"/><text x="{ml}" y="30" class="sheet-title">PLANFORGE · PRELIMINARY ARCHITECTURAL FLOOR PLAN</text><text x="{ml}" y="51" class="sheet-sub">Alternative {n} · {safe(plan.get("strategy","").title())} · {"VALID" if plan.get("valid") else "NOT FEASIBLE"}</text><text x="{ml}" y="69" class="meta">Plot {fmt(data["plot"]["width"])} × {fmt(data["plot"]["depth"])} {safe(data["plot"]["unit"])} · Buildable {fmt(width)} × {fmt(depth)} ft · Facing {safe(str(data["plot"]["facing"]).title())} · Road {safe(str(data["plot"]["road_side"]).replace("_"," ").title())}</text><rect x="{X(0):.1f}" y="{Y(depth):.1f}" width="{W:.1f}" height="{H:.1f}" fill="url(#g{n})" opacity=".45"/><rect x="{X(0):.1f}" y="{Y(depth):.1f}" width="{W:.1f}" height="{H:.1f}" class="outer-wall"/>']
    for r in plan.get('rooms',[]):
        x,y,w,d=[float(r[k]) for k in ('x','y','width','depth')]; sx,sy,sw,sh=X(x),Y(y+d),w*scale,d*scale; k=r.get('kind','room')
        p.append(f'<rect x="{sx:.1f}" y="{sy:.1f}" width="{sw:.1f}" height="{sh:.1f}" fill="{fill(k)}" stroke="#53627a" stroke-width="1.7"/><text x="{sx+sw/2:.1f}" y="{sy+sh/2-3:.1f}" class="room-name" text-anchor="middle">{safe(r["name"])}</text><text x="{sx+sw/2:.1f}" y="{sy+sh/2+12:.1f}" class="room-size" text-anchor="middle">{fmt(w)}′ × {fmt(d)}′</text>')
        if k not in ('parking','buffer'):
            if y<=.05:p.append(f'<line class="window" x1="{X(x+w*.3):.1f}" y1="{Y(y):.1f}" x2="{X(x+w*.7):.1f}" y2="{Y(y):.1f}"/>')
            if y+d>=depth-.05:p.append(f'<line class="window" x1="{X(x+w*.3):.1f}" y1="{Y(y+d):.1f}" x2="{X(x+w*.7):.1f}" y2="{Y(y+d):.1f}"/>')
            if x<=.05:p.append(f'<line class="window" x1="{X(x):.1f}" y1="{Y(y+d*.3):.1f}" x2="{X(x):.1f}" y2="{Y(y+d*.7):.1f}"/>')
            if x+w>=width-.05:p.append(f'<line class="window" x1="{X(x+w):.1f}" y1="{Y(y+d*.3):.1f}" x2="{X(x+w):.1f}" y2="{Y(y+d*.7):.1f}"/>')
        if k=='staircase':
            steps=max(4,int(d//1.5))
            for q in range(1,steps):
                yy=y+q*d/steps; p.append(f'<line class="stair" x1="{X(x)+7:.1f}" y1="{Y(yy):.1f}" x2="{X(x+w)-7:.1f}" y2="{Y(yy):.1f}"/>')
    p.append(f'<line class="dim" x1="{X(0):.1f}" y1="{Y(depth)+28:.1f}" x2="{X(width):.1f}" y2="{Y(depth)+28:.1f}"/><text class="dimension" x="{X(width/2):.1f}" y="{Y(depth)+21:.1f}" text-anchor="middle">{fmt(width)} ft</text><line class="dim" x1="{X(width)+28:.1f}" y1="{Y(0):.1f}" x2="{X(width)+28:.1f}" y2="{Y(depth):.1f}"/><text class="dimension" x="{X(width)+39:.1f}" y="{Y(depth/2):.1f}" transform="rotate(-90 {X(width)+39:.1f} {Y(depth/2):.1f})" text-anchor="middle">{fmt(depth)} ft</text><g transform="translate({tw-48},78)"><circle cx="0" cy="0" r="23" fill="#fff" stroke="#53627a"/><path d="M0-18L6 4 0 1-6 4Z" fill="#53627a"/><text x="0" y="-29" class="north" text-anchor="middle">N</text></g>')
    sb=data['setbacks']; p.append(f'<text x="{ml}" y="{th-48}" class="meta">Setbacks · Front {fmt(sb["front"])}′ · Rear {fmt(sb["rear"])}′ · Left {fmt(sb["left"])}′ · Right {fmt(sb["right"])}′</text><text x="{ml}" y="{th-30}" class="meta">Score {fmt(plan.get("score",0))} · Preliminary planning geometry</text><text x="{ml}" y="{th-14}" class="disclaimer">PRELIMINARY ONLY — verify bylaws, setbacks, fire/life safety, accessibility and structural design with qualified professionals.</text></svg>')
    return ''.join(p)

def page(data,plans):
    cards=[]
    for i,pl in enumerate(plans,1):
        warns=pl.get('warnings',[]); wh=(''.join(['<div class="warn"><strong>Engine warnings</strong><ul>']+[f'<li>{safe(w)}</li>' for w in warns]+['</ul></div>'])) if warns else ''
        bad=' bad' if not pl.get('valid') else ''
        cards.append(f'<section class="card"><div class="plan-head"><div><strong>Alternative {i} · {safe(pl.get("strategy","").title())}</strong><div class="sub">Preliminary architectural arrangement</div></div><span class="badge{bad}">{"VALID" if pl.get("valid") else "NOT FEASIBLE"} · Score {fmt(pl.get("score",0))}</span></div>{wh}{svg(pl,data,i)}</section>')
    return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>PlanForge — Architectural Drawing</title><style>'+CSS+'</style></head><body><div class="wrap"><div class="top"><div><div class="brand">PlanForge · Architectural Drawing</div><div class="sub">Generated server-side from your submitted requirements.</div></div><div class="actions"><span class="btn">Use Ctrl+P / Print → Save as PDF</span></div></div>'+''.join(cards)+'</div></body></html>'
