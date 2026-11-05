"""A quiet, one-question-at-a-time worksheet assistant."""
from copy import deepcopy
from datetime import time
from pathlib import Path
import pandas as pd
import streamlit as st
from ..data_entry import input_variables,new_participant,update_categories,remap_rows,build_input_workbook
from ..models import DomainError
from ..profiles import load_updated_profile


def _builder():
    if 'sheet_builder' not in st.session_state:
        profile=load_updated_profile()
        st.session_state.sheet_builder={'profile':profile,'base_profile':profile,'rows':[],'draft':{},'question':0,'phase':'categories','revision':0,'undo':None,'fictitious':False}
    return st.session_state.sheet_builder


def _move(builder, phase):
    builder['phase']=phase
    st.rerun()


def _categories(builder, on_change=None):
    profile=builder['profile']
    categorical=[v for v in input_variables(profile) if v.labels]
    with st.expander('Personalizar categorias'):
        field=st.selectbox('Pergunta',categorical,format_func=lambda v:v.label,key='builder_category_field')
        entries=pd.DataFrame([{'Código':code,'Significado':label,'original_code':code} for code,label in field.labels.items()])
        changed=st.data_editor(entries,hide_index=True,num_rows='dynamic',column_config={'original_code':None},key=f'category_editor_{field.name}_{builder["revision"]}',width='stretch')
        confirm=st.checkbox('Aplicar também às respostas já preenchidas',key=f'category_confirm_{builder["revision"]}') if builder['rows'] or builder['draft'] else True
        left,right=st.columns(2)
        if left.button('Salvar categorias',key='save_categories'):
            if not confirm:st.warning('Confirme a atualização das respostas para salvar.');return
            new_profile,mapping=update_categories(profile,field.name,changed.to_dict('records'))
            rows=remap_rows(builder['rows'],field.name,mapping,new_profile)
            draft=remap_rows([builder['draft']],field.name,mapping,new_profile)[0] if builder['draft'] else {}
            builder['undo']=(profile,deepcopy(builder['rows']),deepcopy(builder['draft']))
            builder.update(profile=new_profile,rows=rows,draft=draft,revision=builder['revision']+1)
            if on_change:on_change()
            st.rerun()
        if right.button('Restaurar esta pergunta',key='restore_category'):
            base=next(v for v in builder['base_profile'].variables if v.name==field.name)
            # Restore uses the same impact validation as an edit, never overwriting existing codes.
            canonical=profile.canonical_codes.get(field.name,{str(c):c for c in field.labels})
            edited=[{'Código':code,'Significado':label,'original_code':next((old for old in field.labels if canonical.get(str(old))==code),None)} for code,label in base.labels.items()]
            if (builder['rows'] or builder['draft']) and not confirm:st.warning('Confirme a atualização das respostas para restaurar.');return
            new_profile,mapping=update_categories(profile,field.name,edited)
            rows=remap_rows(builder['rows'],field.name,mapping,new_profile)
            draft=remap_rows([builder['draft']],field.name,mapping,new_profile)[0] if builder['draft'] else {}
            builder['undo']=(profile,deepcopy(builder['rows']),deepcopy(builder['draft']))
            builder.update(profile=new_profile,rows=rows,draft=draft,revision=builder['revision']+1)
            if on_change:on_change()
            st.rerun()
        if st.button('Cancelar edição',key='cancel_category'):
            builder['revision']+=1;st.rerun()
        if builder['undo'] and st.button('Desfazer alteração de categorias'):
            profile,rows,draft=builder.pop('undo');builder.update(profile=profile,rows=rows,draft=draft,undo=None,revision=builder['revision']+1)
            if on_change:on_change()
            st.rerun()


def render_create_sheet(on_use, download=None):
    """on_use(payload, filename); optional download(payload, filename, label)."""
    builder=_builder()
    variables=[v for v in input_variables(builder['profile']) if v.name!='ID']
    phase=builder['phase']
    st.header('Monte sua planilha')
    if phase=='categories':
        st.write('As perguntas e categorias já estão prontas. Ajuste somente se precisar.')
        _categories(builder)
        if st.button('Começar preenchimento',type='primary',key='builder_start'):
            builder['draft']=new_participant(tuple(r['ID'] for r in builder['rows']));builder['question']=0;_move(builder,'identify')
    elif phase=='identify':
        st.caption(f'Participante {builder["draft"]["ID"]}')
        with st.form('participant_name'):
            name=st.text_input('Nome ou apelido (opcional)',value=builder['draft'].get('NOME',''),help='Usado somente para identificar a linha da planilha.')
            if st.form_submit_button('Começar perguntas',type='primary'):
                builder['draft']['NOME']=name.strip();_move(builder,'questions')
    elif phase=='questions':
        index=builder['question'];variable=variables[index];draft=builder['draft'];value=draft.get(variable.name)
        group='Sobre a mãe' if index<12 else 'Sobre a criança' if index<27 else 'Sono' if index<46 else 'Sobrecarga'
        st.caption(f'Participante {draft["ID"]} · {group}')
        st.progress((index+1)/len(variables),text=f'Pergunta {index+1} de {len(variables)}')
        with st.form(f'participant_question_{index}_{builder["revision"]}'):
            if variable.labels:
                options=list(variable.labels)
                answer=st.radio(variable.label,options,index=options.index(value) if value in options else None,format_func=lambda code:variable.labels[code])
            elif variable.name in ('H_DEIT','H_LEV'):
                if value is not None and not isinstance(value,time):value=None
                answer=st.time_input(variable.label,value=value,step=60)
            elif variable.kind=='text':answer=st.text_input(variable.label,value=value or '')
            else:answer=st.number_input(variable.label,value=float(value) if value is not None else None,min_value=0.0,step=1.0)
            back,next_=st.columns(2)
            previous=back.form_submit_button('Voltar')
            forward=next_.form_submit_button('Próxima' if index<len(variables)-1 else 'Conferir participante',type='primary')
            if previous or forward:
                draft[variable.name]=answer
                if previous:
                    if index==0:_move(builder,'identify')
                    builder['question']-=1
                elif index==len(variables)-1:_move(builder,'review')
                else:builder['question']+=1
                st.rerun()
        with st.expander('Categorias e opções'):_categories(builder)
    elif phase=='review':
        st.subheader('Confira esta participante')
        st.dataframe(pd.DataFrame([{'Pergunta':v.label,'Resposta':v.labels.get(builder['draft'].get(v.name),builder['draft'].get(v.name)) if v.labels else builder['draft'].get(v.name)} for v in variables]).fillna('Não informado'),hide_index=True,width='stretch')
        selected=st.selectbox('Editar uma resposta',range(len(variables)),format_func=lambda i:variables[i].label)
        if st.button('Editar resposta'):
            builder['question']=selected;_move(builder,'questions')
        if st.button('Salvar participante',type='primary'):
            draft=dict(builder['draft']);existing=next((i for i,r in enumerate(builder['rows']) if r['ID']==draft['ID']),None)
            if existing is None:builder['rows'].append(draft)
            else:builder['rows'][existing]=draft
            builder['draft']={};_move(builder,'saved')
    elif phase in ('saved','finish'):
        st.success(f'{len(builder["rows"])} participante(s) na planilha.')
        add,finish=st.columns(2)
        if add.button('Adicionar participante'):
            builder['draft']=new_participant(tuple(r['ID'] for r in builder['rows']));builder['question']=0;_move(builder,'identify')
        if finish.button('Concluir planilha',type='primary'):_move(builder,'finish')
        with st.expander('Editar participantes'):
            selected=st.selectbox('Participante',range(len(builder['rows'])),format_func=lambda i:str(builder['rows'][i].get('NOME') or f'Participante {builder["rows"][i]["ID"]}'))
            if st.button('Editar participante'):
                builder['draft']=dict(builder['rows'][selected]);builder['question']=0;_move(builder,'identify')
            remove=st.checkbox('Confirmar exclusão desta participante')
            if st.button('Excluir participante',disabled=not remove):
                builder['rows'].pop(selected)
                if not builder['rows']:_move(builder,'categories')
                st.rerun()
        _categories(builder)
    if builder['rows'] or len(builder['draft'])>1:
        rows=list(builder['rows'])
        if builder['draft']:
            rows=[r for r in rows if r['ID']!=builder['draft']['ID']]+[dict(builder['draft'])]
        payload=build_input_workbook(rows,builder['profile'],fictitious=builder.get('fictitious',False))
        if download:download(payload,'banco_preenchido.xlsx','Baixar planilha preenchida')
        else:st.download_button('Baixar planilha preenchida',payload,'banco_preenchido.xlsx','application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',key='builder_download')
        st.caption('Baixe para guardar seu trabalho antes de sair. Respostas em branco continuam em branco.')
        if phase=='finish' and st.button('Usar na análise',type='primary',key='builder_analyze'):on_use(payload,'banco_preenchido.xlsx')


def resume_sheet(imported, profile):
    """Restore filled rows from an uploaded workbook into this session's assistant."""
    rows=imported.raw.astype(object).where(pd.notna(imported.raw),None).to_dict('records')
    from ..scales import clock_to_decimal
    for row in rows:
        for field in ('H_DEIT','H_LEV'):
            if row.get(field) is not None:
                minutes=round(clock_to_decimal(row[field])*60)
                row[field]=time((minutes//60)%24,minutes%60)
    st.session_state.sheet_builder={'profile':profile,'base_profile':load_updated_profile(),'rows':rows,'draft':{},'question':0,'phase':'saved' if rows else 'categories','revision':0,'undo':None,'fictitious':imported.metadata.get('fictitious',False)}


def render_category_editor(state):
    """Optional editor for an imported dataset, preserving original input and undo."""
    from dataclasses import replace
    from ..models import Transformation
    from ..validation import prepare_dataset
    from .state import invalidate_after_change
    if state.prepared is None:return
    key='import_category_editor'
    signature=state.imported.meta.source_sha256
    existing=st.session_state.get(key)
    if existing is None or existing['signature']!=signature:
        st.session_state[key]={'signature':signature,'profile':state.profile,'base_profile':state.profile,'rows':state.prepared.data.astype(object).where(pd.notna(state.prepared.data),None).to_dict('records'),'draft':{},'revision':0,'undo':None}
    builder=st.session_state[key]
    # Re-read rows after other correction tools changed the prepared dataset.
    builder['rows']=state.prepared.data.astype(object).where(pd.notna(state.prepared.data),None).to_dict('records')
    def apply():
        before=state.prepared.data.copy(deep=True)
        data=pd.DataFrame(builder['rows'],index=before.index)
        changes=[]
        for field in data:
            if field not in before:continue
            for index in data.index:
                old=before.at[index,field];new=data.at[index,field]
                if (pd.isna(old) and pd.isna(new)) or old==new:continue
                changes.append(Transformation(index,field,old,new,'Personalização confirmada das categorias'))
        profile=builder['profile']
        temporary=replace(state.imported,raw=data)
        prepared=prepare_dataset(temporary,profile,state.csv_options)
        prepared.transformations=state.prepared.transformations+tuple(changes)+prepared.transformations
        from ..validation import refresh_generated_scores
        prepared=refresh_generated_scores(prepared,profile)
        state.profile=profile;state.prepared=prepared;invalidate_after_change(state)
    _categories(builder,on_change=apply)
