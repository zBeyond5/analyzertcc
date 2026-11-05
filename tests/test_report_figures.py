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


def test_identification_never_becomes_a_scatter_axis():
    df=sample();df['ID']=[1001,1002,1003,1004]
    assert build_chart_data(df,load_updated_profile(),ComparisonSpec('private','ID','ZARIT')) is None


def test_unknown_categories_remain_visually_distinct():
    from dataclasses import replace
    p=load_updated_profile()
    p=replace(p,variables=tuple(replace(v,labels={}) if v.name=='PSQI_G' else v for v in p.variables))
    chart=build_chart_data(sample(),p,ComparisonSpec('unknown','PSQI_G','ZARIT'))
    assert len(set(chart.categories))==2
    assert all('sem definição confirmada' in name for name in chart.categories)


def test_custom_labels_are_literal_not_math_commands():
    from dataclasses import replace
    p=load_updated_profile()
    p=replace(p,variables=tuple(replace(v,label=r'Preço $\notacommand$') if v.name=='ZARIT' else v for v in p.variables))
    chart=build_chart_data(sample(),p,ComparisonSpec('literal','PSQI','ZARIT'))
    assert render_figure(chart).startswith(b'\x89PNG')


def test_long_category_labels_do_not_overlap(monkeypatch):
    from dataclasses import replace
    from matplotlib.figure import Figure
    p=load_updated_profile()
    labels={i:f'Grupo {i} '+('categoria personalizada '*13) for i in range(1,5)}
    p=replace(p,variables=tuple(replace(v,labels=labels) if v.name=='ESCOL' else v for v in p.variables))
    df=pd.DataFrame({'ESCOL':[1,1,2,2,3,3,4,4],'ZARIT':[10,20,30,40,50,60,70,80]})
    original=Figure.savefig
    def check_and_save(fig,*args,**kwargs):
        fig.canvas.draw()
        boxes=sorted((label.get_window_extent(fig.canvas.get_renderer()) for label in fig.axes[0].get_yticklabels()),key=lambda b:b.y0)
        assert all(a.y1+2<=b.y0 for a,b in zip(boxes,boxes[1:]))
        return original(fig,*args,**kwargs)
    monkeypatch.setattr(Figure,'savefig',check_and_save)
    chart=build_chart_data(df,p,ComparisonSpec('long','ESCOL','ZARIT'))
    from PIL import Image
    from io import BytesIO
    png=render_figure(chart)
    image=Image.open(BytesIO(png))
    assert 12*145/72*min(495/image.width,540/image.height)>=9
