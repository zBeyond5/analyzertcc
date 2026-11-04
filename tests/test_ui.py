from pathlib import Path
from streamlit.testing.v1 import AppTest
from tcc_analyzer.ui.downloads import build_download_anchor

def test_private_anchor_not_media_url():
    html=build_download_anchor(b'private',filename='relatorio.pdf',mime='application/pdf')
    assert 'data:application/pdf;base64,' in html
    assert '/media/' not in html and 'runtime' not in html

def test_app_demo_workflow(tmp_path,monkeypatch):
    monkeypatch.setenv('TCC_RUNTIME_ROOT',str(tmp_path/'ui-jobs'))
    at=AppTest.from_file(Path(__file__).resolve().parents[1]/'app.py',default_timeout=30).run()
    assert not at.exception
    at.button(key='demo').click().run()
    assert not at.exception
    assert at.session_state['workflow'].prepared.data.shape==(30,76)
    assert at.session_state['workflow'].fictitious
