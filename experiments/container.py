"""Build + isolated container reconstruction; keeps only the final local app for review."""
import http.cookiejar,json,subprocess,time,urllib.request,urllib.error,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'evidence'/'container';OUT.mkdir(parents=True,exist_ok=True)
def run(*args,check=True):return subprocess.run(['podman',*args],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',errors='replace',check=check)
with (OUT/'build.txt').open('w',encoding='utf-8') as log:
    build=subprocess.run(['podman','build','--memory','1500m','-t','localhost/echocase:lab','.'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
assert build.returncode==0,'Container build failed; see build.txt'
if run('network','inspect','echocase-lab',check=False).returncode:run('network','create','echocase-lab')
# A separate PostgreSQL instance proves reconstruction without relying on the dev schema.
if run('container','exists','echocase-container-db',check=False).returncode:
    run('run','-d','--name','echocase-container-db','--network','echocase-lab','--memory','384m','--cpus','1','-e','POSTGRES_USER=echocase','-e','POSTGRES_PASSWORD=echocase-local-only','-e','POSTGRES_DB=echocase','-v','echocase-container-pgdata:/var/lib/postgresql/data','docker.io/library/postgres:17.7-alpine')
else:run('start','echocase-container-db')
for _ in range(60):
    if run('exec','echocase-container-db','pg_isready','-U','echocase',check=False).returncode==0:break
    time.sleep(.5)
else:raise RuntimeError('Container database readiness timeout')
run('rm','-f','echocase-app',check=False)
env='ConnectionStrings__EchoCase=Host=echocase-container-db;Database=echocase;Username=echocase;Password=echocase-local-only'
migrate=run('run','--rm','--network','echocase-lab','-e',env,'localhost/echocase:lab','--migrate')
(OUT/'migrate.txt').write_text(migrate.stdout+migrate.stderr,encoding='utf-8')
def start():return run('run','-d','--name','echocase-app','--network','echocase-lab','--memory','384m','--cpus','1','-p','127.0.0.1:6080:8080','-e',env,'-e','ASPNETCORE_ENVIRONMENT=Development','-v','echocase-keys:/home/app/.aspnet/DataProtection-Keys','localhost/echocase:lab').stdout.strip()
def ready():
    for _ in range(60):
        try:
            if urllib.request.urlopen('http://127.0.0.1:6080/health/ready',timeout=5).status==200:return
        except (urllib.error.URLError,TimeoutError,OSError):pass
        time.sleep(.5)
    raise RuntimeError('Container readiness timeout')
first=start();ready();jar=http.cookiejar.CookieJar();client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
def call(path,method='GET',body=None,headers=None):
    req=urllib.request.Request('http://127.0.0.1:6080'+path,data=json.dumps(body).encode() if body is not None else None,method=method,headers={'Content-Type':'application/json',**(headers or {})})
    with client.open(req,timeout=15) as r:return r.status,r.read()
html=call('/')[1].decode();assert 'EchoCase' in html and '/assets/' in html
token=json.loads(call('/api/auth/csrf')[1])['token'];headers={'X-CSRF-TOKEN':token}
body={'email':'container-'+uuid.uuid4().hex+'@example.test','password':'StrongLabPassword42'}
assert call('/api/auth/register','POST',body,headers)[0]==200
assert call('/api/auth/login','POST',body,headers)[0]==200
token=json.loads(call('/api/auth/csrf')[1])['token'];headers={'X-CSRF-TOKEN':token,'Idempotency-Key':str(uuid.uuid4())}
session=json.loads(call('/api/investigations','POST',{'caseId':'harbor-01'},headers)[1]);run('rm','-f','echocase-app');second=start();ready()
status,data=call('/api/investigations/'+session['id']);assert status==200 and json.loads(data)['id']==session['id']
inspect=json.loads(run('inspect','echocase-app').stdout)[0];image=json.loads(run('image','inspect','localhost/echocase:lab').stdout)[0]
result={'kind':'REAL_OCI_BUILD_AND_CONTAINER_RECONSTRUCTION','image_id':image['Id'],'first_container':first,'second_container':second,'user':inspect['Config']['User'],'rootless_user':inspect['Config']['User'] not in ('','0','root'),'http_ready':200,'static_frontend_served':True,'database_session_survived':True,'cookie_survived_reconstruction':True,'url':'http://127.0.0.1:6080','scope':'single local container; HTTP loopback lab; paid Azure NOT_RUN'}
assert result['rootless_user']
(OUT/'results.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
