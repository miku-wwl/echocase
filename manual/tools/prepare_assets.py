"""Select genuine historical pixels and observations; no simulated application UI."""
from pathlib import Path
import hashlib, json, subprocess
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
MANUAL = ROOT / 'manual'
HISTORY = '63c587277541b4e700258aad82de9b2ad0ba32f8'

def git_bytes(path):
    return subprocess.check_output(['git', 'show', f'{HISTORY}:{path}'], cwd=ROOT)

def main():
    target = MANUAL / 'figures' / 'ui'
    target.mkdir(parents=True, exist_ok=True)
    records = []
    names = ['02-dashboard', '03-evidence', '04-graph', '05-verdict',
             '08-mobile', 'inflight-draft', 'dirty-refetch',
             'unreadable-body', 'link-revision']
    for name in names:
        path = f'evidence/phase2a/browser/{name}.png'
        data = git_bytes(path)
        (target / (name + '.png')).write_bytes(data)
        with Image.open(target / (name + '.png')) as im:
            size = list(im.size)
        records.append(dict(file=f'figures/ui/{name}.png', commit=HISTORY, path=path,
                            sha256=hashlib.sha256(data).hexdigest(), pixels=size,
                            description='Genuine browser capture; unmodified source pixels.'))
    # Keep a small interpreted numeric dataset, not the historical raw evidence tree.
    plan = json.loads(git_bytes('evidence/phase2a/database/application-query-plan.json'))
    race = json.loads(git_bytes('evidence/phase2a/database/store-race.json'))
    tracking = json.loads(git_bytes('evidence/phase2a/database/migration-tracking.json'))
    precision = json.loads(git_bytes('evidence/phase2a/database/timestamp-precision.json'))
    selected = dict(commit=HISTORY, query={k:v for k,v in plan.items() if k not in ['withoutComposite','ownerOnly','withComposite']},
                    plans={k:plan[k] for k in ['withoutComposite','ownerOnly','withComposite']},
                    race=race, tracking=tracking, precision=precision)
    build = MANUAL / 'build'
    build.mkdir(exist_ok=True)
    (build / 'selected-observations.json').write_text(json.dumps(selected,ensure_ascii=False,indent=2),encoding='utf-8')
    # Validate that historical runtime examples still describe the current application.
    same = []
    for base in ['backend', 'frontend/src']:
        files = subprocess.check_output(['git','ls-files',base],cwd=ROOT,text=True).splitlines()
        for file in files:
            if file.endswith(('.cs','.csproj','.tsx','.ts','.css','.json')) and '/docs/' not in file:
                historical = ('src/' + file[len('backend/'):]) if file.startswith('backend/') else file
                try:
                    old = git_bytes(historical).decode('utf-8-sig').replace('\r\n','\n')
                except subprocess.CalledProcessError:
                    continue
                current = (ROOT/file).read_text(encoding='utf-8-sig').replace('\r\n','\n')
                if old != current:
                    raise RuntimeError(f'Application source drift: {file}')
                same.append(file)
    provenance = dict(screenshots=records, runtimeCommit=HISTORY,
                      sourceCommit='908811b95fb40cf14fa79b8eddf41796aa02cc04',
                      identicalApplicationFiles=same,
                      note='Historical application observations, not a new local runtime execution. '
                           'Current source paths differ mechanically; application code matches after newline normalization.')
    (MANUAL/'reference'/'asset-provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(screenshots=len(records), matchedSourceFiles=len(same), queryKeys=list(plan),trackingKeys=list(tracking)),ensure_ascii=False))

if __name__ == '__main__': main()
