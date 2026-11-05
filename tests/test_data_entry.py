from io import BytesIO
from dataclasses import replace
import openpyxl
import pytest
from tcc_analyzer.models import ResearchProfile, VariableSpec, DomainError
from tcc_analyzer.data_entry import new_participant, update_categories, remap_rows, build_input_workbook


def profile():
    return ResearchProfile('test','1',(VariableSpec('ID','Identificador','text'),VariableSpec('RED_APO','Rede de apoio','categorical',(1,2),mapping_status='confirmed',labels={1:'Sim',2:'Não'}),VariableSpec('IDADE_M','Idade','numeric')))


def test_resume_preserves_simulation_and_prepared_clock(monkeypatch):
    from types import SimpleNamespace
    from datetime import time
    import pandas as pd
    from tcc_analyzer.ui import create_sheet
    from tcc_analyzer.profiles import load_updated_profile
    monkeypatch.setattr(create_sheet.st,'session_state',SimpleNamespace())
    imported=SimpleNamespace(raw=pd.DataFrame([{'ID':1,'H_DEIT':23.5,'H_LEV':7.0}]),metadata={'fictitious':True})
    create_sheet.resume_sheet(imported,load_updated_profile())
    builder=create_sheet.st.session_state.sheet_builder
    assert builder['fictitious'] is True
    assert builder['rows'][0]['H_DEIT']==time(23,30)
    payload=build_input_workbook(builder['rows'],builder['profile'],fictitious=builder['fictitious'])
    book=openpyxl.load_workbook(BytesIO(payload))
    assert dict(book['Metadados'].values)['fictitious']=='true'


def test_empty_answers_and_simultaneous_recoding():
    assert new_participant((1,3)) == {'ID':4}
    p,mapping=update_categories(profile(),'RED_APO',[{'Código':2,'Significado':'Sim','original_code':1},{'Código':1,'Significado':'Não','original_code':2}])
    rows=remap_rows([{'ID':1,'RED_APO':1},{'ID':2,'RED_APO':2}], 'RED_APO',mapping,p)
    assert [r['RED_APO'] for r in rows]==[2,1]
    assert p.variables[1].labels=={2:'Sim',1:'Não'}


def test_invalid_category_edits_do_not_lose_answers():
    with pytest.raises(DomainError): update_categories(profile(),'RED_APO',[{'Código':1,'Significado':'Sim'},{'Código':1,'Significado':'Não'}])
    p,m=update_categories(profile(),'RED_APO',[{'Código':1,'Significado':'Sim','original_code':1}])
    with pytest.raises(DomainError): remap_rows([{'ID':1,'RED_APO':2}], 'RED_APO',m,p)


def test_filled_workbook_contains_answers_metadata_and_no_default_zero():
    payload=build_input_workbook([{'ID':1,'NOME':'Brenda','RED_APO':1}],profile())
    w=openpyxl.load_workbook(BytesIO(payload))
    assert w.sheetnames==['Banco','Categorias','Perguntas','Metadados']
    assert w['Banco'].cell(2,2).value==1
    assert w['Banco'].cell(2,3).value is None
    assert w['Banco'].cell(2,4).value=='Brenda'
    assert w['Categorias'].cell(2,2).value=='1= Sim'
    assert len(w['Banco'].data_validations.dataValidation)==1
    assert w['Banco'].freeze_panes=='B2'
    assert 'fictícios' not in str(list(w['Metadados'].values))


def test_untrusted_text_stays_literal_in_excel():
    w=openpyxl.load_workbook(BytesIO(build_input_workbook([{'ID':1,'NOME':'=1+1'}],profile())))
    assert w['Banco'].cell(2,4).data_type=='s'

def test_guided_entry_starts_with_categories_then_one_question():
    from streamlit.testing.v1 import AppTest
    app=AppTest.from_string('from tcc_analyzer.ui.create_sheet import render_create_sheet\nrender_create_sheet(lambda payload, name: None)',default_timeout=30).run()
    assert not app.exception
    app.button(key='builder_start').click().run()
    assert len(app.text_input)==1
    assert 'opcional' in app.text_input[0].label
    app.text_input[0].set_value('Brenda')
    app.button[0].click().run()
    assert not app.exception
    assert len(app.number_input)==1
    assert len(app.radio)==0
    app.number_input[0].set_value(35.0)
    next(button for button in app.button if button.label=='Próxima').click().run()
    assert not app.exception
    assert len(app.radio)==1
    assert app.session_state['sheet_builder']['draft']['IDADE_M']==35.0
