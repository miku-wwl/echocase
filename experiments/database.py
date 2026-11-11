"""Real PostgreSQL experiments. Creates and drops ONLY a fresh echocase_lab_* database."""
import json, os, statistics, time, uuid
from pathlib import Path
import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'evidence' / 'database'
OUT.mkdir(parents=True, exist_ok=True)
admin = os.environ['ECHOCASE_PG_DSN']
name = 'echocase_lab_' + uuid.uuid4().hex
results = {'kind':'REAL_POSTGRESQL_WITH_CONTROLLED_ANOMALIES','database':name,'timestamp':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
with psycopg.connect(admin, autocommit=True) as control:
    control.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
    try:
        with psycopg.connect(admin, dbname=name, autocommit=True) as setup:
            results['version']=setup.execute('select version()').fetchone()[0]
            setup.execute('create table counter(id int primary key, value int not null, version int not null default 1)')
            setup.execute('insert into counter values (1,0,1)')
            with psycopg.connect(admin, dbname=name, autocommit=True) as a, psycopg.connect(admin, dbname=name, autocommit=True) as b:
                old_a=a.execute('select value from counter where id=1').fetchone()[0]
                old_b=b.execute('select value from counter where id=1').fetchone()[0]
                a.execute('update counter set value=%s where id=1',(old_a+1,));b.execute('update counter set value=%s where id=1',(old_b+1,))
                lost=setup.execute('select value from counter').fetchone()[0]
                assert lost==1
                setup.execute('update counter set value=0, version=1')
                first=a.execute('update counter set value=1,version=2 where id=1 and version=1').rowcount
                second=b.execute('update counter set value=1,version=2 where id=1 and version=1').rowcount
                assert (first,second)==(1,0)
                results['lost_update']={'unsafe_final':lost,'expected_without_loss':2,'versioned_rows_affected':[first,second]}
                isolation={}
                for level in ['READ COMMITTED','REPEATABLE READ']:
                    setup.execute('update counter set value=10')
                    a.execute('BEGIN ISOLATION LEVEL '+level)
                    before=a.execute('select value from counter').fetchone()[0]
                    b.execute('update counter set value=20')
                    after=a.execute('select value from counter').fetchone()[0];a.execute('ROLLBACK')
                    isolation[level]=[before,after]
                assert isolation=={'READ COMMITTED':[10,20],'REPEATABLE READ':[10,10]}
                results['nonrepeatable_read']=isolation
                setup.execute('create table on_call(id int primary key, active bool not null)')
                setup.execute('insert into on_call values (1,true),(2,true)')
                skew={}
                for level in ['REPEATABLE READ','SERIALIZABLE']:
                    setup.execute('update on_call set active=true')
                    a.execute('BEGIN ISOLATION LEVEL '+level);b.execute('BEGIN ISOLATION LEVEL '+level)
                    assert a.execute('select count(*) from on_call where active').fetchone()[0]==2
                    assert b.execute('select count(*) from on_call where active').fetchone()[0]==2
                    a.execute('update on_call set active=false where id=1');a.execute('COMMIT')
                    state='committed'
                    try: b.execute('update on_call set active=false where id=2');b.execute('COMMIT')
                    except psycopg.errors.SerializationFailure: state='40001';b.execute('ROLLBACK')
                    active=setup.execute('select count(*) from on_call where active').fetchone()[0]
                    skew[level]={'second_writer':state,'remaining_active':active}
                assert skew['REPEATABLE READ']['remaining_active']==0
                assert skew['SERIALIZABLE']=={'second_writer':'40001','remaining_active':1}
                results['write_skew']=skew
            setup.execute('create table timeline(id int primary key, owner_id int not null, updated_at timestamptz not null, payload text not null)')
            setup.execute("insert into timeline select g,g%5000, timestamptz '2026-01-01' + g*interval '1 second',repeat('x',200) from generate_series(1,100000) g")
            setup.execute('analyze timeline')
            query='select id,updated_at from timeline where owner_id=17 order by updated_at desc limit 50'
            def measure():
                for _ in range(3): setup.execute(query).fetchall()
                runs=[]
                for _ in range(21):
                    tick=time.perf_counter();rows=setup.execute(query).fetchall();runs.append((time.perf_counter()-tick)*1000)
                plan=setup.execute('EXPLAIN (ANALYZE,BUFFERS,FORMAT JSON) '+query).fetchone()[0]
                return {'rows':len(rows),'samples_ms':runs,'median_ms':statistics.median(runs),'p95_ms':sorted(runs)[19],'plan':plan}
            before=measure()
            setup.execute('create index ix_timeline_owner_time on timeline(owner_id,updated_at desc)')
            setup.execute('analyze timeline');after=measure()
            assert before['rows']==after['rows']==20
            assert 'Seq Scan' in json.dumps(before['plan']) and 'Index' in json.dumps(after['plan'])
            results['query_optimization']={'row_count':100000,'owners':5000,'warmups':3,'samples':21,'before':before,'after':after,'scope':'single-machine warm-cache synthetic table shaped like the application owner timeline; NOT a production capacity claim'}
            # Full transaction rollback: the inserted row must not survive an exception.
            try:
                with setup.transaction():
                    setup.execute('insert into counter values (2,7,1)')
                    setup.execute('insert into counter values (2,8,1)')
            except psycopg.errors.UniqueViolation: pass
            assert setup.execute('select count(*) from counter where id=2').fetchone()[0]==0
            results['rollback']={'sqlstate':'23505','surviving_rows':0}
    finally:
        assert name.startswith('echocase_lab_') and len(name)==45
        control.execute(sql.SQL('DROP DATABASE {} WITH (FORCE)').format(sql.Identifier(name)))
        results['cleanup']='database dropped'
(OUT/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in results.items() if k!='query_optimization'},ensure_ascii=False))
print('Query median ms: before=%.3f after=%.3f' % (before['median_ms'],after['median_ms']))
