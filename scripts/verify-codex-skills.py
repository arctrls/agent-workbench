#!/usr/bin/env python3
"""Verify local skill discovery through Codex app-server, without starting a model turn."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import queue
import subprocess
import threading
import time


def inspect(home, cwd, expected):
    auth=home/'auth.json'
    before=hashlib.sha256(auth.read_bytes()).hexdigest() if auth.exists() else None
    process=subprocess.Popen(['codex','--no-daemon','app-server','--stdio'],
                             env=dict(os.environ,CODEX_HOME=str(home)), stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
    messages=queue.Queue()
    def read():
        for line in process.stdout:
            try:messages.put(json.loads(line))
            except ValueError:continue
    threading.Thread(target=read,daemon=True).start()
    def rpc(identifier,method,params):
        process.stdin.write(json.dumps({'id':identifier,'method':method,'params':params})+'\n')
        process.stdin.flush()
        deadline=time.monotonic()+30
        while time.monotonic()<deadline:
            response=messages.get(timeout=max(.1,deadline-time.monotonic()))
            if response.get('id')==identifier:
                if 'error' in response:raise RuntimeError(response['error'])
                return response['result']
        raise TimeoutError(method)
    try:
        rpc(1,'initialize',{'clientInfo':{'name':'workbench_verify','version':'1.0'}})
        process.stdin.write('{"method":"initialized","params":{}}\n');process.stdin.flush()
        result=rpc(2,'skills/list',{'cwds':[str(cwd)],'forceReload':True})
        entry=result['data'][0]
        skills=entry['skills']
        missing=[name for name in expected if not any(s['name']==name and s.get('enabled',True) for s in skills)]
        duplicates=[name for name in expected if sum(s['name']==name for s in skills)>1]
        errors=entry.get('errors',[])
        summary={'home':str(home),'total':len(skills),'expected':len(expected),
                 'missing_or_disabled':missing,'duplicate_names':duplicates,'load_errors':len(errors)}
    finally:
        process.terminate()
        try:process.wait(timeout=5)
        except subprocess.TimeoutExpired:process.kill();process.wait()
        process.stdin.close();process.stdout.close()
    after=hashlib.sha256(auth.read_bytes()).hexdigest() if auth.exists() else None
    summary['auth_unchanged']=before==after
    print(json.dumps(summary,ensure_ascii=False))
    return not missing and not duplicates and not errors and before==after


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--home',action='append',type=Path,required=True)
    parser.add_argument('--cwd',type=Path,default=Path.cwd())
    args=parser.parse_args()
    skills=Path(__file__).resolve().parents[1]/'codex/skills'
    expected=sorted(p.parent.name for p in skills.glob('*/SKILL.md') if not p.parent.name.startswith('.'))
    good=True
    for home in args.home:
        good=inspect(home.expanduser().resolve(),args.cwd.resolve(),expected) and good
    return 0 if good else 1

if __name__=='__main__':raise SystemExit(main())
