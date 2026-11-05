import json
import pandas as pd
from tcc_analyzer.models import ComparisonSpec
from tcc_analyzer.profiles import load_updated_profile
from tcc_analyzer.ui.charts import build_figures


def example():
    return pd.DataFrame({'ID':[101,102,103,104],'NOME':['Nome privado A']*4,
                         'PSQI_G':[1,1,2,2],'PSQI':[2,3,8,None],
                         'ZARIT':[10,None,40,60],'ZARIT_CLASS':[1,None,2,3]})


def test_selected_comparison_only_and_complete_pairs():
    spec=ComparisonSpec('burden','PSQI_G','ZARIT')
    views=build_figures(example(),load_updated_profile(),(spec,))
    assert len(views)==1 and views[0].id=='burden'
    assert views[0].n_effective==3 and views[0].n_missing==1
    assert sum(len(trace.y) for trace in views[0].figure.data)==3
    serialized=views[0].figure.to_json()
    assert 'Nome privado' not in serialized
    assert 'NOME' not in serialized and '101' not in serialized


def test_proportions_use_complete_group_denominator():
    view=build_figures(example(),load_updated_profile(),(ComparisonSpec('classes','PSQI_G','ZARIT_CLASS'),))[0]
    assert view.n_effective==3
    sums={}
    for trace in view.figure.data:
        for label,value in zip(trace.y,trace.x):sums[label]=sums.get(label,0)+value
    assert sorted(sums.values())==[100,100]
    assert 'denominador' in view.summary.lower()


def test_scatter_has_only_paired_scores_and_no_regression():
    view=build_figures(example(),load_updated_profile(),(ComparisonSpec('scores','PSQI','ZARIT'),))[0]
    assert view.n_effective==2
    assert len(view.figure.data)==1
    trace=view.figure.data[0]
    assert trace.mode=='markers'
    assert list(trace.x)==[2,8] and list(trace.y)==[10,40]
    assert trace.customdata is None and trace.text is None


def test_missing_and_single_category_are_honest():
    data=example();data['PSQI_G']=1
    view=build_figures(data,load_updated_profile(),(ComparisonSpec('one','PSQI_G','ZARIT'),))[0]
    assert 'uma categoria' in view.summary.lower()
    data['ZARIT']=None
    assert build_figures(data,load_updated_profile(),(ComparisonSpec('empty','PSQI_G','ZARIT'),))==()
    assert build_figures(data,load_updated_profile(),())==()
