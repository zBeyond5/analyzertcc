"""The cloud dependency entrypoint must change whenever its included lock changes."""
import hashlib
from pathlib import Path


def test_cloud_requirements_tracks_the_included_lock():
    root=Path(__file__).resolve().parents[1]
    lock=root/'requirements.lock'
    digest=hashlib.sha256(lock.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
    entrypoint=(root/'requirements.txt').read_text(encoding='utf-8')
    assert f'# lock-sha256: {digest}' in entrypoint
    assert '-r requirements.lock' in entrypoint
    assert 'plotly==7.1.0' in lock.read_text(encoding='utf-8').splitlines()
