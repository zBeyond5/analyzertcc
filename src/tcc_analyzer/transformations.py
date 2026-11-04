import pandas as pd
from .models import DomainError

def _same(a,b):return (pd.isna(a) and pd.isna(b)) or a==b

def apply_changes(df,changes,*,confirmed):
    if not confirmed:raise DomainError('confirmation','Confirme as correções antes de aplicar.')
    result=df.copy(deep=True)
    for c in changes:
        if not c.reason.strip() or c.field not in result or c.row_index not in result.index or not _same(result.at[c.row_index,c.field],c.before):
            raise DomainError('change','A correção não corresponde ao valor atual ou não tem justificativa.')
        try:result.at[c.row_index,c.field]=c.after
        except (ValueError,TypeError):
            result[c.field]=result[c.field].astype(object);result.at[c.row_index,c.field]=c.after
    return result

def undo_changes(df,changes):
    from .models import Transformation
    return apply_changes(df,tuple(Transformation(c.row_index,c.field,c.after,c.before,'Desfazer: '+c.reason) for c in reversed(changes)),confirmed=True)
