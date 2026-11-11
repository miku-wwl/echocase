"""PDF outline/TOC and layout checks. Every blocking finding raises/nonzero exits."""
import json, re, sys
from pathlib import Path
from pypdf import PdfReader

def norm(s): return re.sub(r'\s+','',s)
def outline(reader):
    items=[]
    def visit(seq):
        for item in seq:
            if isinstance(item,list):visit(item)
            else:items.append((norm(item.title),reader.get_destination_page_number(item)+1))
    visit(reader.outline);return items
def mapping(pdf,headings):
    reader=PdfReader(pdf);entries=outline(reader);last=-1;out={}
    for h in headings:
        match=next((i for i in range(last+1,len(entries)) if entries[i][0]==norm(h['text'])),None)
        if match is None:raise ValueError('Heading missing from PDF outline: '+h['text'])
        last=match;out[h['id']]=entries[match][1]
    return out
def layout(pdf,out):
    import pymupdf
    doc=pymupdf.open(pdf);issues=[];pages=[]
    for index,page in enumerate(doc):
        text=page.get_text();content=[];tiny=[]
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines',[]):
                for span in line['spans']:
                    if not span['text'].strip():continue
                    x0,y0,x1,y1=span['bbox'];content.append((x0,y0,x1,y1))
                    if x0<20 or x1>page.rect.width-20 or y0<0 or y1>page.rect.height:
                        issues.append({'page':index+1,'kind':'overflow','text':span['text'][:70],'bbox':list(span['bbox'])})
                    if span['size']<6.8 and y0<page.rect.height-40:tiny.append(span['text'][:50])
        if len(text.strip())<25:issues.append({'page':index+1,'kind':'blank_or_image_only'})
        if tiny:issues.append({'page':index+1,'kind':'tiny_text','samples':tiny[:6]})
        pages.append({'page':index+1,'characters':len(text),'bottom':round(max((x[3] for x in content if x[1]<page.rect.height-40),default=0),1)})
    result={'pages':len(doc),'issues':issues,'page_metrics':pages};Path(out).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps({'pages':len(doc),'issues':len(issues)}))
    if issues:raise SystemExit(1)
def render(pdf,out):
    import pymupdf
    from PIL import Image,ImageOps,ImageDraw
    doc=pymupdf.open(pdf);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    thumbs=[]
    for n,page in enumerate(doc):
        pix=page.get_pixmap(matrix=pymupdf.Matrix(1.1,1.1),alpha=False);target=out/f'page-{n+1:03}.png';pix.save(target)
        im=Image.open(target).convert('RGB');im.thumbnail((390,555))
        thumb=Image.new('RGB',(410,585),'#dce3da');thumb.paste(im,((410-im.width)//2,10));ImageDraw.Draw(thumb).text((15,565),f'Page {n+1}',fill='#23483b');thumbs.append(thumb)
    for offset in range(0,len(thumbs),6):
        sheet=Image.new('RGB',(1230,1170),'#dce3da')
        for j,im in enumerate(thumbs[offset:offset+6]):sheet.paste(im,((j%3)*410,(j//3)*585))
        sheet.save(out/f'sheet-{offset//6+1:02}.jpg',quality=90)
    print(f'Rendered {len(doc)} pages; {(len(doc)+5)//6} contact sheets')

def links(pdf,out):
    reader=PdfReader(pdf);page_ids={p.indirect_reference.idnum:n+1 for n,p in enumerate(reader.pages)};internal=external=0;issues=[]
    for n,page in enumerate(reader.pages):
        for ref in page.get('/Annots',[]):
            a=ref.get_object()
            if a.get('/Subtype')!='/Link':continue
            action=a.get('/A',{});dest=a.get('/Dest') or action.get('/D')
            if dest is not None:
                if isinstance(dest,list):valid=getattr(dest[0],'idnum',None) in page_ids
                else:valid=str(dest) in reader.named_destinations
                if not valid:issues.append({'page':n+1,'kind':'unresolved_internal_destination'})
                internal+=1
            elif action.get('/URI'):
                uri=str(action['/URI']);external+=1
                if not uri.startswith(('https://','http://','mailto:')):issues.append({'page':n+1,'kind':'nonportable_uri','uri':uri})
            else:issues.append({'page':n+1,'kind':'empty_link'})
    if internal==0:issues.append({'kind':'no_internal_navigation'})
    result={'pages':len(reader.pages),'internal_links':internal,'external_links':external,'issues':issues};Path(out).write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result));
    if issues:raise SystemExit(1)

if __name__=='__main__':
    mode,*args=sys.argv[1:]
    if mode=='toc':
        pdf,headings,out=args;data=mapping(pdf,json.loads(Path(headings).read_text(encoding='utf-8')));Path(out).write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8');print(f'TOC: {len(data)} headings mapped')
    elif mode=='verify-toc':
        first,final,headings,numbers=args;assert len(PdfReader(first).pages)==len(PdfReader(final).pages),'Pagination changed between passes';assert mapping(final,json.loads(Path(headings).read_text(encoding='utf-8')))==json.loads(Path(numbers).read_text(encoding='utf-8')),'TOC targets changed';print('TOC page numbers stable')
    elif mode=='layout':layout(*args)
    elif mode=='render':render(*args)
    elif mode=='links':links(*args)
    else:raise SystemExit('Unknown mode')
