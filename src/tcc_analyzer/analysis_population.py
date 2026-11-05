"""Observable AV3 eligibility in a copy, never by deleting source records."""
from dataclasses import asdict
import hashlib,json
import pandas as pd
from .models import AnalysisPopulation,DomainError
from .scales import score_psqi,score_zarit

REASONS={'age_missing':'Idade materna não informada','age_below_18':'Idade materna abaixo de 18 anos','psqi_incomplete':'Questionário de sono incompleto','zarit_incomplete':'Questionário de sobrecarga incompleto'}

def select_population(data,profile):
    if profile.instrument_mode!='responses':return AnalysisPopulation(data.copy(deep=True),tuple(data.index),(),'legacy_complete_pairs')
    variables={v.name:v for v in profile.variables}
    from .scales import PSQI_FREQUENCIES,ZARIT_FIELDS
    for field in PSQI_FREQUENCIES+ZARIT_FIELDS:
        if field in profile.canonical_codes:
            mapping=profile.canonical_codes[field]
            if any(str(code) not in mapping and code not in mapping for code in variables[field].allowed_values):
                raise DomainError('instrument_mapping','Há opções de questionário sem significado de pontuação definido. Confira as categorias antes de analisar.')
    included=[];excluded=[]
    for index,row in data.iterrows():
        reasons=[];age=row.get('IDADE_M')
        if pd.isna(age):reasons.append('age_missing')
        elif float(age)<18:reasons.append('age_below_18')
        if score_psqi(row,profile).total is None:reasons.append('psqi_incomplete')
        if score_zarit(row,profile).total is None:reasons.append('zarit_incomplete')
        if reasons:excluded.append({'row':int(index),'reasons':reasons})
        else:included.append(index)
    return AnalysisPopulation(data.loc[included].copy(deep=True),tuple(included),tuple(excluded),'av3_observable_v1')

def population_signature(prepared,profile,selection):
    payload={'source':prepared.source_meta.source_sha256,'profile':asdict(profile),'rows':selection.included_rows,'excluded':selection.excluded,'policy':selection.policy,'data':prepared.data.to_json(date_format='iso',default_handler=str)}
    return hashlib.sha256(json.dumps(payload,sort_keys=True,default=str).encode()).hexdigest()
