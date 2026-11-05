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

    st.markdown('''<style>
    .st-key-project_stepper button{min-height:4.1rem;border-radius:.8rem;font-weight:600;line-height:1.35}
    .st-key-project_stepper button:focus-visible{outline:3px solid #A57530;outline-offset:3px}
    .research-progress{height:3px;border-radius:3px;background:rgba(100,130,140,.16);margin:0 0 1rem}
    .research-progress span{display:block;height:100%;border-radius:inherit;background:#38888A}
    @media(max-width:600px){.st-key-project_stepper button{padding:.6rem .12rem;font-size:.75rem;min-height:3.6rem}}
    </style>''',unsafe_allow_html=True)
    names=[step.split(' · ',1)[-1] for step in steps]
    following=f' · Próximo: {names[current+1]}' if current<len(steps)-1 else ''
    st.caption(f'Etapa atual: {current+1} de {len(steps)} · {names[current]}{following}')
    with st.container(key='project_stepper',horizontal=True,gap='small'):
        for index,step in enumerate(steps):
            is_done=completed[index] and index!=current
            label=('✓ ' if is_done else '')+steps[index]
            help_text='Etapa atual' if index==current else 'Etapa concluída. Você pode voltar.' if is_done else 'Próxima etapa' if available[index] else 'Conclua as etapas anteriores para abrir.'
            st.button(label,key=f'nav_top_{index}',width=124,
                          type='primary' if index==current else 'secondary',
                          disabled=not available[index],help=help_text,
                          on_click=_select,args=(steps[index],))
    st.markdown(f'<div class="research-progress" aria-hidden="true"><span style="width:{100*current/(len(steps)-1):.1f}%"></span></div>',unsafe_allow_html=True)
    return selected
