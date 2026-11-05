# Refinamento visual suave Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Aplicar o refinamento visual proposto pelo Claude sem alterar o comportamento validado do TCC.

**Architecture:** Centralizar tema/CSS no pacote UI existente e reutilizar funções de navegação, importação e análise. Introduzir componentes de apresentação pequenos apenas onde usados. Executar fases sequenciais com evidência visual e regressões, sem reescrever o produto.

**Tech Stack:** Python 3.12, Streamlit 1.66.1, Plotly e testes pytest/Playwright existentes. frontend-design para apresentação, ponytail para menor alteração, context7 somente para API em dúvida.

**Spec:** `docs/superpowers/specs/2026-11-05-soft-ui-refinement.md`; fonte externa identificada na spec. Contrato atual: commit 5672dba e AGENTS.md existente.

## Global Constraints

- Alterar somente apresentação; preservar leitura, validação, população analítica, cálculos, exportações e formatos de dados.
- Preservar topo clicável e barra lateral sincronizados, sem dois estados de navegação independentes.
- Manter temas claro e escuro e o seletor nativo acessível.
- Não adicionar dependências, CDN, fontes remotas ou serviços externos nesta atualização.
- Não usar seletores CSS hasheados nem conteúdo de upload em HTML/CSS.
- Interface em português brasileiro, foco visível, alvos de toque de pelo menos 44 px e texto com contraste mínimo de 4,5:1.
- Funcionar em 360 px sem rolagem horizontal da página nem etapas inacessíveis.
- Preservar sessão proprietária, limites de upload/concorrência, expiração, XSRF e downloads privados.

## Review Focus

1. Trocar Importar/Criar ou voltar etapas: preservar rascunho e não criar nova sessão — fases 2/3.
2. Zero, espaços, None e banco sem células: percentual vazio coerente, sem modificar respostas — fase 4.
3. Tema escuro com destaque claro, tema claro e teclado: contraste e foco reais, navegação disponível — fases 1/2/6.
4. Conteúdo malicioso em nomes/células: somente texto em widgets, sem HTML/JS executado — fases 3/4/6.
5. CSS ausente ou upload inválido: aplicativo funcional com mesma proteção/erros e arquivos privados — fases 1/6.

---

## Arquivos e responsabilidades

| Arquivo | Responsabilidade |
| --- | --- |
| `AGENTS.md` | Complemento curto de contratos visuais sem apagar regras existentes |
| `src/tcc_analyzer/ui/theme.py`, `ui/styles.css` (novos) | Única entrada do CSS estático, layout e tokens |
| `src/tcc_analyzer/ui/components.py` (novo) | card/metric_row, resumo vazio e apresentação de etapas realmente reutilizados |
| `src/tcc_analyzer/ui/navigation.py` | Mantém progress_status/retorno/bloqueios; delega aparência dos controles |
| `src/tcc_analyzer/ui/pages.py`, `ui/create_sheet.py` | Integração nas telas sem mudança dos caminhos de dados |
| `.streamlit/config.toml`, `cloud/.streamlit/config.toml` | Paridade de tema, preservando binds e segurança |
| `tests/test_ui.py`, `test_navigation.py`, `test_guided_flow.py`, `test_browser.py` | Contratos de uso, regressões e evidência real |
| `tests/test_ui_components.py` (novo) | Casos de vazio/zero e componentes sem mutação |
| `docs/acceptance.md`, README | Evidência e instruções atualizadas |

Não mover núcleo estatístico, parser, gerenciador de jobs ou exportadores. Não criar um segundo pacote ui na raiz. Não adicionar requirements.txt concorrente aos locks existentes.

## Fase 1 — Tema central e contratos preservados

**Interfaces:** `ui/theme.py::apply_theme() -> None`, lê styles.css relativo a __file__, injeta somente conteúdo local estático uma vez em main após set_page_config. Sem cache de estado da pesquisa. CSS ausente deve resultar em aviso discreto e continuar com tema nativo, sem falhar na análise.

- [x] **1. Escrever regressão de funcionamento sem CSS**, com monkeypatch de `apply_theme` para no-op no AppTest; carregar demonstração, navegar e baixar. Teste de arquivo inexistente exerce aviso e continuidade; importação do módulo não altera session_state. Não testar apenas presença de seletor.
- [x] **2. Demonstrar vermelho:** `python -m pytest tests/test_ui_components.py tests/test_guided_flow.py -v`; nova API ainda ausente.
- [x] **3. Implementar tema e complemento AGENTS.md.** Acrescentar apenas regras de CSS central, escopo visual, HTML seguro, responsividade e ausência de dependências novas. Remover estilos de main/navigation e centralizar equivalentes no arquivo único. Tokens/raios/largura/padding conforme spec; preservar fontes/foco/download. Configs mudam somente tema; manter toolbar viewer e rede/segurança intactas.
- [x] **4. Verificar:** mesmo comando mais `python -m pytest tests/test_network_config.py tests/test_ui.py -q`; comparar configs antes/depois e inspecionar entrada nos dois temas. Registrar a inspeção; não criar teste de screenshot pixel a pixel.
- [x] **5. Commit:** arquivos desta fase; `refactor: centralize presentation styles without changing workflows`.

## Fase 2 — Passo a passo clicável e componentes mínimos

**Interfaces:** preservar `render_navigation(state, steps) -> str`, `progress_status(state)` e chaves de navegação. Criar `components.py::stepper(current: int, steps: tuple[str,...], available: tuple[bool,...], completed: tuple[bool,...], on_select) -> None`. Somente constants/labels do código; não calcula estado científico. `card(key: str)` retorna contêiner nativo com borda; `metric_row(metrics: tuple[tuple[str,str,str | None],...]) -> None` apresenta valor e ajuda. Criar cada helper só quando usado nesta entrega.

- [x] **1. Escrever testes de navegação:**

```python
before = state.prepared.data.copy(deep=True)
# AppTest: em etapa 3, clicar no topo 2; depois lateral 1; retornar a 3.
assert state.prepared.data.equals(before)
assert state.artifacts is original_artifacts
assert progress_status(state)[0][3] is True  # artefatos existentes
```

Adicionar estados incompletos/desabilitados sem concluir por visita. Browser: todos os cinco controles dentro de 360 px com bounding box de pelo menos 44×44; número e rótulo acessíveis, atual indicado além de cor. Alterar dados mantém invalidação já existente.
- [x] **2. Demonstrar vermelho:** novos aceites visuais/semânticos em `python -m pytest tests/test_navigation.py tests/test_browser.py -v`; registrar quais não são atendidos antes da alteração. Não modificar assertions de privacidade.
- [x] **3. Extrair apresentação para stepper**, mantendo seleção nativa e lógica de navigation. Sem JS que edite DOM, sem converter topo em indicador passivo. Lista ordenada estática complementar pode fornecer aria-current; não duplicar foco ou leitura. Em celular, controles quebram em linhas; não escondem nomes.
- [x] **4. Verificar:** testes anteriores, teclado/Shift+Tab, foco e contraste nos dois temas. Uma única fonte session_state.navigation para topo/lateral.
- [x] **5. Commit:** componentes/navigation/CSS e testes; `style: refine accessible clickable research steps`.

## Fase 3 — Entrada mais clara e upload em destaque

**Interfaces:** preservar `data_route` com valores `Importar planilha`/`Criar planilha` e `render_create_sheet(on_use, download)`. Usar segmented_control nativo se API instalada suportar seleção inicial/retorno por estado; consultar Context7 antes de adaptar. Não usar duas tabs que executam ambos os ramos.

- [x] **1. Escrever testes do contrato de alternância:**

```python
assert at.session_state['sheet_builder']['draft']['IDADE_M'] == 35
# Alternar Importar e voltar Criar no mesmo AppTest.
assert at.session_state['sheet_builder']['draft']['IDADE_M'] == 35
assert at.session_state['workflow'].session is original_session
```

Browser testa demonstração visível sem expander, upload principal, retorno do assistente após reimportação e texto com `<script>` mostrado como texto sem executar. Reutilizar fixtures artificiais.
- [x] **2. Demonstrar vermelho:** `python -m pytest tests/test_guided_flow.py tests/test_browser.py -v`; observar botão demo atualmente recolhido e alteração de seletor ainda não atendida.
- [x] **3. Implementar layout:** um card para upload e instrução curta, dropzone escopada por key/data-testid indispensável, botão secundário de demonstração visível. Seleção Importar/Criar com chave existente e reruns preservados. Não mudar import_bytes, limites ou parsing. Não mandar nomes de arquivo para unsafe HTML. Criador conserva categorias antes de uma pergunta por tela.
- [x] **4. Verificar:** testes anteriores e `python -m pytest tests/test_importers.py tests/test_data_entry.py -q`; desktop/360 px nos dois temas. Apenas o ramo selecionado executa.
- [x] **5. Commit:** UI/CSS/testes; `style: clarify spreadsheet import and guided entry`.

## Fase 4 — Resumo e prévia úteis sem nova limpeza de dados

**Interfaces:** `components.py::input_summary(frame: pd.DataFrame) -> dict[str,int | float]`, chaves `rows`, `columns`, `empty_percent`; `empty_percent=0.0` se não houver células. `metric_row` recebe strings formatadas locais. Consumir state.imported.raw, não prepared.data com derivados.

- [x] **1. Escrever testes puros:**

```python
frame = pd.DataFrame({'a':[0,None], 'b':[' ', 'x']})
original = frame.copy(deep=True)
assert input_summary(frame) == {'rows':2,'columns':2,'empty_percent':50.0}
assert frame.equals(original)
assert input_summary(pd.DataFrame())['empty_percent'] == 0.0
```

Cobrir NaN, string vazia, números/horários, planilha larga e espaços. A métrica não exclui participante nem altera validação.
- [x] **2. Demonstrar vermelho:** `python -m pytest tests/test_ui_components.py -v`.
- [x] **3. Implementar resumo na conferência:** métricas com n/campos/% de vazios de entrada, ajuda explica denominador. Prévia recolhível com head(20), usando display_frame existente. Preservar mensagem de erros reais, população AV3 e retomada; remover apenas métricas duplicadas. Nenhuma cópia em cache global/log.
- [x] **4. Verificar:** testes puros e `python -m pytest tests/test_ui.py tests/test_analysis_population.py -q`; comparar n/p/seleção antes/depois para a mesma fonte.
- [x] **5. Commit:** componentes/pages/testes; `feat: show a read-only input overview`.

## Fase 5 — Aplicar padrão às telas restantes

**Interfaces:** manter assinaturas render_validation/render_comparisons/render_results/render_exports. Reutilizar card/metric_row; Plotly segue theme='streamlit' existente e dados já calculados.

- [x] **1. Escrever/verificar regressões de fluxo:**

```python
assert updated_artifacts.metadata['included_rows'] == baseline_artifacts.metadata['included_rows']
assert [a.result.p_value for a in updated_artifacts.results] == [a.result.p_value for a in baseline_artifacts.results]
# Arquivos/tabulações lidos: mesmos valores e população, ignorando datas de geração.
```

Usar input artificial determinístico e baseline do motor, sem fixtures de dados reais. Browser verifica n/p/IC/aviso fictício visíveis, confirmação contextual de população reduzida e download privado após voltar.
- [x] **2. Demonstrar lacuna visual antes da mudança:** capturar estado atual e rodar novos aceites de hierarquia/ação principal, mantendo regressões numéricas verdes como contrato.
- [x] **3. Ajustar somente composição:** um title global, subheaders por bloco, cards seletivos; uma ação de negócio primária por tela/estado. Download privado recebe destaque quando pronto, sem trocar mecanismo. Sem cards em cada parágrafo, retirada de limitações ou ocultação de resultados não significativos. Reusar abas nativas validadas.
- [x] **4. Verificar:** `python -m pytest tests/test_guided_flow.py tests/test_exports_reports.py tests/test_charts.py tests/test_browser.py -q`; revisar capturas claro/escuro e 360 px, conteúdo e foco.
- [x] **5. Commit:** UI/CSS/testes pertinentes; `style: unify research review results and downloads`.

## Fase 6 — Revisão visual, regressão e entrega

- [x] **1. Preparar matriz de aceites** em docs/acceptance.md: cinco etapas × claro/escuro × desktop/360 px; teclado, alvos ≥44 px, texto ≥4,5:1, foco, cores não exclusivas, sem overflow. Calcular contraste dos pares efetivamente renderizados, não só da tabela de tokens.
- [ ] **2. Executar uploads** CSV/XLSX/XLS, vazio, corrompido e >20 MiB; usar testes importers existentes e browser para confirmação das mensagens. Não afrouxar validação para cumprir estética.
- [x] **3. Executar duas sessões e modo sem CSS**, conservando rascunhos separados, downloads data-URL privados e ausência de chamadas de saída para CDNs/fontes. Revisar diff para assegurar núcleo/parser/jobs/exportadores intactos. HTML dinâmico existente de download permanece escapado e autorizado; novos componentes não interpolam uploads.
- [x] **4. Integrar:** `python -m pytest -q`, `python -m compileall -q src app.py cloud/app.py`, `python -m pip check`. Uma suíte verde não comprova deploy, Hamachi ou Epi Info; registrar pendências reais separadamente. Não criar testes de decoração de baixo valor.
- [x] **5. Mostrar preview e documentar** arquivos alterados e o que não foi testado; commit final de docs/testes. Publicação/push requerem autorização pertinente; este plano não executa nenhuma dessas ações.

## Revisão própria e entrega

As seis propostas do Claude estão mapeadas às fases 1–6. Divergências resolvidas: AGENTS complementado, não substituído; pacote existente em src; topo permanece clicável por resposta explícita do usuário; temas claro/escuro e toolbar nativa preservados; CSS centralizado sem dados; nenhuma dependência nova. Os cinco riscos têm casos atribuídos. Métrica nova tem definição exata e não altera limpeza. Funções/interfaces das fases seguintes coincidem com as definidas aqui.

Execução preferida preservada: nativa, sequencial, revisão específica apenas quando economizar tempo. Planejamento aprovado pelo usuário; implementação e verificação registradas abaixo.


## Registro da execução — 2026-11-05

Implementação concluída nativamente com revisão independente final. 170 testes passaram em121,11s; compileall/pipcheck verdes. Capturas das20combinações de etapa/tema/largura em test-results/soft-ui. Nenhuma fórmula, função de parsing ou exportador foi alterado. Topo continua clicável, estilo sem CSS preserva o fluxo até o download e alteração Importar/Criar preserva rascunho.

Decisões: componentes/funções nativos preservam semântica de botões e texto da etapa atual; não foi adicionado JS para injetar aria-current. CSS e dependências de apresentação são empacotados via package-data. Mudanças de fases interdependentes foram agrupadas num commit coerente após testes, em vez de commits com módulos ainda sem integração. Script Hamachi alheio preservado.

Contraste insuficiente de botões/tags no escuro foi corrigido e coberto no navegador. A apresentação não depende de cor exclusiva. O aceite de upload XLS binário válido e de deploy não foi executado nesta rodada; esses limites constam em docs/acceptance.md e não são declarados concluídos por uma suíte verde. Sem push/publicação nesta execução.
