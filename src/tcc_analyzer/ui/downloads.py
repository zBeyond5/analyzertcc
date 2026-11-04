import base64,html
from ..jobs import ALLOWED_ARTIFACTS
from ..models import DomainError

MIMES={'pdf':'application/pdf','docx':'application/vnd.openxmlformats-officedocument.wordprocessingml.document','xlsx':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','csv':'text/csv','json':'application/json','zip':'application/zip'}
def build_download_anchor(payload,*,filename,mime):
    if filename not in ALLOWED_ARTIFACTS or mime not in MIMES.values():raise DomainError('download','Arquivo de download inválido.')
    data=base64.b64encode(payload).decode('ascii')
    return f'<a class="private-download" download="{html.escape(filename,quote=True)}" href="data:{mime};base64,{data}">Baixar {html.escape(filename)}</a>'
