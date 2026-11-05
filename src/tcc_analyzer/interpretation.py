"""One definition of the AV3 significance threshold for UI and exports."""
import math
ALPHA=.05
LABELS={'significant':'Significativa pelo critério de 5%','not_significant':'Não atingiu o critério de 5%','unavailable':'Inferência não disponível'}

def interpret_p(p_value, *, p_kind):
    valid=p_value is not None and math.isfinite(p_value) and 0<=p_value<=1 and p_kind!='not_computed'
    status='unavailable' if not valid else 'significant' if p_value<ALPHA else 'not_significant'
    display='Não calculado'
    if valid:
        display='<0,001' if p_value<.001 else f'{p_value:.3f}'
        if round(p_value,3)==ALPHA and p_value!=ALPHA:display=repr(float(p_value))
        display=display.replace('.',',')
    explanation={'significant':'A comparação apresentou associação estatisticamente significativa pelo critério do projeto (p < 0,05). Isso não demonstra causa nem, por si só, importância prática.','not_significant':'A comparação não atingiu o critério de significância de 5%. Isso não prova ausência de associação.','unavailable':'Não foi possível calcular inferência para esta comparação. Confira o método e os avisos.'}[status]
    return dict(status=status,p_display=display,explanation=explanation)
