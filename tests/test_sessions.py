from datetime import datetime,timedelta,timezone
from concurrent.futures import ThreadPoolExecutor
import secrets,zipfile
import pytest
from tcc_analyzer.jobs import JobManager,SessionContext
from tcc_analyzer.models import DomainError
from tcc_analyzer.settings import Settings

def test_second_server_cannot_delete_first_jobs(tmp_path):
    root=tmp_path/'exclusive'
    first=JobManager(root)
    try:
        job=first.create_job(SessionContext())
        with pytest.raises(DomainError,match='Outra instância'):
            JobManager(root)
        assert job.directory.exists()
    finally:first.close()

def test_jobs_module_has_no_unconditional_windows_import():
    import ast
    from pathlib import Path
    tree=ast.parse((Path(__file__).parents[1]/'src/tcc_analyzer/jobs.py').read_text(encoding='utf-8'))
    imports=[name.name for node in tree.body if isinstance(node,ast.Import) for name in node.names]
    assert 'msvcrt' not in imports

@pytest.fixture
def setup(tmp_path):
    now=[datetime(2026,11,4,tzinfo=timezone.utc)]
    m=JobManager(tmp_path/'jobs',Settings(),lambda:now[0])
    yield m,now
    m.close()

def test_cross_session_denied_even_with_job(setup):
    m,_=setup;a=SessionContext();b=SessionContext();job=m.create_job(a)
    with pytest.raises(DomainError,match='Acesso não permitido'):m.read_artifact(b,job,'zip')

def test_upload_and_private_file(setup):
    m,_=setup;s=SessionContext();job=m.create_job(s)
    with pytest.raises(DomainError):m.store_upload(s,job,'../test.csv',b'ID\n1\n')
    p=m.store_upload(s,job,'test.csv',b'ID\n1\n')
    assert p.parent==job.directory
    assert p.read_bytes()==b'ID\n1\n'

def test_expiration_and_bundle(setup):
    m,now=setup;s=SessionContext();job=m.create_job(s)
    path=job.directory/'auditoria.json';path.write_bytes(b'{}')
    m.register_artifacts(s,job,{'audit':path})
    z=m.bundle_results(s,job)
    assert zipfile.ZipFile(z).namelist()==['auditoria.json']
    m.complete(s,job)
    now[0]+=timedelta(minutes=59,seconds=59)
    assert m.read_artifact(s,job,'audit')==b'{}'
    now[0]+=timedelta(seconds=1)
    with pytest.raises(DomainError):m.read_artifact(s,job,'audit')
    assert m.purge_expired_jobs().deleted==1

def test_concurrency_and_finally(setup):
    m,_=setup;s=SessionContext();jobs=[m.create_job(s) for _ in range(3)]
    with m.analysis(s,jobs[0]),m.analysis(s,jobs[1]):
        with pytest.raises(DomainError):
            with m.analysis(s,jobs[2]):pass
    with m.analysis(s,jobs[2]):assert jobs[2].status=='running'

def test_two_jobs_and_path_allowlist(setup):
    m,_=setup
    def work(marker):
        s=SessionContext();j=m.create_job(s);p=j.directory/'auditoria.json';p.write_bytes(marker)
        m.register_artifacts(s,j,{'audit':p});m.bundle_results(s,j)
        with pytest.raises(DomainError):m.read_artifact(s,j,'../auditoria.json')
        return m.read_artifact(s,j,'audit')
    with ThreadPoolExecutor(2) as pool:assert list(pool.map(work,[b'A',b'B']))==[b'A',b'B']

def test_active_not_purged_and_orphan_recovery(setup):
    m,now=setup;s=SessionContext();j=m.create_job(s)
    with m.analysis(s,j):
        now[0]+=timedelta(hours=2)
        assert m.purge_expired_jobs().active_skipped==1
    m.close()
    other=JobManager(m.root,Settings(),lambda:now[0]);assert not j.directory.exists();other.close()
