"""Bounded outage of our own lab DB, then restore in finally. No other container is touched."""
import json, os, subprocess, time, urllib.request, urllib.error, http.cookiejar, statistics, uuid
from pathlib import Path
OUT=Path(__file__).resolve().parents[1]/'evidence'/'reliability';OUT.mkdir(parents=True,exist_ok=True)
base=os.environ.get('ECHOCASE_API','http://127.0.0.1:5080')
client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
def call(path,method='GET',body=None,headers=None):
    headers={'Content-Type':'application/json',**(headers or {})}
    req=urllib.request.Request(base+path,data=json.dumps(body).encode() if body is not None else (b'' if method!='GET' else None),headers=headers,method=method)
    try:
        with client.open(req,timeout=12) as r:return r.status,r.read(),dict(r.headers)
    except urllib.error.HTTPError as e:return e.code,e.read(),dict(e.headers)
token=json.loads(call('/api/auth/csrf')[1])['token'];auth={'X-CSRF-TOKEN':token}
credentials={'email':'reliability-'+uuid.uuid4().hex+'@example.test','password':'StrongLabPassword42'}
assert call('/api/auth/register','POST',credentials,auth)[0]==200
assert call('/api/auth/login','POST',credentials,auth)[0]==200
token=json.loads(call('/api/auth/csrf')[1])['token'];auth={'X-CSRF-TOKEN':token,'Idempotency-Key':str(uuid.uuid4())}
status,data,_=call('/api/investigations','POST',{'caseId':'harbor-01'},auth);assert status==200
session=json.loads(data);path='/api/investigations/'+session['id']
samples=[]
for n in range(105):
    start=time.perf_counter();status,_,headers=call(path,headers={'traceparent':'00-'+'1234567890abcdef'*2+'-'+'abcdef1234567890'+'-01'});elapsed=(time.perf_counter()-start)*1000
    assert status==200
    assert headers.get('X-Trace-Id')=='1234567890abcdef'*2
    if n>=5:samples.append(elapsed)
result={'kind':'REAL_HTTP_AND_INJECTED_DATABASE_OUTAGE','latency':{'samples':100,'warmups':5,'concurrency':1,'median_ms':statistics.median(samples),'p95_ms':sorted(samples)[94],'samples_ms':samples},'traceparent_preserved':True}
try:
    subprocess.run(['podman','stop','--time','3','echocase-postgres'],check=True,capture_output=True)
    tick=time.perf_counter();live=call('/health/live')[0];ready=call('/health/ready')[0];business=call(path)[0]
    result['outage']={'live':live,'ready':ready,'business':business,'observed_ms':(time.perf_counter()-tick)*1000}
    assert (live,ready,business)==(200,503,503)
finally:
    subprocess.run(['podman','start','echocase-postgres'],check=True,capture_output=True)
    started=time.perf_counter()
    for _ in range(30):
        if call('/health/ready')[0]==200:break
        time.sleep(.5)
    else:raise RuntimeError('DB did not recover')
    result['recovery_observed_ms']=(time.perf_counter()-started)*1000
status,data,_=call(path);assert status==200 and json.loads(data)['id']==session['id']
result['saved_session_survived']=True
(OUT/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='latency'},ensure_ascii=False));print('HTTP p95 %.3f ms'%result['latency']['p95_ms'])
