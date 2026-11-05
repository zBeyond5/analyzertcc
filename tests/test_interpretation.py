import pytest
from tcc_analyzer.interpretation import interpret_p

@pytest.mark.parametrize('p,status',[(.04996,'significant'),(.05,'not_significant'),(.05004,'not_significant'),(None,'unavailable'),(float('nan'),'unavailable'),(-1,'unavailable'),(1.1,'unavailable'),(0,'significant'),(1,'not_significant')])
def test_strict_threshold(p,status):
    assert interpret_p(p,p_kind='exact')['status']==status

def test_display_and_no_inference():
    assert interpret_p(.04996,p_kind='exact')['p_display']!=interpret_p(.05004,p_kind='exact')['p_display']
    assert interpret_p(0,p_kind='not_computed')['status']=='unavailable'

def test_report_consistency_and_actual_score_origin():
    import pandas as pd
    from tcc_analyzer.profiles import load_updated_profile
    from tcc_analyzer.models import AnalysisResult,ComparisonSpec,TestResult
    from tcc_analyzer.reporting import build_tables
    r=AnalysisResult(ComparisonSpec('a','PSQI','ZARIT'),TestResult('spearman',10,p_value=.04996,p_kind='exact'))
    tables=build_tables((r,),(),load_updated_profile(),data=pd.DataFrame())
    assert 'Significativa pelo critério de 5%' in ' '.join(tables.narrative)
    assert 'pendente de confirmação' not in ' '.join(tables.notes)
    assert '0,05' in ' '.join(tables.notes)

def test_nextafter_display_preserves_side():
    import math
    p=math.nextafter(.05,0)
    assert float(interpret_p(p,p_kind='exact')['p_display'].replace(',','.'))<.05
