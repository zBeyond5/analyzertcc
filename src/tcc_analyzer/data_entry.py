"""Session-local workbook construction; no collected responses are stored globally."""
from dataclasses import replace
from datetime import time
from io import BytesIO
import json
import math
import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from .models import DomainError

DERIVED={'PSQI','ZARIT','PSQI_G','ZARIT_CLASS','ESCOL_B','RENDA_B','FREQ_3'}


def input_variables(profile):
    return tuple(v for v in profile.variables if v.name not in DERIVED)


def new_participant(existing_ids=()):
    return {'ID':max((int(i) for i in existing_ids),default=0)+1}


def update_categories(profile, field, entries):
    variable=next(v for v in profile.variables if v.name==field)
    labels={}; mapping={}
    canonical=dict(profile.canonical_codes)
    old_canonical=canonical.get(field,{str(c):c for c in variable.allowed_values or ()})
    new_canonical={}
    for entry in entries:
        try:
            number=float(entry['Código'])
            if not math.isfinite(number) or not number.is_integer():raise ValueError()
            code=int(number)
            label=str(entry.get('Significado') or '').strip()
            if not label or code in labels:raise ValueError()
        except (ValueError,TypeError,KeyError):
            raise DomainError('category','Use códigos inteiros diferentes e preencha o significado de cada opção.') from None
        labels[code]=label
        old=entry.get('original_code')
        if old is not None and not (isinstance(old,float) and math.isnan(old)):
            old=int(old);mapping[old]=code
            # A changed instrument answer is not silently treated as the original answer.
            if variable.labels.get(old)==label and str(old) in old_canonical:
                new_canonical[str(code)]=old_canonical[str(old)]
    if not labels:raise DomainError('category','Mantenha ao menos uma opção de resposta.')
    canonical[field]=new_canonical
    updated=replace(variable,allowed_values=tuple(labels),labels=labels,mapping_status='confirmed')
    rules=canonical
    return replace(profile,variables=tuple(updated if v.name==field else v for v in profile.variables),canonical_codes=rules),mapping


def remap_rows(rows,field,mapping,profile):
    allowed=next(v.allowed_values for v in profile.variables if v.name==field)
    changed=[]
    for row in rows:
        item=dict(row);value=item.get(field)
        if value is not None:
            if value not in mapping:raise DomainError('category_used','Uma opção removida já tem respostas. Mantenha essa opção ou corrija as participantes antes de removê-la.')
            item[field]=mapping[value]
            if item[field] not in allowed:raise DomainError('category_used','Há respostas sem categoria correspondente.')
        changed.append(item)
    return changed


def _literal(cell,value):
    cell.value=value
    if isinstance(value,str):cell.data_type='s'


def build_input_workbook(rows, profile, *, fictitious=False):
    if not rows:raise DomainError('empty','Adicione uma participante antes de concluir a planilha.')
    variables=input_variables(profile)
    headers=[v.name for v in variables]
    if any(row.get('NOME') for row in rows):headers.append('NOME')
    book=openpyxl.Workbook();bank=book.active;bank.title='Banco'
    categories=book.create_sheet('Categorias');questions=book.create_sheet('Perguntas');meta=book.create_sheet('Metadados')
    for sheet in (bank,categories,questions):
        for col,header in enumerate(headers,1):_literal(sheet.cell(1,col),header)
    for col,variable in enumerate(variables,1):
        _literal(questions.cell(2,col),variable.label)
        if variable.labels:
            for r,(code,label) in enumerate(variable.labels.items(),2):_literal(categories.cell(r,col),f'{code}= {label}')
            validation=DataValidation(type='list',formula1='"'+','.join(str(c) for c in variable.labels)+'"',allow_blank=True)
            validation.errorTitle='Opção não reconhecida';validation.error='Consulte as opções na aba Categorias.';validation.showErrorMessage=True
            validation.promptTitle='Opções de resposta';validation.prompt='; '.join(f'{c}: {label}' for c,label in variable.labels.items())[:250];validation.showInputMessage=True
            bank.add_data_validation(validation);validation.add(f'{get_column_letter(col)}2:{get_column_letter(col)}10001')
        else:_literal(categories.cell(2,col),'Variável nominal' if variable.kind=='text' else 'Variável numérica')
    if 'NOME' in headers:
        _literal(questions.cell(2,len(headers)),'Nome ou apelido (opcional; identificação, não analisado)')
        _literal(categories.cell(2,len(headers)),'Variável nominal')
    for r,row in enumerate(rows,2):
        for col,header in enumerate(headers,1):
            value=row.get(header)
            if isinstance(value,float) and not math.isfinite(value):value=None
            _literal(bank.cell(r,col),value)
            if header in ('H_DEIT','H_LEV'):bank.cell(r,col).number_format='hh:mm'
            elif isinstance(value,(float,int)):bank.cell(r,col).number_format='0.##'
    metadata=[('profile_id',profile.id),('profile_version',profile.version),('fictitious','true' if fictitious else 'false'),('canonical_codes',json.dumps(profile.canonical_codes,ensure_ascii=False))]
    meta.append(('Chave','Valor'))
    for key,value in metadata:meta.append((key,value))
    for sheet in book:
        sheet.freeze_panes='B2' if sheet==bank else 'A2'
        sheet.auto_filter.ref=sheet.dimensions
        sheet.row_dimensions[1].height=28
        for cell in sheet[1]:cell.font=Font(color='FFFFFF',bold=True);cell.fill=PatternFill('solid',fgColor='1F6675');cell.alignment=Alignment(vertical='center')
        for col in range(1,sheet.max_column+1):sheet.column_dimensions[get_column_letter(col)].width=20 if sheet==bank else 42
    output=BytesIO();book.save(output);book.close();return output.getvalue()
