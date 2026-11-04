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
from ..validation import prepare_dataset,validate_dataset
from ..scales import compare_recorded_scores,score_zarit
from ..transformations import apply_changes,undo_changes
from ..statistics.selection import default_comparisons,recommend_test
from ..pipeline import RunOptions,run_pipeline
from ..reporting import FICTITIOUS,format_p
from .state import WorkflowState,invalidate_after_change
from .downloads import build_download_anchor,MIMES

ROOT=Path(__file__).resolve().parents[3]
STEPS=('1 · Importar','2 · Validar','3 · Cruzamentos','4 · Resultados','5 · Exportar')
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
    profile=load_profile()
    state.job=job;state.imported=imported;state.profile=profile
    state.prepared=prepare_dataset(imported,profile,options);state.csv_options=options;state.fictitious=demo
    invalidate_after_change(state)

def render_import(state,manager):
    st.header('Comece pelo seu banco de dados')
    st.write('Importe uma planilha ou experimente a base fictícia. Os dados são processados no servidor da nuvem e ficam separados por sessão.' if os.environ.get('TCC_DEPLOYMENT')=='cloud' else 'Importe uma planilha ou experimente a base fictícia. Os dados são processados neste computador e ficam separados por sessão.')
    col1,col2=st.columns([3,2],gap='large')
    with col1:
        uploaded=st.file_uploader('Arquivo Excel ou CSV',type=['xlsx','xls','csv'],help='Até 20 MiB. O arquivo original não é alterado.')
        sheet=None;options=None
        if uploaded:
            payload=uploaded.getvalue();fmt=inspect_upload(uploaded.name,payload)
            if fmt=='.xlsx':
                w=openpyxl.load_workbook(io.BytesIO(payload),read_only=True,keep_links=False)
                sheet=st.selectbox('Aba da planilha',w.sheetnames);w.close()
            elif fmt=='.xls':
                with pd.ExcelFile(io.BytesIO(payload),engine='xlrd') as book:sheet=st.selectbox('Aba da planilha',book.sheet_names)
            else:
                c1,c2,c3=st.columns(3)
                encoding=c1.selectbox('Encoding',['utf-8-sig','utf-8','cp1252','latin-1'])
                sep=c2.selectbox('Separador',[';',',','\t'],format_func=lambda s:'Tabulação' if s=='\t' else s)
                dec=c3.selectbox('Decimal',[',','.'])
                options=CsvOptions(encoding,sep,dec)
            if st.button('Importar e visualizar',type='primary',key='import'):
                import_bytes(state,manager,payload,uploaded.name,sheet,options);go(1)
        st.caption('Fórmulas, macros e vínculos externos em XLSX são recusados. Salve apenas valores antes de enviar.')
    with col2:
        st.subheader('Conheça o fluxo com segurança')
        st.write('A demonstração contém 30 registros fictícios e 75 variáveis do perfil do TCC. Não representa achados de pesquisa.')
        if st.button('Experimentar dados fictícios',key='demo',width='stretch'):
            source=ROOT/'tests/fixtures/synthetic_tcc.xlsx'
            import_bytes(state,manager,source.read_bytes(),source.name,'Banco_EpiInfo',demo=True);go(1)
    if state.imported:
        st.subheader('Prévia da entrada original')
        st.dataframe(display_frame(state.imported.raw.head(30)),hide_index=True,width='stretch')

def render_validation(state,manager):
    if state.prepared is None:st.info('Importe um banco para visualizar as validações.');return
    st.header('Confira os dados antes de analisar')
    df=state.prepared.data;issues=validate_dataset(df,state.profile).issues
    actual=[i for i in issues if i.code!='mapping_pending']
    c1,c2,c3=st.columns(3)
    c1.metric('Registros',len(df));c2.metric('Colunas originais',state.imported.meta.column_count);c3.metric('Problemas nos dados',len(actual))
    if state.fictitious:st.info('Demonstração: categorias sem legenda confirmada aparecem como códigos neutros. Os cálculos não atribuem significado clínico a esses códigos.')
    else:st.warning('Confira as legendas do seu banco. Escolaridade, renda e códigos binários não têm legenda aprovada nos documentos originais.')
    st.caption('PSQI: uso do escore informado (0–21) e conferência da classificação. Componentes não são recalculados sem manual confirmado.')
    if actual:
        st.dataframe(pd.DataFrame([{'Linha':i.row_index+1 if i.row_index is not None else 'Todas','Campo':i.variable,'Valor':str(i.raw_value),'Nível':i.severity,'Orientação':i.message_pt} for i in actual]),hide_index=True,width='stretch')
    else:st.success('Não foram encontrados erros nos valores, na soma Zarit ou no ponto de corte PSQI informado.')
    with st.expander('Visualizar banco e dicionário',expanded=False):
        st.dataframe(display_frame(df),hide_index=True,width='stretch')
        st.dataframe(dictionary_frame(state.profile),hide_index=True,width='stretch')
        unknown=[c for c in df if c not in {v.name for v in state.profile.variables}|{'ZARIT_CLASS'}]
        if unknown:st.warning('Campos adicionais ficam fora das análises e exportações: '+', '.join(unknown))
    with st.expander('Conferir totais fornecidos e recalculados'):
        st.dataframe(display_frame(compare_recorded_scores(df,state.profile)),hide_index=True,width='stretch')
    with st.expander('Confirmar legendas para analisar dados de pesquisa'):
        st.write('Informe a legenda dos códigos e a referência usada para conferência. Esta confirmação vale apenas nesta sessão e fica no manifesto.')
        rows=[{'Campo':v.name,'Código':str(k),'Legenda':label} for v in state.profile.variables if v.kind=='categorical' for k,label in v.labels.items()]
        edited=st.data_editor(pd.DataFrame(rows),num_rows='dynamic',column_config={'Campo':st.column_config.SelectboxColumn(options=[v.name for v in state.profile.variables if v.kind=='categorical'])},hide_index=True,width='stretch',key='dictionary_editor')
        reference=st.text_input('Referência da conferência (documento, versão ou responsável)',key='mapping_reference')
        acknowledged=st.checkbox('Conferi as legendas com a documentação deste banco.',key='mapping_ack')
        if st.button('Aplicar legendas confirmadas',disabled=not acknowledged or len(reference.strip())<10):
            state.profile=confirm_codebook(state.profile,edited.to_dict('records'),reference)
            invalidate_after_change(state);st.rerun()
    with st.expander('Corrigir um valor com registro e possibilidade de desfazer'):
        with st.form('correction_form'):
            a,b=st.columns(2);row=int(a.number_input('Linha do banco',1,len(df),1))-1
            editable=[c for c in df if c!='ZARIT_CLASS']
            field=b.selectbox('Campo para corrigir',editable,index=editable.index('IDADE_M') if 'IDADE_M' in editable else 0)
            value=st.text_input('Novo valor (vazio = ausente)')
            reason=st.text_input('Motivo da correção')
            confirm=st.checkbox('Confirmo a alteração nesta cópia do banco.')
            submit=st.form_submit_button('Aplicar correção')
        if submit:
            if not confirm or not reason.strip():raise DomainError('confirmation','Confirme a correção e informe o motivo.')
            var=next((v for v in state.profile.variables if v.name==field),None)
            if value=='':after=np.nan
            elif var and var.kind!='text':
                try:after=float(value.replace(',','.'))
                except ValueError:raise DomainError('number','Informe um número válido para este campo.') from None
            else:after=value
            change=Transformation(row,field,df.at[row,field],after,reason)
            state.prepared.data=apply_changes(df,(change,),confirmed=True)
            state.prepared.data['ZARIT_CLASS']=[score_zarit(r,state.profile).category for _,r in state.prepared.data.iterrows()]
            state.prepared.transformations+=(change,)
            invalidate_after_change(state);st.rerun()
        manual=[c for c in state.prepared.transformations if c.reason!='Conversão numérica em cópia']
        if manual and st.button('Desfazer última correção'):
            last=manual[-1];state.prepared.data=undo_changes(df,(last,))
            state.prepared.data['ZARIT_CLASS']=[score_zarit(r,state.profile).category for _,r in state.prepared.data.iterrows()]
            state.prepared.transformations=tuple(c for c in state.prepared.transformations if c is not last)
            invalidate_after_change(state);st.rerun()
    blocked=any(i.severity=='error' and not(state.fictitious and i.code=='mapping_pending') for i in validate_dataset(state.prepared.data,state.profile).issues)
    if st.button('Configurar cruzamentos',type='primary',disabled=blocked,key='to_comparisons'):go(2)
    if blocked:st.caption('Resolva os erros e confirme as legendas para continuar. Nenhum registro será excluído automaticamente.')

def render_comparisons(state,manager):
    if state.prepared is None:st.info('Importe e valide um banco primeiro.');return
    st.header('Defina o que será comparado')
    st.write('As duas comparações principais são pré-definidas. Confira o método, os grupos e os pressupostos antes de executar.')
    selected=st.multiselect('Comparações do perfil',['PSQI_G × ZARIT','PSQI_G × ZARIT_CLASS','PSQI × ZARIT'],default=['PSQI_G × ZARIT','PSQI_G × ZARIT_CLASS','PSQI × ZARIT'])
    options=[]
    defaults=default_comparisons()
    for i,name in enumerate(['PSQI_G × ZARIT','PSQI_G × ZARIT_CLASS','PSQI × ZARIT']):
        if name in selected:options.append(defaults[i])
    extras=st.multiselect('Explorar outras variáveis em relação a PSQI_G',['ALT_SONO','DESP_NOT','SUPERV','RED_APO','IDADE_M','IDADE_C','ESCOL','RENDA','TRAB_NOT','DOENCA','ANTIDEP','ANSIED','DEPRE','ACOMP_TEP','FREQ_TEP','FISIO','FONO','TER_OCUP','PSI','PSICOP'])
    options.extend(ComparisonSpec('explore_'+c,'PSQI_G',c) for c in extras)
    with st.expander('Adicionar outro cruzamento'):
        fields=[v.name for v in state.profile.variables if v.kind!='text' and v.name in state.prepared.data]+['ZARIT_CLASS']
        a,b=st.columns(2);outcome=a.selectbox('Desfecho',fields,index=fields.index('PSQI'))
        predictor=b.selectbox('Preditor',fields,index=fields.index('ZARIT'))
        custom=st.checkbox('Incluir este cruzamento exploratório')
        if custom:options.append(ComparisonSpec('custom',outcome,predictor))
    configured=[]
    for c in options:
        with st.expander(f'{c.outcome} × {c.predictor} — {FAMILIES[c.family]}',expanded=c.family=='primary'):
            rec=recommend_test(state.prepared.data,c,state.profile)
            st.write(' '.join(rec.reasons))
            choices=list(dict.fromkeys([rec.method,*rec.alternatives]))
            method=st.selectbox('Método de comparação',choices,format_func=lambda m:METHOD_NAMES[m],key='method_'+c.id)
            rationale=st.text_input('Justificativa',value=c.rationale,key='rationale_'+c.id)
            st.caption('Grupos por código em ordem crescente. Diferenças numéricas: primeiro grupo menos segundo. Para RP/OR, escolha explicitamente a referência abaixo.')
            order=();event=None
            kinds={v.name:v.kind for v in state.profile.variables};kinds['ZARIT_CLASS']='categorical'
            if kinds.get(c.outcome)=='categorical' and kinds.get(c.predictor)=='categorical':
                y=sorted(state.prepared.data[c.outcome].dropna().unique());x=sorted(state.prepared.data[c.predictor].dropna().unique())
                if len(y)==len(x)==2 and st.checkbox('Calcular RP/OR com orientação explícita',key='ratios_'+c.id):
                    event=st.selectbox('Código do evento no desfecho',y,key='event_'+c.id)
                    exposed=st.selectbox('Código do grupo comparado (outro = referência)',x,key='exposed_'+c.id)
                    order=(exposed,next(g for g in x if g!=exposed))
            configured.append(replace(c,method=method,rationale=rationale,group_order=order,event_value=event))
    if state.options and state.options.comparisons!=tuple(configured):
        invalidate_after_change(state);state.options=None
    st.warning('Valores de p sem ajuste de multiplicidade. Não escolha o método apenas por normalidade ou pelo menor p; associações não estabelecem causalidade.')
    assumptions=st.checkbox('Conferi independência, distribuição, tamanho dos grupos e o que cada método estima.',key='assumptions')
    if st.button('Executar análise',type='primary',disabled=not assumptions or not configured,key='run_analysis'):
        if state.job.status not in ('created','uploaded'):
            manager._check(state.session,state.job)
            payload=state.job.source_path.read_bytes();old=state.job
            state.job=manager.create_job(state.session)
            manager.store_upload(state.session,state.job,'dados'+old.source_path.suffix,payload)
        state.options=RunOptions(tuple(configured),fictitious=state.fictitious)
        with st.status('Preparando análise',expanded=True) as status:
            state.artifacts=run_pipeline(manager=manager,session=state.session,job=state.job,source_path=state.job.source_path,prepared=state.prepared,profile=state.profile,options=state.options,progress=lambda text:status.update(label=text))
            status.update(label='Relatórios prontos para conferência',state='complete')
        state.reviewed=False;state.download_key=None;go(3)

def render_results(state,manager):
    if state.artifacts is None:st.info('Execute os cruzamentos para conferir os resultados.');return
    manager._check(state.session,state.job)
    st.header('Confira os resultados e o relatório')
    titles=('Características sociodemográficas','Características clínicas','Instrumentos de avaliação')
    for i,frame in enumerate(state.artifacts.tables.descriptive):
        with st.expander(f'Tabela {i+1} · {titles[i]}',expanded=i==2):st.dataframe(frame,hide_index=True,width='stretch')
    st.subheader('Comparações bivariadas')
    for frame in state.artifacts.tables.bivariate:st.dataframe(frame,hide_index=True,width='stretch')
    for analysis in state.artifacts.results:
        with st.expander(f'{analysis.spec.outcome} × {analysis.spec.predictor}: método, pressupostos e avisos'):
            st.write('Família: '+FAMILIES[analysis.spec.family])
            st.write(f'n efetivo: {analysis.result.n_effective}. Ausentes: {analysis.result.n_missing}. Tipo do p: {analysis.result.p_kind}.')
            for line in analysis.result.assumptions:st.write(line)
            for line in analysis.result.warnings:st.warning(line)
            st.json(asdict(analysis.result),expanded=False)
    st.subheader('Texto e notas que acompanham o relatório')
    for text in state.artifacts.tables.narrative+state.artifacts.tables.notes:st.write(text)
    state.reviewed=st.checkbox('Revisei as tabelas, os métodos e as limitações deste relatório.',value=state.reviewed,key='review_report_'+state.job.id)
    if st.button('Ir para exportação',type='primary',disabled=not state.reviewed):go(4)

def render_exports(state,manager):
    st.header('Baixe os arquivos desta execução')
    if state.artifacts is None or not state.reviewed:st.info('Confira os resultados e marque a revisão antes de exportar.');return
    manager._check(state.session,state.job)
    st.success('Relatórios conferidos. Cada arquivo pertence somente a esta sessão.')
    labels={'zip':'Todos os arquivos (ZIP)','docx':'Relatório acadêmico (Word)','pdf':'Relatório acadêmico (PDF)','tables':'Tabelas (Excel)','xlsx':'Banco para Epi Info (Excel)','csv':'Banco para Epi Info (CSV)','dictionary':'Dicionário de variáveis','manifest':'Manifesto da análise','audit':'Auditoria das alterações'}
    key=st.selectbox('Arquivo para baixar',list(labels),format_func=labels.get)
    st.caption('CSV: UTF-8 com BOM, separador ponto e vírgula e vírgula decimal. A importação na instalação de destino do Epi Info precisa ser conferida.')
    if st.button('Preparar download',type='primary',key='prepare_download'):state.download_key=key
    if state.download_key:
        p=state.artifacts.files[state.download_key];payload=manager.read_artifact(state.session,state.job,state.download_key)
        st.markdown(build_download_anchor(payload,filename=p.name,mime=MIMES[p.suffix[1:]]),unsafe_allow_html=True)
    st.caption('Arquivos expiram no servidor 60 minutos após a geração. Cópias já baixadas permanecem no seu computador. Recarregar a página pode exigir reprocessamento.')

def main():
    st.set_page_config(page_title='Análise bivariada do TCC',page_icon='📊',layout='wide')
    st.markdown('''<style>
    html,body,[class*="css"]{font-family:"Segoe UI",sans-serif} .block-container{max-width:1360px;padding-top:4rem} h1{font-weight:650;font-size:2.2rem} h2{font-size:1.6rem} h3{font-size:1.18rem} [data-testid="stMetricValue"]{font-variant-numeric:tabular-nums} .private-download{display:inline-block;background:#1F6675;color:white!important;padding:12px 20px;border-radius:6px;text-decoration:none;font-weight:600;margin:10px 0} a:focus-visible,button:focus-visible{outline:3px solid #8A4B00!important;outline-offset:3px}
    </style>''',unsafe_allow_html=True)
    if 'workflow' not in st.session_state:st.session_state.workflow=WorkflowState()
    state=st.session_state.workflow
    st.title('Análise bivariada do TCC')
    st.caption('Importe, confira e transforme seu banco em resultados reproduzíveis.')
    with st.sidebar:
        st.subheader('Seu espaço de análise')
        st.write('Processamento no servidor da nuvem.' if os.environ.get('TCC_DEPLOYMENT')=='cloud' else 'Processamento local no servidor.')
        st.write('Sem histórico compartilhado entre participantes da rede.')
        if state.imported:st.caption(f'{state.imported.meta.row_count} registros carregados. Os originais permanecem preservados.')
        if st.button('Iniciar outra análise',key='reset'):
            st.session_state.workflow=WorkflowState(session=state.session);go(0)
        st.divider();st.caption('Retenção temporária: 60 minutos. Acesso restrito pela plataforma Streamlit.' if os.environ.get('TCC_DEPLOYMENT')=='cloud' else 'Retenção temporária: 60 minutos. Acesso remoto somente pela rede Hamachi autorizada.')
    if 'next_step' in st.session_state:st.session_state.navigation=STEPS[st.session_state.pop('next_step')]
    selected=st.radio('Etapas da análise',STEPS,horizontal=True,key='navigation',label_visibility='collapsed')
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
