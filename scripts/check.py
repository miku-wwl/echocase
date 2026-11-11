"""Run a command and preserve its real output/exit status. No implicit success on failure."""
import datetime,json,subprocess,sys,time
from pathlib import Path
out=Path(sys.argv[1]);command=sys.argv[2:]
if not command:raise SystemExit('usage: python scripts/check.py evidence/path command args...')
out.parent.mkdir(parents=True,exist_ok=True);started=datetime.datetime.now(datetime.timezone.utc).isoformat();tick=time.perf_counter()
with out.with_suffix('.txt').open('w',encoding='utf-8') as stream:
    completed=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT)
metadata={'command':command,'cwd':str(Path.cwd()),'started_utc':started,'duration_seconds':time.perf_counter()-tick,'exit_code':completed.returncode,'output':out.with_suffix('.txt').name}
out.with_suffix('.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8');print(json.dumps(metadata));raise SystemExit(0 if completed.returncode==0 else 1)
