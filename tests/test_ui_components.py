from pathlib import Path
import pandas as pd
from streamlit.testing.v1 import AppTest
from tcc_analyzer.ui.components import input_summary

def test_input_summary_preserves_source_and_zero():
    frame=pd.DataFrame({'a':[0,None],'b':['  ','x']});original=frame.copy(deep=True)
    assert input_summary(frame)=={'rows':2,'columns':2,'empty_percent':50.0}
    assert frame.equals(original)
    assert input_summary(pd.DataFrame())['empty_percent']==0

def test_missing_stylesheet_keeps_app_usable(monkeypatch,tmp_path):
    from tcc_analyzer.ui import theme
    monkeypatch.setattr(theme,'STYLES_PATH',tmp_path/'absent.css')
    monkeypatch.setenv('TCC_RUNTIME_ROOT',str(tmp_path/'jobs'))
    at=AppTest.from_file(Path(__file__).resolve().parents[1]/'app.py',default_timeout=60).run()
    assert not at.exception
    assert any('aparência personalizada' in c.value for c in at.caption)
    at.button(key='demo').click().run()
    at.button(key='to_comparisons').click().run()
    at.button(key='run_analysis').click().run()
    assert not at.exception and at.session_state['workflow'].artifacts is not None
    at.button(key='to_exports').click().run()
    at.button(key='prepare_download').click().run()
    assert any('data:application/zip;base64,' in x.value for x in at.markdown)

def test_route_switch_preserves_draft_and_owner(tmp_path,monkeypatch):
    monkeypatch.setenv('TCC_RUNTIME_ROOT',str(tmp_path/'jobs'))
    at=AppTest.from_file(Path(__file__).resolve().parents[1]/'app.py',default_timeout=60).run()
    owner=at.session_state['workflow'].session.token
    at.segmented_control(key='data_route').set_value('Criar planilha').run()
    at.button(key='builder_start').click().run()
    next(b for b in at.button if b.label=='Começar perguntas').click().run()
    at.number_input[0].set_value(35)
    next(b for b in at.button if b.label=='Próxima').click().run()
    at.segmented_control(key='data_route').set_value('Importar planilha').run()
    at.segmented_control(key='data_route').set_value('Criar planilha').run()
    assert not at.exception
    assert at.session_state['sheet_builder']['draft']['IDADE_M']==35
    assert at.session_state['workflow'].session.token==owner

def test_theme_primary_text_is_readable_in_both_modes(monkeypatch):
    from types import SimpleNamespace
    from tcc_analyzer.ui import theme
    for mode,expected in [('dark','#0F1B24'),('light','#FFFFFF')]:
        captured=[]
        monkeypatch.setattr(theme.st,'context',SimpleNamespace(theme=SimpleNamespace(type=mode)))
        monkeypatch.setattr(theme.st,'markdown',lambda value,**kwargs:captured.append(value))
        theme.apply_theme()
        assert f'--research-on-primary: {expected}' in captured[0]
