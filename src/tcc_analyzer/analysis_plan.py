"""Perguntas de pesquisa e comparações pré-definidas, sem escolher por p."""
from .models import ComparisonSpec
from .statistics.selection import default_comparisons

QUESTIONS = {
    'burden': 'Sobrecarga e qualidade do sono',
    'support': 'Rede de apoio e qualidade do sono',
    'child_sleep': 'Sono da criança e qualidade do sono da mãe',
}


def build_default_plan(data, profile, selected_questions=('burden',)):
    comparisons = []
    if 'burden' in selected_questions:
        comparisons.extend(default_comparisons())
    for question, field in (('support', 'RED_APO'), ('child_sleep', 'ALT_SONO')):
        if question in selected_questions:
            comparisons.append(ComparisonSpec(question, 'PSQI_G', field))
    return tuple(c for c in comparisons if all(
        field in data and data[field].notna().any() for field in (c.outcome, c.predictor)))
