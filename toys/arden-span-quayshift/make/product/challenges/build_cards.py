"""Derive symbolic challenge diagrams directly from the exact footprint grammar.
No raster mockups or invented geometry. Standard-library-only; run after solver.py.
"""
import ast
import html
import json
import math
from pathlib import Path
import solver

ROOT=Path(__file__).resolve().parent
DATA=json.loads((ROOT/'challenges.json').read_text())
assert DATA.get('finite_validation',{}).get('status')=='representative poses passed CAD checks', 'Reconcile representative CAD validation before generating checked customer answers.'
# Read the authored CAD palette without importing its CAD kernel.
cad_source=ROOT.parent/'cad/quayshift_lib.py'
if cad_source.exists():
    tree=ast.parse(cad_source.read_text())
    COLORS=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='COLORS' for t in n.targets))
else:
    COLORS=json.loads((ROOT/'palette.json').read_text())
(ROOT/'palette.json').write_text(json.dumps(COLORS,indent=2)+'\n')
CELL=64;OFF=46

def center(q):return OFF+CELL*(q[0]+.5),OFF+CELL*(4-q[1]+.5)
def pieces(poses):
    return [dict(next(v for v in solver.p.CANDIDATES[r['part']] if v['rotation']==(0 if r['part'] in 'GH' else r['rotation'] if r['part']=='D' else r['rotation']%180) and v['origin']==r['origin']), rotation=r['rotation']) for r in poses]

def span_polygon(v):
    # Exact CAD offset within the symbolic reserved strip, in millimeters.
    # Only the open middle cell is tinted so module labels remain legible.
    a=math.radians(v['rotation'])
    def turn(x,y):return (round(x*math.cos(a)-y*math.sin(a),8),round(x*math.sin(a)+y*math.cos(a),8))
    corners=[turn(x,y) for x,y in [(0,0),(96,0),(96,32),(0,32)]]
    dx=min(x for x,y in corners);dy=min(y for x,y in corners)
    points=[]
    for x,y in [(32,19.6),(64,19.6),(64,31.6),(32,31.6)]:
        tx,ty=turn(x,y);gx=v['origin'][0]+(tx-dx)/32;gy=v['origin'][1]+(ty-dy)/32
        points.append(f'{OFF+gx*CELL:.2f},{OFF+(5-gy)*CELL:.2f}')
    return ' '.join(points)

def svg(poses,route=None):
    out=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 420" role="img" aria-label="Symbolic top view of the five by five QUAYSHIFT grid">',
         '<rect width="420" height="420" rx="12" fill="#f6f0e4"/>',
         '<rect x="42" y="42" width="328" height="328" rx="5" fill="#174b5b"/>']
    for x in range(5):
        cx,_=center((x,0));out.append(f'<text x="{cx}" y="391" text-anchor="middle" font-family="sans-serif" font-size="14" fill="#273c36">{"ABCDE"[x]}</text>')
    for y in range(5):
        _,cy=center((0,y));out.append(f'<text x="28" y="{cy+5}" text-anchor="middle" font-family="sans-serif" font-size="14" fill="#273c36">{y+1}</text>')
    for x in range(6):
        a=OFF+x*CELL
        out.append(f'<path d="M{a} {OFF}V{OFF+5*CELL} M{OFF} {a}H{OFF+5*CELL}" stroke="#ffffff" stroke-opacity=".22" fill="none"/>')
    for v in pieces(poses):
        col='#'+COLORS[v['part']]
        for q in v['feet']:
            x,y=center(q);out.append(f'<rect x="{x-30}" y="{y-30}" width="60" height="60" rx="3" fill="{col}" stroke="#243c36" stroke-width="2"/>')
            out.append(f'<text x="{x}" y="{y+5}" text-anchor="middle" font-family="sans-serif" font-weight="bold" font-size="17" fill="#102c31">{v["part"]}</text>')
        if v['gap'] is not None:
            x,y=center(v['gap']);vert=v['rotation']%180!=0
            # Whole strip belongs to one module. The tinted rear band uses the CAD offset.
            coords=[center(q) for q in v['envelope']];xmin=min(q[0] for q in coords)-30;ymin=min(q[1] for q in coords)-30
            w=max(q[0] for q in coords)-xmin+30;h=max(q[1] for q in coords)-ymin+30
            out.append(f'<rect x="{xmin}" y="{ymin}" width="{w}" height="{h}" rx="3" fill="none" stroke="{col}" stroke-width="3"/>')
            out.append(f'<polygon points="{span_polygon(v)}" fill="{col}" fill-opacity=".92" stroke="#faf7f0" stroke-width="1"/>')
            if v['kind']=='low':out.append(f'<path d="M{x-9} {y-9}L{x+9} {y+9}M{x-9} {y+9}L{x+9} {y-9}" stroke="#efb950" stroke-width="4"/>')
    if route:
        points=' '.join(f'{x},{y}' for x,y in map(center,route))
        out.append(f'<polyline points="{points}" fill="none" stroke="#072c39" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>')
        out.append(f'<polyline points="{points}" fill="none" stroke="#f2be54" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>')
    out+=['<path d="M206 411V371 M206 41V8" stroke="#d9a53d" stroke-width="5"/>','<path d="M200 379L206 371L212 379 M200 16L206 8L212 16" fill="none" stroke="#d9a53d" stroke-width="3"/>','<text x="237" y="410" font-family="sans-serif" font-size="11" fill="#273c36">START · C1</text>','<text x="237" y="18" font-family="sans-serif" font-size="11" fill="#273c36">EXIT · C5</text>','</svg>']
    return '\n'.join(out)

RULES='Hold the pictured clues in place. Place every loose module upright on the grid, using quarter-turns. Reserve each whole bridge strip, including its opening; modules may not overlap. No stacking. Move the ferry from C1 to C5 along orthogonal cell-center lines, through both high bridges, without revisiting a cell. Keep the cabin aimed toward the far edge; slide sideways on horizontal steps. Cross each bridge opening straight and perpendicular to its strip. During the trip, do not lift the ferry or move architecture. The low gate rejects the cabin. Between trials, lift and rearrange loose pieces; keep the clues. To reset, return to the setup picture.'
STYLE='''@page{size:A4;margin:12mm}*{box-sizing:border-box}body{margin:0;background:#e5dfd1;color:#193d40;font:15px/1.5 system-ui,sans-serif}.page{width:186mm;min-height:270mm;background:#faf7f0;margin:20px auto;padding:10mm;break-after:page}.eyebrow{text-transform:uppercase;letter-spacing:.22em;font-size:12px}h1{font-family:Georgia,serif;font-weight:400;font-size:38px;line-height:1.05;margin:12px 0}h2{font-family:Georgia,serif;font-weight:400;font-size:26px;margin:12px 0}p{margin:10px 0}.diagram{display:block;width:125mm;max-width:100%;margin:7mm auto}.chip{display:inline-block;border:1px solid #758b80;border-radius:20px;padding:3px 12px;margin-right:5px;font-weight:600}.note{font-size:12px;color:#516765}.rule{border-top:1px solid #a9b7a8;padding-top:12px;font-size:13px}.folio{margin-top:16px;font-size:11px;letter-spacing:.1em}.answer{display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:start}.answer img{width:100%}.route{font-size:12px;overflow-wrap:anywhere}table{border-collapse:collapse;font-size:13px;width:100%}td,th{padding:5px;border-bottom:1px solid #c8d0c4;text-align:left}@media print{body{background:white}.page{margin:0;padding:6mm;min-height:270mm;width:auto}.page:last-child{break-after:auto}}'''
def document(title,pages):return f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{STYLE}</style><body>'+''.join(pages)+'</body></html>'
def address(q):return 'ABCDE'[q[0]]+str(q[1]+1)
def table(poses):return '<table><tr><th>Module</th><th>Origin*</th><th>Turn CCW</th></tr>'+''.join(f'<tr><td>{v["part"]}</td><td>{address(v["origin"])}</td><td>{v["rotation"]}°</td></tr>' for v in poses)+'</table><p class="note">*Origin is the near-left corner of the rotated, normalized footprint. Diagram labels name modules; board coordinates name cells.</p>'

def main():
    setup_pages=[];answer_pages=[]
    for c in DATA['challenges']:
        name=c['id'];setup=f'{name}-setup.svg';(ROOT/setup).write_text(svg(c['fixed']))
        setup_pages.append(f'<section class="page"><div class="eyebrow">QUAYSHIFT / {name}</div><h1>{html.escape(c["title"])}</h1><p>Build the town. Let the ferry through.</p><p>'+''.join(f'<span class="chip">Loose {n}</span>' for n in c['loose'])+f'</p><img class="diagram" src="{setup}" alt="{name} fixed setup"/><p><b>Begin:</b> Place only the pictured modules. Empty cells are available for the loose pieces and ferry.</p><p class="rule">{RULES}</p><p class="note">Symbolic top view. Offset colored bands show rear bridge spans; match their facing. × marks the low gate. Colors do not constrain placement. More than one solution is allowed.</p><div class="folio">THREE EDITED CHALLENGES · SETUP {name} · ANSWERS IN SOLUTIONS.HTML</div></section>')
        for j,w in enumerate(c['completions'],1):
            fn=f'{name}-solution-{j:02}.svg';(ROOT/fn).write_text(svg(w['placements'],w['routes'][0]))
            routes='<br>'.join(' → '.join(map(address,r)) for r in w['routes'])
            answer_pages.append(f'<section class="page"><div class="eyebrow">QUAYSHIFT / solutions · {name}</div><h1>{html.escape(c["title"])}</h1><h2>Arrangement {j} of {len(c["completions"])}</h2><p>{html.escape(c["deduction"])}</p><div class="answer"><img src="{fn}" alt="{name} solution {j} with one route"/><div>{table(w["placements"])}</div></div><p class="route"><b>Routes ({w["route_count"]}):</b><br>{routes}</p><p class="note">Gold draws the first listed route. Multiple route drawings in one arrangement count as one construction solution. A/B, E/F and G/H share footprint roles; color is not a rule. To reproduce a checked solution, match the shown labels, rotations and rear-span facing.</p><p class="rule">A tempting failure: exchange either required high bridge with the low gate in a full witness layout. The footprints still fit, but the required trip fails. Solids placed across a turn or exit corridor can also leave a town that fits without a legal ferry trip.</p><p class="note">Counts describe footprint arrangements with at least one checked exact pose. They do not count every facade facing: some alternate starter bridge facings fail the conservative finger-access check. Match the shown span orientation when reproducing these answers. Hands-on comfort is unverified.</p><div class="folio">SYMBOLIC FOOTPRINTS · UPRIGHT ONLY · NO STACKING</div></section>')
    setup_pages.append('<section class="page"><div class="eyebrow">QUAYSHIFT / playing reference</div><h1>A town you can rebuild.</h1><p>'+RULES+'</p><h2>Read the modules</h2><p>A and B: high bridges. C: low gate. D: L-shaped courtyard. E and F: two-cell buildings. G and H: single-cell towers.</p><p>Bridge feet occupy the two ends of a three-cell strip. Its opening belongs to that module; never place another module there. The offset colored band shows the rear bridge span; match its position when setting clues or reproducing a solution. Building outlines are symbolic footprints, not literal roof silhouettes.</p><h2>When the trip fails</h2><p>Stop if the ferry touches blocked architecture, cannot clear an opening, leaves the board except at C5, revisits a cell, or misses either high bridge. Reset the ferry to C1 and rearrange loose modules before another trial.</p><h2>Three starting situations</h2><p>The first card introduces headroom. The second asks you to protect a detour. The third asks you to arrange solid buildings around fixed bridges. These are different placement tasks; no measured difficulty or human playtest is claimed.</p><p class="note">This set contains three edited challenges. The aspirational 24-card set has not been produced. The 2 / 4 / 8 counts describe footprint arrangements with checked representative poses, not every physically distinguishable facing. Match the shown rear-span orientation to reproduce solutions. Physical manufacture and hands-on play remain unverified.</p></section>')
    (ROOT/'cards.html').write_text(document('QUAYSHIFT · three challenge cards',setup_pages))
    (ROOT/'solutions.html').write_text(document('QUAYSHIFT · solution arrangements',answer_pages))
    print(json.dumps({'setup_cards':3,'solution_arrangements':len(answer_pages),'svg_assets':len(list(ROOT.glob('*.svg')))}))
if __name__=='__main__':main()
