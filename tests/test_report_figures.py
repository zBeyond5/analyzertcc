import pandas as pd
import pytest
from tcc_analyzer.models import ComparisonSpec
from tcc_analyzer.profiles import load_updated_profile
from tcc_analyzer.report_figures import build_chart_data, render_figure


def sample():
    return pd.DataFrame({'PSQI_G':[1,1,2,2], 'ZARIT_CLASS':[1,2,2,3], 'PSQI':[2,3,8,9], 'ZARIT':[10,20,None,50], 'NOME':['PRIVATE-NAME']*4})


@pytest.mark.parametrize('outcome,predictor,kind',[('PSQI_G','ZARIT','box'),('PSQI_G','ZARIT_CLASS','bar'),('PSQI','ZARIT','scatter')])
def test_chart_pairs_and_private_local_png(outcome,predictor,kind):
    import matplotlib.pyplot as plt
    df=sample();chart=build_chart_data(df,load_updated_profile(),ComparisonSpec(kind,outcome,predictor))
    assert chart.kind==kind
    assert chart.n_effective==len(df[[outcome,predictor]].dropna())
    assert chart.n_missing==4-chart.n_effective
    assert 'PRIVATE-NAME' not in repr(chart)
    before=plt.get_fignums()
    png=render_figure(chart)
    assert png.startswith(b'\x89PNG') and len(png)>1000
    assert plt.get_fignums()==before
    if kind=='bar':
        assert sum(sum(s['counts']) for s in chart.series)==chart.n_effective
        assert 'denominador' in chart.caption.lower()


def test_empty_single_observation_and_long_labels():
    p=load_updated_profile();df=sample().iloc[:1]
    chart=build_chart_data(df,p,ComparisonSpec('one','PSQI_G','ZARIT'))
    assert 'ponto' in chart.caption and 'uma categoria' in chart.caption
    assert render_figure(chart)
    assert build_chart_data(sample().iloc[:0],p,ComparisonSpec('none','PSQI','ZARIT')) is None
