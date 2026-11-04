import numpy as np
import pandas as pd
from ..models import DomainError, SummaryResult

THERAPY_FIELDS = {'FISIO', 'FONO', 'TER_OCUP', 'PSI', 'PSICOP'}

def describe(df, fields, profile):
    variables = {v.name: v for v in profile.variables}
    summaries = []
    for field in fields:
        if field not in df:
            raise DomainError('missing_column', 'Uma variável selecionada não está no banco.')
        variable = variables.get(field)
        kind = variable.kind if variable else 'categorical' if field == 'ZARIT_CLASS' else None
        if kind is None:
            raise DomainError('unknown_variable', 'Variável sem definição no perfil.')
        values = df[field].replace('', np.nan).dropna()
        n_total, n_valid = len(df), len(values)
        metrics, counts = {}, {}
        denominator = 'Respostas válidas da variável'
        if kind in ('numeric', 'integer'):
            numeric = pd.to_numeric(values, errors='coerce')
            if numeric.isna().any() or not np.isfinite(numeric).all():
                raise DomainError('invalid_numeric', 'Corrija valores numéricos inválidos antes da análise.')
            metrics = {key: None for key in ('mean', 'sd', 'median', 'q1', 'q3', 'min', 'max')}
            if n_valid:
                metrics.update(mean=float(numeric.mean()), median=float(numeric.median()),
                               q1=float(numeric.quantile(.25)), q3=float(numeric.quantile(.75)),
                               min=float(numeric.min()), max=float(numeric.max()))
                metrics['sd'] = float(numeric.std(ddof=1)) if n_valid > 1 else None
        else:
            counts = {key: int(count) for key, count in values.value_counts(sort=False).items()}
            denominator_n = n_total if field in THERAPY_FIELDS else n_valid
            if field in THERAPY_FIELDS:
                denominator = 'Total de participantes; terapias são respostas múltiplas'
            metrics['percentages'] = {key: 100 * count / denominator_n for key, count in counts.items()} if denominator_n else {}
        summaries.append(SummaryResult(field, n_total, n_valid, n_total-n_valid, metrics, counts, denominator))
    return tuple(summaries)
