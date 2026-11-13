"""Structural, source and page-geometry QA. Human visual review remains necessary."""
from pathlib import Path
from collections import Counter
import argparse,json,re,hashlib,sys,subprocess,xml.etree.ElementTree as ET
import pdfplumber
from pypdf import PdfReader
from source_excerpts import extract
from editions import load,output_path,protected_history,specifications
from runtime_observations import load as observations_from_git

M=Path(__file__).resolve().parents[1];ROOT=M.parent

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--manifest');parser.add_argument('--output');args=parser.parse_args()
    config=load(args.manifest);build=M/config['buildDirectory'];chapters=M/config['chapterRoot'];specs=specifications(config)
    stats=json.loads((build/'publication-stats.json').read_text(encoding='utf-8'))
    path=output_path(config,args.output);reader=PdfReader(path)
    historical=protected_history()
    errors=[];warnings=[]
    def require(v,m):
        if not v:errors.append(m)
    require(hashlib.sha256(path.read_bytes()).hexdigest()==stats['pdfSha256'],'PDF differs from current build statistics')
    reference=(M/Path(config['manifestPath']).parent/'reference') if config['id']!='historical' else M/'reference'
    provenance=json.loads((reference/'asset-provenance.json').read_text(encoding='utf-8'))
    for asset in provenance['screenshots']:
        require(hashlib.sha256((M/asset['file']).read_bytes()).hexdigest()==asset['sha256'],
                'Original UI pixels changed: '+asset['file'])
    require(set(config['chapters'])=={x.name for x in chapters.glob('*.md')},'Orphan chapter or missing source')
    for e in stats['sourceSelections']:
        now=extract(e['id'],config['sourceCommit'],specs,config['verifyWorkingTree'])
        require(all(now[k]==e[k] for k in ['sha256','start','end','commit','blob','path']),'Source drift: '+e['id'])
        require(now['commit']==config['sourceCommit'] or now['label']!='应用源码','Unlabelled historical comparison: '+e['id'])
    for name in config['chapters']:
        text=(chapters/name).read_text(encoding='utf-8')
        require(not re.search(r'```(?:powershell|bash|shell|sh|json)\b',text),'Procedural/raw JSON block in '+name)
        require('evidence/' not in text and 'docs/experiments' not in text,'Raw historical path in '+name)
        require(not re.search('[\u2011\u2012\u2013\u2014]',text),'Non-ASCII dash in '+name)
    outline=[x for x in reader.outline if not isinstance(x,list)]
    require(len(outline)==len(config['chapters']),'Top-level bookmark count')
    destinations={page.indirect_reference.idnum for page in reader.pages}
    links=Counter();texts=[];pageInfo=[];geometries=[]
    for number,page in enumerate(reader.pages,1):
        text=page.extract_text() or '';texts.append(text)
        require('{{code ' not in text and '{{figure ' not in text,'Unresolved macro on page '+str(number))
        require('\ufffd' not in text,'Replacement character on page '+str(number))
        if number>1:require(f'{number:03d}' in text,'Missing page number '+str(number))
        for a in page.get('/Annots',[]):
            obj=a.get_object()
            if obj.get('/Subtype')!='/Link':continue
            action=obj.get('/A')
            if action and action.get('/URI'):links['external']+=1
            else:
                links['internal']+=1;dest=obj.get('/Dest') or (action.get('/D') if action else None)
                if isinstance(dest,list):require(getattr(dest[0],'idnum',None) in destinations,'Broken internal destination on page '+str(number))
                elif isinstance(dest,str):require(dest in reader.named_destinations,'Missing named destination '+dest)
        pageInfo.append(dict(page=number,characters=len(text),images=len(page.images)))
    require(links['external']>=len(stats['sourceSelections']),'Missing source hyperlinks')
    require(links['internal']>=len(config['chapters']),'Missing linked contents')
    combined='\n'.join(texts)
    require('🔎' in combined,'Non-BMP source glyph or ToUnicode mapping was lost')
    def inspect_sections(entries):
        for entry in entries:
            if isinstance(entry,list):inspect_sections(entry)
            elif entry not in outline:
                page=reader.get_destination_page_number(entry)
                normalized=re.sub(r'\s+','',texts[page])
                require(not normalized.endswith(re.sub(r'\s+','',entry.title)),
                        'Stranded section heading on page '+str(page+1)+': '+entry.title)
    inspect_sections(reader.outline)
    for fig in stats['figures']:
        require(('图 '+fig['number']) in combined,'Missing figure caption '+fig['id'])
        if fig['type']=='svg':
            tree=ET.parse(M/fig['file']).getroot();labels=[''.join(x.itertext()) for x in tree.iter() if x.tag.endswith('}text')]
            # Every vector label must have reached PDF text, not just its background box.
            for label in labels:require(label.replace(' ','') in combined.replace(' ',''),'Missing vector text: '+fig['id']+' / '+label)
    with pdfplumber.open(path) as pdf:
        for i,page in enumerate(pdf.pages,1):
            chars=page.chars
            if i>1:
                outside=[x for x in chars if x['x0']<43 or x['top']<14 or x['bottom']>826 or
                         (x['x1']>553 and not (x['text'] in '。，、；：！？）》」』' and x['x1']<556))]
                if outside:geometries.append(dict(page=i,count=len(outside),sample=''.join(x['text'] for x in outside)[:100]))
            require(bool(chars) or i==1,'Blank page '+str(i))
    require(not geometries,'Text outside page safety area: '+str(geometries[:8]))
    # Exact runtime values used in the narrative and charts.
    observations=observations_from_git()
    require(observations['tracking']['originalVersion']==4 and observations['tracking']['savedVersion']==5,'Tracking values')
    require(sorted(observations['race']['results'])==[200,412],'Race outcomes')
    require(observations['race']['survivingReceipts']==observations['race']['survivingRevisionAudit']==1,'Atomic race results')
    require(observations['precision']['responseTicks']==observations['precision']['readTicks']==639299753895425590,'Precision example')
    if config['id']=='template-first':
        require(config['sourceCommit']=='9f68721e18f15ae603e6502fa46b8fa78f9df55c','Wrong engineering baseline')
        audit=json.loads((reference/'historical-57-excerpt-audit.json').read_text(encoding='utf-8'))
        require(len(audit)==57,'Incomplete historical excerpt audit')
        decisions=json.loads((reference/'figure-decisions.json').read_text(encoding='utf-8'))
        require(sum('historicalFile' in x for x in decisions)==44,'Incomplete historical figure audit')
        inventory=json.loads((reference/'engineering-source-inventory.json').read_text(encoding='utf-8'))
        for entry in inventory['files']:
            pinned=subprocess.check_output(['git','show',config['sourceCommit']+':'+entry['path']],cwd=ROOT)
            require(hashlib.sha256(pinned).hexdigest()==entry['sha256'],'Inventory differs from fixed Git object: '+entry['path'])
            require((ROOT/entry['path']).read_bytes().replace(b'\r\n',b'\n')==pinned.replace(b'\r\n',b'\n'),'Application changed: '+entry['path'])
        require(subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()=='main','Publication branch is not main')
    report=dict(status='PASS' if not errors else 'FAIL',edition=config['id'],pages=len(reader.pages),han=stats['han'],sourceSelections=len(stats['sourceSelections']),sourceLines=stats['sourceLines'],figureCount=len(stats['figures']),uniqueFigures=len({x['id'] for x in stats['figures']}),vectorFigures=sum(x['type']=='svg' for x in stats['figures']),uiFigures=sum(x['type']=='ui' for x in stats['figures']),topLevelBookmarks=len(outline),links=dict(links),errors=errors,warnings=warnings,pageGeometry=geometries,pagesDetail=pageInfo,pdfSha256=stats['pdfSha256'],historicalPdfSha256=historical)
    (build/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (build/'book-text.txt').write_text(combined,encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='pagesDetail'},ensure_ascii=False))
    if errors:sys.exit(1)

if __name__=='__main__':main()
