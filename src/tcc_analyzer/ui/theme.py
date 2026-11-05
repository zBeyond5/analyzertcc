"""Static local styles shared by local and cloud entry points."""
from pathlib import Path
import streamlit as st

STYLES_PATH=Path(__file__).with_name('styles.css')

def apply_theme():
    try:css=STYLES_PATH.read_text(encoding='utf-8')
    except OSError:
        st.caption('A aparência personalizada não está disponível. Você pode continuar usando o aplicativo.')
        return
    dark=st.context.theme.type=='dark'
    css=css.replace('__ON_PRIMARY__','#0F1B24' if dark else '#FFFFFF').replace('__ACCENT__','#86CDD1' if dark else '#216C72').replace('__TEXT__','#E8F1F2' if dark else '#203B43')
    st.markdown('<style>'+css+'</style>',unsafe_allow_html=True)
