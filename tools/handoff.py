"""Seal the already visually reviewed PDFs and copy user-facing outputs with byte checks."""
import argparse,hashlib,json,shutil
from pathlib import Path
from pypdf import PdfReader
root=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();args.output.mkdir(parents=True,exist_ok=True)
items=[]
for name in ['Enterprise-Full-Stack-Engineering.pdf','EchoCase-Acceptance-Report.pdf']:
    p=root/'manual/dist'/name;data=p.read_bytes();pages=len(PdfReader(p).pages);dest=args.output/name;shutil.copy2(p,dest);assert dest.read_bytes()==data
    items.append({'path':'manual/dist/'+name,'pages':pages,'sha256':hashlib.sha256(data).hexdigest(),'reviewed_pages':list(range(1,pages+1)),'review_method':'Every page rendered at 1.1x and inspected on six-page contact sheets; selected diagrams/code/changed answers additionally inspected as complete page PNGs','blocking_visual_findings':[]})
record={'date_local':'2026-11-11','timezone':'Pacific/Auckland','reviewer':'same implementation agent; no external independent reviewer','artifacts':items,'fixed_findings':['Tiny diagram labels: simplified ER and compacted flow layout','Unbalanced chapter heading line breaks','Screenshot detail too small: captured actual DOM region screenshots','Code fragments: at least five orphan/widow lines','Performance diagram corrected to actual Bitmap Heap Scan plus Sort','Missing explicit answer labels corrected and tested'],'accepted_cosmetic_exceptions':[{'pages':[14,23,29,32,35,46,50,53,56,62,65,68],'reason':'Chapter-ending space with exercises kept together and the next chapter starting on a new page; no blank pages inserted'}],'publication_status':'PARTIAL: 97-page review edition, original 300–400-page editorial scope not completed'}
(root/'evidence/qa/visual-review.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
(args.output/'delivery-summary.json').write_text(json.dumps({'artifacts':items,'application_url':'http://127.0.0.1:6080','branch':'codex/enterprise-masterclass-20261111','overall_status':'PARTIAL','reason':'Textbook depth/scale target and production/cloud validations remain incomplete'},ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps([{'pages':i['pages'],'sha256':i['sha256']} for i in items]))
