"""Deterministic offline Crosscurrent printables. ReportLab, no CAD mutation."""
from pathlib import Path
from math import sin, cos, radians
import re
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, A5
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, PageBreak
from reportlab.graphics.shapes import Drawing, Circle, Line, String, Rect, Polygon

ROOT = Path(__file__).resolve().parent
INK = colors.HexColor('#173448')
TEAL = colors.HexColor('#147C80')
PALE = colors.HexColor('#E8F4F2')
GOLD = colors.HexColor('#DDAF48')
PAPER = colors.HexColor('#F5F8FA')
OWNERS = [colors.HexColor(v) for v in ['#CB6852','#4A88B5','#758E47','#A475AB','#BD9541']]
W = A4[0] - 36*mm


def plain(s):
    for a, b in [('−','-'),('–','-'),('—',' - '),('→','to'),('×',' x '),('°',' degrees'),('’',"'"),('“','"'),('”','"'),('≥','>=')]:
        s=s.replace(a,b)
    return s


def inline(s):
    s=escape(plain(s))
    s=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',s)
    s=re.sub(r'`(.+?)`',r'<font name="Courier">\1</font>',s)
    return s

styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyGame',fontName='Helvetica',fontSize=10.4,leading=14.2,textColor=INK,spaceAfter=7))
styles.add(ParagraphStyle(name='TitleGame',fontName='Helvetica-Bold',fontSize=31,leading=34,textColor=INK,spaceAfter=8))
styles.add(ParagraphStyle(name='H2Game',fontName='Helvetica-Bold',fontSize=17,leading=21,textColor=TEAL,spaceBefore=13,spaceAfter=7,keepWithNext=True))
styles.add(ParagraphStyle(name='H3Game',fontName='Helvetica-Bold',fontSize=12.2,leading=16,textColor=INK,spaceBefore=9,spaceAfter=5,keepWithNext=True))
styles.add(ParagraphStyle(name='SmallGame',fontName='Helvetica',fontSize=8.2,leading=10.8,textColor=INK))
styles.add(ParagraphStyle(name='CaptionGame',fontName='Helvetica',fontSize=9,leading=12,textColor=INK,spaceAfter=9))


def board(d,cx,cy,r,tokens,show_rewards=True):
    """Harbor 1 is due right, harbor numbers increase clockwise."""
    d.add(Circle(cx,cy,r,fillColor=PAPER,strokeColor=INK,strokeWidth=1))
    d.add(Circle(cx,cy,r*.77,fillColor=PALE,strokeColor=TEAL,strokeWidth=1))
    d.add(Circle(cx,cy,r*.46,fillColor=colors.white,strokeColor=TEAL,strokeWidth=1))
    for h in range(1,7):
        a=radians(-60*(h-1))
        ux,uy=cos(a),sin(a)
        d.add(Line(cx+ux*r*.8,cy+uy*r*.8,cx+ux*r*.89,cy+uy*r*.89,strokeColor=INK,strokeWidth=1))
        for br in [.32,.65]:
            d.add(Circle(cx+ux*r*br,cy+uy*r*br,r*.112,fillColor=colors.white,strokeColor=colors.HexColor('#B4CED0'),strokeWidth=.6))
        tx,ty=cx+ux*(r+12),cy+uy*(r+12)
        d.add(String(tx,ty-3,str(h),fontName='Helvetica-Bold',fontSize=10,textAnchor='middle',fillColor=INK))
        if show_rewards:
            n=[2,4,3,2,4,3][h-1]
            # Use text for reward only at sufficient radius, to keep IDs unambiguous.
            d.add(String(tx,ty-13,f'{n} pts',fontName='Helvetica',fontSize=6.5,textAnchor='middle',fillColor=TEAL))
    for owner,letter,ring,h in tokens:
        a=radians(-60*(h-1))
        br=.32 if ring=='inner' else .65
        x,y=cx+cos(a)*r*br,cy+sin(a)*r*br
        d.add(Circle(x,y,r*.124,fillColor=OWNERS[owner-1],strokeColor=INK,strokeWidth=.7))
        d.add(String(x,y-2.6,f'{owner}{letter}',fontName='Helvetica-Bold',fontSize=max(5.8,r*.095),textAnchor='middle',fillColor=colors.white))


def setup_illustration():
    d=Drawing(W,246)
    tokens=[]
    for i,(a,b) in enumerate([(1,4),(2,5),(3,6),(4,1),(5,2)],1):
        tokens.extend([(i,'A','inner',a),(i,'B','outer',b)])
    board(d,128,126,90,tokens)
    d.add(String(256,207,'Five-player starting position',fontName='Helvetica-Bold',fontSize=12,fillColor=INK))
    lines=['1A means player 1, boat A.','A boats begin on the inner disk.','B boats begin on the outer ring.','Harbor 1 is shown at the right.','2, 3, 4, 5 and 6 follow clockwise.','Number = harbor; points = reward.','Use the table for 2, 3 or 4 players.']
    for j,t in enumerate(lines):
        d.add(String(256,183-j*19,t,fontName='Helvetica',fontSize=9.2,fillColor=INK))
    # Clockwise cue follows negative polar angles on screen.
    d.add(Line(213,178,223,164,strokeColor=TEAL,strokeWidth=2))
    d.add(Polygon([223,164,217,168,224,172],fillColor=TEAL,strokeColor=TEAL))
    return d


def example_illustration():
    d=Drawing(W,207)
    states=[[(1,'A','inner',1),(2,'B','inner',3),(3,'A','outer',4)],[(1,'A','inner',1),(2,'B','inner',3),(3,'A','outer',5)],[(1,'A','outer',2),(2,'B','outer',4),(3,'A','inner',6)]]
    captions=['BEFORE TURN','AT SCORING','AFTER CROSSING']
    for i,tokens in enumerate(states):
        cx=W*(i+.5)/3
        board(d,cx,110,58,tokens,False)
        d.add(String(cx,190,captions[i],fontName='Helvetica-Bold',fontSize=9,textAnchor='middle',fillColor=INK))
    d.add(String(W/6,20,'Orders: 1A +1, 2B -1, 3A +1',fontName='Helvetica',fontSize=7.5,textAnchor='middle',fillColor=INK))
    d.add(String(W/2,20,'Earned: 1 = 2, 2 = 3, 3 = 4',fontName='Helvetica',fontSize=7.5,textAnchor='middle',fillColor=INK))
    d.add(String(W*5/6,20,'Other ring; one harbor clockwise',fontName='Helvetica',fontSize=7.5,textAnchor='middle',fillColor=INK))
    return d


def page_footer(c,doc):
    c.saveState()
    c.setStrokeColor(TEAL); c.setLineWidth(.7)
    c.line(18*mm,17*mm,A4[0]-18*mm,17*mm)
    c.setFont('Helvetica',8); c.setFillColor(INK)
    c.drawString(18*mm,12*mm,'CROSSCURRENT | Rules revision 1 | Simulated; physical and human testing pending')
    c.drawRightString(A4[0]-18*mm,12*mm,str(doc.page))
    c.restoreState()


def build_rules():
    lines=(ROOT/'RULES.md').read_text().splitlines()
    story=[]; i=0; code_count=0
    while i<len(lines):
        s=lines[i].strip()
        if not s:
            i+=1; continue
        if s.startswith('```'):
            i+=1
            while i<len(lines) and not lines[i].strip().startswith('```'): i+=1
            i+=1;code_count+=1
            if code_count==1:
                story.append(setup_illustration())
                story.append(Paragraph('Illustrated five-player setup. Rotate this entire view to match your seat; the harbor order remains clockwise.',styles['CaptionGame']))
            else:
                story.append(example_illustration())
                story.append(Paragraph('Only the three selected boats are shown here. Unselected boats still ride their rings; they do not harvest or cross.',styles['CaptionGame']))
            continue
        if s.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                row=[v.strip() for v in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[-:]+',v) for v in row): rows.append(row)
                i+=1
            n=len(rows[0]); widths=([42,84,50,58,79,42,W-355] if n==7 else [W/n]*n)
            if n==7:
                rows[0]=["Player","Before reveal","Arrow","Ring total","At scoring","Points","After crossing"]
            data=[[Paragraph(inline(v),styles['SmallGame']) for v in row] for row in rows]
            t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
            t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),PALE),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#B4CED0')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
            story.extend([KeepTogether([t]) if n==2 else t,Spacer(1,8)])
            continue
        if s.startswith('# '): story.append(Paragraph(inline(s[2:]),styles['TitleGame']))
        elif s.startswith('### '): story.append(Paragraph(inline(s[4:]),styles['H3Game']))
        elif s.startswith('## '):
            if s[3:] in ['Set up','Worked round']:
                story.append(PageBreak())
            story.append(Paragraph(inline(s[3:]),styles['H2Game']))
        else:
            # Markdown source paragraphs are one line each; preserve each ordered instruction.
            if s.startswith('- '): s='• '+s[2:]
            story.append(Paragraph(inline(s),styles['BodyGame']))
        i+=1
    doc=SimpleDocTemplate(str(ROOT/'RULES.pdf'),pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,topMargin=16*mm,bottomMargin=23*mm,title='Crosscurrent - complete rules, revision 1',author='Autonomous Workshop / Leo',invariant=1)
    doc.build(story,onFirstPage=page_footer,onLaterPages=page_footer)


def arrow(c,cx,cy,clockwise):
    # Arc from angles 140 to -140 for clockwise; reverse for CCW.
    r=9*mm
    vals=[140-i*280/40 for i in range(41)]
    if not clockwise: vals=vals[::-1]
    p=c.beginPath()
    for i,a in enumerate(vals):
        x,y=cx+r*cos(radians(a)),cy+r*sin(radians(a))
        (p.moveTo if i==0 else p.lineTo)(x,y)
    c.setStrokeColor(TEAL);c.setLineWidth(2.3);c.drawPath(p)
    x,y=cx+r*cos(radians(vals[-1])),cy+r*sin(radians(vals[-1]))
    prevx,prevy=cx+r*cos(radians(vals[-2])),cy+r*sin(radians(vals[-2]))
    dx,dy=x-prevx,y-prevy; norm=(dx*dx+dy*dy)**.5;dx/=norm;dy/=norm
    q=c.beginPath();q.moveTo(x,y);q.lineTo(x-6*dx+3*dy,y-6*dy-3*dx);q.lineTo(x-6*dx-3*dy,y-6*dy+3*dx);q.close()
    c.setFillColor(TEAL);c.drawPath(q,fill=1,stroke=0)


def build_cards():
    c=canvas.Canvas(str(ROOT/'CARDS.pdf'),pagesize=A4,invariant=1)
    c.setTitle('Crosscurrent - 25 action cards and A5 score sheet');c.setAuthor('Autonomous Workshop / Leo')
    c.setFillColor(INK);c.setFont('Helvetica-Bold',20);c.drawString(12*mm,280*mm,'CROSSCURRENT / ACTION CARDS')
    c.setFont('Helvetica',8.5)
    for y,s in [(273,'Print this page on opaque paper at 100%. Cut on the outlines. Leave every back blank.'),(268,'Each row is one player set: three directions and two boat selectors. Do not print the score sheet on the reverse.')]:
        c.drawString(12*mm,y*mm,s)
    cw,ch,gap=35*mm,45*mm,3*mm
    x0=11.5*mm; ytop=261*mm
    for owner in range(1,6):
        for col,kind in enumerate(['-1','0','+1','A','B']):
            x=x0+col*(cw+gap); y=ytop-owner*ch-(owner-1)*gap
            c.setFillColor(colors.white);c.setStrokeColor(colors.HexColor('#738891'));c.setLineWidth(.5);c.rect(x,y,cw,ch,fill=1,stroke=1)
            c.setFillColor(OWNERS[owner-1]);c.rect(x,y+ch-8*mm,cw,8*mm,fill=1,stroke=0)
            c.setFillColor(colors.white);c.setFont('Helvetica-Bold',8)
            c.drawCentredString(x+cw/2,y+ch-5.3*mm,f'PLAYER {owner}  '+('I '*owner).strip())
            c.setFillColor(INK)
            if kind in ['-1','+1']:
                arrow(c,x+cw/2,y+24*mm,kind=='+1')
                c.setFont('Helvetica-Bold',14);c.drawCentredString(x+cw/2,y+22*mm,kind)
                label='CCW' if kind=='-1' else 'CW'
                full='COUNTERCLOCKWISE' if kind=='-1' else 'CLOCKWISE'
                c.setFont('Helvetica-Bold',10);c.drawCentredString(x+cw/2,y+10*mm,label)
                c.setFont('Helvetica',6.6);c.drawCentredString(x+cw/2,y+6*mm,full)
            elif kind=='0':
                c.setFont('Helvetica-Bold',35);c.drawCentredString(x+cw/2,y+21*mm,'0')
                c.setFont('Helvetica-Bold',10);c.drawCentredString(x+cw/2,y+10*mm,'HOLD / STILL')
                c.setFont('Helvetica',6.6);c.drawCentredString(x+cw/2,y+6*mm,'ADD ZERO TO THE TOTAL')
            else:
                c.setFont('Helvetica-Bold',35);c.drawCentredString(x+cw/2,y+21*mm,kind)
                c.setFont('Helvetica-Bold',10);c.drawCentredString(x+cw/2,y+10*mm,'SELECT BOAT')
                c.setFont('Helvetica',6.6);c.drawCentredString(x+cw/2,y+6*mm,'RETURN AFTER EACH ROUND')
    c.setStrokeColor(INK);c.setLineWidth(.6);c.line(12*mm,12*mm,62*mm,12*mm);c.line(12*mm,10*mm,12*mm,14*mm);c.line(62*mm,10*mm,62*mm,14*mm)
    c.setFont('Helvetica',7);c.drawString(67*mm,11*mm,'This line must measure 50 mm. Card size: 35 x 45 mm.')
    c.showPage();c.setPageSize(A5)
    sw,sh=A5
    c.setFillColor(INK);c.setFont('Helvetica-Bold',21);c.drawString(10*mm,sh-17*mm,'CROSSCURRENT')
    c.setFont('Helvetica-Bold',12);c.drawString(10*mm,sh-25*mm,'12-ROUND SCORE SHEET')
    c.setFont('Helvetica',8);c.drawString(10*mm,sh-33*mm,'Date: __________________   Record points earned each round.')
    left=10*mm;top=sh-40*mm;tw=sw-20*mm;rw=18*mm;pw=(tw-rw)/5;rh=8.7*mm
    # Header, name row, twelve score rows, total row.
    for row in range(15):
        y=top-(row+1)*rh
        if row in [0,1,14]:c.setFillColor(PALE);c.rect(left,y,tw,rh,fill=1,stroke=0)
        c.setStrokeColor(colors.HexColor('#B4CED0'));c.setLineWidth(.5);c.rect(left,y,tw,rh,fill=0,stroke=1)
        for j in range(5):c.line(left+rw+j*pw,y,left+rw+j*pw,y+rh)
        c.setFillColor(INK);c.setFont('Helvetica-Bold' if row in [0,14] else 'Helvetica',8)
        label='Round' if row==0 else ('Name' if row==1 else ('TOTAL' if row==14 else str(row-1)))
        c.drawCentredString(left+rw/2,y+3.1*mm,label)
        if row==0:
            for j in range(5):c.drawCentredString(left+rw+(j+.5)*pw,y+3.1*mm,f'Player {j+1}')
        if row in [4,7,10,13]:
            c.setStrokeColor(TEAL);c.setLineWidth(1.4);c.line(left,y,left+tw,y)
    yy=top-15*rh-7*mm
    c.setFont('Helvetica',8)
    for j,s in enumerate(['Refresh all three directions after rounds 3, 6 and 9.','After round 12: highest total wins; tied players share the win.','No extra round. Scores and used direction cards stay public.']):
        c.drawString(left,yy-j*4.5*mm,s)
    c.save()

if __name__=='__main__':
    build_rules();build_cards()
    print('Wrote RULES.pdf and CARDS.pdf')
