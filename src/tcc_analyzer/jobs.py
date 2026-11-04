from contextlib import contextmanager
from dataclasses import dataclass,field
from datetime import datetime,timedelta,timezone
from pathlib import Path
import atexit,re,secrets,shutil,threading,zipfile,os
if os.name == 'nt':
    import msvcrt
else:
    import fcntl
from .models import DomainError
from .settings import Settings
from .importers import inspect_upload

@dataclass(frozen=True)
class SessionContext:
    token: str = field(default_factory=lambda:secrets.token_urlsafe(32))

@dataclass
class JobContext:
    id: str
    owner_token: str
    directory: Path
    created_at: datetime
    expires_at: datetime
    status: str = 'created'
    artifacts: dict = field(default_factory=dict)
    source_path: Path | None = None

@dataclass
class CleanupSummary:
    deleted: int = 0
    active_skipped: int = 0
    failed: int = 0

ALLOWED_ARTIFACTS={'relatorio.docx','relatorio.pdf','tabelas.xlsx','epiinfo_dados.xlsx','epiinfo_dados.csv','dicionario.xlsx','manifesto.json','auditoria.json','resultado_completo.zip'}

def _file_lock(file,acquire):
    file.seek(0)
    if os.name == 'nt':
        msvcrt.locking(file.fileno(),msvcrt.LK_NBLCK if acquire else msvcrt.LK_UNLCK,1)
    else:
        fcntl.flock(file.fileno(),fcntl.LOCK_EX | fcntl.LOCK_NB if acquire else fcntl.LOCK_UN)

class JobManager:
    def __init__(self,root,settings=Settings(),clock=None):
        self.root=Path(root).resolve();self.root.mkdir(parents=True,exist_ok=True)
        self.settings=settings;self.clock=clock or (lambda:datetime.now(timezone.utc))
        self._jobs={};self._lock=threading.RLock();self._slots=threading.BoundedSemaphore(settings.max_heavy_runs)
        self._stop=threading.Event();self._closed=False
        self._file=(self.root/'.server.lock').open('a+b');self._file.write(b'0');self._file.flush();self._file.seek(0)
        try:_file_lock(self._file,True)
        except OSError:
            self._file.close();raise DomainError('instance','Outra instância já utiliza os trabalhos deste diretório.') from None
        for p in self.root.iterdir():
            if re.fullmatch('[0-9a-f]{32}',p.name) and self._contained(p) and (p/'.tcc-job').is_file():
                shutil.rmtree(p)
        self._thread=threading.Thread(target=self._clean_loop,daemon=True);self._thread.start()
        atexit.register(self.close)

    def _contained(self,path):
        p=Path(path)
        return not p.is_symlink() and not p.is_junction() and p.resolve().is_relative_to(self.root) and p.resolve()!=self.root

    def _check(self,session,job):
        if self._closed or self._jobs.get(job.id) is not job or not secrets.compare_digest(session.token,job.owner_token):
            raise DomainError('access','Acesso não permitido.')
        if job.status!='running' and self.clock()>=job.expires_at:raise DomainError('expired','A execução expirou. Importe o arquivo novamente.')
        if not self._contained(job.directory):raise DomainError('access','Acesso não permitido.')

    def create_job(self,session):
        with self._lock:
            now=self.clock();identifier=secrets.token_hex(16);directory=self.root/identifier;directory.mkdir()
            (directory/'.tcc-job').write_text('1',encoding='ascii')
            job=JobContext(identifier,session.token,directory,now,now+timedelta(minutes=self.settings.retention_minutes))
            self._jobs[identifier]=job;return job

    def store_upload(self,session,job,filename,payload):
        with self._lock:
            self._check(session,job)
            if job.status not in ('created','uploaded'):raise DomainError('state','Crie uma nova execução para outro arquivo.')
            suffix=inspect_upload(filename,payload,self.settings.import_limits)
            path=job.directory/('entrada'+suffix)
            path.write_bytes(payload);job.source_path=path;job.status='uploaded';return path

    def register_artifacts(self,session,job,artifacts):
        with self._lock:
            self._check(session,job)
            for key,p in artifacts.items():
                p=Path(p)
                if p.name not in ALLOWED_ARTIFACTS or p.parent!=job.directory or not self._contained(p) or not p.is_file():raise DomainError('artifact','Artefato inválido.')
                if p.stat().st_size>self.settings.max_artifact_bytes:raise DomainError('artifact_size','A exportação excede o limite de download. Reduza o banco ou os cruzamentos.')
            job.artifacts.update(artifacts)

    def read_artifact(self,session,job,artifact_key):
        with self._lock:
            self._check(session,job)
            if artifact_key not in job.artifacts:raise DomainError('artifact','Arquivo indisponível para esta execução.')
            path=job.artifacts[artifact_key]
            if not self._contained(path) or path.parent!=job.directory:raise DomainError('access','Acesso não permitido.')
            if path.stat().st_size>self.settings.max_artifact_bytes:raise DomainError('artifact_size','Arquivo excede o limite de download.')
            return path.read_bytes()

    def bundle_results(self,session,job,artifacts=None):
        with self._lock:
            self._check(session,job)
            if artifacts:self.register_artifacts(session,job,artifacts.files if hasattr(artifacts,'files') else artifacts)
            path=job.directory/'resultado_completo.zip'
            with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
                for key,p in job.artifacts.items():
                    if p.name=='resultado_completo.zip':continue
                    z.writestr(p.name,self.read_artifact(session,job,key))
            self.register_artifacts(session,job,{'zip':path});return path

    @contextmanager
    def analysis(self,session,job):
        with self._lock:
            self._check(session,job)
            if job.status not in ('created','uploaded'):raise DomainError('state','Esta execução já foi processada; crie outra para refazer.')
            if not self._slots.acquire(blocking=False):raise DomainError('busy','O servidor está ocupado com duas análises. Tente novamente em instantes.')
            job.status='running'
        try:yield
        except BaseException:
            job.status='failed';raise
        finally:
            if job.status=='running':job.status='analyzed'
            self._slots.release()

    def complete(self,session,job):
        with self._lock:
            self._check(session,job);job.expires_at=self.clock()+timedelta(minutes=self.settings.retention_minutes);job.status='ready'

    def purge_expired_jobs(self):
        result=CleanupSummary()
        with self._lock:
            for ident,job in list(self._jobs.items()):
                if job.status=='running':result.active_skipped+=1;continue
                if self.clock()<job.expires_at:continue
                try:
                    if not self._contained(job.directory):raise OSError()
                    if job.directory.exists():shutil.rmtree(job.directory)
                    del self._jobs[ident];result.deleted+=1
                except OSError:result.failed+=1
        return result

    def _clean_loop(self):
        while not self._stop.wait(self.settings.cleanup_interval_seconds):self.purge_expired_jobs()

    def close(self):
        if self._closed:return
        self._stop.set();self._closed=True
        self._file.seek(0)
        try:_file_lock(self._file,False)
        finally:self._file.close()

_manager=None
_manager_lock=threading.Lock()
def get_manager():
    global _manager
    with _manager_lock:
        if _manager is None:_manager=JobManager(Path(os.environ.get('TCC_RUNTIME_ROOT',str(Path(__file__).resolve().parents[2]/'runtime/jobs'))))
        return _manager
