"""Reader content is only book.json chapters plus selected source and figures.

This publisher deliberately never imports reference reports, raw runtime JSON or logs
into the book. Bookmarks, links, line numbers and vector figures are native PDF.
"""
from pathlib import Path
import re, json, html, hashlib, argparse, math, xml.etree.ElementTree as ET
from io import BytesIO
from collections import Counter
from itertools import groupby
from PIL import Image as PILImage
from markdown_it import MarkdownIt
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import ttfonts
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (BaseDocTemplate,PageTemplate,Frame,Paragraph,Spacer,
    PageBreak,KeepTogether,Table,TableStyle,Flowable,CondPageBreak,ActionFlowable)
from reportlab.platypus.tableofcontents import TableOfContents
from pypdf import PdfReader
from source_excerpts import extract
from editions import load,output_path,protected_history,specifications
from pygments import lex
from pygments.lexers import CSharpLexer,TypeScriptLexer,SqlLexer,TextLexer
from pygments.token import Token

M=Path(__file__).resolve().parents[1];ROOT=M.parent
CONF=load()
CAT=json.loads((M/CONF['figureCatalog']).read_text(encoding='utf-8'))
SPECS=specifications(CONF)
CHAPTER_ROOT=M/CONF['chapterRoot'];BUILD=M/CONF['buildDirectory']
W,H=595.276,841.89; LEFT=55;RIGHT=51;TOP=59;BOTTOM=49;WIDTH=W-LEFT-RIGHT
INK=colors.HexColor('#213b43');TEAL=colors.HexColor('#1a6c65');MUTED=colors.HexColor('#637677')
FONTS=Path('C:/Windows/Fonts')
pdfmetrics.registerFont(TTFont('Book',str(FONTS/'msyh.ttc'),subfontIndex=0))
pdfmetrics.registerFont(TTFont('BookBold',str(FONTS/'msyhbd.ttc'),subfontIndex=0))
pdfmetrics.registerFont(TTFont('Mono',str(FONTS/'consola.ttf')))
pdfmetrics.registerFont(TTFont('Symbols',str(FONTS/'seguisym.ttf')))
pdfmetrics.registerFontFamily('Book',normal='Book',bold='BookBold',italic='Book',boldItalic='BookBold')
# ReportLab emits non-BMP ToUnicode targets as scalar hex; PDF requires UTF-16BE.
# Preserve the original source glyph while making extraction/search standards-compliant.
_make_cmap=ttfonts.makeToUnicodeCMap
def unicode_cmap(*args,**kwargs):
    value=_make_cmap(*args,**kwargs)
    return re.sub(r'<([0-9A-Fa-f]{5,6})>',lambda m:'<'+chr(int(m[1],16)).encode('utf-16-be').hex().upper()+'>',value)
ttfonts.makeToUnicodeCMap=unicode_cmap
ST={
 'body':ParagraphStyle('body',fontName='Book',fontSize=10.6,leading=18.2,textColor=INK,spaceAfter=7.5,wordWrap='CJK',allowWidows=0,allowOrphans=0),
 'h1':ParagraphStyle('h1',fontName='BookBold',fontSize=23.4,leading=34,spaceAfter=20,textColor=INK,keepWithNext=True,wordWrap='CJK'),
 'h2':ParagraphStyle('h2',fontName='BookBold',fontSize=14.2,leading=22.5,spaceBefore=16,spaceAfter=9,textColor=TEAL,keepWithNext=True,wordWrap='CJK'),
 'h3':ParagraphStyle('h3',fontName='BookBold',fontSize=11.6,leading=18.5,spaceBefore=13,spaceAfter=7,textColor=INK,keepWithNext=True,wordWrap='CJK'),
 'kicker':ParagraphStyle('kicker',fontName='BookBold',fontSize=10,leading=15,spaceAfter=8,textColor=colors.HexColor('#9a702d'),keepWithNext=True),
 'caption':ParagraphStyle('caption',fontName='Book',fontSize=8.7,leading=13.6,spaceAfter=11,textColor=MUTED,wordWrap='CJK'),
 'small':ParagraphStyle('small',fontName='Book',fontSize=8.1,leading=12.3,textColor=MUTED,wordWrap='CJK',spaceAfter=5),
 'table':ParagraphStyle('table',fontName='Book',fontSize=9.1,leading=14.7,textColor=INK,wordWrap='CJK'),
 'quote':ParagraphStyle('quote',fontName='Book',fontSize=10,leading=17,textColor=TEAL,spaceBefore=7,spaceAfter=12,leftIndent=14,rightIndent=12,wordWrap='CJK',borderColor=colors.HexColor('#d0dfd8'),borderWidth=.7,borderPadding=10),
}
MD=MarkdownIt('commonmark').enable('table')
SOURCE=[];FIGURES=[];COUNTS=Counter();CHAPTERS=[]

def codefont(ch):
    if ord(ch)<=255:return 'Mono'
    return 'Book' if ord(ch) in pdfmetrics.getFont('Book').face.charWidths else 'Symbols'

def inline(s):
    toks=MD.parseInline(s)[0].children or [];out=[]
    for t in toks:
        if t.type=='text':out.append(html.escape(t.content))
        elif t.type=='code_inline':out.append('<font face="Book" color="#225f68">'+html.escape(t.content)+'</font>')
        elif t.type=='strong_open':out.append('<b>')
        elif t.type=='strong_close':out.append('</b>')
        elif t.type=='em_open':out.append('<i>')
        elif t.type=='em_close':out.append('</i>')
        elif t.type=='link_open':
            href=t.attrGet('href')
            if href in CONF['chapters']:
                href='#chapter-'+str(CONF['chapters'].index(href))
            elif not href.startswith(('http://','https://','#')):
                href=CONF['repository']+'/blob/'+CONF['sourceCommit']+'/'+str((CHAPTER_ROOT/href).resolve().relative_to(ROOT)).replace('\\','/')
            out.append(f'<a href="{html.escape(href,quote=True)}" color="#1a6c65">')
        elif t.type=='link_close':out.append('</a>')
        elif t.type in ('softbreak','hardbreak'):out.append(' ' if t.type=='softbreak' else '<br/>')
    return ''.join(out)

class Code(Flowable):
    def __init__(self,rows,width=WIDTH,fontSize=8.6,language='text'):
        Flowable.__init__(self);self.width=width;self.fs=fontSize;self.leading=12.4;self.language=language
        self.rows=[]
        for number,line in rows:
            # Exact source characters, only visual soft wrapping. Continuation has no fake line number.
            pieces=[];remain=line.replace('\t','    ');avail=width-61;continuation=False
            while remain:
                prefix='    ' if continuation else '';used=pdfmetrics.stringWidth(prefix,'Mono',fontSize);n=0
                for ch in remain:
                    cw=pdfmetrics.stringWidth(ch,codefont(ch),fontSize)
                    if used+cw>avail:break
                    used+=cw;n+=1
                if n==len(remain):pieces.append(prefix+remain);break
                candidates=[j+1 for j,c in enumerate(remain[:n]) if c in ' ,;(){}[]']
                cut=max([j for j in candidates if j>n*.55],default=n)
                pieces.append(prefix+remain[:cut]);remain=remain[cut:];continuation=True
            if not pieces:pieces=['']
            for i,p in enumerate(pieces):self.rows.append((str(number) if i==0 else '·',p))
        self.height=len(self.rows)*self.leading+18
    def wrap(self,aw,ah):return self.width,self.height
    def split(self,aw,ah):
        n=int((ah-18)/self.leading)
        if n<3:return []
        if n>=len(self.rows):return [self]
        def part(rows):
            p=Code([],self.width,self.fs,self.language);p.rows=rows;p.height=len(rows)*p.leading+18;return p
        return [part(self.rows[:n]),part(self.rows[n:])]
    def draw(self):
        c=self.canv;c.setFillColor(colors.HexColor('#f1f5f4'));c.roundRect(0,0,self.width,self.height,5,fill=1,stroke=0)
        c.setStrokeColor(colors.HexColor('#d2ddd8'));c.line(37,8,37,self.height-8)
        for i,(num,line) in enumerate(self.rows):
            y=self.height-16-i*self.leading;c.setFont('Mono',7.1);c.setFillColor(MUTED);c.drawRightString(30,y,num)
            x=45;comment=line.lstrip().startswith(('//','#','/*','*'))
            lexer={'cs':CSharpLexer,'ts':TypeScriptLexer,'tsx':TypeScriptLexer,'sql':SqlLexer}.get(self.language,TextLexer)()
            for kind,value in lex(line,lexer):
                value=value.rstrip('\n')
                tone=(MUTED if kind in Token.Comment or comment else
                      colors.HexColor('#795081') if kind in Token.Keyword else
                      colors.HexColor('#88612c') if kind in Token.Literal.String else
                      colors.HexColor('#315b91') if kind in Token.Literal.Number else INK)
                for face,characters in groupby(value,key=codefont):
                    run=''.join(characters);c.setFont(face,self.fs);c.setFillColor(tone)
                    c.drawString(x,y,run);x+=pdfmetrics.stringWidth(run,face,self.fs)

class VectorFigure(Flowable):
    def __init__(self,path):
        Flowable.__init__(self);self.tree=ET.parse(path).getroot();self.width=WIDTH
        self.vw=float(self.tree.attrib['width']);self.vh=float(self.tree.attrib['height'])
        self.scale=WIDTH/self.vw;self.height=self.vh*self.scale
    def draw(self):
        c=self.canv;c.saveState();c.scale(self.scale,self.scale)
        def color(value):return colors.HexColor(value)
        for el in self.tree:
            tag=el.tag.split('}')[-1];a=el.attrib
            if tag=='rect':
                fill=a.get('fill','none');stroke=a.get('stroke','none')
                if fill!='none':c.setFillColor(color(fill))
                if stroke!='none':c.setStrokeColor(color(stroke))
                c.setLineWidth(float(a.get('stroke-width',1)))
                c.roundRect(float(a.get('x',0)),self.vh-float(a.get('y',0))-float(a['height']),float(a['width']),float(a['height']),float(a.get('rx',0)),fill=int(fill!='none'),stroke=int(stroke!='none'))
            elif tag=='text':
                c.setFillColor(color(a.get('fill','#173c44')));c.setFont(a.get('font-family','Book'),float(a.get('font-size',22)))
                x=float(a['x']);y=self.vh-float(a['y']);s=el.text or '';anchor=a.get('text-anchor','start')
                if anchor=='middle':c.drawCentredString(x,y,s)
                elif anchor=='end':c.drawRightString(x,y,s)
                else:c.drawString(x,y,s)
            elif tag=='line':
                x1,y1,x2,y2=float(a['x1']),self.vh-float(a['y1']),float(a['x2']),self.vh-float(a['y2'])
                c.setStrokeColor(color(a.get('stroke','#627477')));c.setLineWidth(float(a.get('stroke-width',2)))
                c.setDash([7,6] if 'stroke-dasharray' in a else []);c.line(x1,y1,x2,y2);c.setDash([])
                if 'marker-end' in a:
                    angle=math.atan2(y2-y1,x2-x1);ux,uy=math.cos(angle),math.sin(angle);vx,vy=-uy,ux
                    p=c.beginPath();p.moveTo(x2,y2);p.lineTo(x2-11*ux+5*vx,y2-11*uy+5*vy);p.lineTo(x2-11*ux-5*vx,y2-11*uy-5*vy);p.close()
                    c.setFillColor(color(a.get('stroke','#627477')));c.drawPath(p,fill=1,stroke=0)
        c.restoreState()

class ScreenFigure(Flowable):
    def __init__(self,item):
        Flowable.__init__(self);self.item=item
        original=PILImage.open(M/item['file']).convert('RGB');self.panels=[]
        panels=item.get('panels',[dict(crop=item.get('crop'),marks=item['marks'])]);side=item.get('layout')=='side'
        cell=(WIDTH-12)/2 if side else WIDTH
        for panel in panels:
            im=original;crop=panel.get('crop')
            if crop:
                x,y,w,h=crop
                if x<0 or y<0 or x+w>im.width or y+h>im.height:raise ValueError(f'Invalid crop {item["file"]}: {im.size}, {crop}')
                im=im.crop((x,y,x+w,y+h))
            width=cell if 'panels' in item else min(WIDTH,item.get('maxHeight',370)*im.width/im.height)
            height=width*im.height/im.width
            self.panels.append(dict(image=ImageReader(im),w=width,h=height,marks=panel.get('marks',[]),label=panel.get('label')))
        self.width=WIDTH;self.side=side
        self.height=max(p['h']+18 for p in self.panels) if side else sum(p['h']+(18 if p['label'] else 0) for p in self.panels)+10*(len(self.panels)-1)
    def draw(self):
        c=self.canv;top=self.height
        for i,p in enumerate(self.panels):
            x=i*(p['w']+12) if self.side else (WIDTH-p['w'])/2
            panelTop=self.height if self.side else top
            if p['label']:
                c.setFont('Book',8.2);c.setFillColor(MUTED);c.drawString(x,panelTop-10,p['label']);panelTop-=18
            y=panelTop-p['h'];c.drawImage(p['image'],x,y,p['w'],p['h'])
            c.setStrokeColor(colors.HexColor('#c4d6d0'));c.rect(x,y,p['w'],p['h'],fill=0,stroke=1)
            for px,py,n in p['marks']:
                xx=x+px*p['w'];yy=y+(1-py)*p['h'];c.setFillColor(TEAL);c.setStrokeColor(colors.white);c.setLineWidth(1.3);c.circle(xx,yy,8.3,fill=1,stroke=1)
                c.setFillColor(colors.white);c.setFont('Mono',9.8);c.drawCentredString(xx,yy-3.5,n)
            if not self.side:top=y-10

class Book(BaseDocTemplate):
    def __init__(self,path):
        super().__init__(str(path),pagesize=(W,H),leftMargin=LEFT,rightMargin=RIGHT,topMargin=TOP,bottomMargin=BOTTOM,title=CONF['title'],author='EchoCase',allowSplitting=1,invariant=CONF['invariantPdf'])
        self.running='';self.tocseen=set();self.addPageTemplates(PageTemplate(id='book',frames=Frame(LEFT,BOTTOM,WIDTH,H-TOP-BOTTOM,id='body',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0),onPage=self.chrome))
    def beforeDocument(self):self.running='';self.tocseen=set()
    def chrome(self,c,doc):
        if doc.page==1:return
        c.saveState();c.setStrokeColor(colors.HexColor('#c9d6d1'));c.setLineWidth(.5);c.line(LEFT,H-36,W-RIGHT,H-36)
        c.setFont('Book',7.7);c.setFillColor(MUTED);c.drawString(LEFT,H-28,'EchoCase / 企业级 .NET 全栈软件工程')
        c.setFont('Book',7.2);c.drawRightString(W-RIGHT,28,f'{doc.page:03d}')
        c.drawString(LEFT,28,self.running[:39]);c.restoreState()
    def afterFlowable(self,f):
        if isinstance(f,Paragraph) and getattr(f,'_heading',None):
            level,title,key=f._heading
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title,key,level=level,closed=(level==0))
            self.notify('TOCEntry',(level,title,self.page,key))
            if level==0:self.running=title

class RunningChapter(ActionFlowable):
    def __init__(self,title):self.title=title
    def apply(self,doc):doc.running=self.title

def source(id):
    e=extract(id,CONF['sourceCommit'],SPECS,CONF['verifyWorkingTree']);SOURCE.append({k:v for k,v in e.items() if k!='text'})
    COUNTS['sourceLines']+=len(e['text'].splitlines())
    url=f'{CONF["repository"]}/blob/{e["commit"]}/{e["path"]}#L{e["start"]}'
    label=e['path']
    head=Paragraph(f'<b>{e["label"]}</b>　<a href="{url}" color="#1a6c65">{html.escape(label)}</a> · L{e["start"]}-{e["end"]}',ST['small'])
    head.keepWithNext=True
    return [head,Code([(e['start']+i,l) for i,l in enumerate(e['text'].splitlines())],language=Path(e['path']).suffix.lstrip('.')),Spacer(1,9)]

def figure(id,num):
    it=CAT[id];FIGURES.append(dict(id=id,number=num,**it));COUNTS['figures']+=1
    obj=VectorFigure(M/it['file']) if it['type']=='svg' else ScreenFigure(it)
    cap=Paragraph(f'<b>图 {num}</b>　{inline(it["caption"])}',ST['caption'])
    content=[obj,Spacer(1,6),cap]
    for line in it.get('legend',[]):content.append(Paragraph(html.escape(line),ST['caption']))
    # Keep the illustration and its explanation together; diagrams are smaller than one page.
    return [KeepTogether(content),Spacer(1,4)]

def table(lines):
    rows=[]
    for line in lines:
        if re.match(r'^\s*\|?[\s:|\-]+\|',line):continue
        cells=[x.strip() for x in line.strip().strip('|').split('|')]
        rows.append([Paragraph(inline(x),ST['table']) for x in cells])
    n=len(rows[0]);widths=[WIDTH/n]*n
    if n==2:widths=[WIDTH*.27,WIDTH*.73]
    t=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dcebe5')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f5f7f5')]),('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#c2d4cb')),('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8)]))
    return [Spacer(1,6),t,Spacer(1,12)]

def chapter(path,index):
    text=path.read_text(encoding='utf-8');COUNTS['han']+=len(re.findall(r'[\u4e00-\u9fff]',text));COUNTS['textCharacters']+=len(text)
    lines=text.splitlines();firstTitle=next(x[2:] for x in lines if x.startswith('# '));story=[RunningChapter(firstTitle),PageBreak()];i=0;fig=0;sections=0;title=''
    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        match=re.fullmatch(r'\{\{(code|figure)\s+([\w-]+)\}\}',line)
        if match:
            if match[1]=='code':story.extend(source(match[2]));COUNTS['listings']+=1
            else:fig+=1;story.extend(figure(match[2],f'{index}.{fig}'))
            i+=1;continue
        if line.startswith('# '):
            title=line[2:];display=title;m=re.match(r'第 (\d+) 章 (.*)',title)
            if m:
                story.append(Paragraph(f'第 {int(m[1]):02d} 章',ST['kicker']));display=m[2]
            style=ST['h1']
            natural=pdfmetrics.stringWidth(display,'BookBold',style.fontSize)
            if natural>WIDTH:
                size=max(20,min(style.fontSize,style.fontSize*WIDTH/natural))
                style=ParagraphStyle('h1fit',parent=style,fontSize=size,leading=size*1.45)
            p=Paragraph(inline(display),style);p._heading=(0,title,f'chapter-{index}');story.append(p);i+=1;continue
        if line.startswith(('## ','### ')):
            level=2 if line.startswith('## ') else 3;s=line[level+1:];p=Paragraph(inline(s),ST['h'+str(level)])
            if level==2:
                sections+=1;p._heading=(1,s,f'c{index}-s{sections}')
            story.append(p);i+=1;continue
        if line.startswith('```'):
            lang=line[3:];block=[];i+=1
            while i<len(lines) and not lines[i].strip().startswith('```'):block.append(lines[i]);i+=1
            # Explanatory SQL/HTTP fragments are explicitly labelled, never application source selections.
            story.append(Paragraph('运行摘录' if lang in ('sql','http','text') else '说明片段',ST['small']))
            story.append(Code([(i+1,l) for i,l in enumerate(block)],language=lang));story.append(Spacer(1,10));i+=1;continue
        if line.startswith('|'):
            block=[]
            while i<len(lines) and lines[i].strip().startswith('|'):block.append(lines[i]);i+=1
            story.extend(table(block));continue
        if line.startswith('> '):
            block=[]
            while i<len(lines) and lines[i].strip().startswith('> '):block.append(lines[i].strip()[2:]);i+=1
            story.append(Paragraph(inline(' '.join(block)),ST['quote']));continue
        if re.match(r'^(- |\d+\. )',line):
            m=re.match(r'^(- |\d+\. )(.*)',line);prefix='•　' if m[1]=='- ' else m[1]
            story.append(Paragraph(html.escape(prefix)+inline(m[2]),ST['body']));i+=1;continue
        block=[line];i+=1
        while i<len(lines) and lines[i].strip() and not re.match(r'^(#|\{\{|\||```|>|- |\d+\. )',lines[i].strip()):block.append(lines[i].strip());i+=1
        story.append(Paragraph(inline(''.join(block)),ST['body']))
    CHAPTERS.append(dict(file=path.name,title=title,figures=fig,sections=sections,han=len(re.findall(r'[\u4e00-\u9fff]',text))))
    # Group a heading with its first meaningful block. Flatten figure groups so
    # an interposed wrapper cannot strand a heading at the bottom of a page.
    result=[];k=0
    while k<len(story):
        f=story[k]
        if isinstance(f,Paragraph) and getattr(f,'_heading',None):
            bucket=[f];k+=1;tableFollowing=False
            while k<len(story):
                nxt=story[k]
                if isinstance(nxt,Spacer):bucket.append(nxt);k+=1;continue
                if isinstance(nxt,Paragraph) and nxt.style.name=='small':bucket.append(nxt);k+=1;continue
                if isinstance(nxt,Table):
                    # Long tables must split after the heading instead of moving
                    # an entire appendix table to a mostly empty new page.
                    f.keepWithNext=False
                    result.extend([CondPageBreak(180),*bucket,nxt]);k+=1;tableFollowing=True
                elif isinstance(nxt,KeepTogether):bucket.extend(nxt._content);k+=1
                else:bucket.append(nxt);k+=1
                break
            if not tableFollowing:result.append(KeepTogether(bucket))
        else:result.append(f);k+=1
    return result

class Cover(Flowable):
    def __init__(self):Flowable.__init__(self);self.width=WIDTH;self.height=H-TOP-BOTTOM-1
    def draw(self):
        c=self.canv;c.setFillColor(INK);c.rect(-LEFT,-BOTTOM,W,H,fill=1,stroke=0)
        c.setFillColor(colors.HexColor('#c0d9cb'));c.setFont('Mono',12);c.drawString(0,660,'ECHOCASE / ENGINEERING SERIES')
        c.setFillColor(colors.white);c.setFont('BookBold',31);c.drawString(0,560,'企业级 .NET');c.drawString(0,510,'全栈软件工程')
        c.setFont('Mono',12);c.setFillColor(colors.HexColor('#bfd8ce'));c.drawString(1,465,'ENTERPRISE .NET FULL-STACK SOFTWARE ENGINEERING')
        c.setFont('Book',13);c.drawString(0,408,'从真实实现理解架构、数据一致性与 React 状态')
        if CONF['id']=='template-first':
            c.setFillColor(INK);c.rect(-1,365,WIDTH+2,80,fill=1,stroke=0)
            c.setFillColor(colors.HexColor('#e1ebe5'));c.setFont('Book',15)
            c.drawString(0,419,'官方 Clean Architecture 模板')
            c.drawString(0,390,'数据一致性与 React 状态管理')
        c.setStrokeColor(colors.HexColor('#567b73'));c.line(0,358,WIDTH,358)
        for i,(head,body) in enumerate([('业务意图','领域边界 / 用例 / HTTP 合同'),('持久事实','EF 跟踪 / MVCC / 并发与幂等'),('交互承诺','确认缓存 / 草稿代次 / 冲突决策')]):
            yy=314-i*70;c.setFont('BookBold',12);c.setFillColor(colors.HexColor('#d6bd82'));c.drawString(0,yy,head)
            c.setFont('Book',11);c.setFillColor(colors.HexColor('#e1ebe5'));c.drawString(85,yy,body)
        c.setFont('Book',9);c.setFillColor(colors.HexColor('#bfd8ce'));c.drawString(0,66,CONF['edition'])
        if CONF['id']=='template-first':
            c.setFont('Mono',8.6);c.drawString(0,43,'SOURCE '+CONF['sourceCommit']);c.drawString(0,22,'PUBLISHED '+CONF['publicationDate']+' / TEMPLATE 10.8.0')
        else:c.drawString(0,32,'基于可审阅的 EchoCase 应用源码 · 中文技术教材')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--manifest');parser.add_argument('--output');args=parser.parse_args()
    protected_history()
    out=output_path(CONF,args.output);out.parent.mkdir(parents=True,exist_ok=True);BUILD.mkdir(exist_ok=True,parents=True)
    story=[Cover(),PageBreak(),Paragraph('目录',ST['h1'])]
    toc=TableOfContents();toc.levelStyles=[ParagraphStyle('toc0',fontName='BookBold',fontSize=10.7,leading=18.5,spaceBefore=8,leftIndent=0,rightIndent=26,wordWrap='CJK'),ParagraphStyle('toc1',fontName='Book',fontSize=8.8,leading=14.5,leftIndent=16,rightIndent=26,textColor=MUTED,wordWrap='CJK')]
    story.extend([toc])
    for i,file in enumerate(CONF['chapters']):story.extend(chapter(CHAPTER_ROOT/file,i))
    doc=Book(out);doc.multiBuild(story)
    reader=PdfReader(out)
    stats=dict(COUNTS,pages=len(reader.pages),chapterCount=len(CHAPTERS),figureCount=len(FIGURES),chapters=CHAPTERS,sourceSelections=SOURCE,figures=FIGURES,pdfSha256=hashlib.sha256(out.read_bytes()).hexdigest(),sourceCommit=CONF['sourceCommit'])
    (BUILD/'publication-stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2),encoding='utf-8')
    protected_history()
    print(json.dumps({k:v for k,v in stats.items() if k not in ['chapters','sourceSelections','figures']},ensure_ascii=False))

if __name__=='__main__':main()
