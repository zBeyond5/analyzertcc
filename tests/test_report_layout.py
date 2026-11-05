from dataclasses import replace
from pathlib import Path
import pandas as pd
from pypdf import PdfReader
from docx import Document
from tcc_analyzer.models import ComparisonSpec, AnalysisResult, TestResult as StatisticalResult, EffectEstimate
from tcc_analyzer.profiles import load_updated_profile
from tcc_analyzer.presentation import build_document
from tcc_analyzer.reporting import build_tables, render_pdf, render_docx, table_widths
from tcc_analyzer.report_figures import build_chart_data, render_figure


def report_example():
    p=load_updated_profile()
    data=pd.DataFrame({'PSQI_G':[1,1,2,2,2], 'ZARIT':[10,20,30,50,60], 'PSQI':[2,4,7,9,10], 'ESCOL':[1,2,3,4,4], 'NOME':['PRIVATE-NAME']*5})
    spec=ComparisonSpec('burden','PSQI_G','ZARIT','primary','welch_t')
    analysis=AnalysisResult(spec,StatisticalResult('welch_t',5,p_value=.096,p_kind='parametric',effects={'mean_difference':EffectEstimate(-31,(-50,2))}))
    tables=build_tables((analysis,),(),p,data=data)
    meta={'fictitious':True,'n_source':5,'n_included':5,'score_origins':{'PSQI':'calculado a partir das respostas','ZARIT':'informado no banco'},'source_sha256':'demo-hash'}
    document=build_document((analysis,),tables,p,data,meta)
    png=render_figure(build_chart_data(data,p,spec))
    return tables,meta,document,{'burden':png}


def test_pdf_and_word_have_real_figures_readable_body_and_font(tmp_path):
    tables,meta,document,figures=report_example()
    pdf=render_pdf(tables,meta,tmp_path/'report.pdf',document=document,figures=figures)
    reader=PdfReader(pdf);text='\n'.join(p.extract_text() for p in reader.pages)
    main=text.split('Apêndice técnico')[0]
    assert 'Classificação da qualidade do sono' in main
    assert 'PSQI_G × ZARIT' not in main and 'PRIVATE-NAME' not in text
    assert sum(len(p.images) for p in reader.pages)>=1
    assert all('Dados fictícios' in p.extract_text() for p in reader.pages)
    assert 'calculado a partir das respostas' in text
    word=Document(render_docx(tables,meta,tmp_path/'report.docx',document=document,figures=figures))
    assert len(word.inline_shapes)==1
    assert 'Glossário' in ' '.join(p.text for p in word.paragraphs)
    assert 'tblHeader' in word.tables[0].rows[0]._tr.xml


def test_six_columns_and_long_unicode_values_fit_page(tmp_path):
    tables,meta,document,figures=report_example()
    for frame in tables.bivariate:
        assert len(table_widths(frame,495))==len(frame.columns)
        assert abs(sum(table_widths(frame,495))-495)<.01
    title='Descrição <>& com acentuação e palavras extensas '+('personalização '*20)
    document=replace(document,comparisons=(replace(document.comparisons[0],title=title),))
    pdf=render_pdf(tables,meta,tmp_path/'long.pdf',document=document,figures=figures)
    import pymupdf
    with pymupdf.open(pdf) as doc:
        assert all(40<=b[0] and b[2]<=page.rect.width-38 for page in doc for b in page.get_text('blocks') if str(b[4]).strip())
    assert 'personalização' in '\n'.join(p.extract_text() for p in PdfReader(pdf).pages)


def test_toc_links_point_to_real_pages_and_article_has_no_monograph_structure(tmp_path):
    import pytest
    import pymupdf
    from tcc_analyzer.reporting import load_report_style
    assert load_report_style('editorial')['include_toc'] is True
    assert load_report_style('article')['include_toc'] is False
    with pytest.raises(ValueError):load_report_style('../outro')
    tables,meta,document,figures=report_example()
    pdf=render_pdf(tables,meta,tmp_path/'complete.pdf',document=document,figures=figures)
    with pymupdf.open(pdf) as doc:
        toc=doc.get_toc()
        assert len(toc)>=6
        for level,title,page in toc:
            assert title in doc[page-1].get_text().replace('\n',' ')
        links=[link for page in doc for link in page.get_links() if link['kind']==pymupdf.LINK_GOTO]
        assert len(links)>=len(toc)
        assert 'Lista de figuras' in ''.join(page.get_text() for page in doc)
    article=render_pdf(tables,meta,tmp_path/'article.pdf',document=document,figures=figures,style='article')
    text='\n'.join(page.extract_text() for page in PdfReader(article).pages)
    assert 'Material para o artigo' in text and '0,096' in text
    assert 'Apêndice técnico' not in text and 'Sumário' not in text and 'Glossário' not in text
    assert 'conforme UNEB' not in text
    word=Document(render_docx(tables,meta,tmp_path/'complete.docx',document=document,figures=figures))
    assert 'TOC ' in word._element.xml
    word=Document(render_docx(tables,meta,tmp_path/'article.docx',document=document,figures=figures,style='article'))
    assert 'TOC ' not in word._element.xml


def test_empty_and_hundred_comparison_documents_are_complete(tmp_path):
    import pymupdf
    tables,meta,document,figures=report_example()
    empty=replace(document,comparisons=())
    path=render_pdf(tables,meta,tmp_path/'empty.pdf',document=empty)
    text=' '.join(p.extract_text() for p in PdfReader(path).pages)
    assert 'Lista de figuras' not in text and 'Nenhuma comparação' in text
    comparisons=tuple(replace(document.comparisons[0],id=f'comparison-{i}',title=f'Comparação de demonstração {i}') for i in range(100))
    document=replace(document,comparisons=comparisons)
    png=figures['burden'];figures={c.id:png for c in comparisons}
    path=render_pdf(tables,meta,tmp_path/'hundred.pdf',document=document,figures=figures)
    with pymupdf.open(path) as doc:
        toc=doc.get_toc()
        assert sum(title.startswith('4.') and level==2 for level,title,page in toc)==100
        assert all(title in doc[page-1].get_text().replace('\n',' ') for level,title,page in toc)
        assert path.stat().st_size<64*1024**2


def test_section_heading_stays_with_the_first_table(fictitious_df,tmp_path):
    import pymupdf
    from tcc_analyzer.profiles import load_profile
    p=load_profile()
    results=tuple(AnalysisResult(ComparisonSpec(str(i),'PSQI_G','ZARIT'),StatisticalResult(method,30)) for i,method in enumerate(('welch_t','descriptive','spearman','fisher')))
    tables=build_tables(results,(),p,data=fictitious_df)
    meta={'score_origins':{'PSQI':'informado no banco','ZARIT':'informado no banco'},'fictitious':True}
    document=build_document(results,tables,p,fictitious_df,meta)
    path=render_pdf(tables,meta,tmp_path/'headings.pdf',document=document)
    with pymupdf.open(path) as doc:
        for page in doc:
            spans=[s for b in page.get_text('dict')['blocks'] if 'lines' in b for line in b['lines'] for s in line['spans']]
            if any('3. Caracterização' in s['text'] and s['size']>=14 for s in spans):
                assert 'Tabela 1.' in page.get_text()


def test_shared_unicode_font_is_not_used_in_two_pdfs_at_once(tmp_path,monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from reportlab.platypus import SimpleDocTemplate
    import threading,time
    tables,meta,document,figures=report_example()
    original=SimpleDocTemplate.multiBuild;active=0;peak=0;lock=threading.Lock()
    def measured_build(self,*args,**kwargs):
        nonlocal active,peak
        with lock:active+=1;peak=max(peak,active)
        try:
            time.sleep(.1)
            return original(self,*args,**kwargs)
        finally:
            with lock:active-=1
    monkeypatch.setattr(SimpleDocTemplate,'multiBuild',measured_build)
    def generate(i):return render_pdf(tables,meta,tmp_path/f'{i}.pdf',document=replace(document,title=f'Sessão de teste {i}'),figures=figures)
    with ThreadPoolExecutor(max_workers=2) as pool:paths=list(pool.map(generate,(1,2)))
    assert peak==1  # ReportLab explicitly forbids simultaneous documents sharing a TTFont.
    for i,path in enumerate(paths,1):assert f'Sessão de teste {i}' in PdfReader(path).pages[0].extract_text()
