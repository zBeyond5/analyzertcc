"""Shared, session-local progress for the project menu and its five steps."""
import streamlit as st
from ..validation import analysis_validation_issues


def trusted_demo(state):
    from ..pipeline import DEMO_SHA256,UPDATED_DEMO_SHA256
    return bool(state.fictitious and state.prepared is not None and
                state.prepared.source_meta.source_sha256 in (DEMO_SHA256,UPDATED_DEMO_SHA256))


def progress_status(state):
    loaded=state.prepared is not None and len(state.prepared.data)>0
    valid=False
    if loaded:
        issues=analysis_validation_issues(state.prepared,state.profile)
        valid=not any(i.severity=='error' and not(trusted_demo(state) and i.code=='mapping_pending') for i in issues)
    analyzed=valid and state.artifacts is not None
    reviewed=analyzed and state.reviewed
    available=(True,loaded,valid,analyzed,reviewed)
    # A prepared link is not proof that the user has downloaded its file.
    completed=(loaded,valid,analyzed,reviewed,False)
    return available,completed


def _select(step):
    st.session_state.navigation=step


def render_navigation(state,steps):
    available,completed=progress_status(state)
    selected=st.session_state.get('navigation',steps[0])
    if selected not in steps:selected=steps[0]
    current=steps.index(selected)
    if not available[current]:
        current=next((i for i,done in enumerate(completed) if not done),0)
        selected=steps[current]
    st.session_state.navigation=selected

    with st.sidebar:
        st.caption('Projeto')
        for index,step in enumerate(steps):
            st.button(step,key=f'nav_side_{index}',width='stretch',
                      type='primary' if index==current else 'tertiary',
                      disabled=not available[index],on_click=_select,args=(step,))

    from .components import stepper
    stepper(current,steps,available,completed,_select)
    return selected
