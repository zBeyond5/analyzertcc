"""Session-local figures from the same complete pairs used by the statistics."""
from dataclasses import dataclass
import html
import plotly.graph_objects as go

from ..report_figures import PALETTE, build_chart_data
from ..presentation import field_title


@dataclass
class ChartView:
    id: str
    title: str
    figure: go.Figure
    n_effective: int
    n_missing: int
    summary: str


def build_figures(data,profile,comparisons):
    views=[]
    for spec in comparisons:
        chart=build_chart_data(data,profile,spec)
        if chart is None:continue
        fig=go.Figure()
        if chart.kind=='bar':
            for index,series in enumerate(chart.series):
                fig.add_trace(go.Bar(name=html.escape(series['name']),y=[html.escape(c) for c in chart.categories],
                    x=series['percentages'],orientation='h',marker_color=PALETTE[index%len(PALETTE)],
                    customdata=list(zip(series['counts'],series['totals'])),
                    hovertemplate='%{y}<br>%{x:.1f}% (%{customdata[0]} de %{customdata[1]})<extra>%{fullData.name}</extra>'))
            fig.update_layout(barmode='stack')
            fig.update_xaxes(range=[0,100],ticksuffix='%')
        elif chart.kind=='box':
            for index,series in enumerate(chart.series):
                name=html.escape(series['name'])
                if len(series['values'])<2:
                    fig.add_trace(go.Scatter(x=[name]*len(series['values']),y=series['values'],name=name,mode='markers',marker_color=PALETTE[index%len(PALETTE)]))
                else:
                    fig.add_trace(go.Box(y=series['values'],name=name,marker_color=PALETTE[index%len(PALETTE)],boxpoints='outliers',hovertemplate='%{y}<extra>%{fullData.name}</extra>'))
            fig.update_layout(showlegend=False)
        else:
            series=chart.series[0]
            fig.add_trace(go.Scatter(x=series['x'],y=series['y'],mode='markers',marker={'color':PALETTE[0],'size':9,'opacity':.7},hovertemplate='%{x}<br>%{y}<extra></extra>'))
            fig.update_layout(showlegend=False)
        fig.update_layout(xaxis_title=html.escape(chart.x_title),yaxis_title=html.escape(chart.y_title),
                          template=None,height=360,margin={'l':12,'r':12,'t':12,'b':12},
                          paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
                          legend={'orientation':'h','y':-0.25},font={'family':'sans-serif'})
        title=f'{field_title(spec.outcome,profile)} e {field_title(spec.predictor,profile)}'
        views.append(ChartView(spec.id,title,fig,chart.n_effective,chart.n_missing,chart.caption))
    return tuple(views)


def render_charts(state):
    import streamlit as st
    if state.artifacts is None or state.prepared is None:return
    from ..analysis_population import select_population
    population=select_population(state.prepared.data,state.profile)
    views=build_figures(population.data,state.profile,tuple(result.spec for result in state.artifacts.results))
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
