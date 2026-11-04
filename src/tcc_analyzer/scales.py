import math
import pandas as pd
from .models import DomainError,ScoreResult

ZARIT_FIELDS=('TEMP_VOC','ESTRES','IRRIT','AFET_REL','MEDO','DEPENDE','TENSO','SAU_FIS','PRIV','VID_SOC','DESCONF','UNICA_P','DINHEIRO','CAP_CUI','CONTROLE','INCAPAZ','FAZ_MAIS','CUID_MEL','MAIS_AJUD','EXAUSTO','CONST','UNIC_RESP')

def decimal_hour_to_minutes(value):
    try:v=float(value)
    except (TypeError,ValueError):raise DomainError('clock','Horário inválido; informe horas decimais, como 23,5.') from None
    if not math.isfinite(v) or not 0<=v<24:raise DomainError('clock','Horário fora do intervalo de 0 a menos de 24 horas.')
    return round(v*60)

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
    values=[row.get(f) for f in ZARIT_FIELDS]
    if any(pd.isna(v) for v in values):return ScoreResult(None,None,issues=('missing_item',))
    try:
        if any(float(v)!=int(float(v)) or not 0<=float(v)<=4 for v in values):raise ValueError()
        total=sum(int(float(v)) for v in values)
    except (ValueError,TypeError):return ScoreResult(None,None,issues=('invalid_item',))
    return ScoreResult(total,classify_zarit(total),tuple(int(float(v)) for v in values))

def score_psqi(row,profile):
    # A fonte não traz o manual completo; não inferir algoritmo clínico de terceiros.
    return ScoreResult(None,None,issues=('psqi_rules_unconfirmed',))

def compare_recorded_scores(df,profile):
    records=[]
    for i,row in df.iterrows():
        for name,scorer in [('ZARIT',score_zarit),('PSQI',score_psqi)]:
            result=scorer(row,profile);recorded=row.get(name)
            records.append(dict(row_index=i,instrument=name,recorded=recorded,recalculated=result.total,difference=(result.total-float(recorded)) if result.total is not None and pd.notna(recorded) else None,issues='; '.join(result.issues)))
    return pd.DataFrame(records)
