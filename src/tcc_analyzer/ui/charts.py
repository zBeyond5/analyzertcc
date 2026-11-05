"""Session-local figures from the same complete pairs used by the statistics."""
from dataclasses import dataclass
import html
import numpy as np
import pandas as pd
import plotly.graph_objects as go

PALETTE=('#216C72','#6788B1','#A77C48','#AC7679')
SHORT_LABELS={'PSQI_G':'Qualidade do sono','PSQI':'Pontuação do sono (PSQI)',
              'ZARIT':'Sobrecarga (Zarit)','ZARIT_CLASS':'Classificação da sobrecarga'}


@dataclass
class ChartView:
    id: str
    title: str
    figure: go.Figure
    n_effective: int
    n_missing: int
    summary: str


def _label(field,profile):
    return SHORT_LABELS.get(field,next((v.label for v in profile.variables if v.name==field),field))


def _category(field,value,profile):
    if field=='ZARIT_CLASS':
        return {1:'0–20',2:'21–40',3:'41–60',4:'61–88'}.get(value,str(value))
    labels=next((v.labels for v in profile.variables if v.name==field),{})
    return labels.get(value,f'Código {value:g}' if isinstance(value,(int,float)) else str(value))


def build_figures(data,profile,comparisons):
    """Only selected comparisons; figure payloads never receive identifying columns."""
    kinds={v.name:v.kind for v in profile.variables};kinds['ZARIT_CLASS']='categorical'
    views=[]
    for spec in comparisons:
        fields=(spec.outcome,spec.predictor)
        if not all(field in data for field in fields):continue
        pair=data[list(fields)].replace('',np.nan).dropna()
        if pair.empty:continue
        categorical=[field for field in fields if kinds.get(field)=='categorical']
        # Escape category wording because Plotly labels may interpret HTML.
        labels={field:html.escape(_label(field,profile)) for field in fields}
        fig=go.Figure()
        title=f'{_label(spec.predictor,profile)} e {_label(spec.outcome,profile).lower()}'
        summary=f'{len(pair)} respostas completas; {len(data)-len(pair)} sem par completo.'
        if len(categorical)==2:
            groups=sorted(pair[spec.outcome].unique())
            categories=sorted(pair[spec.predictor].unique())
            names=[html.escape(_category(spec.outcome,g,profile)) for g in groups]
            totals=[int((pair[spec.outcome]==g).sum()) for g in groups]
            for index,category in enumerate(categories):
                counts=[int(((pair[spec.outcome]==g)&(pair[spec.predictor]==category)).sum()) for g in groups]
                fig.add_trace(go.Bar(name=html.escape(_category(spec.predictor,category,profile)),
                    y=names,x=[100*count/total for count,total in zip(counts,totals)],
                    orientation='h',marker_color=PALETTE[index%len(PALETTE)],
                    customdata=list(zip(counts,totals)),
                    hovertemplate='%{y}<br>%{x:.1f}% (%{customdata[0]} de %{customdata[1]})<extra>%{fullData.name}</extra>'))
            fig.update_layout(barmode='stack',xaxis_title='Respostas válidas (%)',yaxis_title=labels[spec.outcome],legend_title_text=labels[spec.predictor])
            fig.update_xaxes(range=[0,100],ticksuffix='%')
            summary+=' Percentuais com denominador de respostas completas em cada grupo.'
            if len(groups)==1 or len(categories)==1:summary+=' Há apenas uma categoria observada em uma das variáveis; leitura descritiva.'
        elif len(categorical)==1:
            group=categorical[0];number=next(field for field in fields if field!=group)
            groups=sorted(pair[group].unique())
            for index,category in enumerate(groups):
                values=pd.to_numeric(pair.loc[pair[group]==category,number]).tolist()
                name=html.escape(_category(group,category,profile))
                fig.add_trace(go.Box(y=values,name=name,marker_color=PALETTE[index%len(PALETTE)],
                                     boxpoints='outliers',hovertemplate='%{y}<extra>%{fullData.name}</extra>'))
            fig.update_layout(xaxis_title=labels[group],yaxis_title=labels[number],showlegend=False)
            summary+=' As caixas mostram a mediana e os 50% centrais das respostas.'
            if len(groups)==1:summary+=' Há apenas uma categoria observada; leitura descritiva.'
        else:
            fig.add_trace(go.Scatter(x=pd.to_numeric(pair[spec.outcome]).tolist(),
                y=pd.to_numeric(pair[spec.predictor]).tolist(),mode='markers',
                marker={'color':PALETTE[0],'size':9,'opacity':.7},
                hovertemplate=f'{labels[spec.outcome]}: %{{x}}<br>{labels[spec.predictor]}: %{{y}}<extra></extra>'))
            fig.update_layout(xaxis_title=labels[spec.outcome],yaxis_title=labels[spec.predictor],showlegend=False)
            summary+=' Cada ponto representa um par de pontuações; sem linha de regressão.'
        fig.update_layout(template=None,height=360,margin={'l':12,'r':12,'t':12,'b':12},
                          paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
                          legend={'orientation':'h','y':-0.25},font={'family':'sans-serif'})
        views.append(ChartView(spec.id,title,fig,len(pair),len(data)-len(pair),summary))
    return tuple(views)


def render_charts(state):
    import streamlit as st
    if state.artifacts is None or state.prepared is None:return
    views=build_figures(state.prepared.data,state.profile,tuple(result.spec for result in state.artifacts.results))
    if not views:
        st.info('Não há pares completos para desenhar os gráficos desta análise. As tabelas continuam disponíveis.')
        return
    by_id={view.id:view for view in views}
    identifier=st.selectbox('Visualização',list(by_id),format_func=lambda key:by_id[key].title,key='result_chart')
    selected=by_id[identifier]
    st.plotly_chart(selected.figure,width='stretch',theme='streamlit',key='chart_'+selected.id,
                    on_select='ignore',config={'displayModeBar':False,'scrollZoom':False,'locale':'pt-BR'},
                    alt=selected.summary)
    st.caption(selected.summary)
    st.caption('A associação entre respostas não demonstra causa.')
