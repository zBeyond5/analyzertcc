"""Teste real: servidor isolado, dois navegadores e download privado."""
from pathlib import Path
import io,json,os,re,socket,subprocess,sys,time,zipfile
import pandas as pd
import pytest,requests
from playwright.sync_api import sync_playwright,expect

def test_two_browsers_full_workflow(tmp_path):
    root=Path(__file__).resolve().parents[1]
    evidence=root/'test-results/soft-ui';evidence.mkdir(parents=True,exist_ok=True)
    candidates=list((Path.home()/'.agent-browser/browsers').glob('chrome-*/chrome.exe'))
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
            executable=os.environ.get('TCC_BROWSER_EXECUTABLE') or (str(candidates[-1]) if candidates else p.chromium.executable_path)
            browser=p.chromium.launch(executable_path=executable,headless=True)
            contexts=[browser.new_context(viewport={'width':1366,'height':900},accept_downloads=True,locale='pt-BR') for _ in range(2)]
            archives=[]
            def step(page,number,label):
                return page.locator('.st-key-project_stepper').get_by_role('button',name=re.compile(rf'{number} · {label}'))
            def run(page,changed=False):
                page.goto(url)
                expect(page.get_by_role('heading',name='Importe sua planilha',exact=True)).to_be_visible(timeout=30000)
                expect(step(page,3,'Analisar')).to_be_disabled()
                expect(step(page,4,'Resultados')).to_be_disabled()
                expect(step(page,5,'Baixar')).to_be_disabled()
                assert not page.get_by_role('heading',name='Análise do TCC',exact=True).count()
                expect(page.get_by_role('button',name='Experimentar dados fictícios')).to_be_visible()
                page.get_by_role('button',name='Experimentar dados fictícios').click()
                expect(page.get_by_role('heading',name='Confira os dados antes de analisar')).to_be_visible()
                if changed:
                    page.get_by_text('Corrigir um valor com registro e possibilidade de desfazer',exact=True).click()
                    field=page.get_by_label('Campo para corrigir',exact=True)
                    expect(field).to_have_value('IDADE_M')
                    page.get_by_label('Novo valor (vazio = ausente)',exact=True).fill('99')
                    page.get_by_label('Observação (opcional)',exact=True).fill('Sentinela fictícia de isolamento')
                    page.get_by_text('Confirmo a alteração nesta cópia do banco.',exact=True).click()
                    page.get_by_role('button',name='Aplicar correção',exact=True).click()
                    expect(page.get_by_role('button',name='Desfazer última correção',exact=True)).to_be_visible()
                page.get_by_role('button',name='Continuar para análise',exact=True).click()
                expect(page.get_by_role('heading',name='O que você quer descobrir?')).to_be_visible()
                # Completed steps remain editable; returning never clears this session's data.
                step(page,2,'Conferir').click()
                expect(page.get_by_role('heading',name='Confira os dados antes de analisar')).to_be_visible()
                step(page,1,'Dados').click()
                expect(page.get_by_role('heading',name='Importe sua planilha',exact=True)).to_be_visible()
                step(page,3,'Analisar').click()
                expect(page.get_by_role('heading',name='O que você quer descobrir?')).to_be_visible()
                page.screenshot(path=str(evidence/('step3-second.png' if changed else 'step3.png')),full_page=True)
                assert not page.get_by_text('Conferi independência, distribuição, tamanho dos grupos e o que cada método estima.',exact=True).count()
                page.get_by_role('button',name='Analisar dados',exact=True).click()
                expect(page.get_by_role('heading',name='Confira os resultados e o relatório')).to_be_visible(timeout=30000)
                expect(page.get_by_text('Como ler o valor de p',exact=True)).to_be_visible()
                assert page.get_by_text(re.compile('Significativa pelo critério de 5%|Não atingiu o critério de 5%|Inferência não disponível')).count() >= 3
                graph=page.get_by_test_id('stPlotlyChart')
                expect(graph).to_be_visible()
                expect(graph.locator('.js-plotly-plot')).to_be_visible()
                assert graph.locator('.js-plotly-plot').evaluate('(element)=>element.data.some(trace=>(trace.x && trace.x.length)||(trace.y && trace.y.length))')
                if not changed:
                    tabs=page  # components.v2 renders in a shadow root, pierced by role locators.
                    tabs.get_by_role('tab',name='Tabelas',exact=True).click()
                    expect(page.get_by_text('Tabela 1 · Características sociodemográficas',exact=True)).to_be_visible()
                    tabs.get_by_role('tab',name='Detalhes',exact=True).click()
                    expect(page.get_by_text('Explicações e notas do relatório',exact=True)).to_be_visible()
                    tabs.get_by_role('tab',name='Resumo',exact=True).click()
                    expect(graph).to_be_visible()
                page.screenshot(path=str(evidence/('results-second.png' if changed else 'results.png')),full_page=True)
                if not changed:
                    page.set_viewport_size({'width':360,'height':800})
                    expect(graph).to_be_visible()
                    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 2')
                    page.get_by_test_id('stMain').evaluate('(element)=>element.scrollTo(0,0)')
                    for number,label in enumerate(('Dados','Conferir','Analisar','Resultados','Baixar'),1):
                        bounds=step(page,number,label).bounding_box()
                        assert bounds is not None and bounds['x']>=0 and bounds['x']+bounds['width']<=362,bounds
                    page.screenshot(path=str(evidence/'results-mobile.png'),full_page=True)
                    graph.scroll_into_view_if_needed()
                    page.screenshot(path=str(evidence/'results-chart-mobile.png'),full_page=True)
                    page.get_by_test_id('stMainMenu').click()
                    page.get_by_role('menuitemradio',name='Dark',exact=True).click()
                    page.keyboard.press('Escape')
                    page.wait_for_function("() => {const c=getComputedStyle(document.querySelector('[data-testid=stApp]')).backgroundColor.match(/\\d+/g);return c && c.slice(0,3).every(n=>Number(n)<100)}")
                    expect(graph).to_be_visible()
                    graph.scroll_into_view_if_needed()
                    page.screenshot(path=str(evidence/'results-dark-mobile.png'),full_page=True)
                    page.get_by_test_id('stMainMenu').click()
                    page.get_by_role('menuitemradio',name='Light',exact=True).click()
                    page.keyboard.press('Escape')
                    page.set_viewport_size({'width':1366,'height':900})
                page.get_by_role('button',name='Baixar resultados',exact=True).click()
                page.get_by_role('button',name='Preparar download',exact=True).click()
                link=page.get_by_role('link',name='Baixar resultado_completo.zip',exact=True)
                expect(link).to_have_attribute('href',re.compile(r'^data:application/zip;base64,'))
                with page.expect_download() as info:link.click()
                path=tmp_path/('second.zip' if changed else 'first.zip');info.value.save_as(path)
                page.screenshot(path=str(evidence/('second.png' if changed else 'first.png')),full_page=True)
                return zipfile.ZipFile(path)
            first=contexts[0].new_page();network=[]
            first.on('request',lambda req:network.append(req.url))
            archives.append(run(first))
            second=contexts[1].new_page();second.goto(url)
            expect(second.get_by_role('heading',name='Importe sua planilha')).to_be_visible()
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
            # Visual acceptance matrix: all five steps, two themes and two widths.
            import math
            def contrast(page,selector):
                return page.locator(selector).first.evaluate(r"""el => {
                    const rgba=s=>(s.match(/[\d.]+/g)||[]).map(Number);
                    const fg=rgba(getComputedStyle(el).color);
                    let bg=[255,255,255,1],node=el;
                    while(node){const c=rgba(getComputedStyle(node).backgroundColor);if(c.length>=3&&(c[3]??1)>0.99){bg=c;break;}node=node.parentElement;}
                    const alpha=fg[3]??1;
                    const color=fg.slice(0,3).map((c,i)=>alpha*c+(1-alpha)*bg[i]);
                    const lum=c=>c.slice(0,3).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4}).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);
                    const a=lum(color),b=lum(bg);return (Math.max(a,b)+.05)/(Math.min(a,b)+.05);
                }""")
            for mode in ('Light','Dark'):
                first.get_by_test_id('stMainMenu').click()
                first.get_by_role('menuitemradio',name=mode,exact=True).click();first.keyboard.press('Escape')
                for width in (1366,360):
                    first.set_viewport_size({'width':width,'height':900})
                    for number,label in enumerate(('Dados','Conferir','Analisar','Resultados','Baixar'),1):
                        step(first,number,label).click()
                        expect(first.get_by_text(re.compile(rf'Etapa atual: {number} de 5'))).to_be_visible()
                        assert first.evaluate('document.documentElement.scrollWidth <= window.innerWidth+2')
                        for n,name in enumerate(('Dados','Conferir','Analisar','Resultados','Baixar'),1):
                            button=step(first,n,name)
                            expect(button).to_be_visible()
                            box=button.bounding_box()
                            assert box and box['width']>=44 and box['height']>=44
                        active=step(first,number,label)
                        active.focus();first.keyboard.press('Tab');first.keyboard.press('Shift+Tab')
                        assert active.evaluate('(el)=>getComputedStyle(el).outlineStyle')!='none'
                        assert contrast(first,'h1')>=4.5
                        assert contrast(first,'.st-key-project_stepper button[kind="primary"]')>=4.5
                        if number==1:
                            dropzone=first.get_by_test_id('stFileUploaderDropzone')
                            assert dropzone.evaluate('(el)=>getComputedStyle(el).borderTopStyle') in ('dashed','solid')
                        if number==3:
                            assert contrast(first,'.st-key-analysis_questions [role="group"] > span > span')>=4.5
                        first.screenshot(path=str(evidence/f'{mode.lower()}-{width}-step{number}.png'),full_page=True)
            first.set_viewport_size({'width':1366,'height':900})
            # Reconfigurar deve invalidar o relatório já revisado.
            step(first,3,'Analisar').click()
            expect(first.get_by_role('heading',name='O que você quer descobrir?')).to_be_visible()
            first.get_by_role('combobox',name='Perguntas da pesquisa',exact=True).click()
            first.get_by_role('option',name='Rede de apoio e qualidade do sono',exact=True).click()
            first.keyboard.press('Escape')
            first.screenshot(path=str(evidence/'analysis-changed.png'),full_page=True)
            (evidence/'analysis-changed.txt').write_text(first.locator('body').inner_text(),encoding='utf-8')
            expect(step(first,5,'Baixar')).to_be_disabled()
            expect(step(first,4,'Resultados')).to_be_disabled()
            assert not first.get_by_role('link',name='Baixar resultado_completo.zip',exact=True).count()
            # A third independent session creates a filled draft, downloads and resumes it.
            creator_context=browser.new_context(viewport={'width':1366,'height':900},accept_downloads=True,locale='pt-BR')
            creator=creator_context.new_page();creator.goto(url)
            creator.get_by_text('Criar planilha',exact=True).click()
            expect(creator.get_by_text('As perguntas e categorias já estão prontas. Ajuste somente se precisar.',exact=True)).to_be_visible()
            creator.screenshot(path=str(evidence/'creator-categories.png'),full_page=True)
            creator.get_by_role('button',name='Começar preenchimento',exact=True).click()
            creator.get_by_role('textbox',name='Nome ou apelido (opcional)',exact=True).fill('Brenda fictícia')
            creator.get_by_role('button',name='Começar perguntas',exact=True).click()
            expect(creator.get_by_text('Pergunta 1 de 68',exact=True)).to_be_visible()
            creator.get_by_role('spinbutton').fill('35')
            creator.get_by_role('button',name='Próxima',exact=True).click()
            expect(creator.get_by_text('Pergunta 2 de 68',exact=True)).to_be_visible()
            creator.get_by_text('Importar planilha',exact=True).click()
            expect(creator.get_by_role('heading',name='Importe sua planilha')).to_be_visible()
            creator.get_by_text('Criar planilha',exact=True).click()
            expect(creator.get_by_text('Pergunta 2 de 68',exact=True)).to_be_visible()
            creator.get_by_text('Com companheiro',exact=True).click()
            creator.get_by_role('button',name='Próxima',exact=True).click()
            expect(creator.get_by_text('Pergunta 3 de 68',exact=True)).to_be_visible()
            creator.get_by_role('button',name='Preparar planilha para baixar',exact=True).click()
            draft_link=creator.get_by_role('link',name='Baixar banco_preenchido.xlsx',exact=True)
            expect(draft_link).to_have_attribute('href',re.compile(r'^data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,'))
            with creator.expect_download() as draft_info:draft_link.click()
            draft_path=tmp_path/'draft.xlsx';draft_info.value.save_as(draft_path)
            draft=pd.read_excel(draft_path,sheet_name='Banco')
            assert len(draft)==1 and draft.iloc[0].IDADE_M==35
            assert draft.iloc[0].SIT_CONJ==1 and pd.isna(draft.iloc[0].ESCOL)
            assert draft.iloc[0].NOME=='Brenda fictícia'
            creator.screenshot(path=str(evidence/'creator-question.png'),full_page=True)
            assert not first.get_by_role('link',name='Baixar banco_preenchido.xlsx',exact=True).count()
            creator.get_by_text('Importar planilha',exact=True).click()
            creator.locator('input[type=file]').set_input_files(draft_path)
            creator.get_by_role('button',name='Continuar',exact=True).click()
            expect(creator.get_by_role('heading',name='Confira os dados antes de analisar')).to_be_visible()
            creator.get_by_role('button',name='Continuar preenchimento no assistente',exact=True).click()
            expect(creator.get_by_text('1 participante(s) na planilha.',exact=True)).to_be_visible()
            creator.get_by_text('Editar participantes',exact=True).click()
            creator.get_by_role('button',name='Editar participante',exact=True).click()
            expect(creator.get_by_role('textbox',name='Nome ou apelido (opcional)',exact=True)).to_have_value('Brenda fictícia')
            creator.get_by_role('button',name='Começar perguntas',exact=True).click()
            expect(creator.get_by_role('spinbutton')).to_have_value(re.compile(r'^35(?:\.0+)?$'))
            creator.set_viewport_size({'width':360,'height':800})
            creator.screenshot(path=str(evidence/'creator-mobile.png'),full_page=True)
            assert creator.evaluate('document.documentElement.scrollWidth <= window.innerWidth + 2')
            # Use the native per-browser theme selector; changing theme must preserve answers.
            creator.get_by_test_id('stMainMenu').click()
            creator.screenshot(path=str(evidence/'theme-menu.png'),full_page=True)
            (evidence/'theme-menu.txt').write_text(creator.locator('body').inner_text(),encoding='utf-8')
            creator.get_by_role('menuitemradio',name='Dark',exact=True).click()
            creator.keyboard.press('Escape')
            expect(creator.get_by_role('spinbutton')).to_have_value(re.compile(r'^35(?:\.0+)?$'))
            creator.wait_for_function("() => {const c=getComputedStyle(document.querySelector('[data-testid=stApp]')).backgroundColor.match(/\\d+/g);return c && c.slice(0,3).every(n=>Number(n)<100)}")
            color=creator.get_by_test_id('stApp').evaluate('(element)=>getComputedStyle(element).backgroundColor')
            channels=[int(c) for c in re.findall(r'\d+',color)[:3]]
            assert len(channels)==3 and max(channels)<100,color
            creator.screenshot(path=str(evidence/'creator-dark-mobile.png'),full_page=True)
            browser.close()
    finally:
        server.terminate();server.wait(timeout=15);log.close()
