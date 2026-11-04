from dataclasses import asdict
from pathlib import Path
import hashlib,json
import pandas as pd
from .models import CsvFormat,ExportManifest
from .profiles import dictionary_frame

def escape_csv_text(value):
    if isinstance(value,str) and value.startswith(('=','+','-','@','\t','\r','\n')):return "'"+value,True
    return value,False

def unescape_csv_text(value,was_escaped):return value[1:] if was_escaped else value

def write_xlsx(frames,path):
    import openpyxl
    from openpyxl.styles import Font,PatternFill,Alignment
    wb=openpyxl.Workbook();wb.remove(wb.active)
    for name,df in frames.items():
        ws=wb.create_sheet(name[:31]);ws.append([str(c) for c in df.columns])
        for row in df.itertuples(index=False,name=None):
            ws.append([None if pd.isna(v) else v.item() if hasattr(v,'item') else v for v in row])
        for row in ws:
            for c in row:
                if isinstance(c.value,str):c.data_type='s'
        for c in ws[1]:c.font=Font(bold=True,color='FFFFFF');c.fill=PatternFill('solid',fgColor='1F6675')
        ws.freeze_panes='A2';ws.auto_filter.ref=ws.dimensions
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width=min(60,max(15,max(len(str(c.value or '')) for c in col)+2))
    wb.save(path);return Path(path)

def export_epiinfo(df,profile,output_dir,csv_format=CsvFormat()):
    output_dir=Path(output_dir);output_dir.mkdir(parents=True,exist_ok=True)
    allowed=[v.name for v in profile.variables if v.export_default and v.name in df]
    allowed += [c for c in ('ZARIT_CLASS',) if c in df and c not in allowed]
    data=df[allowed].copy(deep=True)
    data['ID']=range(1,len(data)+1)
    columns=['ID']+[c for c in data if c!='ID'];data=data[columns]
    xlsx=output_dir/'epiinfo_dados.xlsx';csv=output_dir/'epiinfo_dados.csv'
    write_xlsx({'Banco_EpiInfo':data},xlsx)
    safe=data.copy(deep=True);escapes=[]
    for c in safe:
        if safe[c].dtype==object or pd.api.types.is_string_dtype(safe[c]):
            vals=[]
            for i,v in enumerate(safe[c]):
                value,escaped=escape_csv_text(v);vals.append(value)
                if escaped:escapes.append((i,c))
            safe[c]=vals
    safe.to_csv(csv,index=False,sep=csv_format.separator,decimal=csv_format.decimal,encoding=csv_format.encoding,na_rep='')
    return ExportManifest({'csv':csv.name,'xlsx':xlsx.name},{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (csv,xlsx)},csv_format,tuple(c for c in df if c not in columns),tuple(escapes))

def export_dictionary(profile,output):return write_xlsx({'Dicionario':dictionary_frame(profile)},output)

def write_audit(transformations,profile,output):
    safe={v.name for v in profile.variables if v.export_default and v.name!='ID'}
    rows=[]
    for c in transformations:
        entry={'linha_exportada':c.row_index+1 if c.row_index is not None else None,'campo':c.field,'tipo':'correção confirmada ou conversão em cópia'}
        # Justificativas livres também podem conter nomes; não exportar texto arbitrário.
        if c.field in safe and all(isinstance(v,(int,float,type(None))) for v in (c.before,c.after)):
            entry.update(antes=c.before,depois=c.after)
        else:entry['valores']='omitidos por privacidade'
        rows.append(entry)
    return write_json(output,{'transformacoes':rows,'total':len(rows)})

def write_json(path,data):
    def clean(v):
        import math
        if isinstance(v,dict):return {str(k):clean(x) for k,x in v.items()}
        if isinstance(v,(tuple,list)):return [clean(x) for x in v]
        if hasattr(v,'item'):return clean(v.item())
        if isinstance(v,float) and not math.isfinite(v):return None
        if hasattr(v,'isoformat'):return v.isoformat()
        return v
    Path(path).write_text(json.dumps(clean(data),ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8');return Path(path)
