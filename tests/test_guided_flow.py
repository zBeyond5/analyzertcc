from pathlib import Path
from streamlit.testing.v1 import AppTest


def test_demo_reaches_download_without_technical_confirmations(tmp_path, monkeypatch):
    monkeypatch.setenv('TCC_RUNTIME_ROOT', str(tmp_path/'guided-jobs'))
    at = AppTest.from_file(Path(__file__).resolve().parents[1]/'app.py', default_timeout=60).run()
    at.button(key='demo').click().run()
    assert not at.exception
    assert not any('Referência' in x.label for x in at.text_input)
    at.button(key='to_comparisons').click().run()
    assert not any('pressupostos' in x.label for x in at.checkbox)
    assert at.button(key='run_analysis').disabled is False
    at.button(key='run_analysis').click().run()
    assert not at.exception
    assert at.session_state['workflow'].artifacts is not None
    at.button(key='to_exports').click().run()
    at.button(key='prepare_download').click().run()
    assert any('data:application/zip;base64,' in x.value for x in at.markdown)
