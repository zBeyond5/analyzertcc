import hashlib
from io import BytesIO
import pytest
import openpyxl
from tcc_analyzer.importers import load_table, inspect_upload, list_sheets
from tcc_analyzer.models import CsvOptions, ImportLimits, DomainError

def test_source_unchanged(source_path):
    before = hashlib.sha256(source_path.read_bytes()).hexdigest()
    result = load_table(source_path, sheet="Banco_EpiInfo")
    assert result.raw.shape == (30, 75)
    assert result.raw.ID.nunique() == 30
    assert result.raw.isna().sum().sum() == 0
    assert hashlib.sha256(source_path.read_bytes()).hexdigest() == before

def test_csv_preserves_values(tmp_path):
    p=tmp_path/'data.csv'
    p.write_text('ID;H_DEIT;obs\n001;23,5;ação\n',encoding='utf-8-sig')
    assert load_table(p,csv_options=CsvOptions()).raw.iloc[0].tolist()==['001','23,5','ação']

@pytest.mark.parametrize('payload',[b'',b'ID;ID\n1;2\n',b';age\n1;2\n'])
def test_empty_or_duplicate_headers(tmp_path,payload):
    p=tmp_path/'bad.csv';p.write_bytes(payload)
    with pytest.raises(DomainError): load_table(p,csv_options=CsvOptions())

def test_real_structure_and_limits():
    with pytest.raises(DomainError): inspect_upload('x.xlsx',b'not excel')
    with pytest.raises(DomainError): inspect_upload('../x.csv',b'ID\n1\n')
    with pytest.raises(DomainError): inspect_upload('x.csv',b'12345',ImportLimits(max_bytes=4))

def test_sheets_formulas_and_bounds(tmp_path):
    w=openpyxl.Workbook();w.active.title='one';w.active.append(['ID']);w.active.append([1])
    w.create_sheet('two').append(['ID']);p=tmp_path/'s.xlsx';w.save(p)
    assert list_sheets(p)==('one','two')
    assert load_table(p,sheet='one').raw.iloc[0,0]==1
    with pytest.raises(DomainError):load_table(p)
    with pytest.raises(DomainError):load_table(p,sheet='one',limits=ImportLimits(max_rows=0))
    w.active['A2']='=1+1';w.save(p)
    with pytest.raises(DomainError):load_table(p,sheet='one')

def test_zip_expansion_limit(source_path):
    with pytest.raises(DomainError):inspect_upload(source_path.name,source_path.read_bytes(),ImportLimits(max_unpacked_bytes=100))
