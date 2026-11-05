# Guided Data and Usability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir criar ou importar o banco do TCC e chegar às análises com orientação simples e sem configurações técnicas obrigatórias.

**Architecture:** Reutilizar importadores, motor estatístico, relatórios e gerenciador de trabalhos. Adicionar perfil documentado, configuração opcional de categorias antes do cadastro e assistente de uma pergunta por vez, por sessão. Gerar Excel preenchido e reimportável a partir das respostas. Apresentação simplificada recebe plano de análise preparado pelo núcleo, com tema claro/escuro geral. Sem reescrever o produto.

**Tech Stack:** Python 3.12, Streamlit nativo, pandas, openpyxl e pytest/Playwright existentes. Aplicar frontend-design e ponytail; consultar context7 apenas nas APIs alteradas.

**Spec:** [Revisão de usabilidade e das três fontes](../specs/2026-11-04-usability-guided-data-design.md). Complementa a especificação original apenas nas mudanças descritas; métodos, privacidade e exportações existentes continuam vigentes.

## Global Constraints

- “Interface e relatórios em português brasileiro.”
- “Preservar entrada original e rastreabilidade; não alterar respostas silenciosamente.”
- “Não inferir significado de código desconhecido pelas frequências ou pelo nome do campo.”
- “Não preencher respostas ausentes com zero ou produzir escore de instrumento incompleto.”
- “Automatizar regras documentadas; nunca selecionar método pelo menor p.”
- “Manter dados fictícios identificados e evitar afirmações causais.”
- “Preservar isolamento, expiração, downloads privados, Windows/Hamachi e entrada Linux/cloud.”
- “Sem nova camada de backend, serviço de IA ou banco de dados para esta revisão.”

## Review Focus

1. Planilha nova sem totais PSQI/Zarit: aceitar respostas e gerar somente escores sustentados por regras aprovadas; Tarefas 1–2.
2. Código desconhecido ou dois cabeçalhos que convergem para o mesmo campo: não aplicar legenda errada nem apagar coluna; Tarefa 1.
3. Categorias editadas antes e depois das respostas, campo vazio confundido com zero, volta e reexecução: preservar significado, respostas e participantes sem duplicação; Tarefa 3.
4. Banco válido sem correções: chegar à análise sem referência, justificativa ou checkbox técnico obrigatório; Tarefas 4–5.
5. Alteração posterior ao relatório ou duas sessões: invalidar resultados antigos e manter cadastro/download isolado; Tarefas 3 e 5.
6. Modo claro/escuro geral, contraste e continuidade dos dados ao trocar tema; Tarefa 6.

---

## Avaliação do código atual e arquivos

`validation.py` exige todos os campos do perfil antigo e bloqueia por `mapping_pending`; `pipeline.py` depende dos totais informados e usa exceção de hash para a demonstração. `ui/pages.py` exibe editor de legendas, referência, correção genérica e seletor de método no caminho comum. A correção atual já é opcional, mas sua presença junto das exigências de validação comunica obrigatoriedade. Não remover validação ou auditoria para corrigir a apresentação.

| Arquivo | Mudança |
| --- | --- |
| `configs/profiles/tea_maternal_sleep_updated_v1.yaml` (novo) | 69 entradas, perguntas, opções e aliases extraídos das fontes, sem participantes |
| `src/tcc_analyzer/profiles.py`, `models.py`, `validation.py` | Reconhecimento de formato, campos derivados e capacidades disponíveis |
| `src/tcc_analyzer/scales.py` | Horários nativos/texto/decimal, Zarit e PSQI com regra versionada |
| `src/tcc_analyzer/data_entry.py` (novo) | Categorias personalizadas, respostas e Excel preenchido de ida/volta |
| `src/tcc_analyzer/ui/create_sheet.py` (novo), `ui/state.py` | Categorias antes do cadastro, uma pergunta por vez e rascunho por sessão |
| `src/tcc_analyzer/ui/pages.py` | Entrada importar/criar, conferência contextual, análise em linguagem comum |
| `src/tcc_analyzer/analysis_plan.py` (novo), `pipeline.py`, `statistics/selection.py` | Preparar comparações disponíveis com os métodos existentes |
| `reporting.py`, `exports.py` | Proveniência dos escores, labels humanos, banco gerado reimportável |
| `tests/test_updated_profile.py`, `test_data_entry.py`, `test_guided_flow.py` (novos) | Regressões desta revisão |
| `tests/test_ui.py`, `test_browser.py`, `test_profile_scales.py`, `test_pipeline.py` | Manter regressões existentes e atualizar o fluxo visível |
| `docs/methods.md`, `docs/acceptance.md`, `README.md` | Regras de uma única configuração do estudo e uso simples |
| `.streamlit/config.toml`, `cloud/.streamlit/config.toml`, `ui/pages.py` e `tests/test_ui.py` | Temas claro/escuro geral e escolha visível sem perder dados |

Executar nativamente por padrão; usar agente apenas numa revisão independente que justifique o custo. Preservar alterações locais alheias, especialmente `scripts/start_hamachi.ps1`; esta revisão não modifica esse script.

## Tarefa 1: Incorporar o banco atualizado como modelo reconhecido

**Files:** criar YAML novo e `tests/test_updated_profile.py`; modificar `profiles.py`, `models.py`, `validation.py`, `importers.py` e `tests/test_importers.py`.

**Interfaces:** consumir `ResearchProfile`, `ImportedDataset`, `PreparedDataset` existentes. Produzir `recognize_format(sheet_names: tuple[str, ...], headers: tuple[str, ...]) -> str`, retornando `updated_v1`, `legacy_v1` ou `unknown`; `normalize_columns(df: pd.DataFrame, aliases: dict[str,str]) -> tuple[pd.DataFrame, tuple[Transformation,...]]`. Acrescentar ao perfil campos explícitos `input_fields`, `derived_fields` e `instrument_mode`, com padrões para manter o perfil antigo compatível.

**Metadados do upload:** `recognize_format` identifica apenas um formato candidato. O importador também lê Categorias/Perguntas/AVISO ou Metadados e associa os conteúdos às colunas por chave. Reutilizar `ImportedDataset` para transportar dicionário, perguntas e origem por aba/célula, com defaults compatíveis para CSV e legado. Comparar o conteúdo importado ao perfil antes de usá-lo, conforme o complemento da especificação. Não basta reconhecer os 69 cabeçalhos. Divergências ficam na sessão e não substituem globalmente o perfil.

**Testes adicionais obrigatórios:** planilha de duas participantes construída em memória, colunas reordenadas e alias conhecido devem preservar o vínculo pergunta/código; inverter 1/2 mantendo os cabeçalhos deve produzir conflito explícito; metadados duplicados, código sem legenda e duas abas candidatas devem ter pendências localizadas; modelo conhecido sem metadados informa uso do perfil; arquivo coerente não solicita referência manual. Cobrir XLSX exportado pelo cadastro com a mesma leitura, sem dados reais no teste.

- [x] **1. Escrever testes.** `test_updated_layout_has_69_inputs` exige 69 entradas e as mesmas chaves em perguntas/categorias; `test_known_aliases_are_reversible` exige DOENÇA/TO/NÃO_RESP → DOENCA/TER_OCUP/NAO_RESP com trilha; `test_alias_collision_blocks` exige erro se DOENÇA e DOENCA coexistirem; `test_known_labels_need_no_user_reference` exige RED_APO 1=Sim/2=Não sem `mapping_pending`; `test_unknown_codes_are_not_guessed` exige pendência focal e valor preservado. Usar microbases artificiais nos testes; não copiar o banco enviado para o Git.
- [x] **2. Confirmar vermelho.** `python -m pytest tests/test_updated_profile.py tests/test_importers.py -v`; APIs novas ausentes e casos de metadados ainda não atendidos.
- [x] **3. Implementar o perfil e o reconhecimento.** Extrair somente definições de Categorias/Perguntas, preservar fonte e versão no YAML. Não converter agrupamentos de renda/escolaridade em categorias detalhadas do projeto. Modelo reconhecido usa o dicionário versionado; formato divergente não recebe significado inventado. Separar ausência de entrada obrigatória, resposta faltante e saída derivada ainda não calculada.
- [x] **4. Confirmar verde.** Mesmo comando; o arquivo atualizado pode ser preparado como respostas, sem exigir seis colunas derivadas ausentes. Perfil antigo continua aceito.
- [ ] **5. Commit.** Adicionar somente perfil, importador, modelos, validação e testes desta tarefa; `git commit -m "feat: recognize documented updated TCC data format"`.

## Tarefa 2: Preparar automaticamente horários e escores disponíveis

**Files:** modificar `scales.py`, `models.py`, `validation.py`, `pipeline.py`, `reporting.py`; testes `test_profile_scales.py` e `test_updated_profile.py`; documentar em `docs/methods.md`. Declarar `PreparedInstruments` em `models.py`.

**Interfaces:** `clock_to_decimal(value: datetime.time | str | float) -> float` aceita hora nativa, texto hh:mm e decimal legado; `prepare_instruments(data: pd.DataFrame, profile: ResearchProfile) -> PreparedInstruments`, com `data`, `issues`, `available_outcomes` e `score_provenance`. Não sobrescrever totais fornecidos; derivados e divergências continuam separados.

**Pesquisa já realizada:** partir dos materiais oficiais da Universidade de Pittsburgh e das referências NLM/NINDS vinculadas no complemento da especificação; conferir conteúdo e correspondência com Anexo I, não pedir que a usuária procure manual. Fontes foram localizadas; pontuação do app continua não validada até testar componentes e fronteiras. Manter referências/versão localmente, sem consultas externas na importação ou envio de dados.

- [x] **1. Escrever testes.** Assertar `clock_to_decimal(time(23,30)) == 23.5`, `clock_to_decimal('00:15') == .25` e preservação de `23.5`; rejeitar `25:00`. `test_zarit_generated_from_22_answers` exige soma e faixa, item ausente exige total ausente. `test_missing_derived_columns_are_not_input_errors` aceita os 69 campos. `test_psqi_unavailable_disables_only_sleep_comparisons` exige razão explícita, sem escore inventado. `test_recorded_and_recalculated_scores_both_preserved` exige ambos os valores e aviso.
- [x] **2. Confirmar vermelho.** `python -m pytest tests/test_profile_scales.py tests/test_updated_profile.py -v`; novos comportamentos falham.
- [x] **3. Definir a pontuação PSQI no contexto técnico do estudo.** Obter o manual correspondente à versão do Anexo I, registrar os sete componentes, intervalos sem sobreposição e vetores independentes nos limites. O Excel esclarece opções e perguntas, mas não basta para confirmar o algoritmo. Esta é uma dependência científica única, não um campo “referência da conferência” para a usuária preencher a cada sessão. Enquanto faltar essa definição, entrada/cadastro/exportação e Zarit funcionam; explicar por que as comparações que precisam de PSQI não estão disponíveis. Nunca apresentar esse estado como análise de sono concluída.
- [x] **4. Implementar conversões e preparação.** Converter horários em cópia com auditoria, unidades de TEMP_TEA em meses e IDADE_C em anos; calcular Zarit com os itens completos; calcular PSQI somente com a regra definida no passo anterior e testes independentes. Não criar ESCOL_B/RENDA_B/FREQ_3 sem regra explícita; não são necessários à análise padrão. Pontuação não depende da existência das colunas antigas.
- [x] **5. Confirmar verde.** Rodar o comando do passo 2. Havendo regra PSQI aprovada, vetores de 0/5/6/21 e limites de cada componente devem passar. Sem a regra, registrar o gate pendente, com bloqueio focal verificado; não marcar recálculo como validado.
- [ ] **6. Commit.** `git add src/tcc_analyzer/scales.py src/tcc_analyzer/models.py src/tcc_analyzer/validation.py src/tcc_analyzer/pipeline.py src/tcc_analyzer/reporting.py tests docs/methods.md`; `git commit -m "feat: prepare available instrument scores from questionnaire responses"`.

## Tarefa 3: Configurar categorias, preencher pelo assistente e exportar Excel pronto

**Files:** criar `data_entry.py`, `ui/create_sheet.py`, `tests/test_data_entry.py`; modificar `ui/state.py`, `ui/pages.py`, `exports.py`, `jobs.py`, `profiles.py`, `models.py` e `reporting.py`.

**Interfaces:** `new_participant(existing_ids: tuple[int,...]) -> dict[str,object]` gera ID sem preencher respostas; `encode_answers(answers: dict, profile: ResearchProfile) -> dict` usa o perfil efetivo da sessão; `build_input_workbook(rows: tuple[dict,...], profile: ResearchProfile, *, fictitious: bool) -> bytes` retorna XLSX preenchido com Banco, Categorias, Perguntas e Metadados. Artefato privado: chave `input_workbook`, nome fixo `banco_preenchido.xlsx`. Estado acrescenta `draft_profile`, `effective_profile`, `draft_participant`, `participants`, `draft_question`, `editing_id`; nenhum cadastro global. O perfil da sessão preserva chave estável e significado canônico de respostas dos instrumentos, separados dos códigos exibidos. Nome/apelido opcional é identificação, nunca variável analítica ou texto de relatório.

- [x] **1. Escrever testes.** Categorias aparecem antes da primeira pergunta; começar com padrão dispensa edições. Personalizar código e significado, salvar/cancelar/restaurar deve atualizar formulário e arquivo, sem alterar outra sessão. Rejeitar código duplicado e opção usada removida sem resolução. Trocar 1↔2 após respostas exige remapeamento simultâneo auditado e reversível; renumerar item de instrumento preserva seu valor canônico. Novo registro tem apenas ID, demais respostas ausentes; “não informado” não vira zero. Testar uma pergunta por vez, salvar duas participantes, editar sem duplicar e voltar preservando respostas. `test_created_workbook_round_trip` exige mesmas respostas, identificação opcional, perfil e categorias após exportar/importar; testar formatação/listas no XLSX. Nome não aparece em relatório nem como variável analítica. Impedir aviso fictício num banco real e verificar isolamento de rascunhos.
- [x] **2. Confirmar vermelho.** `python -m pytest tests/test_data_entry.py -v`.
- [x] **3. Implementar configuração e assistente.** Primeiro, resumo das categorias padrão e ação “Começar preenchimento”. Personalização recolhida: selecionar uma pergunta e editar somente tabela Código/Significado; salvar/cancelar/restaurar. Depois, ID automático e nome/apelido opcional; perguntas individuais agrupadas em mãe (12), criança (15), sono (19) e Zarit (22), com progresso, Voltar/Próxima e resumo final. Usar escolhas textuais e campos numéricos/hora adequados; não pedir códigos nem reescrever instrumentos. Rascunhos preservam respostas ausentes sem gerar escore falso. Gerar XLSX preenchido, com formatação, filtros, congelamento, perguntas/categorias personalizadas e listas de validação. Reutilizar openpyxl; não entregar modelo vazio como resultado desse fluxo.
- [x] **4. Integrar ao trabalho privado.** Ações “Adicionar participante”, “Editar”, “Excluir”, “Concluir planilha”, “Baixar planilha preenchida” e “Usar na análise”. Download/reimportação e uso direto entram pelo mesmo importador/pipeline, com hash da entrada e metadados de origem. Disponibilizar o mesmo editor de categorias após a importação; mudanças que afetem respostas têm confirmação, remapeamento, auditoria e desfazer, invalidando resultados anteriores. Download privado com chave fixa e verificação de dono/expiração, sem reutilizar a exportação Epi Info que remove texto livre e redefine IDs. Incluir chave na allowlist de jobs; testar acesso cruzado negado. Não registrar nome/apelido em logs ou relatórios científicos.
- [x] **5. Confirmar verde.** Mesmo comando e `python -m pytest tests/test_sessions.py tests/test_importers.py -q`; upload/download continuam limitados e o cadastro é volátil por sessão, com aviso para baixar antes de sair.
- [ ] **6. Commit.** Adicionar somente arquivos e testes desta tarefa; `git commit -m "feat: create filled workbooks with editable categories and guided entry"`.

## Tarefa 4: Transformar validação em conferência contextual

**Files:** modificar `ui/pages.py`, `validation.py`, `ui/state.py`; criar `tests/test_guided_flow.py` e atualizar `tests/test_ui.py`.

**Interfaces:** `summarize_validation(report: ValidationReport) -> dict` retorna `blocking`, `warnings`, `ready_message`; `render_validation(state, manager)` mantém assinatura. A confirmação de correção usa `Transformation` e `apply_changes` existentes; auditoria é automática, motivo manual fica opcional/avançado e recebe justificativa padronizada quando omitido.

**Conteúdo e aparência:** seguir direção visual do complemento da especificação. Resumo mostra participantes, blocos reconhecidos, documentação encontrada e análises disponíveis. “Como interpretamos sua planilha” revela definições e origens, sem exigir interação. Perguntar somente pelos casos da matriz da especificação; agrupar pendências por campo e mostrar linhas afetadas. Não solicitar confirmação global para compensar falha do parser. Validar em navegador que arquivo documentado e coerente chega à análise sem editar nenhuma categoria, inclusive sem acesso de saída à web.

- [x] **1. Escrever testes.** Banco válido: botão “Continuar para análise” habilitado sem preencher formulário, referência, legenda ou motivo. Erro PSQI/horário: mensagem inclui participante/pergunta e próxima ação. Dicionário recolhido. Correção contextual só aparece ao escolher “Corrigir”; cancelar preserva entrada e confirmar permite desfazer. Entrada desconhecida mostra apenas o problema necessário para reconhecê-la.
- [x] **2. Confirmar vermelho.** `python -m pytest tests/test_guided_flow.py tests/test_ui.py -v`.
- [x] **3. Implementar apresentação.** Mostrar quantidade de participantes e “Dados conferidos. Você pode continuar.” quando não há bloqueio. O formulário genérico de correção e o editor completo do dicionário saem do caminho comum; acesso em “Opções avançadas”. Não exigir nenhuma alteração de um banco válido. “Referência da conferência” deixa de ser um requisito do fluxo reconhecido. Preservar erros de instrumento, fonte original e trilha, sem afrouxar intervalos.
- [x] **4. Confirmar verde.** Mesmo comando; assertar que mudanças no banco invalidam os resultados e não reutilizam aprovação do relatório anterior.
- [ ] **5. Commit.** `git add src/tcc_analyzer/ui src/tcc_analyzer/validation.py tests`; `git commit -m "fix: require attention only for actual data problems"`.

## Tarefa 5: Analisar por perguntas e provar o fluxo inteiro

**Files:** criar `analysis_plan.py`; modificar `ui/pages.py`, `pipeline.py`, `statistics/selection.py`, `reporting.py`, `tests/test_browser.py`, `tests/test_pipeline.py`; atualizar `README.md`, `docs/acceptance.md`.

**Interfaces:** `build_default_plan(data: pd.DataFrame, profile: ResearchProfile, selected_questions: tuple[str,...]) -> tuple[ComparisonSpec,...]`; `question_catalog(profile: ResearchProfile) -> dict[str,str]` liga IDs estáveis a textos humanos. Usar recommend_test/freeze_comparisons/analyze_pair existentes; não duplicar cálculos em UI.

- [x] **1. Escrever testes.** “Sobrecarga e qualidade do sono” produz as duas comparações principais e a complementar contínua existentes quando disponíveis; “Rede de apoio e sono” produz apenas a comparação correspondente. Categoria esparsa resulta em descrição/aviso; variável ausente desabilita só sua pergunta. O fluxo comum executa sem método, justificativa ou checkbox de pressupostos. Metadados continuam guardando método, n, pressupostos e motivo da recomendação. Nenhum método é escolhido pelo p observado.
- [x] **2. Confirmar vermelho.** `python -m pytest tests/test_guided_flow.py tests/test_pipeline.py -v`.
- [x] **3. Implementar análise simples.** Pergunta principal pré-selecionada, outras opções com nomes completos e botão “Analisar dados”. Regras do estudo e diagnósticos dirigem métodos; casos não sustentados são descritos com aviso. Seletores de método/RP/OR/variáveis e justificativas permanecem opcionais em área avançada, sem exigir conhecimento técnico para o plano padrão. Resultados mostram pergunta, explicação curta, n e estimativas; detalhes científicos e limitações continuam disponíveis.
- [x] **4. Verificar no navegador com duas sessões.** Cenários reais: importar banco atualizado → nenhuma confirmação repetitiva → análise disponível → baixar; ver categorias → manter/editar padrão → começar → responder uma pergunta por vez → salvar participantes → concluir → baixar Excel preenchido/reimportar → mesmos valores e categorias. Testar nome/apelido opcional, voltar sem perda e edição posterior com impacto explícito. Arquivo sem pendências não exige formulários; mudança após análise invalida relatório antigo. Testar 360 px, teclado e foco. Comparar análises equivalentes com o motor anterior; aparência não pode mudar fórmulas silenciosamente.
- [ ] **5. Rodar aceite final e documentar.** `python -m pytest -q`, `python -m compileall -q src app.py cloud/app.py`, `python -m pip check`; CI Windows/Linux passa, com somente os testes Windows exclusivos desabilitados em Linux. Registrar status da regra PSQI e reconciliação metodológica sem alegar aprovação inexistente. Nenhuma busca bibliográfica ou alteração de rede entra nesta entrega.
- [ ] **6. Commit.** `git add src tests README.md docs`; `git commit -m "feat: offer automatic research questions with a guided end-to-end flow"`.

## Tarefa 6: Adicionar modo claro e escuro em todo o aplicativo

**Files:** modificar `.streamlit/config.toml`, `cloud/.streamlit/config.toml`, `src/tcc_analyzer/ui/pages.py`, `ui/state.py`, `tests/test_ui.py`, `tests/test_browser.py` e `docs/acceptance.md`. Reutilizar a entrada comum das versões local e cloud.

- [x] **1. Conferir suporte e escrever testes.** Conferir versão instalada do Streamlit; consultar API oficial via context7 somente para definir a escolha de tema suportada, sem dados da pesquisa. Cobrir alternância Claro/Escuro/Sistema em todas as etapas mantendo upload, perfil editado, rascunho e resultados. Tema de uma sessão não muda o de outra. Não usar configuração global mutável para preferência individual.
- [x] **2. Confirmar vermelho.** `python -m pytest tests/test_ui.py -v`; registrar cenário de navegador que demonstra ausência atual de escolha visível do tema.
- [x] **3. Implementar tema geral.** Preferir mecanismo nativo suportado e controle visível compacto. Usar tokens da especificação em texto, superfícies, tabelas, alertas, controles e gráficos. Não usar inversão de cor nem CSS baseado em seletores internos frágeis. Caso o seletor nativo fique oculto no modo de toolbar atual, garantir acesso claro à escolha usando recursos suportados. Exportações continuam com estilo próprio de leitura/impressão.
- [x] **4. Verificar nos dois temas.** Navegador desktop e 360 px: editar categoria, navegar pelo assistente, importar, conferir, analisar e baixar; foco e contraste de texto/controles, mensagens e gráficos. Trocar tema no meio do preenchimento deve preservar todas as respostas. Repetir suíte completa apenas após esta mudança final; registrar evidências em docs/acceptance.md.
- [ ] **5. Commit.** Adicionar somente configuração, UI, testes e aceite desta tarefa; `git commit -m "feat: support light and dark themes throughout the app"`.

## Registro da execução

Implementação integrada em 2026-11-04. Testes focados partiram de falhas demonstradas; suíte completa: 134 testes passaram em 57,93 s, incluindo navegador real. Compilação e dependências conferidas. Regras dos instrumentos e limites documentadas em methods.md. Revisão de código tratou escores após edição, proveniência fictícia e estado ao reimportar. Tema usa o seletor nativo da versão instalada, diretamente no menu ⋮ (Light/Dark/System). Evidências e limites de implantação em docs/acceptance.md. Commits/publicação e CI remota não foram executados nesta etapa.

## Revisão do plano e entrega

Cobertura conferida: importar/criar em 1/3; categorias antes do preenchimento, edição posterior de código/significado e Excel preenchido em 3; uso dos documentos em 1/2; escores/horários em 2; conferência simples em 4; análise por perguntas em 5; claro/escuro geral em 6. Os seis focos têm testes atribuídos. Nenhum registro do novo banco foi copiado para o repositório. A revisão foi implementada e validada localmente; publicação e CI remota não foram executadas. Manter execução nativa como preferência já estabelecida.
