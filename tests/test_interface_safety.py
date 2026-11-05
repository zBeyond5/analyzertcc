"""Regression checks for import transactions and consistent demonstration eligibility."""
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
import openpyxl
import pandas as pd
import pytest
from tcc_analyzer.jobs import JobManager
from tcc_analyzer.models import DomainError,ResearchProfile,VariableSpec,ValidationReport
from tcc_analyzer.pipeline import DEMO_SHA256
from tcc_analyzer.ui import pages
from tcc_analyzer.ui.navigation import progress_status
from tcc_analyzer.ui.state import WorkflowState


def test_failed_preparation_preserves_previous_work(tmp_path,monkeypatch):
    monkeypatch.setattr(pages.st,'session_state',{'import_category_editor':'existing editor'})
    manager=JobManager(tmp_path/'jobs')
    try:
        state=WorkflowState()
        source=Path(__file__).parent/'fixtures/synthetic_tcc.xlsx'
        pages.import_bytes(state,manager,source.read_bytes(),source.name,demo=True)
        pages.st.session_state['import_category_editor']='existing editor'
        state.artifacts=object();state.options=object();state.reviewed=True;state.download_key='pdf'
        before=vars(state).copy()
        book=openpyxl.load_workbook(source)
        sheet=book.active
        column=sheet.max_column+1
        sheet.cell(1,column,'DOENÇA')
        for index in range(2,sheet.max_row+1):sheet.cell(index,column,1)
        payload=BytesIO();book.save(payload);book.close()
        with pytest.raises(DomainError,match='mesma pergunta'):
            pages.import_bytes(state,manager,payload.getvalue(),'duplicated_alias.xlsx')
        assert all(getattr(state,key) is value for key,value in before.items())
        assert pages.st.session_state['import_category_editor']=='existing editor'
    finally:manager.close()


@pytest.mark.parametrize('fictitious,source_hash,enabled',[
    (True,DEMO_SHA256,True),
    (False,DEMO_SHA256,False),
    (True,'unrecognized source',False),
])
def test_navigation_uses_same_demo_eligibility_as_pipeline(fictitious,source_hash,enabled):
    state=WorkflowState(fictitious=fictitious)
    state.profile=ResearchProfile('pending','1',(VariableSpec('ID','Identificador','integer',mapping_status='pending'),))
    state.prepared=SimpleNamespace(data=pd.DataFrame({'ID':[1]}),validation=ValidationReport(()),
                                   source_meta=SimpleNamespace(source_sha256=source_hash))
    assert progress_status(state)[0][2] is enabled
