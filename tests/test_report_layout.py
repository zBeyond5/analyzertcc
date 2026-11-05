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
