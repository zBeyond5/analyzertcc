"""Presentation only: no statistical decisions and no uploaded HTML."""
import pandas as pd
import streamlit as st


def card(key):
    return st.container(border=True,key=key)


def metric_row(metrics):
    for column,(label,value,help_text) in zip(st.columns(len(metrics)),metrics):
        column.metric(label,value,help=help_text)


def input_summary(frame):
    cells=frame.size
    empty=sum(pd.isna(value) or isinstance(value,str) and not value.strip() for row in frame.itertuples(index=False,name=None) for value in row)
    return dict(rows=len(frame),columns=len(frame.columns),empty_percent=100*empty/cells if cells else 0.0)


def stepper(current,steps,available,completed,on_select):
    names=[step.split(' · ',1)[-1] for step in steps]
    following=f' · Próximo: {names[current+1]}' if current<len(steps)-1 else ''
    st.caption(f'Etapa atual: {current+1} de {len(steps)} · {names[current]}{following}')
    with st.container(key='project_stepper',horizontal=True,gap='small'):
        for index,step in enumerate(steps):
            done=completed[index] and index!=current
            label=('✓ ' if done else '')+step
            hint='Etapa atual' if index==current else 'Etapa concluída. Você pode voltar.' if done else 'Próxima etapa' if available[index] else 'Conclua as etapas anteriores para abrir.'
            st.button(label,key=f'nav_top_{index}',width=152,type='primary' if index==current else 'secondary',disabled=not available[index],help=hint,on_click=on_select,args=(step,))
    st.progress(current/(len(steps)-1),text=None)
