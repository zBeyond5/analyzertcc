# Apresentação compreensível dos resultados Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar resultados legíveis para não especialistas e relatórios PDF/Word com gráficos, preservando rigor e rastreabilidade.

**Architecture:** Criar um vocabulário e um modelo estruturado de apresentação compartilhados por UI, relatórios e tabelas. Dados de gráficos derivam da população/pares já usados; Matplotlib gera figuras estáticas locais para ReportLab/python-docx, enquanto Plotly mantém interação. Não reescrever o motor nem transformar strings técnicas em cálculos.

**Tech Stack:** Python 3.12, Streamlit, pandas, Matplotlib Agg, Plotly, ReportLab, python-docx e ferramentas de QA já existentes. ponytail, frontend-design, skills PDF/documentos para verificação visual; Context7 nas APIs em dúvida. Sem novas dependências.

**Spec:** `docs/superpowers/specs/2026-11-05-readable-research-outputs.md`, com evidências em `docs/superpowers/specs/2026-11-05-uneb-physiotherapy-source-review.md`. Base atual: da0f66a. O trecho do anexo é referência de falhas de apresentação, não oráculo de resultados científicos.

## Global Constraints

- Apresentação em português brasileiro, com nomes compreensíveis e termos explicados no contexto.
- Não alterar dados, testes, população, valores de p, estimativas, intervalos ou orientação das comparações.
- Não inferir significado de categoria desconhecida ou personalização clínica pelo código/frequência.
- Não afirmar causalidade, importância prática pelo p, elegibilidade total ou aprovação científica inexistente.
- Preservar aviso de dados fictícios, resultados não significativos, análises indisponíveis e limitações relevantes.
- Sem IA em execução, novas dependências, serviços externos ou cache global de dados/figuras.
- Preservar sessão proprietária, limites de trabalho/artefatos, expiração e downloads privados.
- Códigos internos e cabeçalhos de arquivos de reimportação permanecem estáveis; traduzir a apresentação, não o banco.
- Dois destinos: Relatório completo (`editorial`) com sumário e Material para o artigo (`article`) sem estrutura de monografia. Nenhum selo de conformidade ABNT/UNEB sem template conferido.

## Review Focus

1. Rótulo/categoria personalizados ou desconhecidos: nenhuma equivalência inventada, nenhum script/HTML executado — tarefas 1/4/5.
2. p diferente em comparações da mesma pergunta, efeito ausente e inferência indisponível: leitura específica sem conclusão universal ou valor fabricado — tarefa 2.
3. Grupos desbalanceados/ausentes/exclusões AV3: números e denominadores idênticos no gráfico, texto, tela e relatório — tarefas 2/3.
4. Títulos longos/Unicode/seis colunas/100 comparações: texto e gráficos dentro da página, memória/artefatos limitados e nada truncado — tarefas 3/4/7.
5. Códigos de máquina e dados identificáveis: roundtrip/exportações compatíveis, sem nomes em narrativa, imagens ou arquivos de outra sessão — tarefas 1/5/7.

---

## Mapa de arquivos e interfaces

- Novo `src/tcc_analyzer/presentation.py`: vocabulário, categorias, medidas/termos e objetos ReportComparison/ReportDocument. Usa profile e results; não importa Streamlit.
- Novo `src/tcc_analyzer/report_figures.py`: ChartData + figuras PNG locais, sem UI ou chamadas web.
- Modificar `reporting.py`: build_tables com rótulos legíveis e renderers usando ReportDocument opcional; manter chamadas antigas compatíveis durante migração.
- Modificar `pipeline.py`: cria uma vez o documento com a população final, distribui aos renderers e exporta tabelas/glossário; nenhuma mudança de analyze_pair ou seleção de método.
- Modificar `ui/pages.py`, `ui/charts.py`: consumir o mesmo vocabulário e modelo de leitura, não duplicar mapeamentos.
- `models.py`: somente extensão opcional de RunArtifacts com `presentation: object | None = None`; não alterar estruturas estatísticas. Dataclasses de apresentação ficam em presentation.py.
- `exports.py`: alterar apenas exportação de dicionário se necessário para novas colunas informativas; manter export_epiinfo e cabeçalhos técnicos intocados.
- Novos testes `test_presentation.py`, `test_report_figures.py`, `test_report_layout.py`; ampliar `test_exports_reports.py`, `test_pipeline.py`, `test_charts.py`, `test_browser.py`. Evidências privadas em test-results/readable-reports.
- Novo `configs/report_styles.yaml`: somente os dois destinos documentados; não criar perfil institucional não verificado. Sumário e seleção de destino na tarefa6, antes do aceite final da tarefa7.

## Tarefa 1 — Vocabulário completo de leitura

**Interfaces:** `field_title(code: str, profile: ResearchProfile) -> str`; `category_title(code: str, value: object, profile: ResearchProfile) -> str`; `term_definition(key: str) -> str`. Resolver aliases documentados por chave; títulos curtos conhecidos com pergunta completa disponível como contexto. Constantes `TERM_DEFINITIONS`, `METHOD_DESCRIPTIONS`, `FIELD_TITLES` incluem todos os campos dos dois perfis, derivados e termos listados na spec. Unidade só quando documentada. Personalização usa a descrição efetiva em vez de título padrão incompatível.

- [ ] **1. Escrever testes:**

```python
assert field_title('DEPRE',profile) == 'Depressão (diagnóstico informado)'
assert field_title('ESCOL',profile) == 'Grau de escolaridade'
assert field_title('ACOMP_TEP',profile) == 'Acompanhamento terapêutico da criança'
assert field_title('PSQI_G',profile) == 'Classificação da qualidade do sono'
assert all(field_title(v.name,profile) != v.name for v in profile.variables if v.kind != 'text')
```

Testar ambos perfis, aliases/derivados, categoria sem legenda, texto personalizado longo/<>&, palavra contendo PSI/TO sem substituição parcial e pergunta semanticamente alterada. Nenhum código cru no corpo principal quando há definição; no apêndice é permitido. ID/nome nunca tornam-se variáveis narrativas.
- [ ] **2. Demonstrar vermelho:** `python -m pytest tests/test_presentation.py -v`; APIs ausentes.
- [ ] **3. Implementar presentation.py**, com mapeamento completo conferido em perfis/Perguntas/Categorias e definições curtas da spec. Não modificar nomes internos ou perguntas validadas da coleta. Para campos desconhecidos, mensagem neutra e referência técnica.
- [ ] **4. Verificar:** mesmo comando e testes de profiles/importers existentes; nenhum valor/código de entrada alterado.
- [ ] **5. Commit:** vocabulário e testes; `feat: add a shared reader-friendly research vocabulary`.

## Tarefa 2 — Construir leitura estruturada e fiel por comparação

**Interfaces:** `ReportComparison` com `id`, `title`, `family_label`, `n_effective`, `n_missing`, `method_label`, `method_explanation`, `p_display`, `interpretation`, `estimates: tuple[str,...]`, `reading`, `warnings: tuple[str,...]`, `technical_notes: tuple[str,...]`. `ReportDocument` com `title`, `summary: tuple[str,...]`, `comparisons: tuple[ReportComparison,...]`, `glossary: dict[str,str]`, `limitations`, `technical_notes`. `build_document(results, tables, profile, data, metadata) -> ReportDocument`; somente população final, sem nomes/IDs no objeto. Consumir interpret_p já validado; não recalcular p/IC.

- [ ] **1. Escrever testes com resultados artificiais:**

```python
assert document.comparisons[0].p_display == '0,096'
assert document.comparisons[1].p_display == '0,002'
assert document.comparisons[0].interpretation != document.comparisons[1].interpretation
assert len(document.comparisons) == len(results)
assert 'PSQI_G' not in document.comparisons[0].reading
```

Testar zero/um participante, p=0/.05/vizinhos/None/NaN, IC ausente, diferença negativa com grupos explícitos e categorias invertidas/renumeradas, correlação negativa/constante, ausência de inferência por esparsidade/variância nula. Não classificar a pergunta toda com o menor p. Avisos desconhecidos vão ao apêndice com aviso principal neutro; não inventar tradução clínica.
- [ ] **2. Demonstrar vermelho:** `python -m pytest tests/test_presentation.py tests/test_interpretation.py -v`.
- [ ] **3. Implementar build_document** a partir de TestResult/ComparisonSpec/perfil e descritivas dos pares. Usar group_order/event_value quando declarados; preservar ordem efetiva do motor. Produzir uma frase conclusiva por comparação e nota geral única de causalidade/multiplicidade. Não extrair estatísticas por regex de assumptions. Não tratar pressupostos do método como fatos confirmados pela usuária.
- [ ] **4. Verificar:** testes anteriores e `python -m pytest tests/test_statistics.py tests/test_analysis_population.py -q`; resultados numéricos idênticos. Garantir que todos os status têm explicação específica e valores ausentes legíveis.
- [ ] **5. Commit:** modelo/textos/testes; `feat: explain each analysis from its structured results`.

## Tarefa 3 — Dados e figuras legíveis para tela e documento

**Interfaces:** `ChartData` em report_figures.py com `id`, `kind`, `x_title`, `y_title`, `categories`, `series`, `n_effective`, `n_missing`, `caption`, sem colunas identificáveis. `build_chart_data(data, profile, spec) -> ChartData | None`; `render_figure(chart: ChartData) -> bytes` retorna PNG. `ui/charts.py::build_figures` passa a construir Plotly dos mesmos ChartData, mantendo ChartView e render_charts compatíveis. Uma única definição de pares/denominadores, sem cache global.

- [ ] **1. Escrever testes:**

```python
assert chart.n_effective == analysis.result.n_effective
assert sum(chart.series[0]['counts']) == chart.n_effective  # cenário categórico simples
assert render_figure(chart).startswith(b'\x89PNG')
assert 'PRIVATE-NAME' not in repr(chart)
```

Fixtures artificiais cobrem cada combinação de tipos, ausentes, elegibilidade, categoria única/longa, um ponto por grupo, variância nula e zero pares; percentuais da figura correspondem à tabela. Confirmar chamadas repetidas fecham figuras e não acumulam arquivos. Testar 100 comparações com tamanho/duração registrados, não limite arbitrário de 1 segundo.
- [ ] **2. Demonstrar vermelho:** `python -m pytest tests/test_report_figures.py tests/test_charts.py -v`.
- [ ] **3. Implementar Matplotlib Agg sequencial**, PNG em memória, tipografia/legenda legíveis, rótulos por extenso e padrões para escala de cinza. Sem nomes/IDs em payload/metadados. Reutilizar ChartData para Plotly, com escaping na fronteira HTML. Sem regressão, ajuste de curvas ou teste novo; vazio tem mensagem, não imagem enganosa.
- [ ] **4. Verificar:** testes anteriores; renderizar um exemplo de cada tipo e inspecionar eixos, escala, corte, amostra/denominador e legenda. Conferir uso do job privado e orçamento de artefatos existente; não aumentar limites para fazer o teste passar.
- [ ] **5. Commit:** figuras/UI/testes; `feat: render consistent research figures locally`.

## Tarefa 4 — PDF e Word com edição visual de relatório

**Interfaces:** preservar `render_pdf(tables, metadata, output)` e `render_docx(...)` e acrescentar kw-only `document: ReportDocument | None = None`, `figures: dict[str, bytes] | None = None` durante migração. Criar `reporting.table_widths(frame: pd.DataFrame, available_width: float) -> tuple[float,...]`, com uma largura por coluna e soma igual à área disponível. Pipeline passa documento e figuras; chamadas legadas geram apresentação básica compatível, sem nota falsa de PSQI informado. PNGs em memória não são registrados como downloads independentes. Registrar fonte Unicode local de Matplotlib, conferindo sua licença/caminho, sem depender do Windows ou internet.

- [ ] **1. Criar testes de conteúdo/layout:**

```python
assert len(reader.pages) > 0
assert 'Classificação da qualidade do sono' in main_text
assert 'PSQI_G × ZARIT' not in main_text
assert image_count(pdf_path) >= 1
assert all(len(table_widths(frame,495)) == len(frame.columns) for frame in tables.bivariate)
assert all(abs(sum(table_widths(frame,495))-495) < .01 for frame in tables.bivariate)
```

Os helpers do teste distinguem corpo principal e apêndice pelo marcador “Apêndice técnico”. Testar os dois perfis, origem calculada/informada/mista, vazio, 1/100 comparações, Unicode/<>&, títulos de 300 caracteres e seis colunas; nenhuma figura/célula fora da área útil. DOCX deve conter imagens, glossário e cabeçalhos de tabela repetidos. Não exigir igualdade byte a byte de PDF/ZIP com timestamps.
- [ ] **2. Demonstrar vermelho:** `python -m pytest tests/test_report_layout.py tests/test_exports_reports.py -v`; relatórios atuais não têm figuras e vazam códigos no corpo.
- [ ] **3. Implementar estrutura editorial da spec** em reporting.py. Calcular larguras pelo número real de colunas/área A4, quebrar linhas e repetir cabeçalhos, preservar fonte legível sem reduzir indiscriminadamente. Títulos e figuras/legendas próximos, paginação e rodapé, aviso fictício em todas as páginas. Corpo narrativo de 11 pt e tabelas/legendas >=9 pt. Apêndice recebe referências técnicas, códigos e detalhes. Não colocar tabelas de 100 linhas inteiras em KeepTogether. Nenhuma capa longa ou identidade inventada.
- [ ] **4. Verificar visualmente:** gerar PDFs de demonstração padrão e todos os fatores AV3; renderizar páginas em PNG (PyMuPDF/Poppler disponível) e inspecionar todas as páginas, inclusive primeira/última e continuação de tabelas. Renderizar Word com ferramentas locais das skills documentos/PDF; se indisponível, registrar a limitação e validar XML/conteúdo, sem alegar inspeção visual realizada. Repetir após correção de layout, sem mascarar cortes com fonte minúscula.
- [ ] **5. Commit:** renderers e testes; `feat: produce illustrated readable PDF and Word reports`.

## Tarefa 5 — Integração em todos os outputs sem quebrar dados técnicos

**Files:** pipeline.py, reporting.py, models.py, exports.py (somente dicionário), ui/pages.py, ui/charts.py; testes de pipeline/exports/browser.

**Interfaces:** RunArtifacts recebe `presentation` opcional com default None. Pipeline constrói build_document uma vez da mesma população já selecionada; renderers/tabelas/UI recebem esse objeto. Manifesto acrescenta `presentation_version='readable-reports-v1'`, sem substituir chaves analíticas. Manter filenames/allowlist/registro/ZIP. Tabelas Excel recebem títulos e cabeçalhos de leitura e uma aba Glossário; CSV/Epi Info conservam códigos técnicos e dados existentes. Dicionário adiciona nome de leitura/unidade mantendo colunas antigas.

- [ ] **1. Escrever regressões:**

```python
assert updated_results == baseline_results  # comparar números/specs, não objetos de UI
assert exported_bank.columns.tolist() == baseline_bank.columns.tolist()
assert exported_bank.equals(baseline_bank)
assert metadata['presentation_version'] == 'readable-reports-v1'
assert len(document.comparisons) == len(metadata['comparisons'])
```

Testar tela e PDF/Word/XLSX com mesmos valores/estimativas/legendas; códigos somente em área técnica. Roundtrip do banco, categorias renumeradas, nomes maliciosos e dois usuários com resultados distintos. Banco/manifesto/auditoria não passam por substituição global de texto. Conferir orçamento de PNGs e artefatos no pipeline; erro deixa mensagem segura e não disponibiliza PDF parcial.
- [ ] **2. Demonstrar vermelho:** `python -m pytest tests/test_pipeline.py tests/test_exports_reports.py tests/test_guided_flow.py -v`.
- [ ] **3. Integrar vocabulário e leitura**, eliminando SHORT_LABELS/mapeamentos duplicados quando cobertos. UI não usa pergunta longa como título repetido; contexto fica na ajuda. A técnica permanece acessível em detalhes, sem JSON como apresentação principal. Explicação de n/p/IC aparece ao lado do resultado e glossário nos arquivos. Não alterar algoritmo/seleção/limites de upload, população ou permitir cache global.
- [ ] **4. Verificar:** testes anteriores mais `python -m pytest tests/test_importers.py tests/test_data_entry.py tests/test_sessions.py -q`; preservar hashes/valores dos dados de entrada e n/p/estimativas. Registrar diferenças intencionais de layout, abas e campos informativos.
- [ ] **5. Commit:** integração/testes; `feat: unify readable outputs while preserving machine exports`.

## Tarefa 6 — Sumário e material para integrar o artigo

**Files:** reporting.py, presentation.py, novo `configs/report_styles.yaml`, tests/test_report_layout.py e docs/acceptance.md. Nenhuma mudança nos dados ou métodos estatísticos.

**Interfaces:** perfis de estilo locais versionados `editorial` e `article`; `load_report_style(name: str) -> dict` lê apenas esses identificadores, com ValueError para outro nome, sem eval/HTML ou caminho arbitrário. Cada perfil declara `label`, `include_toc`, `include_lists`, `include_glossary`, `include_technical_appendix`, `font_size_pt`, `margin_pt` e `paper`. Valores de layout comuns:11pt,50pt,A4; legendas/tabelas >=9pt. `editorial` habilita os quatro elementos; `article` os desabilita e usa apenas procedimentos estatísticos/resultados com notas essenciais. Acrescentar kw-only `style: str = 'editorial'` aos renderers. ReportDocument fornece hierarquia de seções e identificadores estáveis de tabelas/figuras; renderers calculam paginação própria. Escolha em Baixar: “Relatório completo”/“Material para o artigo”; alterar destino não recalcula estatísticas. Preservar propriedade/expiração do job e publicar cada artefato apenas após conclusão da geração.

- [ ] **1. Escrever testes de sumário/paginação:** PDF editorial com tabelas longas e títulos multilinha deve ter todos os itens do sumário/listas apontando para suas páginas reais, com links internos corretos. Alterar quantidade de comparações deve atualizar páginas e listas. DOCX editorial contém estilos Heading1/Heading2 e campos TOC/listas atualizáveis, sem copiar páginas do PDF. Testar zero figuras e nenhuma lista vazia. Siglas expandidas apenas quando usadas; nenhum item institucional fictício. Assertar `load_report_style('article')['include_toc'] is False`, `load_report_style('editorial')['include_toc'] is True` e rejeição de `../outro`. Exportação article não contém sumário/capa/apêndice, mas mantém todos os resultados, métodos, denominadores, avisos científicos e notas das figuras/tabelas. Não contém “conforme UNEB”, aprovação ética, ajuste por confundidores não realizado ou redação inventada do estudo inteiro.
- [ ] **2. Demonstrar vermelho:** `python -m pytest tests/test_report_layout.py -v`; sumário/listas ainda ausentes.
- [ ] **3. Aplicar a conferência normativa** de `docs/superpowers/specs/2026-11-05-uneb-physiotherapy-source-review.md`. Evidência publicada orienta o destino artigo; um template específico permanece não verificado. Ambos os destinos usam o layout editorial já definido, sem promessa ABNT/UNEB. Não bloquear o fluxo básico nem escolher periódico pela usuária. Usar STROBE como conferência dos itens observáveis, sem exigir novo teste, simular dados ou declarar cumprimento integral. Não fazer pesquisas externas dentro do aplicativo.
- [ ] **4. Implementar os dois destinos e sumário automático** no ReportLab com múltiplas passagens e destinos internos; DOCX com campos e instrução de atualização local quando necessária. Tabelas/figuras com legendas e numeração geradas da mesma ordem estrutural. Article recebe título claro de material parcial e texto conciso de procedimentos/resultados, sem seções de trabalho completo. As descrições vêm dos objetos estatísticos executados; termos principais são expandidos na primeira ocorrência e as notas preservam significado, sem exigir glossário separado. Não criar conclusão geral, referência, autoria ou aprovação ética. Reutilizar conteúdo/figuras, sem duplicar motor ou analisar o texto livre para recuperar valores.
- [ ] **5. Verificar visualmente os dois modelos**, com paginação curta/longa e mudança de dados; conferir cada entrada do sumário contra o documento final. Se não houver renderizador DOCX disponível, registrar que atualização visual dos campos depende do Word; não alegar sumário DOCX pré-calculado. Executar regressões de pipeline e exportação para provar que trocar estilo não muda números. Preview antes de publicar; commit dos arquivos desta tarefa.

## Tarefa 7 — Aceite editorial e de uso completo

**Files:** tests/test_browser.py, tests/test_report_layout.py, README, docs/acceptance.md.

- [ ] **1. Acrescentar aceites do trecho recebido:** equivalentes artificiais das comparações por médias, classificações e escores, com p distintos, esparsidade e variância nula. Assertar nomes claros e razões específicas no corpo; nenhum “p=Não calculado”, repetição mecânica ou unificação indevida. Testar toda cobertura de campos/termos por enumeração de perfis, sem proibir códigos no apêndice técnico.
- [ ] **2. Demonstrar falha dos novos casos** e fechar integração; `python -m pytest tests/test_presentation.py tests/test_report_layout.py tests/test_browser.py -v`.
- [ ] **3. Conferir cenário completo:** importar → analisar → ler resumo/gráfico → baixar PDF/Word/tabelas → abrir documentos. Browser em360px/claro/escuro, mantendo privacidade/retorno/invalidação; PDF/Word para impressão clara. Capturar preview da UI e páginas reais do relatório em test-results/readable-reports. A figura web não pode ser o único lugar com legenda útil.
- [ ] **4. Rodar suíte final** `python -m pytest -q`, `python -m compileall -q src app.py cloud/app.py`, `python -m pip check`. Registrar separado: matemática já preservada, interpretação de apresentação, leitura visual de arquivos, aceite científico e testes externos Cloud/Hamachi/Epi Info. Não alegar conformidade ABNT ou equivalência de aceite científico.
- [ ] **5. Documentar e mostrar preview:** exemplos de página e nomes completos, testes, o que não foi testado; commit final. Push/publicação somente com autorização pertinente. Não instalar biblioteca nova para “embelezar”.

## Revisão própria e handoff

Cobertura conferida: variáveis/categorias/aliases/termos em1, p/estimativas/motivos em2, gráficos em3, layout real PDF/Word em4, demais outputs e compatibilidade em5, sumário/destinos em6, testes/preview em7. Os cinco riscos possuem casos nas tarefas. Códigos permitidos no apêndice e bancos técnicos são intencionais. Nenhum requisito depende de inferir valores a partir do texto do anexo ou de chamar IA na aplicação.

Preferência de execução nativa preservada, com revisão independente final quando útil. Planejamento salvo; implementação ainda não iniciada. Revisar esta proposta antes de executar.

Complemento revisado: tarefa6 cobre sumário/listas e os destinos editorial/article, com teste de páginas reais; tarefa7 faz o aceite integrado depois de ambos. Adequação específica a template/periódico depende de exigências não confirmadas; isso não impede os relatórios nem autoriza afirmar conformidade institucional.

Atualização de contexto: usuário confirmou Fisioterapia/UNEB e autorizou pesquisa. Conferência oficial registrada em2026-11-05: modalidade artigo sustentada por trechos indexados do PPC atual e anterior; regras específicas de colegiado e eventual periódico não substituídas por normas de UFES/outros cursos. Abertura integral dos documentos UNEB não obtida; não declarar validação normativa integral. Planejamento atualizado; aplicativo e cálculos não alterados nesta etapa.
