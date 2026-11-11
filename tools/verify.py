"""Independent artifact/architecture gate; exit 1 for any blocking problem. No silent skips."""
import argparse,hashlib,json,re,sys,xml.etree.ElementTree as ET
from pathlib import Path

def verify(root):
    failures=[]
    def require(condition,message):
        if not condition:failures.append(message)
    def load(p):return json.loads((root/p).read_text(encoding='utf-8-sig'))
    try:
        for layer,allowed in [('Domain',set()),('Application',{'EchoCase.Domain'})]:
            p=root/f'src/EchoCase.{layer}/EchoCase.{layer}.csproj';xml=ET.parse(p)
            refs={Path(n.attrib['Include'].replace('\\','/')).stem for n in xml.iter('ProjectReference')}
            require(refs<=allowed,f'{layer}: outward project reference {refs-allowed}')
            if layer=='Domain':require(not list(xml.iter('PackageReference')),'Domain: framework package reference')
        manifest=load('evidence/manifest.json');require(len(manifest['experiments'])>=20,'Fewer than 20 experiments')
        for e in manifest['experiments']:
            require(e['status'] in {'VERIFIED','PARTIAL','BLOCKED','NOT_RUN'},e['id']+': invalid status')
            if e['status']=='VERIFIED':require(bool(e['artifacts']),e['id']+': unsupported VERIFIED claim')
            for artifact in e['artifacts']:
                p=(root/artifact['path']).resolve();require(p.is_relative_to(root.resolve()),e['id']+': unsafe artifact path')
                require(p.is_file(),e['id']+': missing '+artifact['path'])
                if p.is_file():
                    raw=p.read_bytes();raw=raw.replace(b'\r\n',b'\n') if p.suffix in ('.json','.trx','.txt','.md') else raw
                    require(hashlib.sha256(raw).hexdigest()==artifact['sha256'],e['id']+': digest mismatch '+artifact['path'])
        trx=ET.parse(root/'evidence/backend/backend.trx');ns={'t':'http://microsoft.com/schemas/VisualStudio/TeamTest/2010'};counts=trx.find('.//t:Counters',ns).attrib
        require(int(counts['total'])>=38 and counts['total']==counts['passed'] and int(counts['failed'])==0,'Backend tests not all passed')
        browser=load('evidence/browser/results.json')['stats'];require(browser['expected']>=4 and browser['unexpected']==0 and browser['skipped']==0,'Browser tests not all passed')
        db=load('evidence/database/results.json');require(db['lost_update']['versioned_rows_affected']==[1,0],'Concurrency evidence inconsistent')
        require(db['write_skew']['SERIALIZABLE']['second_writer']=='40001','Serializable evidence missing')
        for label,data in [('before',db['query_optimization']['before']),('after',db['query_optimization']['after'])]:require(data['rows']==20 and len(data['samples_ms'])==21,'SQL sample/result mismatch '+label)
        rel=load('evidence/reliability/results.json');require(rel['outage']['live']==200 and rel['outage']['ready']==503 and rel['outage']['business']==503,'Outage state mismatch')
        require(rel['saved_session_survived'] and rel['traceparent_preserved'],'Recovery/trace evidence missing')
        require(0<rel['latency']['p95_ms']<200,'Local sequential read p95 exceeds 200ms teaching gate')
        container=load('evidence/container/results.json');require(container['rootless_user'] and container['database_session_survived'] and container['cookie_survived_reconstruction'],'Container reconstruction incomplete')
        if (root/'evidence/ci/results.json').exists():
            ci=load('evidence/ci/results.json')
            if ci['status']=='VERIFIED':require(ci['rejected']['conclusion']=='failure' and ci['repaired']['conclusion']=='success' and ci['failure_matched_missing_manifest'],'CI failure/recovery evidence incomplete')
        require(load('evidence/backup/results.json')['row_count']==3,'Backup restore evidence missing')
        chapters=sorted((root/'manual/chapters').glob('*.md'));require(len(chapters)>=19,'Curriculum chapters missing')
        text='\n'.join(p.read_text(encoding='utf-8') for p in chapters);anchors=set(re.findall(r'\{#([^}]+)\}',text));claims=load('manual/claims.json')
        for anchor in re.findall(r'\]\(#([^\)]+)\)',text):require(anchor in anchors,'Broken internal anchor '+anchor)
        for image in re.findall(r'!\[[^\]]*\]\(([^\)]+)\)',text):require((root/image).is_file(),'Missing figure '+image)
        for token in re.findall(r'\{\{claim:([^}]+)\}\}',text):require(token in claims,'Unsupported measurement '+token)
        for key,claim in claims.items():
            data=load(claim['source'])
            for segment in claim['pointer'].split('.'):data=data[segment]
            require(data is not None,'Missing measurement '+key)
        for file,start,end in re.findall(r'\{\{code:([^:}]+):(\d+)-(\d+)\}\}',text):
            p=root/file;require(p.is_file(),'Missing source excerpt '+file)
            if p.is_file():require(1<=int(start)<=int(end)<=len(p.read_text(encoding='utf-8-sig').splitlines()),'Invalid source excerpt '+file)
        for n in range(1,19):
            chapter=next((p.read_text(encoding='utf-8') for p in chapters if p.name.startswith(f'{n:02}-')),None)
            require(chapter is not None and all(f'{n}-{letter}' in chapter for letter in 'ABC'),'Exercise/answer set incomplete '+str(n))
            if chapter is not None:
                questions=list(re.finditer(r'\*\*'+str(n)+r'-([ABC])[^*]*\*\*',chapter))
                require(len(questions)==3,'Exercise/answer count mismatch '+str(n))
                for index,q in enumerate(questions):
                    section=chapter[q.end():questions[index+1].start() if index+1<len(questions) else len(chapter)]
                    answer=re.search(r'参考答案[：:]\s*(.+)',section,re.S)
                    require(answer is not None and len(answer.group(1).strip())>=20,'Exercise/answer missing '+str(n)+'-'+q.group(1))
        for audit in ['evidence/frontend-audit.json','evidence/publication-audit.json']:require(load(audit)['metadata']['vulnerabilities']['total']==0,'Known npm vulnerability '+audit)
    except Exception as e:failures.append(type(e).__name__+': '+str(e))
    return failures
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);args=ap.parse_args();errors=verify(args.root)
    print(json.dumps({'status':'FAIL' if errors else 'PASS','failures':errors},ensure_ascii=False,indent=2));raise SystemExit(1 if errors else 0)
