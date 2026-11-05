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


def test_missing_plotly_keeps_results_and_exports_available(tmp_path,monkeypatch):
    import builtins,sys
    monkeypatch.setenv('TCC_RUNTIME_ROOT',str(tmp_path/'missing-plotly-jobs'))
    monkeypatch.delitem(sys.modules,'tcc_analyzer.ui.charts',raising=False)
    original=builtins.__import__
    def without_plotly(name,*args,**kwargs):
        if name=='plotly' or name.startswith('plotly.'):
            raise ModuleNotFoundError("No module named 'plotly'",name='plotly')
        return original(name,*args,**kwargs)
    monkeypatch.setattr(builtins,'__import__',without_plotly)
    at=AppTest.from_file(Path(__file__).resolve().parents[1]/'app.py',default_timeout=60).run()
    at.button(key='demo').click().run()
    at.button(key='to_comparisons').click().run()
    at.button(key='run_analysis').click().run()
    assert not at.exception
    assert not at.error
    assert any('Gráficos interativos temporariamente indisponíveis' in message.value for message in at.info)
    assert any('Participaram desta comparação' in message.value for message in at.markdown)
    at.button(key='to_exports').click().run()
    at.button(key='prepare_download').click().run()
    assert any('data:application/zip;base64,' in message.value for message in at.markdown)

def test_updated_population_ui_uses_eligible_rows(tmp_path,monkeypatch):
    import pandas as pd
    from dataclasses import replace
    from types import SimpleNamespace
    from test_updated_profile import good_row
    from tcc_analyzer.profiles import load_updated_profile
    from tcc_analyzer.models import ImportedDataset,DatasetMeta
    from tcc_analyzer.validation import prepare_dataset
    from tcc_analyzer.ui.state import WorkflowState
    import tcc_analyzer.ui.pages as pages
    p=load_updated_profile();df=pd.DataFrame([{**good_row(),'ID':i+1,'IDADE_M':17 if i==2 else 30} for i in range(3)])
    imported=ImportedDataset(df,DatasetMeta(3,len(df.columns),tuple(df.columns),'synthetic'))
    state=WorkflowState(profile=p,imported=imported,prepared=prepare_dataset(imported,p))
    seen=[];original=pages.recommend_test
    def record(data,*args):
        seen.append(len(data));return original(data,*args)
    monkeypatch.setattr(pages,'recommend_test',record)
    at=AppTest.from_string("import streamlit as st\nfrom tcc_analyzer.ui.pages import render_comparisons\nrender_comparisons(st.session_state.test_state,None)",default_timeout=30)
    at.session_state['test_state']=state;at.run()
    assert not at.exception
    assert seen and set(seen)=={2}
    assert '2 participantes elegíveis' in at.button(key='run_analysis').label
