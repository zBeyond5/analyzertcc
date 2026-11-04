from dataclasses import replace
import numpy as np
import pandas as pd
import pytest
from tcc_analyzer.profiles import load_profile
from tcc_analyzer.validation import prepare_dataset, validate_dataset
from tcc_analyzer.transformations import apply_changes, undo_changes
from tcc_analyzer.models import Transformation, DomainError
from tcc_analyzer.scales import score_zarit, score_psqi, classify_psqi, classify_zarit, hours_in_bed, decimal_hour_to_minutes
from tcc_analyzer.importers import load_table

def test_profile_all_fields(fictitious_df):
    p=load_profile()
    assert p.id=='tea_maternal_sleep_v1'
    assert [v.name for v in p.variables]==list(fictitious_df.columns)
    assert validate_dataset(fictitious_df,p).blocks_analysis

def test_prepare_preserves_original(source_path):
    imported=load_table(source_path,sheet='Banco_EpiInfo');original=imported.raw.copy(deep=True)
    prepared=prepare_dataset(imported,load_profile())
    assert prepared.data.ZARIT_CLASS.value_counts().sort_index().tolist()==[2,8,16,4]
    pd.testing.assert_frame_equal(imported.raw,original)

def test_reversible(fictitious_df):
    changes=(Transformation(0,'IDADE_M',34,35,'Conferência'),)
    with pytest.raises(DomainError):apply_changes(fictitious_df,changes,confirmed=False)
    changed=apply_changes(fictitious_df,changes,confirmed=True)
    assert changed.iloc[0].IDADE_M==35
    pd.testing.assert_frame_equal(undo_changes(changed,changes),fictitious_df)

def test_unknown_missing_duplicate(fictitious_df):
    df=fictitious_df.copy();df.loc[0,'PSQI_G']=9;df.loc[1,'ID']=df.loc[0,'ID']
    codes={i.code for i in validate_dataset(df,load_profile()).issues}
    assert {'unknown_category','duplicate_id'}<=codes
    assert validate_dataset(df.drop(columns='ZARIT'),load_profile()).blocks_analysis

@pytest.mark.parametrize('v,m',[(23.5,1410),(0.25,15)])
def test_decimal_clock(v,m):assert decimal_hour_to_minutes(v)==m

@pytest.mark.parametrize('v',[-1,24,float('nan')])
def test_invalid_clock(v):
    with pytest.raises(DomainError):decimal_hour_to_minutes(v)

def test_midnight():
    assert hours_in_bed(23.5,6.5)==7
    with pytest.raises(DomainError):hours_in_bed(6.5,6.5)

@pytest.mark.parametrize('s,c',[(0,1),(20,1),(21,2),(40,2),(41,3),(60,3),(61,4),(88,4)])
def test_zarit_boundaries(s,c):assert classify_zarit(s)==c

def test_scores(fictitious_df):
    p=load_profile()
    assert all(score_zarit(row,p).total==row.ZARIT for _,row in fictitious_df.iterrows())
    assert classify_psqi(5)==1 and classify_psqi(6)==2
    row=fictitious_df.iloc[0].copy();row['TEMP_VOC']=np.nan
    assert score_zarit(row,p).total is None
    assert score_psqi(row,p).total is None
    assert 'psqi_rules_unconfirmed' in score_psqi(row,p).issues

@pytest.mark.parametrize('field,value',[('PSQI',30),('PSQI',2.5),('ZARIT',-1),('N_MIN',-5),('DESP_NOT',-1),('H_DEIT',24)])
def test_invalid_numeric_bounds(fictitious_df,field,value):
    p=load_profile();p=replace(p,variables=tuple(replace(v,mapping_status='confirmed') for v in p.variables))
    df=fictitious_df.astype(object);df.loc[0,field]=value
    assert validate_dataset(df,p).blocks_analysis

def test_incomplete_instrument_with_supplied_total_is_blocked(fictitious_df):
    p=load_profile();p=replace(p,variables=tuple(replace(v,mapping_status='confirmed') for v in p.variables))
    df=fictitious_df.copy();df.loc[0,'TEMP_VOC']=np.nan
    assert any(i.code=='incomplete_instrument' for i in validate_dataset(df,p).issues)

def test_confirmed_codebook_can_add_new_codes():
    from tcc_analyzer.profiles import confirm_codebook
    profile=load_profile()
    entries=[{'Campo':v.name,'Código':str(k),'Legenda':f'Legenda confirmada {k}'} for v in profile.variables if v.kind=='categorical' for k in v.labels]
    entries.append({'Campo':'ESCOL','Código':'7','Legenda':'Nível conferido no formulário'})
    confirmed=confirm_codebook(profile,entries,'Formulário conferido pela responsável')
    assert 7 in next(v for v in confirmed.variables if v.name=='ESCOL').allowed_values

@pytest.mark.parametrize('field,value',[('ZARIT','inválido'),('TEMP_VOC',float('inf')),('N_MIN',float('nan'))])
def test_invalid_or_incomplete_instrument_never_crashes(fictitious_df,field,value):
    df=fictitious_df.astype(object);df.loc[0,field]=value
    report=validate_dataset(df,load_profile())
    assert any(i.severity=='error' and i.code!='mapping_pending' for i in report.issues)

def test_comparison_handles_invalid_recorded_total(fictitious_df):
    from tcc_analyzer.scales import compare_recorded_scores
    df=fictitious_df.astype(object);df.loc[0,'ZARIT']='inválido'
    compared=compare_recorded_scores(df,load_profile())
    row=compared[(compared.row_index==0)&(compared.instrument=='ZARIT')].iloc[0]
    assert pd.isna(row.difference)
    assert 'invalid_recorded_score' in row.issues
