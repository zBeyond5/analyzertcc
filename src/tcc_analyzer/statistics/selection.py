from dataclasses import dataclass
import numpy as np
import pandas as pd
from ..models import ComparisonSpec, DomainError

@dataclass(frozen=True)
class TestRecommendation:
    method: str
    alternatives: tuple[str, ...]
    reasons: tuple[str, ...]
    blocked: bool = False

METHODS = {'auto','fisher','chi_square','descriptive','welch_t','mann_whitney','welch_anova','kruskal','pearson','spearman'}

def default_comparisons():
    return (
        ComparisonSpec('primary_zarit', 'PSQI_G', 'ZARIT', 'primary', 'welch_t', 'Comparar a média da sobrecarga entre grupos de qualidade do sono.'),
        ComparisonSpec('primary_zarit_class', 'PSQI_G', 'ZARIT_CLASS', 'primary', 'auto', 'Examinar a associação entre classificações dos instrumentos.'),
        ComparisonSpec('complementary_psqi_zarit', 'PSQI', 'ZARIT', 'complementary', 'spearman', 'Examinar associação monotônica entre escores contínuos.'),
    )

def _variables(profile):
    return {**{v.name: v.kind for v in profile.variables}, 'ZARIT_CLASS': 'ordinal'}

def freeze_comparisons(comparisons, profile):
    variables = _variables(profile)
    if len({c.id for c in comparisons}) != len(comparisons):
        raise DomainError('comparison_ids', 'Cada cruzamento deve ter identificador distinto.')
    for c in comparisons:
        if c.outcome not in variables or c.predictor not in variables or c.outcome == c.predictor:
            raise DomainError('comparison_fields', 'Selecione duas variáveis distintas presentes no perfil.')
        if not c.rationale.strip() or c.method not in METHODS or c.family not in ('primary','complementary','exploratory'):
            raise DomainError('comparison_method', 'Informe família, método válido e justificativa do cruzamento.')
    return tuple(comparisons)

def recommend_test(df, comparison, profile):
    freeze_comparisons((comparison,), profile)
    if comparison.outcome not in df or comparison.predictor not in df:
        return TestRecommendation('descriptive', (), ('Coluna selecionada ausente.',), True)
    pair = df[[comparison.outcome, comparison.predictor]].replace('', np.nan).dropna()
    if len(pair) < 3:
        return TestRecommendation('descriptive', (), ('Poucos pares completos para inferência.',), True)
    kinds = _variables(profile)
    # As faixas de Zarit são tratadas como categorias neste cruzamento principal.
    cats = [field for field in pair if kinds[field] == 'categorical' or field == 'ZARIT_CLASS']
    if len(cats) == 2:
        table = pd.crosstab(pair.iloc[:,0], pair.iloc[:,1]).to_numpy()
        if min(table.shape) < 2:
            return TestRecommendation('descriptive', (), ('Apenas uma categoria observada.',), True)
        expected = np.outer(table.sum(axis=1), table.sum(axis=0))/table.sum()
        if table.shape == (2,2):
            method = 'fisher' if (expected < 5).any() else 'chi_square'
            return TestRecommendation(method, ('fisher','chi_square'), ('Frequências esperadas conferidas; observações devem ser independentes.',))
        if (expected < 1).any() or np.mean(expected < 5) > .2:
            return TestRecommendation('descriptive', (), ('Tabela RxC esparsa: somente descrição, sem p.',))
        return TestRecommendation('chi_square', (), ('Esperados atendem ao critério da tabela RxC.',))
    if len(cats) == 1:
        group = cats[0]
        sizes = pair.groupby(group, observed=True).size()
        if len(sizes) < 2 or sizes.min() < 2:
            return TestRecommendation('descriptive', (), ('Cada grupo necessita de ao menos duas observações.',), True)
        if len(sizes) == 2:
            return TestRecommendation('welch_t', ('welch_t','mann_whitney'), ('Welch compara médias; confirme independência, distribuição e influência de extremos. Mann–Whitney compara ordenação/distribuições.',))
        return TestRecommendation('welch_anova', ('welch_anova','kruskal'), ('Comparação de vários grupos; confirmar estimando e pressupostos.',))
    return TestRecommendation('spearman', ('spearman','pearson'), ('Spearman avalia associação monotônica/ordinal; Pearson exige relação linear e pressupostos confirmados.',))
