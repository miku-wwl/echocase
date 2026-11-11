import argparse,json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'evidence/ci';out.mkdir(parents=True,exist_ok=True)
ap=argparse.ArgumentParser();ap.add_argument('--baseline',required=True);ap.add_argument('--rejected',required=True);ap.add_argument('--repaired');args=ap.parse_args()
def run(id):return json.loads(subprocess.run(['gh','run','view',id,'--json','databaseId,headSha,status,conclusion,jobs,url'],cwd=root,capture_output=True,text=True,encoding='utf-8',check=True).stdout)
baseline=run(args.baseline);rejected=run(args.rejected);repaired=run(args.repaired) if args.repaired else None
log=subprocess.run(['gh','run','view',args.rejected,'--log-failed'],cwd=root,capture_output=True,text=True,encoding='utf-8',check=True).stdout
assert baseline['conclusion']=='success' and rejected['conclusion']=='failure'
assert 'manifest.json' in log and 'FileNotFoundError' in log
if repaired is not None:assert repaired['conclusion']=='success'
data={'kind':'REAL_GITHUB_ACTIONS_MISSING_EVIDENCE_DRILL','status':'VERIFIED' if repaired else 'PARTIAL','baseline':baseline,'rejected':rejected,'repaired':repaired,'failure_matched_missing_manifest':True,'main_merged':False}
(out/'results.json').write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8');(out/'rejected.txt').write_text(log,encoding='utf-8');print(data['status'])
