"""Teste real: servidor isolado, dois navegadores e download privado."""
from pathlib import Path
import io,json,os,socket,subprocess,sys,time,zipfile
import pandas as pd
import pytest,requests
from playwright.sync_api import sync_playwright,expect

def test_two_browsers_full_workflow(tmp_path):
    root=Path(__file__).resolve().parents[1]
    candidates=list((Path.home()/'.agent-browser/browsers').glob('chrome-*/chrome.exe'))
    assert candidates,'Instale o navegador com npx agent-browser install antes de validar a interface.'
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    env={**os.environ,'TCC_RUNTIME_ROOT':str(tmp_path/'jobs'),'STREAMLIT_SERVER_FILE_WATCHER_TYPE':'none'}
    log=(tmp_path/'server.log').open('w')
    server=subprocess.Popen([sys.executable,'-m','streamlit','run',str(root/'app.py'),'--server.address','127.0.0.1','--server.port',str(port)],cwd=root,env=env,stdout=log,stderr=log)
    url=f'http://127.0.0.1:{port}'
    try:
        deadline=time.monotonic()+30
        while time.monotonic()<deadline:
            try:
                if requests.get(url+'/_stcore/health',timeout=1).ok:break
            except requests.RequestException:pass
            time.sleep(.2)
        else:raise AssertionError('Servidor não iniciou: '+(tmp_path/'server.log').read_text())
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=str(candidates[-1]),headless=True)
            contexts=[browser.new_context(viewport={'width':1366,'height':900},accept_downloads=True,locale='pt-BR') for _ in range(2)]
            archives=[]
            def run(page,changed=False):
                page.goto(url);page.get_by_role('button',name='Experimentar dados fictícios').click()
                expect(page.get_by_role('heading',name='Confira os dados antes de analisar')).to_be_visible()
                if changed:
                    page.get_by_text('Corrigir um valor com registro e possibilidade de desfazer',exact=True).click()
                    field=page.get_by_label('Campo para corrigir',exact=True)
                    field.click();field.press('ArrowDown')
                    field.fill('IDADE_M')
                    page.get_by_role('option',name='IDADE_M',exact=True).click()
                    expect(field).to_have_value('IDADE_M')
                    page.get_by_label('Novo valor (vazio = ausente)',exact=True).fill('99')
                    page.get_by_label('Motivo da correção',exact=True).fill('Sentinela fictícia de isolamento')
                    page.get_by_text('Confirmo a alteração nesta cópia do banco.',exact=True).click()
                    page.get_by_role('button',name='Aplicar correção',exact=True).click()
                page.get_by_role('button',name='Configurar cruzamentos',exact=True).click()
                expect(page.get_by_role('heading',name='Defina o que será comparado')).to_be_visible()
                page.get_by_text('Conferi independência, distribuição, tamanho dos grupos e o que cada método estima.',exact=True).click()
                page.get_by_role('button',name='Executar análise',exact=True).click()
                expect(page.get_by_role('heading',name='Confira os resultados e o relatório')).to_be_visible(timeout=30000)
                page.get_by_text('Revisei as tabelas, os métodos e as limitações deste relatório.',exact=True).click()
                page.get_by_role('button',name='Ir para exportação',exact=True).click()
                page.get_by_role('button',name='Preparar download',exact=True).click()
                link=page.get_by_role('link',name='Baixar resultado_completo.zip',exact=True)
                expect(link).to_have_attribute('href',__import__('re').compile(r'^data:application/zip;base64,'))
                with page.expect_download() as info:link.click()
                path=tmp_path/('second.zip' if changed else 'first.zip');info.value.save_as(path)
                page.screenshot(path=str(tmp_path/('second.png' if changed else 'first.png')),full_page=True)
                return zipfile.ZipFile(path)
            first=contexts[0].new_page();network=[]
            first.on('request',lambda req:network.append(req.url))
            archives.append(run(first))
            second=contexts[1].new_page();second.goto(url)
            expect(second.get_by_role('heading',name='Comece pelo seu banco de dados')).to_be_visible()
            assert not second.get_by_role('link',name='Baixar resultado_completo.zip').count()
            archives.append(run(second,True))
            frames=[]
            for archive in archives:
                assert len(archive.namelist())==8
                manifest=json.loads(archive.read('manifesto.json'))
                assert manifest['fictitious'] and 'owner_token' not in str(manifest)
                frames.append(pd.read_excel(io.BytesIO(archive.read('epiinfo_dados.xlsx'))))
            assert frames[0].iloc[0].IDADE_M==34
            assert frames[1].iloc[0].IDADE_M==99
            private_media=[u for u in network if '/media/' in u and '/static/media/' not in u]
            assert not private_media,private_media  # Fontes locais em /static/media não são relatórios.
            assert all(u.startswith(url) for u in network if u.startswith('http'))
            job=next(p for p in (tmp_path/'jobs').iterdir() if p.is_dir())
            attempt=contexts[1].request.get(url+'/runtime/jobs/'+job.name+'/resultado_completo.zip')
            assert not attempt.body().startswith(b'PK')
            # Reconfigurar deve invalidar o relatório já revisado.
            first.get_by_text('3 · Cruzamentos',exact=True).click()
            expect(first.get_by_role('heading',name='Defina o que será comparado')).to_be_visible()
            first.get_by_label('Justificativa',exact=True).first.fill('Nova justificativa associativa')
            first.get_by_role('heading',name='Defina o que será comparado').click()
            first.get_by_text('5 · Exportar',exact=True).click()
            expect(first.get_by_text('Confira os resultados e marque a revisão antes de exportar.',exact=True)).to_be_visible()
            browser.close()
    finally:
        server.terminate();server.wait(timeout=15);log.close()
