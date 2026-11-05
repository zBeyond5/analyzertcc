# Update de cobertura AV3 e interpretação de resultados Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Cobrir fatores bivariados do AV3 e explicar significância de 5% sem exigir conhecimento estatístico da usuária.

**Architecture:** Reutilizar catálogo, validação, escores, pipeline e relatórios. Acrescentar uma função pura de interpretação e uma seleção explícita de população analítica; UI e arquivos usam os mesmos resultados e linhas. Sem alterar fórmulas estatísticas nem introduzir serviços.

**Tech Stack:** Python 3.12, Streamlit 1.66.1, pandas, SciPy, Plotly, pytest/Playwright existentes; ponytail e frontend-design. Context7 somente para API em dúvida, sem dados da pesquisa.

**Spec:** `docs/superpowers/specs/2026-11-04-av3-analysis-update.md`; auditoria `docs/2026-11-04-av3-coverage.md`; fonte `fontes/PROJETO TCC - AV3 FINAL.docx`, seções 7.2/7.5/7.6/7.7.

## Global Constraints

- Interface e relatórios em português brasileiro.
- Significância definida por p < 0,05; comparar o valor numérico original, nunca o texto arredondado.
- Sem IA, buscas web ou envio de respostas a serviços externos durante o uso.
- Não escolher testes ou variáveis pelo menor p nem ocultar resultados não significativos.
- Preservar entrada original, auditoria, desfazer, isolamento por sessão e downloads privados.
- Sem regressão múltipla, backend adicional, reconstrução de categorias perdidas ou imputação de respostas.

## Review Focus

1. p na fronteira 0,05 ou arredondado: classificação estrita e apresentação sem contradição — tarefa 1.
2. p ausente/inválido e dados fictícios: sem alegação científica nem significância inventada — tarefas 1/4.
3. Alterar seleção de fatores: sem testes duplicados, seleção por p ou resultados antigos disponíveis — tarefa 2.
4. Questionário incompleto versus campo auxiliar vazio: nenhuma exclusão indevida ou perda do original; mesma população em figuras/arquivos — tarefa 3.
5. Perfil legado, recalculado e categorias personalizadas: origem correta, sem nota contraditória ou equivalência inventada — tarefa 4.

---

## Mapa de arquivos

- Criar `src/tcc_analyzer/interpretation.py`: p, limiar e explicações compartilhadas.
- Modificar `analysis_plan.py`, `ui/pages.py`: catálogo agrupado, execução/resultado simples.
- Criar `analysis_population.py`: critérios observáveis em cópia e motivos de exclusão.
- Modificar `pipeline.py`, `models.py`, `ui/state.py`, `ui/charts.py`: população única, metadados e invalidação.
- Modificar `reporting.py`, `profiles.py`: notas de origem/categorias e interpretação coerente.
- Testes novos `test_interpretation.py`, `test_analysis_plan.py`, `test_analysis_population.py`; ampliar `test_pipeline.py`, `test_exports_reports.py`, `test_guided_flow.py`, `test_browser.py`.
- Documentar em `docs/methods.md`, `docs/acceptance.md` e README. Não editar fontes nem copiar participantes para testes.

## Tarefa 1 — Interpretar p sem confundir com desvio padrão

**Interfaces:** `ALPHA = 0.05`; `interpret_p(p_value: float | None, *, p_kind: str) -> dict[str,str]`, chaves `status`, `p_display`, `explanation`. Status: `significant`, `not_significant`, `unavailable`. Somente p finito entre 0 e 1 com p_kind diferente de not_computed permite comparação. `format_p` existente delega a apresentação compartilhada sem alterar os números guardados.

- [x] **1. Escrever testes de fronteira e indisponibilidade.**

```python
assert interpret_p(.04996, p_kind='exact')['status'] == 'significant'
assert interpret_p(.05, p_kind='exact')['status'] == 'not_significant'
assert interpret_p(.05004, p_kind='exact')['status'] == 'not_significant'
assert interpret_p(None, p_kind='not_computed')['status'] == 'unavailable'
assert interpret_p(float('nan'), p_kind='exact')['status'] == 'unavailable'
assert interpret_p(0, p_kind='not_computed')['status'] == 'unavailable'
```

Também testar -1, 1.1, infinito, p=0 válido, p=1, apresentação distinta em .04996/.05004, explicações da spec e nenhuma afirmação de ausência/causalidade. Desvio padrão baixo/alto não é entrada dessa função.
- [x] **2. Demonstrar falha:** `python -m pytest tests/test_interpretation.py -v`; falha pela função ausente.
- [x] **3. Implementar em interpretation.py**, com textos exatos da spec; adaptar `reporting.format_p` para precisão adicional só quando arredondamento mascara fronteira, preservando `<0,001`. Não converter inválido em zero.
- [x] **4. Verificar:** mesmo comando e `python -m pytest tests/test_exports_reports.py -q`; verde, sem regressão de formatação.
- [x] **5. Commit:** somente módulo, reporting e testes desta tarefa; `feat: explain significance using the study threshold`.

## Tarefa 2 — Ampliar perguntas sem ampliar a complexidade da tela

**Interfaces:** manter `build_default_plan(data, profile, selected_questions=('burden',))`; adicionar `question_groups(profile) -> dict[str,dict[str,str]]`, grupos `principal`, `mae`, `crianca`. Catálogo de campos exato na spec. Preservar IDs `burden`, `support`, `child_sleep`; novos `factor_<CAMPO>`. Todas as opções adicionais usam `ComparisonSpec(id,'PSQI_G',field,'exploratory','auto',justificativa)`; sem duplicações.

- [x] **1. Escrever testes:**

```python
plan = build_default_plan(data, profile, ('burden','factor_IDADE_M','support'))
assert len(plan) == 5  # três existentes + idade + apoio
assert len({c.id for c in plan}) == len(plan)
assert any(c.predictor == 'IDADE_M' and c.family == 'exploratory' for c in plan)
assert all(c.predictor not in ('QUA_SONO','N_MIN') for c in plan)
```

Usar microbase artificial completa. Testar campo ausente/todo ausente, mesmas opções com p diferentes não mudam seleção, `support` não duplicado, padrão só burden e alteração invalida arquivos.
- [x] **2. Demonstrar falha:** `python -m pytest tests/test_analysis_plan.py tests/test_guided_flow.py -v`.
- [x] **3. Implementar catálogo/agrupamentos** em analysis_plan.py e seletores recolhidos mãe/criança em pages.py. Preservar métodos principais atuais; extras seguem recommend_test. Indicar apenas perguntas disponíveis, sem menus técnicos, seleção automática por significância ou testes de normalidade como chave seletora.
- [x] **4. Verificar:** comando anterior e `python -m pytest tests/test_statistics.py -q`; números/métodos existentes preservados.
- [x] **5. Commit:** catálogo, UI e testes focados; `feat: expose the AV3 maternal and child factors`.

## Tarefa 3 — Delimitar população do perfil atualizado sem destruir dados

**Interfaces:** `select_population(data: pd.DataFrame, profile: ResearchProfile) -> AnalysisPopulation`, dataclass em models.py com `data`, `included_rows: tuple[int,...]`, `excluded: tuple[dict,...]`, `policy: str`. Motivos permitidos: `age_missing`, `age_below_18`, `psqi_incomplete`, `zarit_incomplete`. Erros semânticos/de código são bloqueios existentes, não motivos de exclusão. Perfil legado retorna cópia e política explícita `legacy_complete_pairs`; atualizado `av3_observable_v1`.

**Integração:** WorkflowState recebe `population_ack_signature: str | None`. Assinatura inclui fonte, dados preparados, versão do perfil e seleção de linhas; muda com qualquer correção/categoria e não pode ser aprovação global. RunOptions recebe `population_policy` e `population_ack_signature`, defaults compatíveis para legado. Pipeline recalcula a seleção e verifica confirmação somente quando há excluídos no perfil atualizado. Não confiar num N enviado pela UI.

- [x] **1. Escrever testes:**

```python
selection = select_population(data, profile)
assert selection.included_rows == (0,)
assert len(selection.excluded) == 2  # menor de idade e Zarit incompleto
assert len(data) == 3
assert data.equals(original)
```

Microbase com todos os itens, 18 anos incluído, 17 excluído, idade faltante, item PSQI/Zarit vazio; OCUP vazio não exclui. Totais não fornecidos mas itens completos incluem. Configuração incompatível bloqueia sem excluir tudo. Testar zero elegíveis, legado inalterado, confirmação obsoleta negada, correção/desfazer, arquivo fictício e mesma seleção nas tabelas/figuras/exportações.
- [x] **2. Demonstrar falha:** `python -m pytest tests/test_analysis_population.py tests/test_pipeline.py -v`.
- [x] **3. Implementar seleção** em analysis_population.py e integração em pipeline/pages/state. Fonte e Excel preenchido preservados. UI mostra N e motivos agrupados; havendo exclusões, botão contextual confirma população reduzida. Tabelas/estatísticas/CSV de resultados usam selection.data; plots usam a mesma seleção recalculada e verificada. Metadados distinguem n da fonte/n analisado/motivos sem nomes. Bloqueios de validação relevantes permanecem antes da execução. Ausentes nos demais fatores continuam por pares completos.
- [x] **4. Verificar:** comando anterior e `python -m pytest tests/test_sessions.py tests/test_charts.py tests/test_data_entry.py -q`.
- [x] **5. Commit:** arquivos/testes da tarefa; `feat: apply observable AV3 eligibility without modifying source data`.

## Tarefa 4 — Mostrar a mesma conclusão na tela e nos arquivos

**Interfaces:** manter `build_tables(results,summaries,profile,*,data=None)`; consumir `interpret_p` em cada AnalysisResult. `run_pipeline` grava `alpha=.05`, `interpretation_version='av3-p-v1'`, origem por instrumento e população. `profiles.py` registra diferenças de categorias por versão/origem já conhecida, sem nova confirmação de importação. Não presumir perfil AV3 detalhado para um arquivo agrupado.

- [x] **1. Escrever testes:**

```python
assert '0,05' in ' '.join(tables.notes)
assert 'Significativa pelo critério de 5%' in ' '.join(tables.narrative)
assert 'recálculo dos componentes pendente' not in ' '.join(updated_tables.notes)
assert all(c.spec.id in manifest_ids for c in selected_results)
```

Preparar resultados artificiais significante, não significante e descritivo; verificar nenhum omitido. p=0,04996 tem mesma classificação/display na UI, DOCX, PDF e tabelas XLSX; p ausente não ganha frase significativa. Origem calculada/informada/mista descreve o que ocorreu por instrumento, não só perfil. Texto fictício continua visível. Ausência de nomes em manifesto/figura. Registrar divergências renda/escolaridade/estado civil, limitação de elegibilidade e múltiplos testes sem ajuste.
- [x] **2. Demonstrar falha:** `python -m pytest tests/test_interpretation.py tests/test_exports_reports.py tests/test_pipeline.py -v`.
- [x] **3. Implementar apresentação** em reporting/pages/pipeline/profiles: estado de significância junto do p, estimativa/IC/método/n; ajuda recolhida distingue DP e p. Um bloco por comparação, sem “variável relevante”, ranqueamento por p ou discussão bibliográfica automática. Corrigir nota fixa antiga. Usar alerta neutro/texto em vez de depender apenas de cores. Atualizar methods.md com a decisão efetiva dos testes e o desvio metodológico que ainda exige aceite científico único.
- [x] **4. Verificar** comando anterior; extrair texto DOCX/PDF e ler XLSX gerado para confirmar consistência. Não é necessário renderizar novos gráficos estáticos.
- [x] **5. Commit:** arquivos/testes/documentação desta tarefa; `feat: report consistent AV3 interpretations and score provenance`.

## Tarefa 5 — Aceite completo sem novas perguntas técnicas

**Files:** `tests/test_browser.py`, `tests/test_guided_flow.py`, README e `docs/acceptance.md`.

- [x] **1. Escrever regressões de percurso:** fixture artificial com p conhecido abaixo/acima de 0,05 e cenário sem inferência. Assertar estado/texto/p coerentes, extras recolhidos, exclusão contextual somente quando necessária e ausência de referência/checkbox de pressupostos. Preservar testes de duas sessões e invalidação.
- [x] **2. Demonstrar falha** dos novos casos antes de ajustar integração; `python -m pytest tests/test_guided_flow.py tests/test_browser.py -v`.
- [x] **3. Concluir integração mínima** e testar desktop/360 px, claro/escuro, teclado, retorno e download. Mostrar pergunta sono/sobrecarga e três comparações distintas, sem fundir seus p. Planilha fictícia deve ser demonstração em todos os formatos.
- [x] **4. Verificar suíte final:** `python -m pytest -q`, `python -m compileall -q src app.py cloud/app.py`, `python -m pip check`. Registrar separadamente testes, aceite científico e Windows/Hamachi/Epi Info. Somente os testes atuais não equivalem a nova aprovação científica.
- [x] **5. Commit e preview:** registrar docs e testes; mostrar preview antes de publicação. Commit/push e publicação dependem da autorização de execução dessa atualização; não repetir checks verdes sem mudança/motivo.

## Revisão e entrega do plano

Revisão própria concluída: cobertura das lacunas da auditoria nas tarefas 2/3/4; interpretação solicitada na 1/4; todas as cinco classes de risco possuem testes atribuídos. A população reduzida precisa ser a mesma na UI/pipeline/gráficos/arquivos. Regra estrita de p e textos definidos uma única vez. O plano não acrescenta regressão nem coleta ética digital. Preferência preservada: execução nativa; agentes apenas quando uma revisão independente economizar tempo. A implementação ainda não foi iniciada.


## Execução — 2026-11-05

Concluída nativamente com revisão independente final. 166 testes passaram em93,36s; compileall/pip check verdes. Commits das tarefas agrupados na integração por dependências UI/pipeline; sem push/publicação nesta execução. Revisão tratou população do método explicativo, origem efetiva no manifesto, instrumento incompleto com total fornecido e p imediatamente vizinho de0,05. Todas as correções têm regressão. Preview local aberto.

Decisão de execução: preservado branch de trabalho existente e script Hamachi alheio. Critérios não observáveis e aceite científico não foram inventados; risco residual é alinhamento metodológico humano, documentado em methods.md. Nenhuma funcionalidade da coleta/ética/regressão entrou neste update.
