"""Shared, non-identifying complete pairs for web and printed figures."""
from dataclasses import dataclass
from io import BytesIO
import textwrap
import threading
import pandas as pd
from .presentation import complete_pairs,field_title,category_titles

PALETTE=('#216C72','#6788B1','#A77C48','#AC7679','#767F88')
_RENDER_LOCK=threading.Lock()


@dataclass(frozen=True)
class ChartData:
    id: str
    kind: str
    x_title: str
    y_title: str
    categories: tuple
    series: tuple
    n_effective: int
    n_missing: int
    caption: str


def build_chart_data(data,profile,spec):
    kinds={v.name:v.kind for v in profile.variables};kinds['ZARIT_CLASS']='categorical'
    if any(kinds.get(c)=='text' for c in (spec.outcome,spec.predictor)):return None
    pair=complete_pairs(data,spec)
    if pair.empty:return None
    cats=[c for c in pair if kinds.get(c)=='categorical']
    caption=f'{len(pair)} respostas completas; {len(data)-len(pair)} sem par completo.'
    if len(cats)==2:
        outcomes=tuple(sorted(pair[spec.outcome].unique()))
        predictors=tuple(sorted(pair[spec.predictor].unique()))
        categories=category_titles(spec.outcome,outcomes,profile)
        totals=tuple(int((pair[spec.outcome]==g).sum()) for g in outcomes)
        series=[]
        for value,name in zip(predictors,category_titles(spec.predictor,predictors,profile)):
            counts=tuple(int(((pair[spec.outcome]==g)&(pair[spec.predictor]==value)).sum()) for g in outcomes)
            series.append(dict(name=name,counts=counts,totals=totals,
                               percentages=tuple(100*n/t for n,t in zip(counts,totals))))
        caption+=' As barras mostram percentuais; o denominador é o total de respostas completas de cada grupo, indicado entre parênteses.'
        if len(outcomes)==1 or len(predictors)==1:caption+=' Há apenas uma categoria observada; leitura descritiva.'
        return ChartData(spec.id,'bar','Respostas completas (%)',field_title(spec.outcome,profile),categories,tuple(series),len(pair),len(data)-len(pair),caption)
    if len(cats)==1:
        group=cats[0];number=next(c for c in pair if c!=group)
        order=spec.group_order or tuple(sorted(pair[group].unique()))
        categories=category_titles(group,order,profile)
        series=tuple(dict(name=name,values=tuple(pd.to_numeric(pair.loc[pair[group]==v,number]).astype(float))) for v,name in zip(order,categories))
        caption+=' As caixas mostram a mediana e os 50% centrais das respostas. Grupos com menos de duas respostas são apresentados como pontos.'
        if len(order)==1:caption+=' Há apenas uma categoria observada; leitura descritiva.'
        return ChartData(spec.id,'box',field_title(group,profile),field_title(number,profile),categories,series,len(pair),len(data)-len(pair),caption)
    caption+=' Cada ponto representa um par de pontuações; sem linha de regressão.'
    series=(dict(x=tuple(pd.to_numeric(pair[spec.outcome]).astype(float)),y=tuple(pd.to_numeric(pair[spec.predictor]).astype(float))),)
    return ChartData(spec.id,'scatter',field_title(spec.outcome,profile),field_title(spec.predictor,profile),(),series,len(pair),len(data)-len(pair),caption)


def render_figure(chart):
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib import rc_context
    wrap=lambda value,width=42:'\n'.join(textwrap.wrap(str(value),width=width,break_long_words=True))
    with _RENDER_LOCK,rc_context({'font.family':'DejaVu Sans','font.size':10,'axes.unicode_minus':False}):
        longest=max([len(chart.x_title),len(chart.y_title)]+[len(str(c)) for c in chart.categories])
        height=max(4.2,2.7+.32*len(chart.categories)+.16*(longest//42))
        if chart.kind=='bar':height+=.25*len(chart.series)
        fig=Figure(figsize=(7.4,height),layout='constrained');FigureCanvasAgg(fig)
        ax=fig.add_subplot(111)
        try:
            if chart.kind=='scatter':
                s=chart.series[0];ax.scatter(s['x'],s['y'],color=PALETTE[0],s=30,alpha=.7)
                ax.set_xlabel(wrap(chart.x_title));ax.set_ylabel(wrap(chart.y_title))
            elif chart.kind=='box':
                for i,s in enumerate(chart.series):
                    if len(s['values'])>=2:
                        box=ax.boxplot([s['values']],positions=[i],orientation='horizontal',widths=.5,patch_artist=True,showfliers=True)
                        box['boxes'][0].set(facecolor=PALETTE[i%len(PALETTE)],alpha=.3)
                        box['medians'][0].set(color='#23343B',linewidth=2)
                    else:ax.scatter(s['values'],[i]*len(s['values']),color=PALETTE[i%len(PALETTE)])
                ax.set_yticks(range(len(chart.series)),[wrap(s['name'])+f" ({len(s['values'])})" for s in chart.series])
                ax.set_xlabel(wrap(chart.y_title));ax.set_ylabel(wrap(chart.x_title))
            else:
                left=[0.]*len(chart.categories)
                for i,s in enumerate(chart.series):
                    ax.barh(range(len(chart.categories)),s['percentages'],left=left,label=wrap(s['name']),color=PALETTE[i%len(PALETTE)],hatch=('','//','..','xx','--')[i%5],edgecolor='white')
                    left=[a+b for a,b in zip(left,s['percentages'])]
                totals=chart.series[0]['totals']
                ax.set_yticks(range(len(chart.categories)),[wrap(c)+f' ({n})' for c,n in zip(chart.categories,totals)])
                ax.set_xlim(0,100);ax.set_xlabel(chart.x_title);ax.set_ylabel(wrap(chart.y_title))
                ax.legend(loc='upper center',bbox_to_anchor=(.5,-.2),frameon=False,fontsize=9)
            ax.spines[['top','right']].set_visible(False)
            ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
            output=BytesIO();fig.savefig(output,format='png',dpi=145,bbox_inches='tight',pad_inches=.15,metadata={'Software':'Análise Bivariada'})
            return output.getvalue()
        finally:fig.clear()
