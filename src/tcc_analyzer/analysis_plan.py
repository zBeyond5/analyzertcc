"""Perguntas de pesquisa e comparações pré-definidas, sem escolher por p."""
from .models import ComparisonSpec
from .statistics.selection import default_comparisons

QUESTIONS = {
    'burden': 'Sobrecarga e qualidade do sono',
    'support': 'Rede de apoio e qualidade do sono',
    'child_sleep': 'Sono da criança e qualidade do sono da mãe',
}


MATERNAL=('IDADE_M','SIT_CONJ','ESCOL','RENDA','RED_APO','FILHOS','TRAB_NOT','DOENCA','ANTIDEP','ANSIED','DEPRE')
CHILD=('IDADE_C','SEXO','TEMP_TEA','ACOMP_TEP','FISIO','FONO','TER_OCUP','PSI','PSICOP','FREQ_TEP','ALT_SONO','DESP_NOT','CHORO','SUPERV')

def question_groups(profile):
    labels={v.name:v.label for v in profile.variables}
    def group(fields):
        return {('support' if f=='RED_APO' else 'child_sleep' if f=='ALT_SONO' else 'factor_'+f):labels[f] for f in fields if f in labels}
    return dict(principal={'burden':QUESTIONS['burden']},mae=group(MATERNAL),crianca=group(CHILD))

def build_default_plan(data, profile, selected_questions=('burden',)):
    comparisons=list(default_comparisons()) if 'burden' in selected_questions else []
    for field in MATERNAL+CHILD:
        key='support' if field=='RED_APO' else 'child_sleep' if field=='ALT_SONO' else 'factor_'+field
        if key in selected_questions:
            comparisons.append(ComparisonSpec(key,'PSQI_G',field))
    return tuple(c for c in comparisons if all(field in data and data[field].notna().any() for field in (c.outcome,c.predictor)))
