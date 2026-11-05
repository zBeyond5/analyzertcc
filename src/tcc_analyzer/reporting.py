from pathlib import Path
from xml.sax.saxutils import escape
import pandas as pd
from .models import ReportTables
from .interpretation import interpret_p,LABELS
from .presentation import field_title,category_title,ReportDocument,readable_number

FICTITIOUS='Dados fictícios para teste; não representam resultados da pesquisa.'
MULTIPLICITY='Valores de p bilaterais sem ajuste; análises exploratórias estão sujeitas à multiplicidade. Associações não demonstram causalidade.'
METHOD_LABELS={'welch_t':'Welch t','welch_anova':'Welch ANOVA','mann_whitney':'Mann–Whitney','kruskal':'Kruskal–Wallis','spearman':'Spearman','pearson':'Pearson','fisher':'Fisher exato','chi_square':'Qui-quadrado','descriptive':'Descritiva'}
EFFECT_LABELS={'mean_difference':'Diferença média','odds_ratio':'Razão de chances (OR)','prevalence_ratio':'Razão de prevalências','probability_superiority':'Probabilidade de superioridade','correlation':'Correlação'}
FAMILY_LABELS={'primary':'principal','complementary':'complementar','exploratory':'exploratória'}
P_LABELS={'parametric':'paramétrico','asymptotic':'assintótico','exact':'exato','permutation_exact':'permutação exaustiva','not_computed':'não calculado'}

def number(v,digits=1):
    return '' if v is None or pd.isna(v) else f'{float(v):.{digits}f}'.replace('.',',')

def format_p(value):
    from .interpretation import interpret_p
    return interpret_p(value,p_kind='reported')['p_display']


def build_tables(results,summaries,profile,*,data=None):
    variables={v.name:v for v in profile.variables};frames=[]
    groups=(('IDADE_M','SIT_CONJ','ESCOL','RENDA','RED_APO','FILHOS','TRAB_NOT','IDADE_C','SEXO'),('DOENCA','ANTIDEP','ANSIED','DEPRE','TEMP_TEA','ACOMP_TEP','FISIO','FONO','TER_OCUP','PSI','PSICOP','FREQ_TEP','ALT_SONO','DESP_NOT','CHORO','SUPERV'),('PSQI','PSQI_G','ZARIT','ZARIT_CLASS'))
    if data is not None:
        for fields in groups:
            rows=[]
            for name in fields:
                if name not in data:continue
                var=variables.get(name);label=field_title(name,profile);valid=data[name].dropna();n=len(valid)
                if name in ('ZARIT_CLASS','PSQI_G') or (var and var.kind in ('categorical','ordinal')):
                    for code,count in valid.value_counts().sort_index().items():
                        labels={1:'Ausente ou leve (0–20)',2:'Moderada (21–40)',3:'Moderada a severa (41–60)',4:'Severa (61–88)'} if name=='ZARIT_CLASS' else (var.labels if var else {})
                        category=category_title(name,code,profile)
                        denominator=len(data) if name in ('FISIO','FONO','TER_OCUP','PSI','PSICOP') else n
                        rows.append([label,str(category),int(count),number(100*count/denominator)+'%' if denominator else 'Não disponível'])
                else:
                    numeric=pd.to_numeric(valid,errors='coerce').dropna()
                    rows.append([label,'Média (desvio padrão amostral)',len(numeric),f'{readable_number(numeric.mean())} ({readable_number(numeric.std(ddof=1))})'])
                    rows.append([label,'Mediana [50% centrais]',len(numeric),f'{readable_number(numeric.median())} [{readable_number(numeric.quantile(.25))}; {readable_number(numeric.quantile(.75))}]'])
                if len(data)>n:rows.append([label,'Ausentes',len(data)-n,'Não imputados'])
            frames.append(pd.DataFrame(rows,columns=['Variável','Medida / categoria','Participantes','Resultado']))
    else:
        for _ in groups:frames.append(pd.DataFrame(columns=['Variável','Medida / categoria','Participantes','Resultado']))
    bivariate=[];narrative=[];notes=[MULTIPLICITY,'Percentuais por respostas válidas da variável; terapias múltiplas usam o total de participantes, com ausentes indicados separadamente.','Critério do projeto: p < 0,05, por comparação; o p não mede a importância prática.']
    origin=profile.derived_rules.get('score_origins',{})
    for instrument in ('PSQI','ZARIT'):
        source=origin.get(instrument,'calculado a partir das respostas' if profile.instrument_mode=='responses' else 'informado no banco')
        notes.append(f'{instrument}: {source}.')
    if profile.instrument_mode=='responses':notes.append('Modelo do banco atualizado: renda, escolaridade e estado civil agrupados diferem do Apêndice II. Não foram reconstruídas categorias detalhadas. Critérios não observáveis de elegibilidade não foram certificados.')
    rows=[]
    for analysis in results:
        s=analysis.spec;r=analysis.result;effect=[]
        for name,e in r.effects.items():
            text=f'{EFFECT_LABELS.get(name,name)}: {number(e.value,3)}'
            text+=f' [{number(e.ci95[0],3)}; {number(e.ci95[1],3)}]' if e.ci95 else ' (IC não disponível: '+str(e.unavailable_reason or 'método/amostra insuficiente')+')'
            effect.append(text)
        interpretation=interpret_p(r.p_value,p_kind=r.p_kind)
        method=METHOD_LABELS.get(r.method,r.method)
        rows.append([f'{s.outcome} × {s.predictor}',r.n_effective,method,interpretation['p_display'],LABELS[interpretation['status']],'; '.join(effect) or 'Sem estimativa global'])
        narrative.append(f"{s.outcome} e {s.predictor}: análise {FAMILY_LABELS.get(s.family,s.family)}, {method}, n={r.n_effective}, p={interpretation['p_display']}. {LABELS[interpretation['status']]}. {interpretation['explanation']}")
        warnings=[text.replace('zero_cell_no_automatic_correction','Célula zero: nenhuma correção automática aplicada') for text in r.warnings]
        notes.append(f'{s.outcome} × {s.predictor}: ausentes={r.n_missing}; p {P_LABELS.get(r.p_kind,r.p_kind)}; pressupostos: '+', '.join(r.assumptions)+'; avisos: '+(', '.join(warnings) or 'nenhum adicional'))
    if rows:bivariate.append(pd.DataFrame(rows,columns=['Comparação','n','Método','p','Interpretação','Estimativa / IC95%']))
    return ReportTables(tuple(frames),tuple(bivariate),tuple(notes),tuple(narrative))


def table_widths(frame,available_width):
    if not len(frame.columns):return ()
    weights=[1.25,1.6,.65,1.1] if len(frame.columns)==4 else [1.5,.65,1,.65,1.3,1.8] if len(frame.columns)==6 else [1]*len(frame.columns)
    return tuple(available_width*w/sum(weights) for w in weights)


def _fallback_document(tables,metadata):
    summary=('Origem dos instrumentos: '+str(metadata.get('score_origins') or metadata.get('score_source','não registrada'))+'.',)
    return ReportDocument('Resultados da análise bivariada',summary,(),{},(MULTIPLICITY,),tuple(tables.narrative+tables.notes))


def _blocks(tables,metadata,document,figures):
    """One content order for both formats; renderers own pagination."""
    yield 'title',document.title,None
    if metadata.get('fictitious'):yield 'warning',FICTITIOUS,None
    if metadata.get('generated_at'):yield 'small','Gerado em '+str(metadata['generated_at'])[:10]+'.',None
    yield 'h1','1. Base analisada',None
    for text in document.summary:yield 'text',text,None
    yield 'h1','2. Procedimentos estatísticos',None
    yield 'text','Foram utilizadas respostas completas em cada comparação, sem imputação. O critério de significância do projeto é valor de p menor que 0,05. Análises bivariadas não incluem ajuste por confundidores.',None
    for label,description in dict.fromkeys((c.method_label,c.method_explanation) for c in document.comparisons):
        yield 'text',f'{label}: {description}',None
    yield 'h1','3. Caracterização das participantes',None
    table_number=0
    for frame,title in zip(tables.descriptive,('Características sociodemográficas','Características clínicas','Instrumentos de avaliação')):
        if frame.empty:continue
        table_number+=1
        yield 'table_caption',f'Tabela {table_number}. {title}',None
        yield 'table','',frame
        yield 'small','Percentuais por respostas válidas. Terapias múltiplas usam o total de participantes e podem somar mais de 100%; ausências são indicadas separadamente.',None
    yield 'h1','4. Resultados das comparações',None
    figure_number=0
    if not document.comparisons:yield 'text','Nenhuma comparação foi incluída neste documento.',None
    for i,c in enumerate(document.comparisons,1):
        yield 'h2',f'4.{i}. {c.title}',None
        yield 'small',c.family_label,None
        yield 'text',c.reading,None
        yield 'text',c.method_label+'. '+c.method_explanation,None
        for text in c.estimates:yield 'text',text,None
        for text in c.warnings:yield 'warning',text,None
        if c.id in figures:
            figure_number+=1
            yield 'figure_caption',f'Figura {figure_number}. {c.title}',None
            yield 'image','',figures[c.id]
            yield 'small',figures.get(c.id+'_caption','Distribuição das respostas completas desta comparação.'),None
            yield 'small','Fonte: elaboração do aplicativo a partir do banco informado.'+(' Dados fictícios para demonstração.' if metadata.get('fictitious') else ''),None
    yield 'h1','5. Limitações da análise',None
    for text in document.limitations:yield 'text',text,None
    if document.glossary:
        yield 'h1','6. Como ler este relatório — Glossário',None
        for term,meaning in document.glossary.items():yield 'text',term+': '+meaning,None
    yield 'h1','Apêndice técnico',None
    yield 'text','Códigos, métodos e notas originais são preservados abaixo para rastreabilidade. As condições de aplicação de um teste não constituem confirmação do desenho do estudo.',None
    for frame in tables.bivariate:
        if not frame.empty:yield 'table','',frame
    for text in document.technical_notes:yield 'small',text,None
    if metadata.get('source_sha256'):yield 'small','SHA-256 da fonte: '+metadata['source_sha256'],None


def _pdf_styles():
    import matplotlib
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.lib import colors
    fonts=Path(matplotlib.get_data_path())/'fonts/ttf'
    for name,filename in (('DejaVuSans','DejaVuSans.ttf'),('DejaVuSans-Bold','DejaVuSans-Bold.ttf')):
        if name not in pdfmetrics.getRegisteredFontNames():pdfmetrics.registerFont(TTFont(name,str(fonts/filename)))
    pdfmetrics.registerFontFamily('DejaVuSans',normal='DejaVuSans',bold='DejaVuSans-Bold',italic='DejaVuSans',boldItalic='DejaVuSans-Bold')
    styles=getSampleStyleSheet()
    for name in ('Normal','Title','Heading1','Heading2'):
        styles[name].fontName='DejaVuSans' if name=='Normal' else 'DejaVuSans-Bold'
        styles[name].textColor=colors.HexColor('#23343B')
    styles['Normal'].fontSize=11;styles['Normal'].leading=16;styles['Normal'].spaceAfter=8
    styles['Title'].fontSize=23;styles['Title'].leading=29;styles['Title'].alignment=0
    styles['Heading1'].fontSize=15;styles['Heading1'].leading=20;styles['Heading1'].spaceBefore=16
    styles['Heading2'].fontSize=12;styles['Heading2'].leading=17;styles['Heading2'].spaceBefore=12
    styles.add(ParagraphStyle('Cell',fontName='DejaVuSans',fontSize=9,leading=12,wordWrap='CJK'))
    styles.add(ParagraphStyle('Small',parent=styles['Normal'],fontSize=9,leading=13,textColor=colors.HexColor('#52616B')))
    styles.add(ParagraphStyle('Caption',parent=styles['Small'],fontName='DejaVuSans-Bold',keepWithNext=True))
    styles.add(ParagraphStyle('Warning',parent=styles['Normal'],backColor=colors.HexColor('#E7F1F2'),borderPadding=7,spaceBefore=8,spaceAfter=12))
    return styles


def render_pdf(tables,metadata,output,*,document=None,figures=None):
    from io import BytesIO
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,LongTable,TableStyle,Image
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    document=document or _fallback_document(tables,metadata);figures=figures or {}
    styles=_pdf_styles();available=A4[0]-100;elements=[]
    for kind,text,value in _blocks(tables,metadata,document,figures):
        if kind=='table':
            rows=[list(value.columns)]+list(value.itertuples(index=False,name=None))
            cells=[[Paragraph(escape(str(v)),styles['Cell']) for v in row] for row in rows]
            table=LongTable(cells,colWidths=table_widths(value,available),repeatRows=1,hAlign='LEFT',splitInRow=1)
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E7F1F2')),('VALIGN',(0,0),(-1,-1),'TOP'),
                ('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor('#216C72')),('LINEBELOW',(0,1),(-1,-1),.2,colors.HexColor('#D8E1E4')),
                ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
            elements.extend((table,Spacer(1,10)))
        elif kind=='image':
            img=Image(BytesIO(value));scale=min(available/img.imageWidth,290/img.imageHeight)
            img.drawWidth=img.imageWidth*scale;img.drawHeight=img.imageHeight*scale;img.hAlign='LEFT'
            elements.extend((img,Spacer(1,5)))
        else:
            style={'title':'Title','h1':'Heading1','h2':'Heading2','small':'Small','warning':'Warning',
                   'figure_caption':'Caption','table_caption':'Caption'}.get(kind,'Normal')
            elements.append(Paragraph(escape(str(text)),styles[style]))
    def footer(canvas,doc):
        canvas.setFont('DejaVuSans',9);canvas.setFillColor(colors.HexColor('#52616B'))
        canvas.drawString(50,25,'Dados fictícios • demonstração' if metadata.get('fictitious') else 'Relatório de análise')
        canvas.drawRightString(A4[0]-50,25,str(doc.page))
    SimpleDocTemplate(str(output),pagesize=A4,leftMargin=50,rightMargin=50,topMargin=50,bottomMargin=50,title=document.title,author='').build(elements,onFirstPage=footer,onLaterPages=footer)
    return Path(output)


def render_docx(tables,metadata,output,*,document=None,figures=None):
    from io import BytesIO
    from docx import Document
    from docx.shared import Pt,RGBColor
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from PIL import Image
    doc=Document();section=doc.sections[0]
    section.page_width=Pt(595.28);section.page_height=Pt(841.89)
    section.top_margin=section.bottom_margin=section.left_margin=section.right_margin=Pt(50)
    for name in ('Normal','Title','Heading 1','Heading 2','Caption'):
        style=doc.styles[name];style.font.name='DejaVu Sans';style.font.color.rgb=RGBColor.from_string('23343B')
    normal=doc.styles['Normal'];normal.font.size=Pt(11);normal.paragraph_format.line_spacing=1.35
    normal.paragraph_format.space_after=Pt(8)
    for name in ('Heading 1','Heading 2','Caption'):doc.styles[name].paragraph_format.keep_with_next=True
    doc.styles['Caption'].font.size=Pt(9)
    document=document or _fallback_document(tables,metadata);figures=figures or {}
    for kind,text,value in _blocks(tables,metadata,document,figures):
        if kind=='table':
            table=doc.add_table(rows=1,cols=len(value.columns));table.style='Light Shading Accent 1'
            header=OxmlElement('w:tblHeader');table.rows[0]._tr.get_or_add_trPr().append(header)
            for cell,v in zip(table.rows[0].cells,value.columns):cell.text=str(v)
            for row in value.itertuples(index=False,name=None):
                for cell,v in zip(table.add_row().cells,row):cell.text=str(v)
            for row in table.rows:
                for cell,width in zip(row.cells,table_widths(value,495)):
                    cell.width=Pt(width)
                    for paragraph in cell.paragraphs:
                        for run in paragraph.runs:run.font.size=Pt(9)
        elif kind=='image':
            image=Image.open(BytesIO(value));width,height=image.size;scale=min(495/width,290/height)
            doc.add_picture(BytesIO(value),width=Pt(width*scale),height=Pt(height*scale))
        elif kind in ('title','h1','h2'):doc.add_heading(text,{'title':0,'h1':1,'h2':2}[kind])
        else:
            paragraph=doc.add_paragraph(text,style='Caption' if kind.endswith('_caption') else None)
            if kind=='small':
                for run in paragraph.runs:run.font.size=Pt(9)
    footer=section.footer.paragraphs[0]
    footer.add_run(('Dados fictícios • demonstração' if metadata.get('fictitious') else 'Relatório de análise')+' | Página ')
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)
    for run in footer.runs:run.font.size=Pt(9)
    doc.core_properties.author='';doc.core_properties.title=document.title
    doc.save(output)
    return Path(output)

