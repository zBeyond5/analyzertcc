from types import SimpleNamespace
import pandas as pd
from streamlit.testing.v1 import AppTest
from tcc_analyzer.models import ResearchProfile, VariableSpec, ValidationReport, ValidationIssue
from tcc_analyzer.ui.state import WorkflowState
from tcc_analyzer.ui.navigation import progress_status


def loaded_state():
    state=WorkflowState()
    state.profile=ResearchProfile('minimal','1',(VariableSpec('ID','ID','integer',mapping_status='confirmed'),))
    state.prepared=SimpleNamespace(data=pd.DataFrame({'ID':[1]}),validation=ValidationReport(()))
    return state


def test_progress_requires_data_validation_and_actual_results():
    assert progress_status(WorkflowState())==((True,False,False,False,False),(False,False,False,False,False))
    state=loaded_state()
    assert progress_status(state)==((True,True,True,False,False),(True,True,False,False,False))
    state.artifacts=object()
    assert progress_status(state)[0]==(True,True,True,True,False)
    state.reviewed=True
    assert progress_status(state)[0][-1] is True
    state.artifacts=None
    assert progress_status(state)[0][3:]==(False,False)


def test_metadata_blockers_disable_analysis():
    state=loaded_state()
    state.prepared.validation=ValidationReport((ValidationIssue(None,'ID',None,'metadata','error','Conflito'),))
    assert progress_status(state)[0][2] is False


def test_native_stepper_navigation_does_not_complete_by_visiting():
    app=AppTest.from_string('''
import streamlit as st
from tcc_analyzer.ui.state import WorkflowState
from tcc_analyzer.ui.navigation import render_navigation
if 'workflow' not in st.session_state: st.session_state.workflow=WorkflowState()
render_navigation(st.session_state.workflow,('1 · Dados','2 · Conferir','3 · Analisar','4 · Resultados','5 · Baixar'))
''').run()
    assert not app.exception
    assert not app.button(key='nav_top_0').disabled
    assert all(app.button(key=f'nav_top_{i}').disabled for i in range(1,5))
    assert app.session_state['navigation']=='1 · Dados'


def test_returning_to_completed_steps_preserves_the_work():
    app=AppTest.from_string('''
import streamlit as st
import pandas as pd
from types import SimpleNamespace
from tcc_analyzer.models import ResearchProfile,VariableSpec,ValidationReport
from tcc_analyzer.ui.state import WorkflowState
from tcc_analyzer.ui.navigation import render_navigation
if 'workflow' not in st.session_state:
    state=WorkflowState()
    state.profile=ResearchProfile('minimal','1',(VariableSpec('ID','ID','integer',mapping_status='confirmed'),))
    state.prepared=SimpleNamespace(data=pd.DataFrame({'ID':[7]}),validation=ValidationReport(()))
    state.artifacts='preserved'
    st.session_state.workflow=state
    st.session_state.navigation='4 · Resultados'
render_navigation(st.session_state.workflow,('1 · Dados','2 · Conferir','3 · Analisar','4 · Resultados','5 · Baixar'))
''').run()
    assert app.button(key='nav_top_1').label.startswith('✓')
    app.button(key='nav_top_1').click().run()
    assert app.session_state['navigation']=='2 · Conferir'
    assert app.session_state['workflow'].artifacts=='preserved'
    assert app.session_state['workflow'].prepared.data.iloc[0].ID==7
    app.button(key='nav_side_0').click().run()
    assert app.session_state['navigation']=='1 · Dados'
    assert not app.button(key='nav_top_3').disabled
