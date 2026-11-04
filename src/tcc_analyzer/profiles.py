from pathlib import Path
from dataclasses import replace
import yaml
from .models import ResearchProfile,VariableSpec,DomainError

PROFILE_PATH=Path(__file__).resolve().parents[2]/'configs/profiles/tea_maternal_sleep_v1.yaml'

def load_profile(path=PROFILE_PATH):
    try:
        d=yaml.safe_load(Path(path).read_text(encoding='utf-8'))
        variables=tuple(VariableSpec(**{**v,'allowed_values':tuple(v['allowed_values']) if v.get('allowed_values') is not None else None}) for v in d['variables'])
        if len({v.name for v in variables})!=len(variables):raise ValueError()
        return ResearchProfile(d['id'],str(d['version']),variables,d.get('psqi_rules',{'status':'pending'}),d.get('derived_rules',{}))
    except Exception:raise DomainError('profile','O perfil de pesquisa é inválido.') from None

def dictionary_frame(profile):
    import pandas as pd
    return pd.DataFrame([{'Campo':v.name,'Rótulo':v.label,'Tipo':v.kind,'Códigos':str(v.allowed_values or ''),'Legenda':'; '.join(f'{k}: {val}' for k,val in v.labels.items()),'Confirmação':v.mapping_status,'Exportar':v.export_default} for v in profile.variables])

def confirm_codebook(profile,entries,reference):
    if len(reference.strip())<10:raise DomainError('reference','Informe a referência da conferência.')
    allowed={v.name for v in profile.variables if v.kind=='categorical'};by_field={}
    for row in entries:
        field=str(row.get('Campo',''));label=str(row.get('Legenda','')).strip()
        try:
            code=float(row.get('Código'))
            if code!=int(code):raise ValueError()
            code=int(code)
        except (TypeError,ValueError,OverflowError):raise DomainError('codes','Informe códigos inteiros válidos.') from None
        if field not in allowed or not label or 'não confirmada' in label:raise DomainError('labels','Preencha campos e legendas confirmadas para cada código.')
        if code in by_field.setdefault(field,{}):raise DomainError('codes','Há códigos repetidos para o mesmo campo.')
        by_field[field][code]=label
    variables=[]
    for v in profile.variables:
        if v.kind=='categorical':
            labels=by_field.get(v.name)
            if not labels:raise DomainError('labels','Cada campo categórico precisa de sua legenda.')
            if v.name=='PSQI_G' and set(labels)!={1,2}:raise DomainError('psqi','PSQI_G permite somente 1 e 2.')
            if v.name=='PSQI_G':labels=v.labels
            variables.append(replace(v,mapping_status='confirmed',labels=labels,allowed_values=tuple(sorted(labels))))
        else:variables.append(v)
    return replace(profile,variables=tuple(variables),confirmation=reference.strip())
