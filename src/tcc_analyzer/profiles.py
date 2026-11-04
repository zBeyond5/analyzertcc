from pathlib import Path
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
