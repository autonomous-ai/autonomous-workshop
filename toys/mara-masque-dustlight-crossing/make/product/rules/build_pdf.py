"""Build printable original rules from RULES.md; render actual PDF via PDFium."""
from pathlib import Path
from hashlib import sha256
import json
import re
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.graphics.shapes import Drawing, Rect, Circle, Line, String, Polygon
import pypdfium2 as pdfium
from pypdf import PdfReader

HERE=Path(__file__).resolve().parent
PRODUCT=HERE.parent
WORKSPACE=PRODUCT.parents[3]
EVIDENCE=WORKSPACE/'design'/'rules-pdf-evidence'
EVIDENCE.mkdir(parents=True,exist_ok=True)
source=(PRODUCT/'RULES.md').read_text()
pdf=PRODUCT/'RULES.pdf'
INK=colors.HexColor('#182633')
MUTED=colors.HexColor('#4b5860')
LIGHT=colors.HexColor('#e9edf0')
styles={
    'title':ParagraphStyle('title',fontName='Helvetica-Bold',fontSize=26,leading=30,textColor=INK,spaceAfter=10),
    'h':ParagraphStyle('h',fontName='Helvetica-Bold',fontSize=16,leading=20,textColor=INK,spaceAfter=10),
    'body':ParagraphStyle('body',fontName='Helvetica',fontSize=10.7,leading=14.8,textColor=INK,spaceAfter=9),
    'small':ParagraphStyle('small',fontName='Helvetica',fontSize=8.8,leading=11.8,textColor=INK,spaceAfter=6),
    'cell':ParagraphStyle('cell',fontName='Helvetica',fontSize=9.5,leading=12,textColor=INK),
}
def markup(text):
    text=escape(text)
    text=re.sub(r'\[([^]]+)\]\(([^)]+)\)',r'<link href="\2" color="#205573">\1</link>',text)
    return re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',text)
def p(text,style='body'):
    return Paragraph(markup(text),styles[style])
def paragraphs(text,style='body'):
    return [p(' '.join(block.splitlines()),style) for block in text.strip().split('\n\n') if block.strip()]
parts={}
sections=re.split(r'^## ',source,flags=re.M)
intro=sections[0].split('\n',1)[1].strip()
for section in sections[1:]:
    heading,body=section.split('\n',1)
    parts[heading.strip()]=body.strip()
def table_from_md(block,widths):
    lines=[line for line in block.splitlines() if line.startswith('|')]
    rows=[]
    for line in lines:
        cells=[x.strip() for x in line.strip('|').split('|')]
        if all(re.fullmatch(r'[-:]+',x) for x in cells):
            continue
        rows.append([p(x,'cell') for x in cells])
    table=Table(rows,colWidths=widths,hAlign='LEFT',repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),LIGHT),('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),
        ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('LINEBELOW',(0,0),(-1,0),0.7,INK),('LINEBELOW',(0,1),(-1,-1),0.3,colors.HexColor('#c7cdd1')),
    ]))
    return table

def setup_diagram():
    d=Drawing(246,332)
    s=29; ox=23; oy=37
    water={(x,y) for x in (1,2,4,5) for y in (3,4,5)}
    traps={(2,0),(3,1),(4,0),(2,8),(3,7),(4,8)}
    dens={(3,0),(3,8)}
    for x in range(7):
        for y in range(9):
            xx,yy=ox+x*s,oy+y*s
            d.add(Rect(xx,yy,s,s,fillColor=colors.white,strokeColor=colors.HexColor('#a8afb5'),strokeWidth=0.6))
            if (x,y) in water:
                for offset in (6,12,18,24):
                    d.add(Line(xx+4,yy+offset,xx+25,yy+offset,strokeColor=MUTED,strokeWidth=1))
            if (x,y) in traps:
                for a,b,c,e in [(9,5,20,5),(9,24,20,24),(5,9,5,20),(24,9,24,20)]:
                    d.add(Line(xx+a,yy+b,xx+c,yy+e,strokeColor=INK,strokeWidth=1.7))
            if (x,y) in dens:
                d.add(Rect(xx+5,yy+5,19,19,fillColor=None,strokeColor=INK,strokeWidth=1.4))
    for i,char in enumerate('abcdefg'):
        d.add(String(ox+(i+.5)*s,oy-14,char,fontName='Helvetica',fontSize=10,textAnchor='middle',fillColor=INK))
    for i in range(9):
        d.add(String(ox-10,oy+(i+.5)*s-3,str(i+1),fontName='Helvetica',fontSize=10,textAnchor='middle',fillColor=INK))
    starts=[['g3','b2','c3','f2','e3','a1','g1','a3'],['a7','f8','e7','b8','c7','g9','a9','g7']]
    for side,coords in enumerate(starts):
        for rank,coord in enumerate(coords,1):
            cx=ox+(ord(coord[0])-97+.5)*s;cy=oy+(int(coord[1])-.5)*s
            if side==0:
                d.add(Circle(cx,cy,10,fillColor=colors.white,strokeColor=INK,strokeWidth=1.5))
                fg=INK
            else:
                d.add(Polygon([cx-7,cy-10,cx+7,cy-10,cx+10,cy-7,cx+10,cy+7,cx+7,cy+10,cx-7,cy+10,cx-10,cy+7,cx-10,cy-7],fillColor=INK,strokeColor=INK))
                fg=colors.white
            d.add(String(cx,cy-3.5,str(rank),fontName='Helvetica-Bold',fontSize=11,textAnchor='middle',fillColor=fg))
    d.add(String(ox+3.5*s,oy+9*s+15,'BLACK · CLIPPED-SQUARE BASES',fontName='Helvetica-Bold',fontSize=8.5,textAnchor='middle',fillColor=INK))
    d.add(String(ox+3.5*s,6,'WHITE · CIRCULAR BASES · FIRST MOVE',fontName='Helvetica-Bold',fontSize=8.2,textAnchor='middle',fillColor=INK))
    return d

def footer(canvas,doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#c7cdd1'));canvas.line(40,37,A4[0]-40,37)
    canvas.setFont('Helvetica',8);canvas.setFillColor(MUTED)
    canvas.drawString(40,23,'DUSTLIGHT CROSSING  /  Jungle Chess - Leiden baseline')
    canvas.drawRightString(A4[0]-40,23,str(doc.page))
    canvas.restoreState()

doc=SimpleDocTemplate(str(pdf),pagesize=A4,rightMargin=40,leftMargin=40,topMargin=36,bottomMargin=48,
                      title='Dustlight Crossing - complete rules',author='Autonomous Workshop',pageCompression=1)
story=[p('Dustlight Crossing','title')]+paragraphs(intro)
story.append(p('1 / Set up','h'))
setup=parts['Set up']
before,rest=setup.split('|Rank|',1)
tableblock,terrain=('|Rank|'+rest).split('\n\n',1)
story+=paragraphs(before)
# Original setup vector drawing alongside a compact eight-role key.
keyrows=[['Rank','Source role','Celestial form']]
for line in tableblock.splitlines()[2:]:
    cells=[x.strip() for x in line.strip('|').split('|')]
    keyrows.append(cells[:3])
keytable=Table([[p(c,'small') for c in row] for row in keyrows],colWidths=[32,69,133])
keytable.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),LIGHT),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),('LINEBELOW',(0,0),(-1,-1),0.3,colors.HexColor('#ccd1d5'))]))
layout=Table([[setup_diagram(),keytable]],colWidths=[262,253])
layout.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0)]))
story += [layout,Spacer(1,6)]+paragraphs(terrain,'small')
story += [PageBreak(),p('2 / Play and finish','title')]
story += paragraphs(parts['Take a turn'])
story += [Spacer(1,8),p('End the game','h')]+paragraphs(parts['End the game'])
theme=parts['What the astronomy means']
theme_intro,rest=theme.split('|Rule|',1)
themetable,after=('|Rule|'+rest).split('\n\n',1)
inventory,provenance=after.split('\n\n',1)
story += [Spacer(1,8),p('Inventory and replacements','h')]+paragraphs(inventory)
story += [Spacer(1,8),p('Rule source','h')]+paragraphs(provenance,'small')
story += [PageBreak(),p('3 / Read the sky','title')]+paragraphs(theme_intro)
story += [table_from_md(themetable,[132,383])]
doc.build(story,onFirstPage=footer,onLaterPages=footer)

reader=PdfReader(str(pdf))
assert len(reader.pages)==3, f'Expected three readable pages, got {len(reader.pages)}'
text='\n'.join(page.extract_text() for page in reader.pages)
for phrase in ('Rat','Wolf','Dog','stalemate','three times','either team','rank0','Rat1 too','reference aperture'):
    assert phrase in text,phrase
pdfdoc=pdfium.PdfDocument(str(pdf))
renderpaths=[]
for number in range(len(pdfdoc)):
    page=pdfdoc[number]
    bitmap=page.render(scale=1.7)
    path=EVIDENCE/f'page-{number+1}.png'
    bitmap.to_pil().save(path)
    renderpaths.append(str(path.relative_to(WORKSPACE)))
    bitmap.close();page.close()
pdfdoc.close()
evidence={'pdf':str(pdf.relative_to(WORKSPACE)),'pages':len(reader.pages),
          'pdf_sha256':sha256(pdf.read_bytes()).hexdigest(),
          'rules_md_sha256':sha256((PRODUCT/'RULES.md').read_bytes()).hexdigest(),
          'rendered_pages':renderpaths,'render_method':'PDFium renders of final PDF at 1.7x A4 point size',
          'setup_diagram':'Original vector diagram, coordinates and shapes; not source artwork.',
          'visual_inspection':'pending native image inspection'}
(EVIDENCE/'manifest.json').write_text(json.dumps(evidence,indent=2)+'\n')
print(json.dumps(evidence,indent=2))
