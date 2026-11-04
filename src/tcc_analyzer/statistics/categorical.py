import math
import numpy as np
from scipy import stats
from ..models import DomainError, EffectEstimate, TestResult

def analyze_contingency(table, *, method='auto', event_column=None, exposed_row=None):
    try:
        values = np.asarray(table, dtype=float)
    except (ValueError, TypeError):
        raise DomainError('counts', 'A tabela deve conter contagens inteiras não negativas.') from None
    if values.ndim != 2 or min(values.shape) < 2 or not np.isfinite(values).all() or (values < 0).any() or not np.equal(values, np.floor(values)).all():
        raise DomainError('counts', 'A tabela deve conter pelo menos duas linhas e colunas de contagens inteiras não negativas.')
    if method not in ('auto','fisher','chi_square','descriptive'):
        raise DomainError('method', 'Método categórico inválido.')
    n = int(values.sum())
    result = TestResult(method, n, assumptions=('Observações independentes; uma contribuição por participante na tabela.',))
    if not n or (values.sum(axis=0) == 0).any() or (values.sum(axis=1) == 0).any():
        result.warnings = ('Margem vazia: inferência não calculada.',)
        return result
    expected = np.outer(values.sum(axis=1), values.sum(axis=0)) / n
    binary = values.shape == (2,2)
    sufficient = bool((expected >= 5).all()) if binary else bool((expected >= 1).all() and np.mean(expected < 5) <= .2)
    chosen = ('chi_square' if sufficient else 'fisher' if binary else 'descriptive') if method == 'auto' else method
    result.method = chosen
    if chosen == 'descriptive' or (chosen == 'chi_square' and not sufficient) or (chosen == 'fisher' and not binary):
        result.warnings = ('Tabela esparsa ou método incompatível: apresentação descritiva sem p.',)
    elif chosen == 'fisher':
        answer = stats.fisher_exact(values.astype(np.int64), alternative='two-sided')
        result.statistic = float(answer.statistic) if np.isfinite(answer.statistic) else None
        result.p_value, result.p_kind = float(answer.pvalue), 'exact'
    else:
        answer = stats.chi2_contingency(values, correction=False)
        result.statistic, result.p_value, result.p_kind = float(answer.statistic), float(answer.pvalue), 'asymptotic'
    if binary and event_column is not None and exposed_row is not None:
        if event_column not in (0,1) or exposed_row not in (0,1):
            raise DomainError('orientation', 'Selecione a categoria de evento e a linha exposta da tabela 2×2.')
        a,b = values[exposed_row, event_column], values[exposed_row, 1-event_column]
        c,d = values[1-exposed_row, event_column], values[1-exposed_row, 1-event_column]
        rp = (a/(a+b))/(c/(c+d)) if c else None
        odds = a*d/(b*c) if b*c else None
        rp_ci = odds_ci = None
        reason = None
        if min(a,b,c,d) > 0:
            rp_se = math.sqrt(1/a-1/(a+b)+1/c-1/(c+d))
            or_se = math.sqrt(1/a+1/b+1/c+1/d)
            rp_ci = (math.exp(math.log(rp)-1.959963984540054*rp_se), math.exp(math.log(rp)+1.959963984540054*rp_se))
            odds_ci = (math.exp(math.log(odds)-1.959963984540054*or_se), math.exp(math.log(odds)+1.959963984540054*or_se))
        else:
            result.warnings += ('zero_cell_no_automatic_correction',)
            reason = 'IC logarítmico indisponível com célula zero; nenhuma correção automática aplicada.'
        result.effects = {
            'prevalence_ratio': EffectEstimate(float(rp) if rp is not None else None, rp_ci, 'Razão de prevalências; IC95% log-Katz aproximado', reason),
            'odds_ratio': EffectEstimate(float(odds) if odds is not None else None, odds_ci, 'Odds ratio amostral; IC95% log-Wald aproximado', reason),
        }
    return result
