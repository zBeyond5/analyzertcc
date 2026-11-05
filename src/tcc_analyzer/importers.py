import csv
import hashlib
import io
from pathlib import Path
import re
import zipfile
import json
import pandas as pd
import openpyxl
from .models import DomainError, ImportLimits, CsvOptions, DatasetMeta, ImportedDataset
from .profiles import ALIASES

def _workbook_metadata(workbook,limits):
    metadata={'categories':{},'questions':{},'origins':{},'issues':[]}
    for name in ('Categorias','Perguntas','AVISO','Metadados'):
        if name not in workbook:continue
        ws=workbook[name]
        if ws.max_row>1000 or ws.max_column>limits.max_columns:raise DomainError('metadata','As abas de documentação excedem o limite permitido.')
        rows=[]
        for row in ws.iter_rows():
            if any(c.data_type=='f' for c in row):raise DomainError('formula','Remova fórmulas das abas de documentação.')
            rows.append([c.value for c in row])
        if name in ('Categorias','Perguntas') and rows:
            headers=_headers(rows[0])
            normalized=[ALIASES.get(h,h) for h in headers]
            metadata[f'{name.lower()}_fields']=normalized
            if len(set(normalized))!=len(normalized):raise DomainError('metadata','Há definições duplicadas para uma pergunta.')
            for col,field in enumerate(normalized):
                vals=[(i+2,row[col]) for i,row in enumerate(rows[1:]) if col<len(row) and row[col] is not None]
                metadata['origins'][field]=f'{name}, coluna {col+1}'
                if name=='Perguntas':
                    if len(vals)!=1:metadata['issues'].append((field,'A pergunta precisa de uma única definição.'))
                    elif vals:metadata['questions'][field]=' '.join(str(vals[0][1]).split())
                else:
                    labels={}
                    for _,value in vals:
                        match=re.match(r'^\s*(-?\d+)\s*=\s*(.+)$',str(value),re.S)
                        if match:
                            code=int(match[1]);label=' '.join(match[2].split())
                            if code in labels:metadata['issues'].append((field,'Há códigos repetidos na categoria.'))
                            labels[code]=label
                    if labels:metadata['categories'][field]=labels
        elif name=='AVISO':
            text=' '.join(str(v) for row in rows for v in row if v is not None).casefold()
            if 'fict' in text or 'simula' in text:metadata['fictitious']=True
        elif name=='Metadados':
            pairs={str(row[0]):row[1] for row in rows if len(row)>1 and row[0] is not None}
            metadata['fictitious']=metadata.get('fictitious',False) or str(pairs.get('fictitious','')).lower()=='true'
            if 'canonical_codes' in pairs:
                try:
                    maps=json.loads(pairs['canonical_codes'])
                    if not isinstance(maps,dict) or any(not isinstance(v,dict) for v in maps.values()):raise ValueError()
                    metadata['canonical_codes']=maps
                except (ValueError,TypeError):raise DomainError('metadata','A correspondência das categorias é inválida.') from None
    return metadata

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
    metadata={}
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
                metadata=_workbook_metadata(w,limits)
                if sheet is None and len(w.sheetnames)>1:
                    candidates=[n for n in w.sheetnames if n not in ('Categorias','Perguntas','AVISO','Metadados')]
                    if len(candidates)==1:sheet=candidates[0]
                    else:raise DomainError('sheet','Selecione a aba que contém as participantes.')
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
        return ImportedDataset(df,DatasetMeta(len(df),len(header),tuple(header),hashlib.sha256(payload).hexdigest()),metadata)
    except DomainError:raise
    except UnicodeError:raise DomainError('encoding','Não foi possível decodificar o CSV. Escolha outro encoding.') from None
    except Exception:raise DomainError('read','Não foi possível ler o arquivo. Confira o formato e as opções de importação.') from None
