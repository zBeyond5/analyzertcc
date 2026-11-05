from pathlib import Path
from streamlit.testing.v1 import AppTest
from tcc_analyzer.ui.downloads import build_download_anchor

def test_private_anchor_not_media_url():
    html=build_download_anchor(b'private',filename='relatorio.pdf',mime='application/pdf')
    assert 'data:application/pdf;base64,' in html
    assert '/media/' not in html and 'runtime' not in html

def test_cloud_entry_preserves_local_bind_and_explains_processing(tmp_path,monkeypatch):
    import tomllib
    root=Path(__file__).resolve().parents[1]
    local=tomllib.loads((root/'.streamlit/config.toml').read_text())
    cloud=tomllib.loads((root/'cloud/.streamlit/config.toml').read_text())
    assert local['server']['address']=='127.0.0.1'
    assert cloud['server']['address']=='0.0.0.0'
    monkeypatch.setenv('TCC_RUNTIME_ROOT',str(tmp_path/'cloud-jobs'))
    monkeypatch.setenv('TCC_DEPLOYMENT','cloud')
    at=AppTest.from_file(root/'cloud/app.py',default_timeout=30).run()
    assert not at.exception
    assert any('nuvem' in element.value for element in [*at.markdown,*at.caption])

def test_app_demo_workflow(tmp_path,monkeypatch):
    monkeypatch.setenv('TCC_RUNTIME_ROOT',str(tmp_path/'ui-jobs'))
    at=AppTest.from_file(Path(__file__).resolve().parents[1]/'app.py',default_timeout=30).run()
    assert not at.exception
    at.button(key='demo').click().run()
    assert not at.exception
    assert at.session_state['workflow'].prepared.data.shape==(30,76)
    assert at.session_state['workflow'].fictitious
    assert at.session_state['navigation']=='2 · Conferir'
