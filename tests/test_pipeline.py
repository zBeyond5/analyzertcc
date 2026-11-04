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
        assert result.results[0].result.n_effective==30
        manifest=json.loads(m.read_artifact(s,j,'manifest'))
        assert manifest['fictitious'] is True and manifest['score_source']=='recorded'
        assert manifest['source_sha256']==prepared.source_meta.source_sha256
        assert 'owner_token' not in str(manifest)
        with zipfile.ZipFile(result.files['zip']) as z:
            assert len(z.namelist())==8
            assert 'entrada.xlsx' not in z.namelist()
    finally:m.close()

def test_pending_profile_blocks_real_analysis(source_path,tmp_path):
    m=JobManager(tmp_path/'jobs');s=SessionContext();j=m.create_job(s)
    try:
        path=m.store_upload(s,j,source_path.name,source_path.read_bytes());p=load_profile()
        prepared=prepare_dataset(load_table(path,sheet='Banco_EpiInfo'),p)
        with pytest.raises(DomainError):run_pipeline(manager=m,session=s,job=j,source_path=path,prepared=prepared,profile=p,options=RunOptions(default_comparisons()))
    finally:m.close()
