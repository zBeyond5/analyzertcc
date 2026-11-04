import csv
import hashlib
import io
from pathlib import Path
import re
import zipfile
import pandas as pd
import openpyxl
from .models import DomainError, ImportLimits, CsvOptions, DatasetMeta, ImportedDataset

def safe_filename(filename):
    if not filename or len(filename)>160 or any(c in filename for c in '/\\:\x00') or '..' in filename:
        raise DomainError('filename','Nome de arquivo inválido. Use um nome simples, sem caminhos.')
    if re.match(r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)',filename,re.I):
        raise DomainError('filename','Nome de arquivo reservado pelo Windows.')

def inspect_upload(filename, payload, limits=ImportLimits()):
    safe_filename(filename)
    if not payload: raise DomainError('empty','O arquivo está vazio.')
    if len(payload)>limits.max_bytes: raise DomainError('size','O arquivo excede o limite permitido de upload.')
    suffix=Path(filename).suffix.lower()
    if suffix not in ('.xlsx','.xls','.csv'): raise DomainError('format','Escolha um arquivo XLSX, XLS ou CSV.')
    if suffix=='.xlsx':
        try:
            with zipfile.ZipFile(io.BytesIO(payload)) as z:
                entries=z.infolist();names={i.filename for i in entries}
                if len(entries)>limits.max_zip_entries or sum(i.file_size for i in entries)>limits.max_unpacked_bytes:
                    raise DomainError('expanded_size','A planilha descompactada excede os limites permitidos.')
                if '[Content_Types].xml' not in names or 'xl/workbook.xml' not in names: raise ValueError()
                if any('vbaproject' in n.lower() or 'externallinks/' in n.lower() for n in names):
                    raise DomainError('active_content','Remova macros e vínculos externos antes de enviar.')
                if any(i.flag_bits&1 for i in entries): raise ValueError()
        except (zipfile.BadZipFile,ValueError,OSError):
            raise DomainError('structure','O arquivo não contém uma planilha XLSX válida.') from None
    elif suffix=='.xls' and not payload.startswith(bytes.fromhex('D0CF11E0A1B11AE1')):
        raise DomainError('structure','O arquivo não contém uma planilha XLS válida.')
    elif suffix=='.csv' and b'\x00' in payload:
        raise DomainError('structure','O CSV contém conteúdo binário inválido.')
    return suffix

def list_sheets(path, limits=ImportLimits()):
    path=Path(path);fmt=inspect_upload(path.name,path.read_bytes(),limits)
    if fmt=='.csv':return ()
    try:
        with pd.ExcelFile(path,engine='xlrd' if fmt=='.xls' else 'openpyxl') as x:return tuple(x.sheet_names)
    except ImportError:raise DomainError('xls_dependency','Suporte XLS indisponível; salve como XLSX.') from None
    except Exception:raise DomainError('structure','Não foi possível ler as abas da planilha.') from None

def _headers(headers):
    if not headers or any(h is None or not str(h).strip() for h in headers):
        raise DomainError('headers','O cabeçalho contém nomes vazios.')
    h=[str(v) for v in headers]
    if len(set(h))!=len(h) or len({v.strip() for v in h})!=len(h):
        raise DomainError('duplicate_headers','Há nomes de colunas repetidos. Corrija o cabeçalho.')
    return h

def load_table(path, *, sheet=None, csv_options=None, limits=ImportLimits()):
    path=Path(path);payload=path.read_bytes();fmt=inspect_upload(path.name,payload,limits)
    try:
        if fmt=='.csv':
            opts=csv_options or CsvOptions()
            if len(opts.separator)!=1 or opts.encoding not in ('utf-8','utf-8-sig','cp1252','latin-1'):
                raise DomainError('csv_options','Encoding ou separador CSV inválido.')
            reader=csv.reader(io.StringIO(payload.decode(opts.encoding)),delimiter=opts.separator)
            header=_headers(next(reader,[]));rows=[]
            for row in reader:
                if not row:continue
                if len(row)!=len(header):raise DomainError('ragged_csv','As linhas do CSV têm quantidades diferentes de colunas.')
                rows.append(row)
                if len(rows)>limits.max_rows:raise DomainError('rows','O arquivo excede o limite de linhas.')
        elif fmt=='.xlsx':
            w=openpyxl.load_workbook(io.BytesIO(payload),read_only=True,data_only=False,keep_links=False)
            try:
                if sheet is None and len(w.sheetnames)>1:raise DomainError('sheet','Selecione a aba que deseja importar.')
                if sheet is not None and sheet not in w.sheetnames:raise DomainError('sheet','A aba selecionada não existe.')
                ws=w[sheet or w.sheetnames[0]]
                if ws.max_column>limits.max_columns or ws.max_row>limits.max_rows+1:raise DomainError('dimensions','A planilha excede os limites de linhas ou colunas.')
                source=ws.iter_rows();header=_headers([c.value for c in next(source,[])])
                rows=[]
                for row in source:
                    if any(c.data_type=='f' for c in row):raise DomainError('formula','A planilha contém fórmulas. Exporte apenas valores antes de enviar.')
                    vals=[c.value for c in row]
                    if any(v is not None for v in vals):rows.append(vals)
                    if len(rows)>limits.max_rows:raise DomainError('rows','O arquivo excede o limite de linhas.')
            finally:w.close()
        else:
            sheets=list_sheets(path,limits)
            if sheet is None and len(sheets)>1:raise DomainError('sheet','Selecione a aba que deseja importar.')
            raw=pd.read_excel(io.BytesIO(payload),sheet_name=sheet or sheets[0],header=None,engine='xlrd',nrows=limits.max_rows+2)
            header=_headers(raw.iloc[0].tolist());rows=raw.iloc[1:].values.tolist()
        if not rows:raise DomainError('empty','Não há registros abaixo do cabeçalho.')
        if len(header)>limits.max_columns or len(rows)>limits.max_rows:raise DomainError('dimensions','O arquivo excede os limites de linhas ou colunas.')
        df=pd.DataFrame(rows,columns=header)
        return ImportedDataset(df,DatasetMeta(len(df),len(header),tuple(header),hashlib.sha256(payload).hexdigest()))
    except DomainError:raise
    except UnicodeError:raise DomainError('encoding','Não foi possível decodificar o CSV. Escolha outro encoding.') from None
    except Exception:raise DomainError('read','Não foi possível ler o arquivo. Confira o formato e as opções de importação.') from None
