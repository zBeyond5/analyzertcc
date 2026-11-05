import math
from datetime import time
import pandas as pd
from .models import DomainError,ScoreResult

ZARIT_FIELDS=('TEMP_VOC','ESTRES','IRRIT','AFET_REL','MEDO','DEPENDE','TENSO','SAU_FIS','PRIV','VID_SOC','DESCONF','UNICA_P','DINHEIRO','CAP_CUI','CONTROLE','INCAPAZ','FAZ_MAIS','CUID_MEL','MAIS_AJUD','EXAUSTO','CONST','UNIC_RESP')

def decimal_hour_to_minutes(value):
    try:v=clock_to_decimal(value)
    except (TypeError,ValueError):raise DomainError('clock','Horário inválido; informe horas decimais, como 23,5.') from None
    if not math.isfinite(v) or not 0<=v<24:raise DomainError('clock','Horário fora do intervalo de 0 a menos de 24 horas.')
    return round(v*60)

def clock_to_decimal(value):
    if isinstance(value,time):return value.hour+value.minute/60+value.second/3600
    try:
        if isinstance(value,str) and ':' in value:
            pieces=value.split(':')
            if len(pieces)!=2:raise ValueError()
            h,m=map(int,pieces)
            if not 0<=m<60:raise ValueError()
            result=h+m/60
            if not 0<=h<24:raise ValueError()
        else:result=float(str(value).replace(',','.'))
        if not math.isfinite(result) or not 0<=result<24:raise ValueError()
        return result
    except (ValueError,TypeError):raise DomainError('clock','Informe um horário válido, como 23:30.') from None

def hours_in_bed(bed,rise):
    minutes=(decimal_hour_to_minutes(rise)-decimal_hour_to_minutes(bed))%1440
    if not minutes:raise DomainError('clock','Horário de deitar igual ao de levantar; confira as respostas.')
    return minutes/60

def classify_psqi(total):
    if not 0<=total<=21 or int(total)!=total:raise DomainError('psqi','O PSQI deve ser inteiro de 0 a 21.')
    return 1 if total<=5 else 2

def classify_zarit(total):
    if not 0<=total<=88 or int(total)!=total:raise DomainError('zarit','O Zarit deve ser inteiro de 0 a 88.')
    return 1 if total<=20 else 2 if total<=40 else 3 if total<=60 else 4

def score_zarit(row,profile=None):
    values=[canonical_value(row,f,profile) for f in ZARIT_FIELDS]
    if any(pd.isna(v) for v in values):return ScoreResult(None,None,issues=('missing_item',))
    try:
        if any(float(v)!=int(float(v)) or not 0<=float(v)<=4 for v in values):raise ValueError()
        total=sum(int(float(v)) for v in values)
    except (ValueError,TypeError,OverflowError):return ScoreResult(None,None,issues=('invalid_item',))
    return ScoreResult(total,classify_zarit(total),tuple(int(float(v)) for v in values))

def canonical_value(row,field,profile):
    value=row.get(field)
    mappings=getattr(profile,'canonical_codes',{})
    mapping=mappings.get(field,{})
    if field in mappings and pd.notna(value):
        try:return mapping.get(str(int(float(value))),mapping.get(value))
        except (ValueError,TypeError):return value
    return value

PSQI_FREQUENCIES=('NAO_CONS','ACORD','PREC_LEV','NAO_RESP','TOS_RONC','FRIO','CALOR','SONHOS','DOR','DIF_DORM','QUA_SONO','FREQ_MED','DIF_ACOR','ANIMO')

def score_psqi(row,profile):
    if profile.psqi_rules.get('status')!='confirmed':return ScoreResult(None,None,issues=('psqi_rules_unconfirmed',))
    try:
        values={f:canonical_value(row,f,profile) for f in PSQI_FREQUENCIES}
        if any(pd.isna(v) or v=='' for v in values.values()):return ScoreResult(None,None,issues=('missing_item',))
        if any(float(v)!=int(float(v)) or not 0<=float(v)<=3 for v in values.values()):raise ValueError()
        values={f:int(float(v)) for f,v in values.items()}
        minutes=float(row.get('N_MIN'));duration=float(row.get('H_SONO'))
        if not math.isfinite(minutes) or minutes<0 or not math.isfinite(duration) or not 0<=duration<=24:raise ValueError()
        bed=hours_in_bed(row.get('H_DEIT'),row.get('H_LEV'))
        if duration>bed:raise ValueError()
        latency=0 if minutes<=15 else 1 if minutes<=30 else 2 if minutes<=60 else 3
        combined=lambda n:0 if n==0 else 1 if n<=2 else 2 if n<=4 else 3
        # Pitt duration table overlaps at 6 h; upper band includes 6, matching its 6–7 h entry.
        sleep_duration=0 if duration>7 else 1 if duration>=6 else 2 if duration>=5 else 3
        efficiency=100*duration/bed
        # NLM/NINDS C20357 explicitly resolves exact 85/75/65 percent boundaries.
        hse=0 if efficiency>=85 else 1 if efficiency>=75 else 2 if efficiency>=65 else 3
        disturbance=sum(values[f] for f in PSQI_FREQUENCIES[1:10])
        dist_score=0 if disturbance==0 else 1 if disturbance<=9 else 2 if disturbance<=18 else 3
        components=(values['QUA_SONO'],combined(latency+values['NAO_CONS']),sleep_duration,hse,dist_score,values['FREQ_MED'],combined(values['DIF_ACOR']+values['ANIMO']))
        total=sum(components)
        return ScoreResult(total,classify_psqi(total),components)
    except (ValueError,TypeError,DomainError,OverflowError):return ScoreResult(None,None,issues=('invalid_item',))

def compare_recorded_scores(df,profile):
    records=[]
    for i,row in df.iterrows():
        for name,scorer in [('ZARIT',score_zarit),('PSQI',score_psqi)]:
            result=scorer(row,profile);recorded=row.get(name)
            numeric=pd.to_numeric(pd.Series([recorded]),errors='coerce').iloc[0]
            flags=result.issues+(('invalid_recorded_score',) if pd.notna(recorded) and pd.isna(numeric) else ())
            records.append(dict(row_index=i,instrument=name,recorded=recorded,recalculated=result.total,difference=(result.total-float(numeric)) if result.total is not None and pd.notna(numeric) else None,issues='; '.join(flags)))
    return pd.DataFrame(records)
