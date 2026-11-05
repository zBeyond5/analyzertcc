from datetime import time
from io import BytesIO
import openpyxl
import pandas as pd
import pytest
from tcc_analyzer.profiles import load_updated_profile, profile_for_import
from tcc_analyzer.importers import load_table
from tcc_analyzer.validation import prepare_dataset
from tcc_analyzer.scales import clock_to_decimal, score_psqi, ZARIT_FIELDS
from tcc_analyzer.models import DomainError


def good_row():
    p=load_updated_profile()
    row={v.name: (0 if 0 in (v.allowed_values or ()) else next(iter(v.allowed_values),1) if v.allowed_values else 1) for v in p.variables if v.name in p.input_fields}
    row.update(ID=1,H_DEIT=time(22),H_LEV=time(6),H_SONO=8,N_MIN=10,IDADE_M=30,IDADE_C=5,TEMP_TEA=12)
    return row


def workbook(tmp_path, row=None, inverted=False):
    p=load_updated_profile();w=openpyxl.Workbook();s=w.active;s.title='Banco'
    fields=list(reversed(p.input_fields));r=row or good_row()
    s.append(fields);s.append([r[f] for f in fields])
    c=w.create_sheet('Categorias');c.append(fields)
    variables={v.name:v for v in p.variables}
    for level in range(5):
        vals=[]
        for f in fields:
            labels=dict(variables[f].labels)
            if f=='RED_APO' and inverted:labels={1:'Não',2:'Sim'}
            options=list(labels.items());vals.append(f'{options[level][0]}= {options[level][1]}' if level<len(options) else None)
        c.append(vals)
    q=w.create_sheet('Perguntas');q.append(fields);q.append([f'Pergunta {f}' for f in fields])
    dest=tmp_path/'bank.xlsx';w.save(dest);return dest


def test_updated_profile_and_native_hours(tmp_path):
    imported=load_table(workbook(tmp_path));p=profile_for_import(imported)
    assert len(p.input_fields)==69
    assert imported.metadata['questions']['RED_APO']=='Pergunta RED_APO'
    prepared=prepare_dataset(imported,p)
    assert not prepared.validation.blocks_analysis
    assert prepared.data.iloc[0].PSQI==0
    assert prepared.data.iloc[0].ZARIT==0
    assert imported.raw.iloc[0].H_DEIT==time(22)


def test_alias_collision_is_blocked(tmp_path):
    path=workbook(tmp_path);imp=load_table(path);imp.raw['DOENÇA']=imp.raw['DOENCA']
    with pytest.raises(DomainError):prepare_dataset(imp,profile_for_import(imp))


def test_imported_dictionary_keeps_its_meaning(tmp_path):
    imported=load_table(workbook(tmp_path,inverted=True));p=profile_for_import(imported)
    assert next(v for v in p.variables if v.name=='RED_APO').labels[1]=='Não'


@pytest.mark.parametrize('value,expected',[(time(23,30),23.5),('00:15',.25),(23.5,23.5)])
def test_clocks(value,expected):assert clock_to_decimal(value)==expected


def test_psqi_independent_vectors():
    p=load_updated_profile();r=good_row()
    assert score_psqi(r,p).total==0
    r['QUA_SONO']=3;r['FREQ_MED']=2
    assert score_psqi(r,p).total==5
    r['FREQ_MED']=3
    assert score_psqi(r,p).total==6
    r.update({f:3 for f in ('NAO_CONS','ACORD','PREC_LEV','NAO_RESP','TOS_RONC','FRIO','CALOR','SONHOS','DOR','DIF_DORM','DIF_ACOR','ANIMO')})
    r.update(N_MIN=90,H_SONO=4)
    assert score_psqi(r,p).total==21
    r['ACORD']=None
    assert score_psqi(r,p).total is None


@pytest.mark.parametrize('minutes,expected',[(15,0),(16,1),(30,1),(31,1),(60,1),(61,2)])
def test_psqi_latency_limits(minutes,expected):
    r=good_row();r['N_MIN']=minutes
    assert score_psqi(r,load_updated_profile()).components[1]==expected


@pytest.mark.parametrize('duration,expected',[(4.99,3),(5,2),(5.99,2),(6,1),(7,1),(7.01,0)])
def test_psqi_duration_limits(duration,expected):
    r=good_row();r['H_SONO']=duration
    assert score_psqi(r,load_updated_profile()).components[2]==expected


@pytest.mark.parametrize('efficiency,expected',[(64.9,3),(65,2),(74.9,2),(75,1),(84.9,1),(85,0)])
def test_psqi_efficiency_limits(efficiency,expected):
    r=good_row();r.update(H_DEIT=time(20),H_LEV=time(6),H_SONO=efficiency/10)
    assert score_psqi(r,load_updated_profile()).components[3]==expected


def test_changed_instrument_meaning_cannot_use_old_score(tmp_path):
    p=workbook(tmp_path);w=openpyxl.load_workbook(p)
    fields=[c.value for c in w['Categorias'][1]];col=fields.index('TEMP_VOC')+1
    w['Categorias'].cell(2,col).value='0= Uma resposta diferente'
    w.save(p);imported=load_table(p);prepared=prepare_dataset(imported,profile_for_import(imported))
    assert pd.isna(prepared.data.iloc[0].ZARIT)


def test_duplicate_auxiliary_code_is_localized(tmp_path):
    p=workbook(tmp_path);w=openpyxl.load_workbook(p)
    fields=[c.value for c in w['Categorias'][1]];col=fields.index('RED_APO')+1
    w['Categorias'].cell(3,col).value='1= Outro significado'
    w.save(p);imported=load_table(p);prepared=prepare_dataset(imported,profile_for_import(imported))
    assert any(i.code=='metadata' and i.variable=='RED_APO' for i in prepared.validation.issues)


def test_correction_refreshes_generated_outputs(tmp_path):
    from tcc_analyzer.validation import refresh_generated_scores
    imp=load_table(workbook(tmp_path));profile=profile_for_import(imp);prepared=prepare_dataset(imp,profile)
    prepared.data.loc[0,'TEMP_VOC']=4
    prepared.data.loc[0,'QUA_SONO']=3
    changed=refresh_generated_scores(prepared,profile)
    assert changed.data.loc[0,'ZARIT']==4 and changed.data.loc[0,'PSQI']==3
    changed.data.loc[0,'TEMP_VOC']=0
    assert refresh_generated_scores(changed,profile).data.loc[0,'ZARIT']==0
