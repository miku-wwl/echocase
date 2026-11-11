"""Run the production gate against controlled corruptions in temporary copies."""
import importlib.util,json,shutil,subprocess,sys,tempfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
cases=[('missing_artifact','missing'),('tampered_artifact','tamper'),('outward_dependency','boundary'),('unsupported_status','status'),('performance_regression','performance'),('missing_answer','answer'),('unsupported_measurement','claim')]
observed=[]
for name,kind in cases:
    with tempfile.TemporaryDirectory(prefix='echocase_gate_') as tmp:
        target=Path(tmp)
        for folder in ['src','frontend','manual','evidence']:
            shutil.copytree(root/folder,target/folder,ignore=shutil.ignore_patterns('node_modules','build','dist','bin','obj','test-results','playwright-report'))
        normal=subprocess.run([sys.executable,str(root/'tools/verify.py'),'--root',str(target)],capture_output=True,text=True,encoding='utf-8')
        assert normal.returncode==0,'Unmodified fixture failed: '+normal.stdout
        if kind=='missing':(target/'evidence/backup/results.json').unlink()
        elif kind=='tamper':
            p=target/'evidence/database/results.json';p.write_text(p.read_text(encoding='utf-8')+' ',encoding='utf-8')
        elif kind=='boundary':
            p=target/'src/EchoCase.Domain/EchoCase.Domain.csproj';p.write_text('<Project><ItemGroup><ProjectReference Include="../EchoCase.Infrastructure/EchoCase.Infrastructure.csproj"/></ItemGroup></Project>',encoding='utf-8')
        elif kind=='status':
            p=target/'evidence/manifest.json';data=json.loads(p.read_text(encoding='utf-8'));data['experiments'][0]['status']='LOOKS_GOOD';p.write_text(json.dumps(data),encoding='utf-8')
        elif kind=='performance':
            p=target/'evidence/reliability/results.json';data=json.loads(p.read_text(encoding='utf-8'));data['latency']['p95_ms']=9999;p.write_text(json.dumps(data),encoding='utf-8')
            # Refresh artifact hashes so this case tests the semantic performance gate.
            manifest=target/'evidence/manifest.json';m=json.loads(manifest.read_text(encoding='utf-8'));import hashlib
            for e in m['experiments']:
                for a in e['artifacts']:
                    if a['path']=='evidence/reliability/results.json':a['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
            manifest.write_text(json.dumps(m),encoding='utf-8')
        elif kind=='answer':
            p=target/'manual/chapters/01-requirements.md';p.write_text(p.read_text(encoding='utf-8').replace('1-C','removed'),encoding='utf-8')
        elif kind=='claim':
            p=target/'manual/chapters/01-requirements.md';p.write_text(p.read_text(encoding='utf-8')+'\n{{claim:invented_result}}',encoding='utf-8')
        run=subprocess.run([sys.executable,str(root/'tools/verify.py'),'--root',str(target)],capture_output=True,text=True,encoding='utf-8')
        assert run.returncode!=0,name+' was incorrectly accepted'
        expected={'missing':'missing evidence/backup','tamper':'digest mismatch','boundary':'outward project reference','status':'invalid status','performance':'p95 exceeds','answer':'Exercise/answer set incomplete','claim':'Unsupported measurement'}[kind]
        assert any(expected in message for message in json.loads(run.stdout)['failures']),name+' failed for an unrelated reason'
        observed.append({'case':name,'exit_code':run.returncode,'diagnostics':json.loads(run.stdout)['failures']})
baseline=subprocess.run([sys.executable,str(root/'tools/verify.py')],capture_output=True,text=True,encoding='utf-8');assert baseline.returncode==0,baseline.stdout
result={'baseline_exit_code':baseline.returncode,'corruptions_rejected':len(observed),'cases':observed};(root/'evidence/qa').mkdir(exist_ok=True);(root/'evidence/qa/gate-selftest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False,indent=2))
