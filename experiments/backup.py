"""Real pg_dump / pg_restore of a small disposable synthetic database, not a production DR claim."""
import hashlib,json,os,subprocess,uuid
from pathlib import Path
import psycopg
from psycopg import sql
root=Path(__file__).resolve().parents[1];out=root/'evidence'/'backup';out.mkdir(parents=True,exist_ok=True)
admin=os.environ['ECHOCASE_PG_DSN'];source='echocase_backup_'+uuid.uuid4().hex;target='echocase_restore_'+uuid.uuid4().hex
with psycopg.connect(admin,autocommit=True) as control:
    try:
        for name in (source,target):control.execute(sql.SQL('create database {}').format(sql.Identifier(name)))
        with psycopg.connect(admin,dbname=source,autocommit=True) as conn:
            conn.execute('create table journal(id int primary key, note text not null)')
            conn.execute("insert into journal values(1,'门禁'),(2,'凭证'),(3,'调度')")
        dump=subprocess.run(['podman','exec','echocase-postgres','pg_dump','-U','echocase','-Fc','-d',source],capture_output=True,check=True).stdout
        restore=subprocess.run(['podman','exec','-i','echocase-postgres','pg_restore','-U','echocase','--no-owner','--exit-on-error','-d',target],input=dump,capture_output=True,check=True)
        with psycopg.connect(admin,dbname=target,autocommit=True) as conn:rows=conn.execute('select * from journal order by id').fetchall()
        assert rows==[(1,'门禁'),(2,'凭证'),(3,'调度')]
        result={'kind':'REAL_PG_DUMP_PG_RESTORE_SYNTHETIC_DATABASE','dump_bytes':len(dump),'sha256':hashlib.sha256(dump).hexdigest(),'restored_rows':rows,'row_count':3,'scope':'one disposable local PostgreSQL database; NOT complete application DR, off-host backup, or PITR'}
    finally:
        for name in (source,target):
            assert name.startswith(('echocase_backup_','echocase_restore_'))
            control.execute(sql.SQL('drop database if exists {} with (force)').format(sql.Identifier(name)))
        result['cleanup']='both disposable databases removed; dump not persisted'
(out/'results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False))
