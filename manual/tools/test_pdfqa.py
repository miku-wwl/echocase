import json,subprocess,sys,tempfile
from pathlib import Path
from reportlab.pdfgen import canvas
root=Path(__file__).resolve().parents[2];tool=root/'manual/tools/pdfqa.py';results=[]
with tempfile.TemporaryDirectory(prefix='echocase_pdfqa_') as tmp:
    p=Path(tmp)
    for kind in ['blank','overflow']:
        pdf=p/(kind+'.pdf');c=canvas.Canvas(str(pdf),pagesize=(595.3,841.9))
        if kind=='overflow':c.drawString(580,500,'THIS TEXT OVERFLOWS THE PAGE')
        c.showPage();c.save()
        run=subprocess.run([sys.executable,str(tool),'layout',str(pdf),str(p/'layout.json')],capture_output=True,text=True)
        assert run.returncode!=0,kind+' was incorrectly accepted';results.append({'case':kind,'exit_code':run.returncode})
    headings=p/'headings.json';headings.write_text(json.dumps([{'id':'missing','text':'Heading that does not exist'}]),encoding='utf-8')
    run=subprocess.run([sys.executable,str(tool),'toc',str(pdf),str(headings),str(p/'toc.json')],capture_output=True,text=True)
    assert run.returncode!=0;results.append({'case':'missing_outline_heading','exit_code':run.returncode})
(root/'evidence/qa').mkdir(parents=True,exist_ok=True)
(root/'evidence/qa/pdf-selftest.json').write_text(json.dumps({'corruptions_rejected':len(results),'cases':results},indent=2),encoding='utf-8');print(json.dumps(results))
