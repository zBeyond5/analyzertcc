from dataclasses import dataclass,asdict,replace
from datetime import datetime,timezone
import hashlib,importlib.metadata,json
import numpy as np
import pandas as pd
from .models import DomainError,CsvFormat,AnalysisResult,TestResult,RunArtifacts
from .validation import validate_dataset,analysis_validation_issues
from .reporting import build_tables,render_docx,render_pdf
from .exports import export_epiinfo,export_dictionary,write_audit,write_xlsx,write_json
from .statistics.selection import freeze_comparisons,recommend_test
from .statistics.descriptive import describe
from .statistics.categorical import analyze_contingency
from .statistics.numeric import compare_groups,correlate
from .presentation import build_document
from .report_figures import build_chart_data,render_figure

DEMO_SHA256='e2a2fb48502e3a31b06af7c421417afc3819465a59c54127a1805fab3c137f3c'
UPDATED_DEMO_SHA256='833acfeb3e5fee0c384c825acbc825fde105962871d823da9e591b80c4c44d81'
@dataclass(frozen=True)
class RunOptions:
    comparisons: tuple
    score_source: str = 'recorded'
    fictitious: bool = False
    csv_format: CsvFormat = CsvFormat()
    population_policy: str = "auto"
    population_ack_signature: str | None = None

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
    trusted_demo=options.fictitious and prepared.source_meta.source_sha256 in (DEMO_SHA256,UPDATED_DEMO_SHA256)
    demo=bool(options.fictitious)
    if options.score_source!='recorded' and profile.psqi_rules.get('status')!='confirmed':raise DomainError('psqi_rules','A regra de pontuação deste questionário ainda não está definida.')
    issues=analysis_validation_issues(prepared,profile)
    blockers=[i for i in issues if i.severity=='error' and not (trusted_demo and i.code=='mapping_pending')]
    if blockers:raise DomainError('validation','Confira os problemas indicados nos dados antes de analisar.')
    from .analysis_population import select_population,population_signature
    population=select_population(prepared.data,profile)
    if options.population_policy not in ('auto',population.policy):raise DomainError('population','A política de análise mudou. Confira a população novamente.')
    if population.data.empty:raise DomainError('population','Nenhuma participante atende aos critérios observáveis. Complete os questionários; o banco original foi preservado.')
    if population.excluded and options.population_ack_signature!=population_signature(prepared,profile,population):raise DomainError('population_confirmation','Confira e confirme a quantidade de participantes elegíveis antes de analisar.')
    comparisons=freeze_comparisons(options.comparisons,profile)
    if not comparisons:raise DomainError('comparisons','Selecione ao menos um cruzamento.')
    if len(comparisons)>100:raise DomainError('comparisons','Selecione no máximo 100 cruzamentos por execução.')
    with manager.analysis(session,job):
        progress('Calculando cruzamentos e medidas descritivas')
        df=population.data
        results=tuple(analyze_pair(df,c,profile) for c in comparisons)
        fields=tuple(v.name for v in profile.variables if v.name in df and v.kind!='text')
        summaries=describe(df,fields,profile)
        origins={name:('calculado a partir das respostas' if any(t.field==name and t.reason.startswith('Escore gerado:') for t in prepared.transformations) else 'informado no banco') for name in ('PSQI','ZARIT')}
        reporting_profile=replace(profile,derived_rules={**profile.derived_rules,'score_origins':origins})
        tables=build_tables(results,summaries,reporting_profile,data=df)
        tables.notes+=(f'População: {len(prepared.data)} registros na fonte; {len(df)} incluídos; {len(population.excluded)} excluídos pelos critérios observáveis. Política {population.policy}.',)
        meta=dict(profile_id=profile.id,profile_version=profile.version,profile_sha256=hashlib.sha256(json.dumps(asdict(profile),sort_keys=True,default=str).encode()).hexdigest(),source_sha256=prepared.source_meta.source_sha256,generated_at=datetime.now(timezone.utc).isoformat(),fictitious=demo,score_source=('calculated_from_responses' if profile.instrument_mode=='responses' else 'recorded'),score_rules=profile.psqi_rules,seed=20261104,package_versions={n:importlib.metadata.version(n) for n in ('streamlit','pandas','numpy','scipy','statsmodels','openpyxl','python-docx','reportlab')},code_version='0.1.0',mapping_confirmation=profile.confirmation or 'Demonstração com códigos neutros, sem aprovação científica',missing_policy='Pares completos; sem imputação',comparisons=[asdict(c) for c in comparisons],results=[asdict(a) for a in results],n_total=len(df),csv_format=asdict(options.csv_format),limitations=[('PSQI calculado pelas regras documentadas' if profile.instrument_mode=='responses' else 'PSQI informado: componentes não recalculados'),'Não comprova elegibilidade não observável no banco','Compatibilidade Epi Info requer teste na instalação Windows de destino'])
        meta['score_source']='calculated_from_responses' if all('calculado' in v for v in origins.values()) else 'recorded' if all('informado' in v for v in origins.values()) else 'mixed'
        meta['limitations'][0]='PSQI: '+origins['PSQI']
        meta.update(score_origins=origins,alpha=.05,interpretation_version='av3-p-v1',population_policy=population.policy,n_source=len(prepared.data),n_included=len(df),included_rows=population.included_rows,excluded=population.excluded)
        document=build_document(results,tables,reporting_profile,df,meta)
        tables.narrative=tuple(c.reading for c in document.comparisons)
        tables.notes=document.summary+document.limitations
        if document.comparisons:
            tables.bivariate=(pd.DataFrame([[c.title,c.n_effective,c.method_label,c.p_display or 'Não calculado',c.interpretation,'; '.join(c.estimates) or 'Sem estimativa global disponível'] for c in document.comparisons],columns=['Comparação','Participantes','Método','Valor de p','Interpretação','Estimativa / intervalo de confiança de 95%']),)
        figures=build_report_figures(df,profile,comparisons,manager.settings.max_artifact_bytes)
        meta['presentation_version']='readable-reports-v1'
        meta['report_style']='editorial'
        progress('Gerando relatórios e arquivos de exportação')
        folder=job.directory
        files={'docx':render_docx(tables,meta,folder/'relatorio.docx',document=document,figures=figures),'pdf':render_pdf(tables,meta,folder/'relatorio.pdf',document=document,figures=figures)}
        frames={f'Descritiva {i+1}':f for i,f in enumerate(tables.descriptive)}
        frames.update({f'Bivariada {i+1}':f for i,f in enumerate(tables.bivariate)})
        frames['Resultados numéricos']=pd.DataFrame([[c.title,c.method_label,a.result.n_effective,a.result.p_value,a.result.statistic] for a,c in zip(results,document.comparisons)],columns=['Comparação','Método','Participantes','Valor de p','Estatística do teste'])
        frames['Glossário']=pd.DataFrame(document.glossary.items(),columns=['Termo','Significado'])
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
        return RunArtifacts(files,tables,results,meta,document)


def build_report_figures(data,profile,comparisons,max_bytes):
    figures={};total=0
    for spec in comparisons:
        chart=build_chart_data(data,profile,spec)
        if chart is None:continue
        png=render_figure(chart);total+=len(png)
        if total>max_bytes:raise DomainError('artifact_size','Os gráficos excedem o limite desta exportação. Reduza os cruzamentos para gerar o relatório completo.')
        figures[spec.id]=png;figures[spec.id+'_caption']=chart.caption
    return figures


def refresh_report_style(*,manager,session,job,artifacts,data,profile,style):
    """Replace only document presentation; calculations, bank and expiry are retained."""
    from pathlib import Path
    from tempfile import TemporaryDirectory
    import os,shutil,zipfile
    from .reporting import load_report_style
    load_report_style(style)
    manager._check(session,job)
    if style==artifacts.metadata.get('report_style'):return artifacts
    with manager.presentation(session,job):
        figures=build_report_figures(data,profile,tuple(a.spec for a in artifacts.results),manager.settings.max_artifact_bytes)
        meta={**artifacts.metadata,'report_style':style,'files_sha256':dict(artifacts.metadata['files_sha256'])}
        with TemporaryDirectory(prefix='.presentation-',dir=job.directory) as temporary:
            stage=Path(temporary)
            if not stage.resolve().is_relative_to(job.directory.resolve()):raise DomainError('access','Diretório de exportação inválido.')
            docx=render_docx(artifacts.tables,meta,stage/'relatorio.docx',document=artifacts.presentation,figures=figures,style=style)
            pdf=render_pdf(artifacts.tables,meta,stage/'relatorio.pdf',document=artifacts.presentation,figures=figures,style=style)
            for path in (docx,pdf):meta['files_sha256'][path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
            manifest=write_json(stage/'manifesto.json',meta)
            archive=stage/'resultado_completo.zip'
            with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as zipped:
                for key,path in job.artifacts.items():
                    if key=='zip':continue
                    replacement=stage/path.name
                    zipped.write(replacement if replacement.exists() else path,path.name)
            replacements={'docx':docx,'pdf':pdf,'manifest':manifest,'zip':archive}
            if any(p.stat().st_size>manager.settings.max_artifact_bytes for p in replacements.values()):
                raise DomainError('artifact_size','O relatório excede o limite de download. Reduza os cruzamentos.')
            backup=stage/'backup';backup.mkdir()
            moved=[]
            try:
                for key,path in replacements.items():
                    destination=job.artifacts[key]
                    shutil.copy2(destination,backup/destination.name)
                    os.replace(path,destination);moved.append(destination)
            except BaseException:
                for path in moved:os.replace(backup/path.name,path)
                raise
        return RunArtifacts(dict(artifacts.files),artifacts.tables,artifacts.results,meta,artifacts.presentation)
