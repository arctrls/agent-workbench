#!/usr/bin/env python3
"""Extract installed, non-secret connection identifiers into a private environment file."""
import argparse
import os
from pathlib import Path
import tempfile
import tomllib

from environment import environment_file, load_environment


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path(os.environ.get('CODEX_HOME') or Path.home()/'.codex')/'config.toml')
    parser.add_argument('--env-file', type=Path, default=environment_file(dict(os.environ)))
    args=parser.parse_args()
    settings=tomllib.loads(args.config.expanduser().read_text()).get('mcp_servers', {})
    values={}
    mysql=settings.get('mysql-mcp-server', {})
    argv=mysql.get('args', [])
    flags={'--hostname':'MYSQL_READ_DEV_HOST','--secret_arn':'MYSQL_READ_DEV_SECRET_ARN',
           '--database':'MYSQL_READ_DEV_DATABASE','--region':'MYSQL_READ_DEV_REGION'}
    for flag,key in flags.items():
        if flag in argv and argv.index(flag)+1 < len(argv):values[key]=argv[argv.index(flag)+1]
    if values:
        values['MYSQL_READ_DEV_PROFILE']=mysql.get('env',{}).get('AWS_PROFILE','default')
    rea=settings.get('rea', {})
    if rea.get('command'):
        values['REA_NPX']=rea['command']
        if Path(rea['command']).is_absolute():values['REA_NODE_PATH']=str(Path(rea['command']).parent)
    path=args.env_file.expanduser()
    if path.is_symlink():raise ValueError('Refusing to replace a symlinked environment file')
    original=path.read_text() if path.exists() else ''
    existing=load_environment({'AGENT_WORKBENCH_ENV_FILE':str(path)})
    additions={key:value for key,value in values.items() if key not in existing}
    if not additions:
        print('No environment values to migrate.');return
    if any('\n' in value or '\r' in value for value in additions.values()):raise ValueError('Multiline values are unsupported')
    path.parent.mkdir(parents=True,exist_ok=True)
    output=original+('' if not original or original.endswith('\n') else '\n')
    output+=''.join(key+'='+value+'\n' for key,value in additions.items())
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(mode='w',dir=path.parent,delete=False,prefix='.env-') as f:
            temporary=Path(f.name);os.fchmod(f.fileno(),0o600);f.write(output)
        if (path.read_text() if path.exists() else '') != original:raise ValueError('Environment file changed during migration')
        os.replace(temporary,path)
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)
    print('Migrated keys: '+', '.join(additions))
    print('Saved private environment file: '+str(path))

if __name__=='__main__':main()
