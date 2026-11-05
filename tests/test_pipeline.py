from dataclasses import replace
import json,zipfile
import pytest
from tcc_analyzer.pipeline import run_pipeline,RunOptions
from tcc_analyzer.jobs import JobManager,SessionContext
from tcc_analyzer.profiles import load_profile
from tcc_analyzer.importers import load_table
from tcc_analyzer.validation import prepare_dataset
from tcc_analyzer.models import DomainError
from tcc_analyzer.statistics.selection import default_comparisons


def test_pipeline_demo_outputs(source_path,tmp_path):
    m=JobManager(tmp_path/'jobs');s=SessionContext();j=m.create_job(s)
    try:
        path=m.store_upload(s,j,source_path.name,source_path.read_bytes())
        p=load_profile();prepared=prepare_dataset(load_table(path,sheet='Banco_EpiInfo'),p)
        result=run_pipeline(manager=m,session=s,job=j,source_path=path,prepared=prepared,profile=p,options=RunOptions(default_comparisons(),fictitious=True))
        assert {'docx','pdf','tables','csv','xlsx','dictionary','manifest','audit','zip'}==set(result.files)
        assert len(result.results)==3
        assert result.presentation is not None
        assert len(result.presentation.comparisons)==3
        assert result.metadata['presentation_version']=='readable-reports-v1'
        import pandas as pd
        from pypdf import PdfReader
        sheets=pd.read_excel(result.files['tables'],sheet_name=None)
        assert 'Glossário' in sheets
        assert 'PSQI_G' not in str(sheets['Bivariada 1'].values)
        assert 'Nome para leitura' in pd.read_excel(result.files['dictionary']).columns
        reader=PdfReader(result.files['pdf'])
        assert sum(len(page.images) for page in reader.pages)>=2
        assert result.results[0].result.n_effective==30
        assert any('n=4' in text for text in result.results[0].result.assumptions)
        assert any('primeiro menos segundo' in text for text in result.results[0].result.assumptions)
        manifest=json.loads(m.read_artifact(s,j,'manifest'))
        assert manifest['fictitious'] is True and manifest['score_source']=='recorded'
        assert manifest['source_sha256']==prepared.source_meta.source_sha256
        assert 'owner_token' not in str(manifest)
        with zipfile.ZipFile(result.files['zip']) as z:
            assert len(z.namelist())==8
            assert 'entrada.xlsx' not in z.namelist()
        from tcc_analyzer.pipeline import refresh_report_style
        import hashlib
        before=[(a.result.p_value,a.result.n_effective) for a in result.results]
        expiry=j.expires_at
        with pytest.raises(DomainError):refresh_report_style(manager=m,session=SessionContext(),job=j,artifacts=result,data=prepared.data,profile=p,style='article')
        article=refresh_report_style(manager=m,session=s,job=j,artifacts=result,data=prepared.data,profile=p,style='article')
        assert article.metadata['report_style']=='article'
        assert [(a.result.p_value,a.result.n_effective) for a in article.results]==before
        assert j.expires_at==expiry and j.status=='ready'
        text='\n'.join(page.extract_text() for page in PdfReader(article.files['pdf']).pages)
        assert 'Material para o artigo' in text and 'Apêndice técnico' not in text
        manifest=json.loads(m.read_artifact(s,j,'manifest'))
        assert manifest['files_sha256']['relatorio.pdf']==hashlib.sha256(m.read_artifact(s,j,'pdf')).hexdigest()
        with zipfile.ZipFile(article.files['zip']) as z:
            assert z.read('relatorio.pdf')==m.read_artifact(s,j,'pdf')
    finally:m.close()

def test_pending_profile_blocks_real_analysis(source_path,tmp_path):
    m=JobManager(tmp_path/'jobs');s=SessionContext();j=m.create_job(s)
    try:
        path=m.store_upload(s,j,source_path.name,source_path.read_bytes());p=load_profile()
        prepared=prepare_dataset(load_table(path,sheet='Banco_EpiInfo'),p)
        with pytest.raises(DomainError):run_pipeline(manager=m,session=s,job=j,source_path=path,prepared=prepared,profile=p,options=RunOptions(default_comparisons()))
    finally:m.close()
