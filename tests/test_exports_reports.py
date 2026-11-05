from pathlib import Path
import json
import pandas as pd
import pytest
from docx import Document
from pypdf import PdfReader
from tcc_analyzer.exports import export_epiinfo,export_dictionary,write_audit,escape_csv_text,unescape_csv_text
from tcc_analyzer.reporting import format_p,build_tables,render_docx,render_pdf
from tcc_analyzer.profiles import load_profile
from tcc_analyzer.models import CsvFormat,Transformation

def test_format_p():
    assert format_p(.0009)=='<0,001'
    assert format_p(.001)=='0,001'
    assert format_p(None)=='Não calculado'

def test_csv_roundtrip(fictitious_df,tmp_path):
    m=export_epiinfo(fictitious_df,load_profile(),tmp_path,CsvFormat())
    c=pd.read_csv(tmp_path/m.files['csv'],sep=';',decimal=',',encoding='utf-8-sig')
    x=pd.read_excel(tmp_path/m.files['xlsx'])
    assert len(c)==len(x)==30
    assert c.ID.tolist()==list(range(1,31))
    assert c.H_DEIT.tolist()==fictitious_df.H_DEIT.tolist()
    assert c.PSQI_G.tolist()==x.PSQI_G.tolist()
    assert 'OCUP' not in c and 'OUTRA' not in c

@pytest.mark.parametrize('text',['=1+1','+SUM(A1)','-text','@cmd','\tfoo',"'original",'ação;"teste"'])
def test_safe_text_reversible(text):
    value,escaped=escape_csv_text(text)
    assert unescape_csv_text(value,escaped)==text
    if text[0] in '=+-@\t':assert value.startswith("'")

def test_audit_no_private_values(tmp_path):
    p=write_audit((Transformation(0,'OCUP','PRIVATE-NAME','OTHER','Conferência'),),load_profile(),tmp_path/'auditoria.json')
    content=p.read_text(encoding='utf-8')
    assert 'PRIVATE-NAME' not in content and 'OTHER' not in content

def test_reports_are_readable_and_fictitious(fictitious_df,tmp_path):
    tables=build_tables((),(),load_profile(),data=fictitious_df)
    assert len(tables.descriptive)==3
    meta={'fictitious':True,'profile_id':'tea_maternal_sleep_v1','source_sha256':'test','score_source':'recorded'}
    doc=render_docx(tables,meta,tmp_path/'relatorio.docx')
    text=' '.join(p.text for p in Document(doc).paragraphs)
    assert 'Dados fictícios' in text
    pdf=render_pdf(tables,meta,tmp_path/'relatorio.pdf')
    reader=PdfReader(pdf)
    assert len(reader.pages)>0 and 'Dados fictícios' in reader.pages[0].extract_text()
    assert all(len(p.extract_text())>10 for p in reader.pages)

def test_therapy_percentages_use_total(fictitious_df):
    fictitious_df.loc[fictitious_df.index[fictitious_df.FONO==2][0],'FONO']=float('nan')
    table=build_tables((),(),load_profile(),data=fictitious_df).descriptive[1]
    row=table[(table['Variável']=='Fonoaudiologia') & (table['Participantes']==24)].iloc[0]
    assert row['Resultado']=='80,0%'
