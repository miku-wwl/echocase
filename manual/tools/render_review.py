"""Render every page and make numbered contact sheets for visual review."""
from pathlib import Path
import argparse,hashlib,json,subprocess
from PIL import Image,ImageOps,ImageDraw,ImageFont
from pypdf import PdfReader
from editions import load,output_path,protected_history

M=Path(__file__).resolve().parents[1]
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--manifest');parser.add_argument('--output');args=parser.parse_args()
    config=load(args.manifest);build=M/config['buildDirectory'];pdf=output_path(config,args.output)
    protected_history()
    sha=hashlib.sha256(pdf.read_bytes()).hexdigest();out=build/('render-'+sha[:12]);pages=out/'pages';pages.mkdir(parents=True,exist_ok=True)
    subprocess.run(['pdftoppm','-r','110','-png',str(pdf),str(pages/'page')],check=True)
    images=sorted(pages.glob('page-*.png'));reader=PdfReader(pdf)
    if len(images)!=len(reader.pages):raise RuntimeError('Incomplete rendering')
    font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',20)
    sheets=[]
    for start in range(0,len(images),6):
        sheet=Image.new('RGB',(1860,1820),'#dce2df');d=ImageDraw.Draw(sheet)
        for j,path in enumerate(images[start:start+6]):
            x=(j%3)*620+10;y=(j//3)*910+38
            thumb=ImageOps.contain(Image.open(path).convert('RGB'),(600,856))
            sheet.paste(thumb,(x,y));d.text((x,y-29),f'PAGE {start+j+1:03d}',font=font,fill='#173c44')
        target=out/f'contact-{start+1:03d}-{min(start+6,len(images)):03d}.png';sheet.save(target);sheets.append(str(target))
    report=dict(pdfSha256=sha,pages=len(images),renderDirectory=str(out),contactSheets=sheets)
    (build/'render-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
