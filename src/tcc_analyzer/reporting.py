from pathlib import Path
from xml.sax.saxutils import escape
import pandas as pd
from .models import ReportTables

FICTITIOUS='Dados fictícios para teste; não representam resultados da pesquisa.'
MULTIPLICITY='Valores de p bilaterais sem ajuste; análises exploratórias estão sujeitas à multiplicidade. Associações não demonstram causalidade.'
METHOD_LABELS={'welch_t':'Welch t','welch_anova':'Welch ANOVA','mann_whitney':'Mann–Whitney','kruskal':'Kruskal–Wallis','spearman':'Spearman','pearson':'Pearson','fisher':'Fisher exato','chi_square':'Qui-quadrado','descriptive':'Descritiva'}
EFFECT_LABELS={'mean_difference':'Diferença média','odds_ratio':'Razão de chances (OR)','prevalence_ratio':'Razão de prevalências','probability_superiority':'Probabilidade de superioridade','correlation':'Correlação'}
FAMILY_LABELS={'primary':'principal','complementary':'complementar','exploratory':'exploratória'}
P_LABELS={'parametric':'paramétrico','asymptotic':'assintótico','exact':'exato','permutation_exact':'permutação exaustiva','not_computed':'não calculado'}

def number(v,digits=1):
    return '' if v is None or pd.isna(v) else f'{float(v):.{digits}f}'.replace('.',',')

def format_p(value):
    if value is None or pd.isna(value):return 'Não calculado'
    return '<0,001' if value<.001 else number(value,3)

def build_tables(results,summaries,profile,*,data=None):
    variables={v.name:v for v in profile.variables};frames=[]
    groups=(('IDADE_M','SIT_CONJ','ESCOL','RENDA','RED_APO','FILHOS','TRAB_NOT','IDADE_C','SEXO'),('DOENCA','ANTIDEP','ANSIED','DEPRE','TEMP_TEA','ACOMP_TEP','FISIO','FONO','TER_OCUP','PSI','PSICOP','FREQ_TEP','ALT_SONO','DESP_NOT','CHORO','SUPERV'),('PSQI','PSQI_G','ZARIT','ZARIT_CLASS'))
    if data is not None:
        for fields in groups:
            rows=[]
            for name in fields:
                if name not in data:continue
                var=variables.get(name);label=var.label if var else 'Classificação Zarit';valid=data[name].dropna();n=len(valid)
                if name in ('ZARIT_CLASS','PSQI_G') or (var and var.kind in ('categorical','ordinal')):
                    for code,count in valid.value_counts().sort_index().items():
                        labels={1:'Ausente ou leve (0–20)',2:'Moderada (21–40)',3:'Moderada a severa (41–60)',4:'Severa (61–88)'} if name=='ZARIT_CLASS' else (var.labels if var else {})
                        category=labels.get(code,f'Código {code}')
                        denominator=len(data) if name in ('FISIO','FONO','TER_OCUP','PSI','PSICOP') else n
                        rows.append([label,str(category),int(count),number(100*count/denominator)+'%'])
                else:
                    numeric=pd.to_numeric(valid,errors='coerce').dropna()
                    rows.append([label,'Média (DP amostral)',len(numeric),f'{number(numeric.mean())} ({number(numeric.std(ddof=1))})'])
                    rows.append([label,'Mediana [Q1; Q3]',len(numeric),f'{number(numeric.median())} [{number(numeric.quantile(.25))}; {number(numeric.quantile(.75))}]'])
                if len(data)>n:rows.append([label,'Ausentes',len(data)-n,'Não imputados'])
            frames.append(pd.DataFrame(rows,columns=['Variável','Medida / categoria','n','Resultado']))
    else:
        for _ in groups:frames.append(pd.DataFrame(columns=['Variável','Medida / categoria','n','Resultado']))
    bivariate=[];narrative=[];notes=[MULTIPLICITY,'Percentuais por respostas válidas da variável; terapias múltiplas usam o total de participantes, com ausentes indicados separadamente.','PSQI informado: recálculo dos componentes pendente de confirmação do manual.']
    rows=[]
    for analysis in results:
        s=analysis.spec;r=analysis.result;effect=[]
        for name,e in r.effects.items():
            text=f'{EFFECT_LABELS.get(name,name)}: {number(e.value,3)}'
            text+=f' [{number(e.ci95[0],3)}; {number(e.ci95[1],3)}]' if e.ci95 else ' (IC não disponível: '+str(e.unavailable_reason or 'método/amostra insuficiente')+')'
            effect.append(text)
        method=METHOD_LABELS.get(r.method,r.method)
        rows.append([f'{s.outcome} × {s.predictor}',r.n_effective,method,format_p(r.p_value),'; '.join(effect) or 'Sem estimativa global'])
        narrative.append(f'{s.outcome} e {s.predictor}: análise {FAMILY_LABELS.get(s.family,s.family)}, {method}, n={r.n_effective}, p={format_p(r.p_value)}. '+('Não foi calculada inferência para esta comparação.' if r.p_value is None else 'A comparação descreve associação, sem estabelecer causalidade.'))
        warnings=[text.replace('zero_cell_no_automatic_correction','Célula zero: nenhuma correção automática aplicada') for text in r.warnings]
        notes.append(f'{s.outcome} × {s.predictor}: ausentes={r.n_missing}; p {P_LABELS.get(r.p_kind,r.p_kind)}; pressupostos: '+', '.join(r.assumptions)+'; avisos: '+(', '.join(warnings) or 'nenhum adicional'))
    if rows:bivariate.append(pd.DataFrame(rows,columns=['Comparação','n','Método','p','Estimativa / IC95%']))
    return ReportTables(tuple(frames),tuple(bivariate),tuple(notes),tuple(narrative))

def render_docx(tables,metadata,output):
    from docx import Document
    from docx.shared import Inches,Pt,RGBColor
    doc=Document();section=doc.sections[0];section.top_margin=Inches(.75);section.bottom_margin=Inches(.75)
    normal=doc.styles['Normal'];normal.font.name='Calibri';normal.font.size=Pt(10)
    for name in ('Title','Heading 1','Heading 2'):doc.styles[name].font.color.rgb=RGBColor(0,0,0)
    doc.add_heading('Análise bivariada do TCC',0)
    if metadata.get('fictitious'):doc.add_paragraph(FICTITIOUS)
    doc.add_paragraph('Perfil '+str(metadata.get('profile_id',''))+' | Origem do PSQI: informado. Estudo transversal.')
    titles=['Características sociodemográficas','Características clínicas','Instrumentos de avaliação']
    for i,frame in enumerate(tables.descriptive+tables.bivariate):
        doc.add_heading(f'Tabela {i+1} '+(titles[i] if i<3 else 'Comparações bivariadas'),1)
        table=doc.add_table(rows=1,cols=len(frame.columns));table.style='Light Shading Accent 1'
        for cell,value in zip(table.rows[0].cells,frame.columns):cell.text=str(value)
        for row in frame.itertuples(index=False,name=None):
            for cell,value in zip(table.add_row().cells,row):cell.text=str(value)
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:run.font.size=Pt(8)
    doc.add_heading('Resultados e limitações',1)
    for text in tables.narrative+tables.notes:doc.add_paragraph(text)
    doc.add_paragraph('SHA-256 da fonte: '+metadata.get('source_sha256',''))
    doc.save(output);return Path(output)

def render_pdf(tables,metadata,output):
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,LongTable,TableStyle
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    styles=getSampleStyleSheet();styles.add(ParagraphStyle(name='Cell',fontName='Helvetica',fontSize=8,leading=10))
    elements=[Paragraph('Análise bivariada do TCC',styles['Title'])]
    if metadata.get('fictitious'):elements += [Paragraph(FICTITIOUS,styles['Normal']),Spacer(1,10)]
    elements += [Paragraph('Perfil '+escape(str(metadata.get('profile_id','')))+' | PSQI informado. Estudo transversal.',styles['Normal']),Spacer(1,12)]
    titles=['Características sociodemográficas','Características clínicas','Instrumentos de avaliação']
    for i,frame in enumerate(tables.descriptive+tables.bivariate):
        elements += [Paragraph(f'Tabela {i+1} '+(titles[i] if i<3 else 'Comparações bivariadas'),styles['Heading2'])]
        records=[list(frame.columns)]+list(frame.itertuples(index=False,name=None))
        cells=[[Paragraph(escape(str(v)),styles['Cell']) for v in row] for row in records]
        widths=[145,165,30,155] if len(frame.columns)==4 else [120,25,75,45,230]
        table=LongTable(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#DCEBEF')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#CBD8DE')),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
        elements += [table,Spacer(1,12)]
    elements += [Paragraph('Resultados e limitações',styles['Heading2'])]
    for text in tables.narrative+tables.notes:elements += [Paragraph(escape(text),styles['Normal']),Spacer(1,6)]
    def footer(canvas,doc):
        canvas.setFont('Helvetica',8);canvas.drawString(50,28,'Análise local | '+('Dados fictícios' if metadata.get('fictitious') else 'Relatório de pesquisa'));canvas.drawRightString(545,28,str(doc.page))
    SimpleDocTemplate(str(output),pagesize=A4,leftMargin=50,rightMargin=50,topMargin=45,bottomMargin=45).build(elements,onFirstPage=footer,onLaterPages=footer)
    return Path(output)
