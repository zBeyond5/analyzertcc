from dataclasses import asdict,replace
from pathlib import Path
import io,json,logging,traceback,os
import numpy as np
import openpyxl
import pandas as pd
import streamlit as st
from ..models import DomainError,CsvOptions,Transformation,ComparisonSpec,ImportedDataset
from ..profiles import load_profile,dictionary_frame,confirm_codebook
from ..importers import inspect_upload,load_table
from ..jobs import get_manager
from ..validation import prepare_dataset,validate_dataset,analysis_validation_issues
from ..scales import compare_recorded_scores,score_zarit
from ..transformations import apply_changes,undo_changes
from ..statistics.selection import default_comparisons,recommend_test
from ..pipeline import RunOptions,run_pipeline
from ..analysis_plan import QUESTIONS,build_default_plan,question_groups
from ..reporting import FICTITIOUS,format_p
from .state import WorkflowState,invalidate_after_change
from .downloads import build_download_anchor,MIMES
from .navigation import trusted_demo

ROOT=Path(__file__).resolve().parents[3]
STEPS=('1 · Dados','2 · Conferir','3 · Analisar','4 · Resultados','5 · Baixar')
METHOD_NAMES={'auto':'Recomendação conforme a tabela','welch_t':'Welch — diferença entre médias','mann_whitney':'Mann–Whitney — ordenação das respostas','welch_anova':'Welch — vários grupos','kruskal':'Kruskal–Wallis — vários grupos','fisher':'Fisher exato','chi_square':'Qui-quadrado','descriptive':'Somente descrição, sem p','spearman':'Correlação de Spearman','pearson':'Correlação de Pearson'}
FAMILIES={'primary':'Principal','complementary':'Complementar','exploratory':'Exploratória'}

def display_frame(frame):
    result=frame.copy()
    for name in result:
        if pd.api.types.is_object_dtype(result[name]):result[name]=result[name].map(lambda x:'' if pd.isna(x) else str(x))
    return result

def go(step):
    st.session_state.next_step=step
    st.rerun()

@st.cache_resource(show_spinner=False)
def server_manager():
    # Compartilhar somente controle de concorrência e propriedade; nunca DataFrames ou resultados.
    return get_manager()

def import_bytes(state,manager,payload,filename,sheet=None,options=None,demo=False):
    job=manager.create_job(state.session)
    path=manager.store_upload(state.session,job,filename,payload)
    imported=load_table(path,sheet=sheet,csv_options=options)
    from ..profiles import profile_for_import
    profile=profile_for_import(imported)
    prepared=prepare_dataset(imported,profile,options)
    state.job=job;state.imported=imported;state.profile=profile
    state.prepared=prepared;state.csv_options=options;state.fictitious=demo or getattr(imported,'metadata',{}).get('fictitious',False)
    st.session_state.pop('import_category_editor',None)
    invalidate_after_change(state)

def render_import(state,manager):
    route=st.radio('Como deseja preparar os dados?', ['Importar planilha','Criar planilha'],horizontal=True,key='data_route',label_visibility='collapsed')
    if route=='Criar planilha':
        from .create_sheet import render_create_sheet
        def use(payload,filename):
            import_bytes(state,manager,payload,filename);go(1)
        def download(payload,filename,label):
            import hashlib
            digest=hashlib.sha256(payload).hexdigest()
            if st.button('Preparar planilha para baixar',key='builder_prepare'):
                job=manager.create_job(state.session)
                path=job.directory/filename;path.write_bytes(payload)
                manager.register_artifacts(state.session,job,{'input_workbook':path})
                st.session_state.builder_download=(digest,job)
            ready=st.session_state.get('builder_download')
            if ready and ready[0]==digest:
                content=manager.read_artifact(state.session,ready[1],'input_workbook')
                st.markdown(build_download_anchor(content,filename=filename,mime=MIMES['xlsx']),unsafe_allow_html=True)
        render_create_sheet(use,download=download)
        return
    st.header('Importe sua planilha')
    uploaded=st.file_uploader('Escolha seu Excel ou CSV',type=['xlsx','xls','csv'],help='Até 20 MB. Seu arquivo original é preservado.')
    sheet=None;options=None
    if uploaded:
        payload=uploaded.getvalue();fmt=inspect_upload(uploaded.name,payload)
        if fmt in ('.xlsx','.xls'):
            with pd.ExcelFile(io.BytesIO(payload),engine='openpyxl' if fmt=='.xlsx' else 'xlrd') as book:
                candidates=[name for name in book.sheet_names if name.casefold() not in ('categorias','perguntas','aviso','metadados')]
            if len(candidates)==1:sheet=candidates[0]
            else:sheet=st.selectbox('Qual aba contém as respostas?',candidates)
        else:
            with st.expander('Opções do CSV'):
                enc=st.selectbox('Codificação',['utf-8-sig','utf-8','cp1252','latin-1'])
                sep=st.selectbox('Separador',[';',',','\t'])
                dec=st.selectbox('Decimal',[',','.'])
                options=CsvOptions(enc,sep,dec)
        if st.button('Continuar',type='primary',key='import'):
            import_bytes(state,manager,payload,uploaded.name,sheet,options);go(1)
    with st.expander('Experimentar antes de usar meus dados'):
        st.caption('Demonstração fictícia, sem resultados de pesquisa.')
        if st.button('Experimentar dados fictícios',key='demo'):
            source=ROOT/'tests/fixtures/synthetic_tcc.xlsx'
            import_bytes(state,manager,source.read_bytes(),source.name,'Banco_EpiInfo',demo=True);go(1)


def refresh_prepared(state,data):
    from ..validation import refresh_generated_scores
    state.prepared.data=data
    state.prepared=refresh_generated_scores(state.prepared,state.profile)


def render_validation(state,manager):
    if state.prepared is None:st.info('Importe um banco para visualizar as validações.');return
    st.header('Confira os dados antes de analisar')
    df=state.prepared.data;issues=analysis_validation_issues(state.prepared,state.profile)
    actual=[i for i in issues if not(trusted_demo(state) and i.code=='mapping_pending')]
    warnings=[i for i in actual if i.severity!='error']
    actual=[i for i in actual if i.severity=='error']
    c1,c2,c3=st.columns(3)
    c1.metric('Participantes',len(df));c2.metric('Perguntas',len(getattr(state.profile,'input_fields',())) or state.imported.meta.column_count);c3.metric('Pendências',len(actual))
    if getattr(state.profile,'confirmation',''):st.caption('Perguntas e categorias reconhecidas na documentação.')
    if actual:
        st.dataframe(pd.DataFrame([{'Linha':i.row_index+1 if i.row_index is not None else 'Todas','Pergunta':next((v.label for v in state.profile.variables if v.name==i.variable),i.variable),'Valor':str(i.raw_value),'Nível':i.severity,'Orientação':i.message_pt} for i in actual]),hide_index=True,width='stretch')
    else:st.success('Dados conferidos. Você pode continuar.')
    unavailable=[label for field,label in (('PSQI','sono'),('ZARIT','sobrecarga')) if field not in df or not df[field].notna().any()]
    if unavailable:st.info('Para calcular '+ ' e '.join(unavailable)+', complete as respostas do questionário e mantenha o significado das opções. Você pode retomar o preenchimento abaixo.')
    if warnings:
        with st.expander(f'{len(warnings)} observações sobre os dados'):
            st.dataframe(pd.DataFrame([{'Pergunta':next((v.label for v in state.profile.variables if v.name==i.variable),i.variable),'Linha':i.row_index+1 if i.row_index is not None else 'Todas','Orientação':i.message_pt} for i in warnings]),hide_index=True,width='stretch')
    with st.expander('Visualizar banco e dicionário',expanded=False):
        st.dataframe(display_frame(df),hide_index=True,width='stretch')
        st.dataframe(dictionary_frame(state.profile),hide_index=True,width='stretch')
        unknown=[c for c in df if c not in {v.name for v in state.profile.variables}|{'ZARIT_CLASS'}]
        if unknown:st.warning('Campos adicionais ficam fora das análises e exportações: '+', '.join(unknown))
    from .create_sheet import render_category_editor,resume_sheet
    render_category_editor(state)
    if getattr(state.profile,'input_fields',()) and st.button('Continuar preenchimento no assistente'):
        resume_sheet(replace(state.imported,raw=state.prepared.data),state.profile)
        st.session_state.data_route='Criar planilha';go(0)
    with st.expander('Conferir totais fornecidos e recalculados'):
        st.dataframe(display_frame(compare_recorded_scores(df,state.profile)),hide_index=True,width='stretch')
    if any(i.code=='mapping_pending' for i in actual):
        st.info('Há categorias sem definição. Abra a edição apenas para completar as que faltam.')
    with st.expander('Corrigir um valor com registro e possibilidade de desfazer'):
        with st.form('correction_form'):
            a,b=st.columns(2);row=int(a.number_input('Linha do banco',1,len(df),1))-1
            generated={t.field for t in state.prepared.transformations if t.reason.startswith('Escore gerado:')}
            editable=[c for c in df if c not in generated|{'ZARIT_CLASS','PSQI_G'}]
            field=b.selectbox('Campo para corrigir',editable,index=editable.index('IDADE_M') if 'IDADE_M' in editable else 0)
            value=st.text_input('Novo valor (vazio = ausente)')
            reason=st.text_input('Observação (opcional)')
            confirm=st.checkbox('Confirmo a alteração nesta cópia do banco.')
            submit=st.form_submit_button('Aplicar correção')
        if submit:
            if not confirm:raise DomainError('confirmation','Confirme a alteração antes de aplicar.')
            var=next((v for v in state.profile.variables if v.name==field),None)
            if value=='':after=np.nan
            elif var and var.kind!='text':
                try:after=float(value.replace(',','.'))
                except ValueError:raise DomainError('number','Informe um número válido para este campo.') from None
            else:after=value
            change=Transformation(row,field,df.at[row,field],after,'Correção: '+(reason.strip() or 'confirmada pela pessoa na sessão'))
            state.prepared.data=apply_changes(df,(change,),confirmed=True)
            state.prepared.transformations+=(change,)
            refresh_prepared(state,state.prepared.data)
            invalidate_after_change(state);st.rerun()
        manual=[c for c in state.prepared.transformations if c.reason.startswith('Correção:')]
        if manual and st.button('Desfazer última correção'):
            last=manual[-1];state.prepared.data=undo_changes(df,(last,))
            state.prepared.transformations=tuple(c for c in state.prepared.transformations if c is not last)
            refresh_prepared(state,state.prepared.data)
            invalidate_after_change(state);st.rerun()
    blocked=any(i.severity=='error' and not(trusted_demo(state) and i.code=='mapping_pending') for i in issues)
    if st.button('Continuar para análise',type='primary',disabled=blocked,key='to_comparisons'):go(2)
    if blocked:st.caption('Confira os problemas indicados acima. Suas respostas estão preservadas.')

def render_comparisons(state,manager):
    if state.prepared is None:st.info('Importe uma planilha para começar.');return
    st.header('O que você quer descobrir?')
    selected=st.multiselect('Perguntas da pesquisa',list(QUESTIONS),default=['burden'],format_func=QUESTIONS.get,key='research_questions')
    groups=question_groups(state.profile)
    for group,label in (('mae','Outros fatores da mãe'),('crianca','Outros fatores da criança')):
        with st.expander(label):
            options={k:v for k,v in groups[group].items() if k not in QUESTIONS and build_default_plan(state.prepared.data,state.profile,(k,))}
            selected+=st.multiselect('Fatores para comparar com o sono',list(options),format_func=options.get,key='factors_'+group)
    from ..analysis_population import select_population,population_signature,REASONS
    population=select_population(state.prepared.data,state.profile)
    signature=population_signature(state.prepared,state.profile,population)
    if population.excluded:
        st.info(f'{len(population.data)} de {len(state.prepared.data)} participantes atendem aos critérios observáveis do projeto. O banco original será preservado.')
        with st.expander('Por que algumas participantes não entram?'):
            for code,label in REASONS.items():
                count=sum(code in e['reasons'] for e in population.excluded)
                if count:st.write(f'{label}: {count}')
    if population.data.empty:st.info('Complete os questionários para ter participantes elegíveis para análise.')
    configured=build_default_plan(population.data,state.profile,selected)
    with st.expander('Como a análise será feita'):
        st.caption('Métodos definidos para cada pergunta. Pares completos, sem preencher respostas ausentes. Associação não comprova causa.')
        for c in configured:
            rec=recommend_test(population.data,c,state.profile)
            st.write(f'{c.outcome} × {c.predictor}: {METHOD_NAMES.get(c.method if c.method!="auto" else rec.method,rec.method)}')
            st.caption(' '.join(rec.reasons))
    if state.options and state.options.comparisons!=configured:
        invalidate_after_change(state);state.options=None;st.rerun()
    if not configured:st.info('Escolha uma pergunta com respostas disponíveis para analisar.')
    run_label=f'Analisar {len(population.data)} participantes elegíveis' if population.excluded else 'Analisar dados'
    if st.button(run_label,type='primary',disabled=not configured or population.data.empty,key='run_analysis'):
        state.population_ack_signature=signature
        if state.job.status not in ('created','uploaded'):
            manager._check(state.session,state.job)
            payload=state.job.source_path.read_bytes();old=state.job
            state.job=manager.create_job(state.session)
            manager.store_upload(state.session,state.job,'dados'+old.source_path.suffix,payload)
        state.options=RunOptions(configured,fictitious=state.fictitious,population_policy=population.policy,population_ack_signature=state.population_ack_signature)
        with st.status('Preparando seus resultados',expanded=False) as status:
            state.artifacts=run_pipeline(manager=manager,session=state.session,job=state.job,source_path=state.job.source_path,prepared=state.prepared,profile=state.profile,options=state.options,progress=lambda text:status.update(label=text))
            status.update(label='Resultados prontos',state='complete')
        state.reviewed=False;state.download_key=None;go(3)


def render_results(state,manager):
    if state.artifacts is None:st.info('Execute os cruzamentos para conferir os resultados.');return
    manager._check(state.session,state.job)
    st.header('Confira os resultados e o relatório')
    summary,tables,details=st.tabs(['Resumo','Tabelas','Detalhes'])
    with summary:
        from .charts import render_charts
        from ..interpretation import interpret_p,LABELS
        with st.expander('Como ler o valor de p'):
            st.write('O projeto usa p < 0,05. Desvio padrão mostra a variação das respostas; p avalia a comparação estatística. Significância não demonstra causa nem importância prática.')
        for analysis in state.artifacts.results:
            result=analysis.result;answer=interpret_p(result.p_value,p_kind=result.p_kind)
            labels={v.name:v.label for v in state.profile.variables}
            title=f'{labels.get(analysis.spec.outcome,analysis.spec.outcome)} × {labels.get(analysis.spec.predictor,analysis.spec.predictor)}'
            st.subheader(title)
            st.write(f"**{LABELS[answer['status']]}** · p = {answer['p_display']}")
            st.caption(f'{METHOD_NAMES.get(result.method,result.method)} · {result.n_effective} pares completos · {result.n_missing} ausentes')
            st.write(answer['explanation'])
            if answer['status']=='unavailable':
                for warning in result.warnings:st.caption(warning)
            for name,effect in result.effects.items():
                from ..reporting import EFFECT_LABELS,number
                interval=f' — IC95% {number(effect.ci95[0],3)} a {number(effect.ci95[1],3)}' if effect.ci95 else ' — IC indisponível'
                st.caption(f'{EFFECT_LABELS.get(name,name)}: {number(effect.value,3)}{interval}')
        render_charts(state)
    with tables:
        titles=('Características sociodemográficas','Características clínicas','Instrumentos de avaliação')
        for i,frame in enumerate(state.artifacts.tables.descriptive):
            with st.expander(f'Tabela {i+1} · {titles[i]}',expanded=i==2):st.dataframe(frame,hide_index=True,width='stretch')
        st.subheader('Comparações bivariadas')
        for frame in state.artifacts.tables.bivariate:st.dataframe(frame,hide_index=True,width='stretch')
    with details:
        for analysis in state.artifacts.results:
            with st.expander(f'{analysis.spec.outcome} × {analysis.spec.predictor}: método, pressupostos e avisos'):
                st.write('Família: '+FAMILIES[analysis.spec.family])
                st.write(f'n efetivo: {analysis.result.n_effective}. Ausentes: {analysis.result.n_missing}. Tipo do p: {analysis.result.p_kind}.')
                for line in analysis.result.assumptions:st.write(line)
                for line in analysis.result.warnings:st.warning(line)
                st.json(asdict(analysis.result),expanded=False)
        with st.expander('Explicações e notas do relatório'):
            for text in state.artifacts.tables.narrative+state.artifacts.tables.notes:st.write(text)
    if st.button('Baixar resultados',type='primary',key='to_exports'):
        state.reviewed=True;go(4)

def render_exports(state,manager):
    st.header('Baixe os arquivos desta execução')
    if state.artifacts is None or not state.reviewed:st.info('Abra os resultados para continuar até o download.');return
    manager._check(state.session,state.job)
    st.caption('Escolha o formato. O pacote completo reúne todos os arquivos.')
    labels={'zip':'Todos os arquivos (ZIP)','docx':'Relatório acadêmico (Word)','pdf':'Relatório acadêmico (PDF)','tables':'Tabelas (Excel)','xlsx':'Banco para Epi Info (Excel)','csv':'Banco para Epi Info (CSV)','dictionary':'Dicionário de variáveis','manifest':'Manifesto da análise','audit':'Auditoria das alterações'}
    key=st.selectbox('Arquivo para baixar',list(labels),format_func=labels.get)

    if st.button('Preparar download',type='primary',key='prepare_download'):state.download_key=key
    if state.download_key:
        p=state.artifacts.files[state.download_key];payload=manager.read_artifact(state.session,state.job,state.download_key)
        st.markdown(build_download_anchor(payload,filename=p.name,mime=MIMES[p.suffix[1:]]),unsafe_allow_html=True)
    st.caption('Arquivos expiram no servidor 60 minutos após a geração. Cópias já baixadas permanecem no seu computador. Recarregar a página pode exigir reprocessamento.')

def main():
    st.set_page_config(page_title='Análise bivariada do TCC',page_icon='📊',layout='centered')
    st.markdown('''<style>
    h1{font-weight:600;font-size:2.1rem;letter-spacing:-.035em}
    h2{font-size:1.45rem;font-weight:550} h3{font-size:1.12rem}
    .private-download{display:inline-block;background:#216C72;color:white!important;padding:12px 20px;border-radius:10px;text-decoration:none;font-weight:600;margin:10px 0;box-shadow:0 4px 14px #216c7218}
    a:focus-visible,button:focus-visible{outline:3px solid #A57530!important;outline-offset:3px}

    </style>''',unsafe_allow_html=True)
    if 'workflow' not in st.session_state:st.session_state.workflow=WorkflowState()
    state=st.session_state.workflow
    st.title('Sua pesquisa, com clareza')
    st.caption('Dos dados ao relatório, uma etapa por vez.')
    if 'next_step' in st.session_state:st.session_state.navigation=STEPS[st.session_state.pop('next_step')]
    from .navigation import render_navigation
    selected=render_navigation(state,STEPS)
    with st.sidebar:
        st.divider()
        with st.popover('Nova análise',width='stretch'):
            st.caption('Começar novamente descarta o trabalho desta sessão. Baixe sua planilha antes de continuar.')
            if st.button('Descartar e iniciar',key='reset',type='primary'):
                for key in ('sheet_builder','import_category_editor','builder_download'):
                    st.session_state.pop(key,None)
                st.session_state.workflow=WorkflowState(session=state.session);go(0)
        with st.expander('Sobre este espaço'):
            st.caption('Processamento no servidor da nuvem.' if os.environ.get('TCC_DEPLOYMENT')=='cloud' else 'Processamento local no servidor.')
            st.caption('Arquivos privados por sessão. Retenção: 60 minutos.')
            st.caption('Aparência: menu ⋮ → Light / Dark / System.')
    if state.fictitious:st.warning(FICTITIOUS)
    try:
        manager=server_manager()
        [render_import,render_validation,render_comparisons,render_results,render_exports][STEPS.index(selected)](state,manager)
    except DomainError as error:st.error(str(error))
    except Exception as error:
        last=traceback.extract_tb(error.__traceback__)[-1]
        logging.error('Falha na etapa %s: %s em %s:%s',STEPS.index(selected),type(error).__name__,Path(last.filename).name,last.lineno)
        st.error('Não foi possível concluir esta etapa. Confira os dados e tente novamente; nenhum arquivo de outra sessão foi acessado.')

if __name__=='__main__':main()
