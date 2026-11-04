import pandas as pd
import numpy as np
from .models import ValidationIssue,ValidationReport,PreparedDataset,Transformation
from .scales import score_zarit,classify_psqi,hours_in_bed

def validate_dataset(df,profile):
    issues=[]
    def add(row,field,raw,code,severity,message):issues.append(ValidationIssue(row,field,raw,code,severity,message))
    for v in profile.variables:
        if v.name not in df:
            add(None,v.name,None,'missing_column','error','Coluna obrigatória ausente.');continue
        if v.mapping_status=='pending':add(None,v.name,None,'mapping_pending','error','Legenda não confirmada: usar códigos neutros apenas na demonstração.')
        for i,x in df[v.name].items():
            if pd.isna(x) or x=='':
                add(i,v.name,None,'missing','warning','Resposta ausente; sem imputação.');continue
            if v.kind in ('numeric','integer','ordinal','categorical'):
                try:
                    n=float(str(x).replace(',','.'))
                    if not np.isfinite(n):raise ValueError()
                    if v.kind!='numeric' and n!=int(n):raise ValueError()
                except (ValueError,TypeError):
                    add(i,v.name,x,'invalid_number','error','Valor numérico inválido.');continue
                if v.allowed_values is not None and n not in v.allowed_values:add(i,v.name,x,'unknown_category','error','Código ou resposta fora dos valores permitidos.')
    if 'ID' in df:
        for i in df.index[df.ID.duplicated(keep=False)]:add(i,'ID',df.at[i,'ID'],'duplicate_id','error','ID repetido; confira os registros.')
    for i,row in df.iterrows():
        try:
            if pd.notna(row.get('PSQI')) and pd.notna(row.get('PSQI_G')) and classify_psqi(float(row.PSQI))!=float(row.PSQI_G):add(i,'PSQI_G',row.PSQI_G,'psqi_discrepancy','error','Classificação PSQI_G difere do ponto de corte do PSQI informado.')
        except (ValueError,TypeError):pass
        z=score_zarit(row,profile)
        if z.total is not None and pd.notna(row.get('ZARIT')) and float(row.ZARIT)!=z.total:add(i,'ZARIT',row.ZARIT,'zarit_discrepancy','error','Total Zarit informado difere da soma dos itens.')
        if all(pd.notna(row.get(c)) for c in ('H_DEIT','H_LEV','H_SONO')):
            try:
                if not 0<float(row.H_SONO)<=hours_in_bed(float(row.H_DEIT),float(row.H_LEV)):raise ValueError()
            except (ValueError,TypeError):add(i,'H_SONO',row.H_SONO,'invalid_sleep_hours','error','Confira horários decimais e horas de sono: duração incompatível com horas na cama.')
        if pd.notna(row.get('IDADE_M')):
            try:
                if float(row.IDADE_M)<18:add(i,'IDADE_M',row.IDADE_M,'eligibility','warning','Idade abaixo do critério de 18 anos do projeto; conferir elegibilidade.')
            except (ValueError,TypeError):pass
    return ValidationReport(tuple(issues))

def prepare_dataset(imported,profile,csv_options=None):
    df=imported.raw.copy(deep=True);changes=[]
    for v in profile.variables:
        if v.name not in df or v.kind=='text' or v.name=='ID':continue
        original=df[v.name].copy()
        vals=original.map(lambda x: str(x).replace(',','.') if pd.notna(x) and x!='' else np.nan)
        converted=pd.to_numeric(vals,errors='coerce')
        # Valores não numéricos ficam visíveis para validação, nunca viram missing silenciosamente.
        invalid=converted.isna() & original.notna() & original.ne('')
        df[v.name]=converted.astype(object) if invalid.any() else converted
        df.loc[invalid,v.name]=original[invalid]
        for i in df.index:
            if isinstance(original.at[i],str) and not invalid.at[i]:changes.append(Transformation(i,v.name,original.at[i],df.at[i,v.name],'Conversão numérica em cópia'))
    if all(f in df for f in ('ZARIT',)):
        df['ZARIT_CLASS']=[score_zarit(row,profile).category for _,row in df.iterrows()]
    report=validate_dataset(df,profile)
    return PreparedDataset(df,imported.meta,tuple(changes),report)
