import pandas as pd
import pytest
from test_updated_profile import good_row
from tcc_analyzer.analysis_population import select_population,population_signature
from tcc_analyzer.profiles import load_updated_profile,load_profile
from tcc_analyzer.models import DomainError

def test_complete_instruments_and_observable_eligibility():
    r=good_row();r2={**r,'ID':2,'IDADE_M':17};r3={**r,'ID':3,'TEMP_VOC':None}
    df=pd.DataFrame([r,r2,r3]);original=df.copy(deep=True)
    selection=select_population(df,load_updated_profile())
    assert selection.included_rows==(0,)
    assert len(selection.excluded)==2 and df.equals(original)
    assert select_population(df,load_profile()).included_rows==(0,1,2)
    df.loc[0,'OCUP']=None
    assert select_population(df,load_updated_profile()).included_rows==(0,)

def test_semantic_change_is_configuration_error():
    from dataclasses import replace
    p=replace(load_updated_profile(),canonical_codes={'TEMP_VOC':{}})
    with pytest.raises(DomainError):select_population(pd.DataFrame([good_row()]),p)

def test_pipeline_confirms_population_and_exports_same_rows(tmp_path):
    import io,json
    from tcc_analyzer.data_entry import build_input_workbook
    from tcc_analyzer.importers import load_table
    from tcc_analyzer.validation import prepare_dataset
    from tcc_analyzer.jobs import JobManager,SessionContext
    from tcc_analyzer.pipeline import RunOptions,run_pipeline
    from tcc_analyzer.statistics.selection import default_comparisons
    from dataclasses import replace
    from docx import Document
    from pypdf import PdfReader
    p=load_updated_profile();rows=[{**good_row(),'ID':i+1,'TEMP_VOC':i,'NOME':'PRIVATE PERSON'} for i in range(3)]
    rows[0]['ZARIT']=0;rows[1]['TEMP_VOC']=None;rows[1]['ZARIT']=0;rows[2]['ZARIT']=2;rows[2]['IDADE_M']=17
    manager=JobManager(tmp_path/'jobs');session=SessionContext();job=manager.create_job(session)
    try:
        path=manager.store_upload(session,job,'filled.xlsx',build_input_workbook(rows,p,fictitious=True))
        prepared=prepare_dataset(load_table(path),p);population=select_population(prepared.data,p)
        args=dict(manager=manager,session=session,job=job,source_path=path,prepared=prepared,profile=p)
        with pytest.raises(DomainError,match='confirme'):run_pipeline(**args,options=RunOptions(default_comparisons(),fictitious=True))
        signature=population_signature(prepared,p,population)
        result=run_pipeline(**args,options=RunOptions(default_comparisons(),fictitious=True,population_ack_signature=signature))
        assert result.metadata['n_source']==3 and result.metadata['n_included']==1
        assert len(prepared.data)==3
        assert len(pd.read_excel(result.files['xlsx']))==1
        assert all(r.result.n_effective==1 for r in result.results)
        assert 'PRIVATE PERSON' not in result.files['manifest'].read_text(encoding='utf-8')
        assert 'Inferência não disponível' in ' '.join(p.text for p in Document(result.files['docx']).paragraphs)
        assert 'Inferência não disponível' in ''.join(p.extract_text() for p in PdfReader(result.files['pdf']).pages)
        prepared.data.loc[0,'IDADE_M']=32
        with pytest.raises(DomainError,match='confirme'):run_pipeline(**args,options=RunOptions(default_comparisons(),population_ack_signature=signature))
    finally:manager.close()

@pytest.mark.parametrize('provided,expected',[('PSQI','mixed'),('both','recorded')])
def test_manifest_score_origin_matches_actual_inputs(tmp_path,provided,expected):
    from tcc_analyzer.data_entry import build_input_workbook
    from tcc_analyzer.importers import load_table
    from tcc_analyzer.validation import prepare_dataset
    from tcc_analyzer.jobs import JobManager,SessionContext
    from tcc_analyzer.pipeline import RunOptions,run_pipeline
    from tcc_analyzer.statistics.selection import default_comparisons
    p=load_updated_profile();row=good_row();payload=build_input_workbook([row],p)
    m=JobManager(tmp_path/'jobs');s=SessionContext();j=m.create_job(s)
    try:
        path=m.store_upload(s,j,'f.xlsx',payload);imported=load_table(path)
        imported.raw['PSQI']=0
        if provided=='both':imported.raw['ZARIT']=0
        prepared=prepare_dataset(imported,p)
        r=run_pipeline(manager=m,session=s,job=j,source_path=path,prepared=prepared,profile=p,options=RunOptions(default_comparisons()))
        assert r.metadata['score_source']==expected
        assert not any('PSQI calculado' in t for t in r.metadata['limitations'])
    finally:m.close()

def test_invalid_codes_remain_blockers_and_zero_population_is_empty():
    from tcc_analyzer.models import ImportedDataset,DatasetMeta
    from tcc_analyzer.validation import prepare_dataset,analysis_validation_issues
    p=load_updated_profile();row=good_row();row['TEMP_VOC']=99
    df=pd.DataFrame([row]);prepared=prepare_dataset(ImportedDataset(df,DatasetMeta(1,len(df.columns),tuple(df.columns),'test')),p)
    assert any(i.code=='unknown_category' and i.severity=='error' for i in analysis_validation_issues(prepared,p))
    row=good_row();row['IDADE_M']=17
    assert select_population(pd.DataFrame([row]),p).data.empty
