from dataclasses import dataclass,asdict
from datetime import datetime,timezone
import hashlib,importlib.metadata,json
import numpy as np
import pandas as pd
from .models import DomainError,CsvFormat,AnalysisResult,TestResult,RunArtifacts
from .validation import validate_dataset
from .reporting import build_tables,render_docx,render_pdf
from .exports import export_epiinfo,export_dictionary,write_audit,write_xlsx,write_json
from .statistics.selection import freeze_comparisons,recommend_test
from .statistics.descriptive import describe
from .statistics.categorical import analyze_contingency
from .statistics.numeric import compare_groups,correlate

DEMO_SHA256='e2a2fb48502e3a31b06af7c421417afc3819465a59c54127a1805fab3c137f3c'
@dataclass(frozen=True)
class RunOptions:
    comparisons: tuple
    score_source: str = 'recorded'
    fictitious: bool = False
    csv_format: CsvFormat = CsvFormat()

def analyze_pair(df,spec,profile):
    recommendation=recommend_test(df,spec,profile)
    fields=[spec.outcome,spec.predictor];pair=df[fields].replace('',np.nan).dropna()
    kinds={v.name:v.kind for v in profile.variables};kinds['ZARIT_CLASS']='categorical'
    cats=[f for f in fields if kinds.get(f)=='categorical']
    method=recommendation.method if spec.method=='auto' else spec.method
    if recommendation.blocked or method=='descriptive':
        result=TestResult('descriptive',len(pair),warnings=recommendation.reasons)
    elif len(cats)==2:
        table=pd.crosstab(pair[spec.predictor],pair[spec.outcome])
        event=table.columns.get_loc(spec.event_value) if spec.event_value in table.columns else None
        exposed=table.index.get_loc(spec.group_order[0]) if len(spec.group_order)==2 and spec.group_order[0] in table.index else None
        result=analyze_contingency(table.to_numpy(),method=method,event_column=event,exposed_row=exposed)
    elif len(cats)==1:
        group=cats[0];number=fields[1] if group==fields[0] else fields[0]
        order=spec.group_order or tuple(sorted(pair[group].unique()))
        groups=tuple(pd.to_numeric(pair.loc[pair[group]==g,number]).to_numpy(dtype=float) for g in order)
        result=compare_groups(groups,method=method,seed=20261104)
        descriptions=tuple(f'Grupo {group}={code}: n={len(values)}, média={np.mean(values):.3f}, mediana={np.median(values):.3f}.' for code,values in zip(order,groups))
        result.assumptions+=descriptions
        if len(groups)==2:result.assumptions+=(f'Ordem: {order[0]} e {order[1]}; diferença do primeiro menos segundo; superioridade do primeiro grupo.',)
    else:
        result=correlate(pd.to_numeric(pair[fields[0]]).to_numpy(float),pd.to_numeric(pair[fields[1]]).to_numpy(float),method=method,seed=20261104)
    result.n_missing=len(df)-len(pair)
    return AnalysisResult(spec,result)

def run_pipeline(*,manager,session,job,source_path,prepared,profile,options,progress=lambda _:None):
    manager._check(session,job)
    if source_path!=job.source_path or hashlib.sha256(source_path.read_bytes()).hexdigest()!=prepared.source_meta.source_sha256:
        raise DomainError('source','A fonte não corresponde à execução atual.')
    demo=options.fictitious and prepared.source_meta.source_sha256==DEMO_SHA256
    if options.fictitious and not demo:raise DomainError('demo_source','Use a base de demonstração fornecida para o modo fictício.')
    if options.score_source!='recorded':raise DomainError('psqi_rules','Recálculo PSQI indisponível até confirmação científica do manual.')
    issues=validate_dataset(prepared.data,profile).issues
    blockers=[i for i in issues if i.severity=='error' and not (demo and i.code=='mapping_pending')]
    if blockers:raise DomainError('validation','Corrija os erros de validação e confirme as legendas antes de analisar.')
    comparisons=freeze_comparisons(options.comparisons,profile)
    if not comparisons:raise DomainError('comparisons','Selecione ao menos um cruzamento.')
    if len(comparisons)>100:raise DomainError('comparisons','Selecione no máximo 100 cruzamentos por execução.')
    with manager.analysis(session,job):
        progress('Calculando cruzamentos e medidas descritivas')
        df=prepared.data.copy(deep=True)
        results=tuple(analyze_pair(df,c,profile) for c in comparisons)
        fields=tuple(v.name for v in profile.variables if v.name in df and v.kind!='text')
        summaries=describe(df,fields,profile)
        tables=build_tables(results,summaries,profile,data=df)
        meta=dict(profile_id=profile.id,profile_version=profile.version,profile_sha256=hashlib.sha256(json.dumps(asdict(profile),sort_keys=True,default=str).encode()).hexdigest(),source_sha256=prepared.source_meta.source_sha256,generated_at=datetime.now(timezone.utc).isoformat(),fictitious=demo,score_source='recorded',seed=20261104,package_versions={n:importlib.metadata.version(n) for n in ('streamlit','pandas','numpy','scipy','statsmodels','openpyxl','python-docx','reportlab')},code_version='0.1.0',mapping_confirmation=profile.confirmation or 'Demonstração com códigos neutros, sem aprovação científica',missing_policy='Pares completos; sem imputação',comparisons=[asdict(c) for c in comparisons],results=[asdict(a) for a in results],n_total=len(df),csv_format=asdict(options.csv_format),limitations=['PSQI informado: componentes não recalculados','Não comprova elegibilidade não observável no banco','Compatibilidade Epi Info requer teste na instalação Windows de destino'])
        progress('Gerando relatórios e arquivos de exportação')
        folder=job.directory
        files={'docx':render_docx(tables,meta,folder/'relatorio.docx'),'pdf':render_pdf(tables,meta,folder/'relatorio.pdf')}
        frames={f'Descritiva {i+1}':f for i,f in enumerate(tables.descriptive)}
        frames.update({f'Bivariada {i+1}':f for i,f in enumerate(tables.bivariate)})
        frames['Resultados numericos']=pd.DataFrame([dict(comparacao=a.spec.id,metodo=a.result.method,n=a.result.n_effective,p=a.result.p_value,estatistica=a.result.statistic) for a in results])
        files['tables']=write_xlsx(frames,folder/'tabelas.xlsx')
        export=export_epiinfo(df,profile,folder,options.csv_format)
        files.update({k:folder/v for k,v in export.files.items()})
        files['dictionary']=export_dictionary(profile,folder/'dicionario.xlsx')
        files['audit']=write_audit(prepared.transformations,profile,folder/'auditoria.json')
        meta.update(excluded_fields=export.excluded_fields,text_escapes=export.text_escapes,files_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files.values()})
        files['manifest']=write_json(folder/'manifesto.json',meta)
        manager.register_artifacts(session,job,files)
        files['zip']=manager.bundle_results(session,job)
        manager.complete(session,job)
        progress('Análise concluída')
        return RunArtifacts(files,tables,results,meta)
