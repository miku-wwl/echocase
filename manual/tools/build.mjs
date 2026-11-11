import {readFile,writeFile,mkdir,readdir} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {chromium} from '../../frontend/node_modules/playwright/index.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..'),manual=path.join(root,'manual'),build=path.join(manual,'build');
await mkdir(build,{recursive:true});await mkdir(path.join(manual,'dist'),{recursive:true});
const report=process.argv.includes('--report');
let files=report?[path.join(root,'docs/ACCEPTANCE-REPORT.md')]:(await readdir(path.join(manual,'chapters'))).filter(f=>f.endsWith('.md')).sort().map(f=>path.join(manual,'chapters',f));
if(!files.length)throw Error('No chapters');
let markdown=(await Promise.all(files.map(f=>readFile(f,'utf8')))).join('\n\n');
const claims=JSON.parse(await readFile(path.join(manual,'claims.json'),'utf8'));
for(const [name,claim] of Object.entries(claims)){
  let data=JSON.parse(await readFile(path.join(root,claim.source),'utf8'));
  for(const key of claim.pointer.split('.'))data=data[key];
  if(data===undefined||data===null)throw Error('Missing claim '+name);
  const formatted=typeof data==='number'&&claim.decimals!==undefined?data.toFixed(claim.decimals):String(data);
  markdown=markdown.replaceAll('{{claim:'+name+'}}',formatted);
}
// Embed exact, bounded excerpts. Line numbers in the caption refer to the current checkout.
markdown=await replaceAsync(markdown,/\{\{code:([^:}]+):(\d+)-(\d+)\}\}/g,async(_m,file,start,end)=>{
  const p=path.resolve(root,file);if(!p.startsWith(root+path.sep))throw Error('Unsafe source path');
  const lines=(await readFile(p,'utf8')).split(/\r?\n/);start=Number(start);end=Number(end);if(start<1||end>lines.length||end<start||end-start>50)throw Error('Invalid excerpt '+file);
  const lang=file.endsWith('.cs')?'csharp':file.endsWith('.tsx')||file.endsWith('.ts')?'typescript':file.endsWith('.py')?'python':'';
  const fence=String.fromCharCode(96).repeat(3);
  return '\n\n'+fence+lang+'\n'+lines.slice(start-1,end).join('\n')+'\n'+fence+'\n\n*源码：'+file+'，第 '+start+'-'+end+' 行。*\n';
});
if(/\{\{/.test(markdown))throw Error('Unresolved content token');
const input=path.join(build,report?'report.md':'book.md');await writeFile(input,markdown);
const body=execFileSync('pandoc',[input,'-f','markdown+east_asian_line_breaks','-t','html5','--wrap=none','--syntax-highlighting=pygments'],{encoding:'utf8',maxBuffer:20_000_000});
const css=await readFile(path.join(manual,'assets/book.css'),'utf8');
const cover=report?'EchoCase<br>工程验收报告':'Enterprise Full-Stack<br>Engineering<br><em>with .NET & React</em>';
const coverHtml=`<section class="cover"><div class="imprint">ECHOCASE / ENGINEERING MASTERCLASS</div><div class="cover-rule"></div><span class="cover-kicker">${report?'INDEPENDENT ACCEPTANCE ARTIFACT':'从一条证据，到一个可靠的系统'}</span><h1>${cover}</h1><p class="cover-subtitle">Clean Architecture · Domain-Driven Design<br>Data Consistency · React · Security · Reliability</p><div class="cover-diagram"><span>DOMAIN</span><b>→</b><span>APPLICATION</span><b>→</b><span>EVIDENCE</span></div><div class="cover-bottom"><strong>${report?'设计、实测、限制与剩余动作':'基于真实应用与可复现实验的中文工程教材'}</strong><span>2026.11 / REVIEW EDITION<br>miku-wwl/echocase</span></div></section>`;
const html=`<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>${report?'EchoCase 工程验收报告':'Enterprise Full-Stack Engineering with .NET & React'}</title><base href="${new URL('file:///'+root.replaceAll('\\','/')+'/').href}"><style>${css}</style></head><body>${coverHtml}<nav class="toc"><span class="eyebrow">CONTENTS</span><h1>目录</h1><div id="toc-list"></div></nav><main>${body}</main></body></html>`;
const htmlPath=path.join(build,report?'report.html':'book.html');await writeFile(htmlPath,html);
const browser=await chromium.launch(process.env.CI?{headless:true}:{channel:'msedge',headless:true});
try{
 const page=await browser.newPage();await page.goto(new URL('file:///'+htmlPath.replaceAll('\\','/')).href);
 await page.addScriptTag({path:path.join(manual,'node_modules/mermaid/dist/mermaid.min.js')});
 await page.evaluate(async()=>{
  for(const block of document.querySelectorAll('pre.mermaid,pre:has(code.mermaid)')){const el=document.createElement('div');el.className='mermaid';el.textContent=block.textContent;block.replaceWith(el)}
  window.mermaid.initialize({startOnLoad:false,securityLevel:'strict',theme:'base',themeVariables:{fontFamily:'Microsoft YaHei, sans-serif',fontSize:'16px',primaryColor:'#edf3f1',primaryTextColor:'#21483f',primaryBorderColor:'#89a99c',lineColor:'#66877b',secondaryColor:'#f4eedf',tertiaryColor:'#f6f8f4'},flowchart:{htmlLabels:false,useMaxWidth:true,rankSpacing:22,nodeSpacing:24},sequence:{useMaxWidth:true,wrap:true}});
  await window.mermaid.run({querySelector:'.mermaid'});await document.fonts.ready;
  for(const img of document.images){if(!img.complete)await new Promise((res,rej)=>{img.onload=res;img.onerror=rej});if(!img.naturalWidth)throw Error('Broken image '+img.src)}
  for(const h of [...document.querySelectorAll('main h2')].filter(h=>h.textContent==='练习与参考答案')){const group=document.createElement('section');group.className='chapter-exercises';h.before(group);group.append(h);while(group.nextElementSibling&&group.nextElementSibling.tagName!=='H1'&&group.nextElementSibling.tagName!=='H2')group.append(group.nextElementSibling)}
  const headings=[...document.querySelectorAll('main h1,main h2')];
  for(let i=0;i<headings.length;i++){const h=headings[i];if(!h.id)h.id='h-'+i;const a=document.createElement('a');a.href='#'+h.id;a.className=h.tagName==='H1'?'toc-entry chapter-entry':'toc-entry';const title=document.createElement('span');title.textContent=h.textContent;const number=document.createElement('b');number.textContent='000';number.dataset.heading=h.id;a.append(title,number);document.querySelector('#toc-list').append(a)}
 });
 await page.emulateMedia({media:'print'});
 const footer='<div style="font-family:Microsoft YaHei,sans-serif;font-size:8px;color:#7e8e86;width:100%;padding:0 17mm;display:flex;justify-content:space-between"><span>EchoCase · Enterprise Full-Stack Engineering</span><span class="pageNumber"></span></div>';
 const print=async p=>page.pdf({path:p,format:'A4',printBackground:true,preferCSSPageSize:true,displayHeaderFooter:true,headerTemplate:'<div></div>',footerTemplate:footer,outline:true,tagged:true,margin:{top:'17mm',right:'17mm',bottom:'19mm',left:'19mm'}});
 const first=path.join(build,report?'report-pass1.pdf':'book-pass1.pdf');await print(first);
 const py=process.env.ECHOCASE_PYTHON??path.join(root,'work/venv',process.platform==='win32'?'Scripts/python.exe':'bin/python');
 const headings=await page.evaluate(()=>[...document.querySelectorAll('main h1,main h2')].map(h=>({id:h.id,text:h.textContent})));
 await writeFile(path.join(build,'headings.json'),JSON.stringify(headings));
 execFileSync(py,[path.join(manual,'tools/pdfqa.py'),'toc',first,path.join(build,'headings.json'),path.join(build,'toc-pages.json')],{stdio:'inherit'});
 const numbers=JSON.parse(await readFile(path.join(build,'toc-pages.json'),'utf8'));
 await page.evaluate(numbers=>{for(const el of document.querySelectorAll('[data-heading]')){const n=numbers[el.dataset.heading];if(!n)throw Error('Unmapped TOC '+el.dataset.heading);el.textContent=n}},numbers);
 const final=path.join(manual,'dist',report?'EchoCase-Acceptance-Report.pdf':'Enterprise-Full-Stack-Engineering.pdf');await print(final);
 execFileSync(py,[path.join(manual,'tools/pdfqa.py'),'verify-toc',first,final,path.join(build,'headings.json'),path.join(build,'toc-pages.json')],{stdio:'inherit'});
 const content=await page.content();await writeFile(htmlPath,content);
 console.log(final);
}finally{await browser.close()}
async function replaceAsync(s,re,fn){const all=[...s.matchAll(re)];const values=await Promise.all(all.map(m=>fn(...m)));let i=0;return s.replace(re,()=>values[i++])}
