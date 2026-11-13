"""Read historical observations from immutable Git, never from a fresh claim."""
import json,subprocess
from editions import ROOT

COMMIT='63c587277541b4e700258aad82de9b2ad0ba32f8'
def load():
    def read(name):
        data=subprocess.check_output(['git','show',COMMIT+':evidence/phase2a/database/'+name+'.json'],cwd=ROOT)
        return json.loads(data.decode('utf-8-sig'))
    plan=read('application-query-plan')
    arms=['withoutComposite','ownerOnly','withComposite']
    return dict(commit=COMMIT,query={k:v for k,v in plan.items() if k not in arms},
                plans={k:plan[k] for k in arms},race=read('store-race'),
                tracking=read('migration-tracking'),precision=read('timestamp-precision'))
