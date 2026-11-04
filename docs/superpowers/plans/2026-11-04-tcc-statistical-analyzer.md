# TCC Statistical Analyzer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir um analisador bivariado privado em Python/Streamlit para o TCC, com instrumentos verificáveis, resultados reproduzíveis, relatórios acadêmicos e exportação para Epi Info, hospedado em Windows 11 e acessado por Hamachi.

**Architecture:** Núcleo Python independente da interface, acompanhado do perfil versionado `tea_maternal_sleep_v1`. Cada sessão mantém seu próprio estado e uma execução privada em `runtime/jobs/<random_job_id>/`; uma camada de orquestração liga importação, validação, análise, revisão e exportação. O servidor executa um único processo Streamlit, limita análises pesadas e remove trabalhos expirados sem publicar diretórios de arquivos.

**Tech Stack:** Python 3.12; Streamlit, pandas, NumPy, SciPy, statsmodels, openpyxl, PyYAML, python-docx, Matplotlib e pytest. Extra `xls` com xlrd; extra de desenvolvimento com Playwright e Pester 5 para Windows. PDF por LibreOffice local quando disponível; versões exatas e hashes fixados após instalação e testes em Windows 11, sem assumir compatibilidade da versão mais recente.

**Spec:** [Especificação fornecida](../specs/2026-11-04-tcc-statistical-analyzer-design.md), acompanhada da [conferência das fontes e das 75 colunas](../specs/2026-11-04-source-review.md). O segundo texto anexado é o plano preliminar que este documento detalha e corrige. Ler ambos os documentos locais antes de executar.

## Global Constraints

As linhas entre aspas são requisitos copiados da especificação; as decisões operacionais posteriores não alteram esses requisitos.

- “Interface e análises em português brasileiro.”
- “A arquitetura escolhida é núcleo estatístico reutilizável + perfil específico do TCC.”
- “Os arquivos devem ser copiados para fixtures/source/ pelo implementador, se disponíveis, e mantidos inalterados. Não versionar dados reais identificáveis.”
- “Preservar nomes e dados originais; normalizações e recodificações devem ser reversíveis e rastreáveis.”
- “Confirmar a versão/pontuação do instrumento do projeto antes de codificar detalhes.”
- “Não escolher teste somente por teste de normalidade.”
- “Não corrigir zero ou calcular IC inválido silenciosamente.”
- “Não incluir regressão multivariável no MVP.”
- “Processar localmente no servidor, sem serviços de IA remotos ou internet pública.”
- “Clientes ingressam na rede virtual Hamachi e acessam o endereço IP Hamachi do servidor; não haverá login adicional na aplicação.”
- “Upload permitido apenas .xlsx, .xls (se suportado) e .csv, com limite configurável inicial de 20 MiB por arquivo, limites de linhas/colunas e verificação real de estrutura/conteúdo, não apenas extensão.”
- “Uma análise por execução, com fila/limite de concorrência configurável (proposta inicial: duas análises pesadas simultâneas), indicação de progresso e erros sem vazamento de caminhos internos ou conteúdo de outros usuários.”
- “Usar exclusão por expiração (proposta: 60 minutos após geração, com limpeza periódica), limpeza em encerramento quando possível e recuperação após reinício para remover órfãos.”
- “Manter proteção XSRF habilitada; não desligar segurança do Streamlit para resolver conexões.”
- “Não configurar port forwarding, túneis públicos ou publicação em nuvem.”
- “CSV com codificação compatível e instruções sobre delimitador; testar a importação real no Epi Info em Windows antes de declarar compatibilidade comprovada.”
- “Dados fictícios são adequados para testes funcionais, não para conclusões do TCC.”

## Review Focus

1. Upload pequeno que se expande excessivamente, cabeçalho duplicado ou ID `001` em CSV: rejeitar conteúdo abusivo e preservar valores originais; testes na Tarefa 1.
2. Categorias sem legenda, renda/escolaridade divergentes e edição parcial: bloquear interpretações não confirmadas e permitir desfazer a alteração; testes na Tarefa 2.
3. Horas decimais cruzando meia-noite, horas de sono impossíveis e respostas parciais: não produzir escore aparentemente válido; testes na Tarefa 3.
4. Zero em 2×2, ausência de grupo, empates e variável constante: devolver método e advertência sem p ou IC artificial; testes nas Tarefas 5 e 6.
5. Segundo navegador com identificador/URL alheio, reinício e expiração durante processamento: não entregar dados de outro trabalho nem apagar trabalho ativo; testes nas Tarefas 9 e 10.

---

## Estado inicial, escopo e decisões

Em 2026-11-04 a pasta contém apenas `fontes/` com os três documentos, sem aplicação ou repositório Git. O XLSX foi conferido: 30×75, zero vazios, IDs distintos, Zarit somado corretamente em 30/30, `PSQI_G` coerente em 30/30 (4 boas/26 más), idade materna média 37,4 e faixas Zarit 2/8/16/4. Os hashes e a ordem exata dos campos estão no documento de conferência. Não foi recalculado o PSQI a partir das respostas.

O núcleo e a hospedagem atendem a um único fluxo de pesquisa; este plano mantém um MVP integrado e divide o motor estatístico em tarefas separadas que podem ser rejeitadas ou aprovadas individualmente. Aplicar na própria raiz atual, sem criar outra pasta `tcc-statistical-analyzer/` dentro dela. Não implementar código ao entregar este plano.

**Dependências científicas, antes das partes afetadas das Tarefas 2 e 3:** obter da responsável a legenda numérica das 75 variáveis e derivados, a reconciliação de renda/escolaridade e a versão/manual de pontuação PSQI. A AV3 contém as perguntas, mas não resolve essas codificações nem o algoritmo completo. Registrar a confirmação em `docs/methods.md` e no perfil; não deduzir legendas pelas frequências da AV2. Sem resposta, implementar os bloqueios e continuar somente tarefas independentes com perfis artificiais de teste; o aceite científico permanece pendente.

Orientação adicional do usuário: usabilidade em primeiro lugar e backend funcional simples. Manter um único processo Python, funções diretas, arquivos privados e semáforo; sem FastAPI, Redis, Celery, microsserviços, repositórios genéricos ou camadas extras. As separações de arquivos servem à leitura e aos testes, não criam serviços. Usar ponytail para evitar abstrações e context7 apenas para a API em dúvida; consultar uma vez e reutilizar a referência na tarefa.

Decisões propostas para esta versão:

- Limites iniciais configuráveis: 100.000 registros, 500 colunas, 128 MiB descompactados por XLSX e 2.000 entradas ZIP; arquivo enviado até `20 * 1024**2` bytes. Recusar antes de materializar conteúdo que ultrapasse o limite.
- Trabalho pesado: limite 2, uma execução por trabalho, sem submissões duplicadas. Quando ocupado, informar que é necessário tentar novamente; não manter uma fila ilimitada em memória.
- Trabalhos concluídos expiram em 60 minutos; uploads abandonados em 60 minutos da criação. Limpeza a cada 5 minutos e no início; um trabalho marcado ativo não é removido pelo limpador. Após reinício do único servidor, diretórios de processos anteriores são órfãos.
- Exportações individuais e ZIP até 64 MiB cada, limite configurável. Exibir só o download preparado naquele momento para conter duplicação de bytes em memória.
- Missing: sem imputação; escore incompleto ausente; análise por pares completos, com n total, n efetivo, ausentes e motivo das exclusões. Valor inválido não vira zero. Não excluir automaticamente participantes por critérios não observáveis no banco.
- Família principal proposta: `PSQI_G × ZARIT` e `PSQI_G × ZARIT_CLASS`. `PSQI × ZARIT` é complementar; os demais cruzamentos são exploratórios. Exibir p bilateral sem ajuste com aviso explícito de multiplicidade; não selecionar resultados por p. Congelar a lista antes de executar e incluí-la no manifesto.
- RxC esparsa: no MVP, tabela descritiva sem p, com motivo. Monte Carlo para RxC fica fora desta entrega, evitando um algoritmo adicional sem validação independente.
- Texto livre (`OCUP`, `OUTRA`) e campos desconhecidos ficam fora das exportações por padrão. O ID exportado é sequencial por execução; a ligação com o ID de entrada fica privada. Isso reduz identificadores diretos e não constitui garantia de anonimização.
- Não reutilizar código dos repositórios citados sem verificar licença. Não adicionar `.sav`, `.prj`, banco de dados, API de IA, histórico global ou regressão.

## Mapa de arquivos e responsabilidades

| Arquivos | Responsabilidade |
| --- | --- |
| `pyproject.toml`, `requirements.lock`, `requirements-dev.lock`, `.gitignore`, `README.md` | Instalação reproduzível, testes e operação local |
| `fixtures/source/` (privado), `tests/fixtures/synthetic_tcc.xlsx`, `tests/conftest.py` | Originais imutáveis, base explicitamente fictícia e fixtures de teste |
| `src/tcc_analyzer/models.py`, `settings.py` | Contratos de domínio e limites configuráveis, sem Streamlit |
| `src/tcc_analyzer/importers.py` | Inspeção de conteúdo, abas e importação sem coerção silenciosa |
| `configs/profiles/tea_maternal_sleep_v1.yaml`, `src/tcc_analyzer/profiles.py` | Dicionário e regras científicas versionadas |
| `src/tcc_analyzer/validation.py`, `transformations.py` | Diagnósticos, preparação tipada, recodificação e desfazer |
| `src/tcc_analyzer/scales/clock.py`, `zarit.py`, `psqi.py` | Horários e pontuação dos instrumentos |
| `src/tcc_analyzer/statistics/descriptive.py`, `selection.py`, `categorical.py`, `numeric.py` | Resumos, escolha documentada e cálculos estatísticos |
| `src/tcc_analyzer/reporting/tables.py`, `docx_report.py`, `pdf.py` | Mesmo conteúdo numérico para prévia, DOCX e PDF |
| `src/tcc_analyzer/exports/epiinfo.py`, `audit.py` | XLSX/CSV, dicionário, manifesto e auditoria exportável |
| `src/tcc_analyzer/jobs.py`, `pipeline.py`, `scripts/cleanup_jobs.py` | Isolamento, autorização de artefatos, retenção e orquestração sem UI |
| `app.py`, `src/tcc_analyzer/ui/state.py`, `pages.py`, `downloads.py`, `.streamlit/config.toml` | Fluxo de cinco passos e downloads pela sessão |
| `scripts/start_hamachi.ps1`, `configure_firewall.ps1`, `docs/hamachi-setup.md` | Início e restrição de rede no Windows |
| `docs/methods.md`, `epiinfo-import.md`, `acceptance.md` | Regras confirmadas e evidência de aceites científicos/manuais |
| `tests/test_*.py`, `tests/ui/test_*.py`, `tests/windows/network.Tests.ps1` | Testes atribuídos em cada tarefa abaixo |

Criar `__init__.py` nos pacotes Python. Contratos novos entram em `models.py` junto da tarefa que os introduz. Não criar camadas genéricas extras. Testes exibidos abaixo são os casos mínimos concretos; incluir imports nos arquivos correspondentes.

## Tarefa 1: Importação verificável e preservação dos originais

**Files:** Create `pyproject.toml`, `requirements.lock`, `requirements-dev.lock`, `.gitignore`, `README.md`, `src/tcc_analyzer/{__init__,models,settings,importers}.py`, `tests/conftest.py`, `tests/test_importers.py`, `tests/fixtures/synthetic_tcc.xlsx`; copiar os três originais para `fixtures/source/` sem versioná-los.

**Interfaces:**

- Consumes: arquivos locais de `fontes/` e hashes da conferência.
- Produces: `ImportLimits(max_bytes=20971520, max_rows=100000, max_columns=500, max_unpacked_bytes=134217728, max_zip_entries=2000)`; `CsvOptions(encoding: str, separator: str, decimal: str)`; `DatasetMeta(row_count: int, column_count: int, columns: tuple[str, ...], source_sha256: str)`; `ImportedDataset(raw: pd.DataFrame, meta: DatasetMeta)`.
- Produces: `inspect_upload(filename: str, payload: bytes, limits: ImportLimits) -> str`; `list_sheets(path: Path, limits: ImportLimits) -> tuple[str, ...]`; `load_table(path: Path, *, sheet: str | None, csv_options: CsvOptions | None, limits: ImportLimits) -> ImportedDataset`. Erros esperados usam `DomainError(code: str, message_pt: str)` sem valores privados em logs.
- Fixtures: `source_path: Path` aponta à cópia fictícia; `fictitious_df: pd.DataFrame` retorna uma cópia nova por teste. `tmp_path` e `monkeypatch` são do pytest. Demais microbases são construídas explicitamente nos próprios testes.

- [ ] **Passo 1: Preparar o ambiente de execução e os insumos.** Conferir hashes antes/depois das cópias; ignorar `fontes/`, `fixtures/source/`, `runtime/`, uploads, outputs, `.venv/` e caches. Se não houver Git, inicializar na execução e criar `codex/tcc-statistical-analyzer`; se houver trabalho alheio, aplicar `superpowers:using-git-worktrees`. Instalar dependências em `.venv` Python 3.12 e fixar os locks com hashes; não alterar o Python empacotado do Codex.
- [ ] **Passo 2: Escrever os testes de importação.**

```python
def test_fictitious_source_is_unchanged(source_path):
    before = sha256(source_path.read_bytes()).hexdigest()
    result = load_table(source_path, sheet="Banco_EpiInfo", csv_options=None,
                        limits=ImportLimits())
    assert result.raw.shape == (30, 75)
    assert result.raw["ID"].nunique() == 30
    assert result.raw.isna().sum().sum() == 0
    assert sha256(source_path.read_bytes()).hexdigest() == before

def test_portuguese_csv_preserves_raw_values(tmp_path):
    path = tmp_path / "dados.csv"
    path.write_text('ID;H_DEIT;observacao\n001;23,5;ação\n', encoding="utf-8-sig")
    result = load_table(path, sheet=None,
        csv_options=CsvOptions("utf-8-sig", ";", ","), limits=ImportLimits())
    assert result.raw.iloc[0].tolist() == ["001", "23,5", "ação"]
```

Adicionar `test_sheet_selection` com duas abas e valores distintos; `test_empty_file`, `test_duplicate_or_blank_headers`, `test_malformed_xlsx`, `test_wrong_extension_content`, `test_zip_expansion_limit`, `test_row_column_limits` e `test_oversized_upload`: todos exigem `DomainError` com códigos distintos e sem traceback/caminho ao usuário. `test_xls_without_extra` exige mensagem de dependência indisponível; com extra instalado, um XLS de teste deve abrir.

- [ ] **Passo 3: Rodar para confirmar vermelho.** `python -m pytest tests/test_importers.py -v`; esperado: falha por API ainda ausente, sem erro de instalação.
- [ ] **Passo 4: Implementar as APIs de importação.** Usar leitura tabular local; preservar cabeçalho e valores brutos, inspecionar duplicados antes do tratamento do pandas. CSV entra como texto; conversão numérica ocorre em cópia na Tarefa 2. Inspecionar estrutura ZIP/OLE, limites e conteúdo, rejeitar XLSX com macros, vínculos externos ou fórmulas em células; nunca recalcular fórmulas ou executar conteúdo de XLS/CSV. Falta de aba exige escolha, não união automática. Limitar memória antes de construir o DataFrame.
- [ ] **Passo 5: Confirmar verde e fixar instalação.** `python -m pytest tests/test_importers.py -v` e `python -m pip check`; esperado: todos os testes passam e `No broken requirements found`. Testar a instalação dos locks em ambiente limpo no Windows antes de aceitá-los.
- [ ] **Passo 6: Commit.** `git add pyproject.toml requirements.lock requirements-dev.lock .gitignore README.md src tests`; `git commit -m "feat: import bounded research datasets without changing sources"`. Conferir que nenhum original privado foi adicionado.

## Tarefa 2: Perfil versionado, validação e alterações reversíveis

**Files:** Create `configs/profiles/tea_maternal_sleep_v1.yaml`, `src/tcc_analyzer/{profiles,validation,transformations}.py`, `tests/test_profile.py`, `tests/test_transformations.py`, `docs/methods.md`; Modify `models.py`, `tests/conftest.py`.

**Interfaces:**

- Consumes: `ImportedDataset`, `CsvOptions` e ordem das 75 colunas na conferência.
- Produces: `VariableSpec(name: str, label: str, kind: str, allowed_values: tuple | None, missing_values: tuple, export_default: bool, mapping_status: str)`; `ResearchProfile(id: str, version: str, variables: tuple[VariableSpec, ...], derived_rules: dict, psqi_rules: dict, comparisons: tuple)`; status científico `pending` ou `confirmed`, com evidência da aprovação.
- Produces: `ValidationIssue(row_index: int | None, variable: str, raw_value: object, code: str, severity: str, message_pt: str)`; `ValidationReport(issues: tuple[ValidationIssue, ...], blocks_analysis: bool)`; `validate_dataset(df: pd.DataFrame, profile: ResearchProfile) -> ValidationReport`; `prepare_dataset(imported: ImportedDataset, profile: ResearchProfile, csv_options: CsvOptions | None) -> PreparedDataset`.
- Produces: `PreparedDataset(data: pd.DataFrame, source_meta: DatasetMeta, transformations: tuple[Transformation, ...], validation: ValidationReport)`; `Transformation(row_index: int | None, field: str, before: object, after: object, reason: str)`; `apply_changes(df: pd.DataFrame, changes: tuple[Transformation, ...], *, confirmed: bool) -> pd.DataFrame`; `undo_changes(df: pd.DataFrame, changes: tuple[Transformation, ...]) -> pd.DataFrame`. O histórico com valores originais permanece privado.
- Fixtures: `confirmed_profile` é um perfil **artificial** de teste com códigos explicitamente definidos, sem representar aprovação do perfil de pesquisa.

- [ ] **Passo 1: Escrever os testes do perfil e da reversão.**

```python
def test_draft_profile_has_75_fields_and_blocks_unknown_coding(fictitious_df):
    profile = load_profile(Path("configs/profiles/tea_maternal_sleep_v1.yaml"))
    assert profile.id == "tea_maternal_sleep_v1"
    assert len(profile.variables) == 75
    assert [v.name for v in profile.variables] == list(fictitious_df.columns)
    pending = replace(profile, variables=tuple(
        replace(v, mapping_status="pending") for v in profile.variables))
    assert validate_dataset(fictitious_df, pending).blocks_analysis

def test_changes_require_confirmation_and_are_reversible(fictitious_df):
    original = fictitious_df.copy(deep=True)
    change = Transformation(0, "IDADE_M", 34, 35, "Conferência do formulário")
    with pytest.raises(DomainError):
        apply_changes(original, (change,), confirmed=False)
    changed = apply_changes(original, (change,), confirmed=True)
    pd.testing.assert_frame_equal(undo_changes(changed, (change,)), original)
    pd.testing.assert_frame_equal(original, fictitious_df)
```

Adicionar casos que exigem: coluna renomeada só após mapeamento confirmado e auditado; coluna desconhecida visível mas não analisada/exportada; categoria desconhecida com linha/campo; ID duplicado bloqueado; zero distinto de missing; conversão de `23,5` apenas na cópia; falta de coluna obrigatória bloqueada; inconsistência entre acompanhamento e terapias avisada. Não impor exclusão por TCLE/distúrbio prévio ausentes no esquema. O teste usa `dataclasses.replace` para construir um perfil pendente, independentemente do status do YAML de produção; aprovar o perfil não exige remover testes de bloqueio.

- [ ] **Passo 2: Confirmar vermelho.** `python -m pytest tests/test_profile.py tests/test_transformations.py -v`; esperado: APIs ausentes.
- [ ] **Passo 3: Implementar perfil e preparação.** `load_profile(path: Path) -> ResearchProfile` usa YAML seguro, esquema fechado e ID/versionamento obrigatórios. Registrar todos os 75 campos, intervalos dos instrumentos, derivados e a matriz da Tarefa 4. Marcar códigos não demonstrados como `pending`; converter apenas campos confirmados, sem descartar linhas. Derivados recebem nomes novos (`ZARIT_CLASS`, `PSQI_RECALC`, `PSQI_G_RECALC`), nunca substituem as colunas fornecidas. A confirmação de renda, escolaridade, sexo e sim/não é uma dependência de dados, não uma tarefa para adivinhar significados.
- [ ] **Passo 4: Confirmar verde.** Mesmo comando; esperado: todos passam, incluindo bloqueio legível de perfil pendente. Registrar em `docs/methods.md` o que foi confirmado e o que impede análises rotuladas.
- [ ] **Passo 5: Commit.** `git add configs src/tcc_analyzer tests docs/methods.md`; `git commit -m "feat: validate versioned research profiles and reversible changes"`.

## Tarefa 3: Horários, Zarit e PSQI com confirmação de pontuação

**Files:** Create `src/tcc_analyzer/scales/{__init__,clock,zarit,psqi}.py`, `tests/test_scales.py`, `tests/fixtures/psqi_approved_vectors.json`; Modify `models.py`, perfil YAML, `docs/methods.md`.

**Interfaces:**

- Consumes: `ResearchProfile`, `PreparedDataset` e manual/mapeamento PSQI confirmado pela responsável.
- Produces: `ScoreResult(total: int | None, category: int | None, components: tuple[int | None, ...], issues: tuple[str, ...])`; `decimal_hour_to_minutes(value: float) -> int`; `hours_in_bed(bed: float, rise: float) -> float`; `classify_psqi(total: int) -> int`; `classify_zarit(total: int) -> int` (faixas 1–4).
- Produces: `score_zarit(row: Mapping[str, object], profile: ResearchProfile) -> ScoreResult`; `score_psqi(row: Mapping[str, object], profile: ResearchProfile) -> ScoreResult`; `compare_recorded_scores(df: pd.DataFrame, profile: ResearchProfile) -> pd.DataFrame`, com colunas `row_index`, `instrument`, `recorded`, `recalculated`, `difference`, `issues`.

- [ ] **Passo 1: Registrar a regra aprovada e seus vetores independentes.** Antes do corpo de `score_psqi`, confrontar Anexo I com o [material oficial da University of Pittsburgh](https://www.sleep.pitt.edu/research/measures-and-study-instruments). Registrar manual/versão, limites com desigualdades explícitas e aprovação. A fixture JSON deve conter respostas completas e sete componentes esperados para: global 0/5/6/21; minutos 15/16/30/31/60/61; durações exatamente 5/6/7; eficiências exatamente 65/75/85%; perturbações e disfunção diurna nos limiares do manual. Confirmar `DIF_DORM`/5j e exclusão de `PARCEIRO`. Sem essa confirmação, manter `score_psqi` retornando total ausente e `psqi_rules_unconfirmed`, com esse comportamento testado; não preencher a fixture com saídas do próprio algoritmo.
- [ ] **Passo 2: Escrever os testes dos instrumentos.**

```python
@pytest.mark.parametrize("value, minutes", [(23.5, 1410), (0.25, 15)])
def test_decimal_clock(value, minutes):
    assert decimal_hour_to_minutes(value) == minutes

def test_midnight_and_equal_clock():
    assert hours_in_bed(23.5, 6.5) == 7.0
    with pytest.raises(DomainError):
        hours_in_bed(6.5, 6.5)  # Não presumir permanência de 24 horas.

@pytest.mark.parametrize("score, category", [(20,1),(21,2),(40,2),(41,3),(60,3),(61,4),(88,4)])
def test_zarit_boundaries(score, category):
    assert classify_zarit(score) == category

def test_psqi_cutoff():
    assert classify_psqi(5) == 1
    assert classify_psqi(6) == 2
```

`test_zarit_matches_all_30_records` exige igualdade em todas as linhas e contagens `[2,8,16,4]`. `test_missing_item_no_total` exige `total is None` para um item ausente em cada instrumento. `test_invalid_clock` cobre -1, 24, NaN; `test_sleep_exceeds_time_in_bed` exige escore ausente e aviso. `test_psqi_approved_vectors` compara **cada componente e total** aos vetores aprovados; `test_recorded_discrepancy_preserves_source` altera somente uma cópia e exige diferença, sem sobrescrever `PSQI`/`PSQI_G`.

- [ ] **Passo 3: Confirmar vermelho.** `python -m pytest tests/test_scales.py -v`; esperado: funções ausentes ou regras ainda não implementadas.
- [ ] **Passo 4: Implementar as funções.** Zarit soma exatamente `TEMP_VOC` a `UNIC_RESP`, 22 inteiros 0–4, sem imputação. Horas do banco são decimais, não frações Excel de dia; calcular minutos com tolerância de arredondamento documentada, depois duração modular. PSQI só pontua com regra confirmada, sete componentes 0–3 e global 0–21. Guardar fornecido e recalculado lado a lado; desfecho para análise exige escolha explícita, registrada, se houver divergências.
- [ ] **Passo 5: Confirmar verde.** Mesmo comando; esperado: todos os testes implementáveis passam. Se o manual não estiver confirmado, registrar esse gate como pendente e não declarar a pontuação PSQI validada; teste de bloqueio não substitui vetores aprovados.
- [ ] **Passo 6: Commit.** `git add src/tcc_analyzer/scales src/tcc_analyzer/models.py configs tests docs/methods.md`; `git commit -m "feat: score research instruments with explicit validation gates"`.

## Tarefa 4: Descritivas e plano estatístico congelado

**Files:** Create `src/tcc_analyzer/statistics/{__init__,descriptive,selection}.py`, `tests/test_descriptive.py`, `tests/test_selection.py`; Modify `models.py`, perfil YAML, `docs/methods.md`.

**Interfaces:**

- Consumes: `PreparedDataset`, `ResearchProfile`, escores da Tarefa 3.
- Produces: `ComparisonSpec(id: str, outcome: str, predictor: str, family: str, method: str, rationale: str, group_order: tuple, event_value: object | None)`; `TestRecommendation(method: str, alternatives: tuple[str, ...], reasons: tuple[str, ...], blocked: bool)`.
- Produces: `SummaryResult(field: str, n_total: int, n_valid: int, n_missing: int, metrics: dict, counts: dict, denominator: str)`; `EffectEstimate(value: float | None, ci95: tuple[float, float] | None, method: str, unavailable_reason: str | None)`; `TestResult(method: str, n_effective: int, n_missing: int, statistic: float | None, p_value: float | None, p_kind: str, effects: dict[str, EffectEstimate], warnings: tuple[str, ...], assumptions: tuple[str, ...], seed: int | None)`; `AnalysisResult(spec: ComparisonSpec, result: TestResult)`.
- Produces: `describe(df: pd.DataFrame, fields: tuple[str, ...], profile: ResearchProfile) -> tuple[SummaryResult, ...]`; `recommend_test(df: pd.DataFrame, comparison: ComparisonSpec, profile: ResearchProfile) -> TestRecommendation`; `freeze_comparisons(comparisons: tuple[ComparisonSpec, ...], profile: ResearchProfile) -> tuple[ComparisonSpec, ...]`.

- [ ] **Passo 1: Escrever testes de denominadores e seleção.**

```python
def test_age_summary_is_sample_sd(fictitious_df, confirmed_profile):
    summary, = describe(fictitious_df, ("IDADE_M",), confirmed_profile)
    assert summary.n_valid == 30
    assert summary.metrics["mean"] == pytest.approx(37.4)
    assert summary.metrics["sd"] == pytest.approx(6.392883974955386)

def test_missing_uses_variable_denominator(confirmed_profile):
    df = pd.DataFrame({"ALT_SONO": [1, 2, None]})
    summary, = describe(df, ("ALT_SONO",), confirmed_profile)
    assert (summary.n_total, summary.n_valid, summary.n_missing) == (3, 2, 1)
    assert summary.metrics["percentages"][1] == 50.0
```

`test_multiple_therapy_denominator` exige 24/30=80% para FONO, não 24/27; `test_primary_family_is_prespecified` exige os dois cruzamentos principais definidos acima, sem ranking por p; `test_selection_requires_rationale` recusa método manual sem justificativa; `test_normality_does_not_select_alone` mantém escolha orientada ao estimando/diagnósticos quando só muda o p de normalidade. Campo de escala ordinal não vira contínuo só porque contém números.

- [ ] **Passo 2: Confirmar vermelho.** `python -m pytest tests/test_descriptive.py tests/test_selection.py -v`.
- [ ] **Passo 3: Implementar resumos e política.** Descritivas numéricas: média, DP amostral, mediana, Q1/Q3, mínimo/máximo; categóricas: n/% válidos e ausentes separados. Prévia inclui grupos, n, distribuição/outliers e justificativa. Recomendar Fisher para 2×2 com qualquer esperado <5; qui-quadrado sem Yates se todos esperados ≥5. RxC usa qui-quadrado somente sem esperado <1 e no máximo 20% <5; caso contrário, descritiva sem p. Welch é a opção para diferenças de médias justificadas; Mann–Whitney para comparação de distribuições/ordem; vários grupos usam Welch/Kruskal; associação linear usa Pearson, monotônica/ordinal Spearman. O usuário confirma o método e pressupostos; registrar mudanças, sem automatizar por Shapiro. Todas as famílias, métodos, referências e política de missing viajam no manifesto.
- [ ] **Passo 4: Confirmar verde.** Mesmo comando; todos passam. Verificar que não há import de Streamlit no núcleo.
- [ ] **Passo 5: Commit.** `git add src/tcc_analyzer/statistics src/tcc_analyzer/models.py configs tests docs/methods.md`; `git commit -m "feat: describe research data and freeze analysis decisions"`.

## Tarefa 5: Comparações categóricas e medidas epidemiológicas

**Files:** Create `src/tcc_analyzer/statistics/categorical.py`, `tests/test_categorical.py`; Modify `docs/methods.md`.

**Interfaces:**

- Consumes: `TestResult`, `EffectEstimate` e política da Tarefa 4.
- Produces: `analyze_contingency(table: np.ndarray, *, method: str, event_column: int | None, exposed_row: int | None) -> TestResult`. Entradas são contagens inteiras não negativas. Orientação 2×2 para efeitos: `[[expostas_evento, expostas_sem_evento], [referencia_evento, referencia_sem_evento]]`. Não derivar exposição pelo ordenamento acidental dos códigos.

- [ ] **Passo 1: Escrever os testes com referências independentes.**

```python
def test_fisher_and_effect_orientation():
    result = analyze_contingency(np.array([[8, 2], [1, 5]]),
        method="fisher", event_column=0, exposed_row=0)
    assert result.p_value == pytest.approx(0.034965034965034975)
    assert result.n_effective == 16
    assert result.effects["odds_ratio"].value == pytest.approx(20.0)
    assert result.effects["prevalence_ratio"].value == pytest.approx(4.8)

def test_zero_cell_does_not_add_half():
    result = analyze_contingency(np.array([[0, 5], [4, 1]]),
        method="fisher", event_column=0, exposed_row=0)
    assert 0 <= result.p_value <= 1
    assert result.effects["prevalence_ratio"].value == 0
    assert result.effects["prevalence_ratio"].ci95 is None
    assert "zero_cell_no_automatic_correction" in result.warnings
```

`test_dense_chi_square` usa `[[10,10],[10,10]]` e exige estatística 0/p=1. `test_sparse_rxc` exige `p_value is None` e aviso para `[[1,0,0],[0,1,1]]`. `test_zero_margin` exige bloqueio de inferência; `test_no_binary_orientation_no_ratio` exige efeitos RP/OR ausentes; `test_invalid_counts` recusa negativos, frações e entrada vazia. O teste não usa a própria rotina SciPy como valor esperado.

- [ ] **Passo 2: Confirmar vermelho.** `python -m pytest tests/test_categorical.py -v`.
- [ ] **Passo 3: Implementar com SciPy/statsmodels.** Fisher bilateral exato para 2×2 e qui-quadrado conforme a política. RP pontual é prevalência exposta/referência, com IC log-Katz somente quando as células necessárias são positivas; OR amostral usa IC log-Wald somente com quatro células positivas. Em zero/denominador inválido, manter a estimativa finita quando definida e deixar IC ausente com motivo; não serializar infinito como número válido. Usar `shift_zeros=False` se empregar `Table2x2`, cujo padrão corrige zeros. Nunca chamar OR de RP ou de risco prospectivo. Identificar aproximações dos ICs e pressupostos de independência/amostragem.
- [ ] **Passo 4: Confirmar verde.** Mesmo comando; todos passam. Registrar em métodos a definição de p bilateral e as diferenças possíveis de convenção em comparação com Epi Info.
- [ ] **Passo 5: Commit.** `git add src/tcc_analyzer/statistics/categorical.py tests/test_categorical.py docs/methods.md`; `git commit -m "feat: analyze contingency tables without hidden zero corrections"`.

## Tarefa 6: Comparações numéricas e correlações

**Files:** Create `src/tcc_analyzer/statistics/numeric.py`, `tests/test_numeric.py`; Modify `docs/methods.md`.

**Interfaces:**

- Consumes: `TestResult`, `EffectEstimate` e métodos confirmados na Tarefa 4.
- Produces: `compare_groups(groups: tuple[np.ndarray, ...], *, method: str, seed: int) -> TestResult`; métodos `welch_t`, `mann_whitney`, `welch_anova`, `kruskal`.
- Produces: `correlate(x: np.ndarray, y: np.ndarray, *, method: str, seed: int) -> TestResult`; métodos `pearson`, `spearman`. A função `correlate` filtra x/y conjuntamente, contabilizando pares ausentes; não remover NaN separadamente. `compare_groups` contabiliza ausentes em cada grupo.

- [ ] **Passo 1: Escrever testes de estimando e limites.**

```python
def test_welch_reports_mean_difference():
    result = compare_groups((np.array([1.,2.,3.]), np.array([4.,5.,6.])),
                            method="welch_t", seed=20261104)
    assert result.effects["mean_difference"].value == -3
    assert result.effects["mean_difference"].ci95[1] < 0
    assert result.p_value == pytest.approx(0.021311641128756727)

def test_mann_whitney_is_not_a_median_difference():
    result = compare_groups((np.array([1.,2.,3.]), np.array([4.,5.,6.])),
                            method="mann_whitney", seed=20261104)
    assert result.statistic == 0
    assert result.p_value == pytest.approx(0.1)
    assert result.effects["probability_superiority"].value == 0
    assert "median_difference" not in result.effects
```

`test_pearson_known_correlation` usa x=[1,2,3,4], y=[1,3,2,4], exige r=0,8 e p=0,2. `test_spearman_monotonic` exige rho=1 para x=[1,2,3,4,5], y=[1,4,9,16,25]. `test_three_group_methods` usa [1,2,3]/[4,5,6]/[7,8,9]: Welch F=27, gl=(2,4), p=0,0047562425683709865; Kruskal H=7,2, p=0,02732372244729256; ambos n=9. Referências calculáveis independentemente: médias 2/5/8, variâncias 1 e postos 1 a 9; comparar com `pytest.approx`. `test_constant_data`, `test_group_with_one_observation`, `test_ties_small_sample`, `test_empty_group`, `test_paired_missing` exigem bloqueio/aviso definido e n correto; `test_seed_reproducible` exige mesmos p/IC com a mesma semente.

- [ ] **Passo 2: Confirmar vermelho.** `python -m pytest tests/test_numeric.py -v`.
- [ ] **Passo 3: Implementar os cálculos.** Welch t via `ttest_ind(equal_var=False)` com IC95% da diferença média e graus de liberdade; Welch ANOVA via `statsmodels.stats.oneway.anova_oneway(use_var="unequal")`; Kruskal via SciPy. Inferência de grupos exige pelo menos 2 observações por grupo; recomendar apenas descritiva quando insuficiente e avisar aproximação Kruskal em grupos <5. Não apresentar comparações pós-hoc não planejadas.
- [ ] **Passo 4: Implementar os efeitos não paramétricos e correlações.** Mann–Whitney: U do primeiro grupo e probabilidade de superioridade `U/(n1*n2)`, não diferença de medianas; exato sem empates quando menor grupo ≤8, permutação exaustiva com empates se número de alocações ≤10.000, senão aproximação com correção de empates e aviso. Spearman: permutação exaustiva se n≤8, assintótico com aviso acima disso; Pearson p paramétrico e IC Fisher-z para n>3. Para superioridade e Spearman, IC percentil por 1.999 reamostragens pareadas/por grupo, semente 20261104, somente com n≥5 em cada amostra necessária e distribuição não degenerada; senão IC ausente com motivo. Variável constante não produz correlação. Omnibus apresenta estatística, n e médias/medianas por grupo; efeito/IC global indisponível é explicitado, sem fórmula improvisada. Guardar `p_kind` como `exact`, `permutation_exact`, `asymptotic` ou `parametric`.
- [ ] **Passo 5: Confirmar verde.** Mesmo comando; todos passam, incluindo reamostragem reproduzível e intervalos ausentes quando não sustentados.
- [ ] **Passo 6: Commit.** `git add src/tcc_analyzer/statistics/numeric.py tests/test_numeric.py docs/methods.md`; `git commit -m "feat: compare numeric outcomes with explicit estimands"`.

## Tarefa 7: Tabelas acadêmicas, prévia e relatórios

**Files:** Create `src/tcc_analyzer/reporting/{__init__,tables,docx_report,pdf}.py`, `tests/test_reports.py`; Modify `models.py`.

**Interfaces:**

- Consumes: `tuple[AnalysisResult, ...]`, `tuple[SummaryResult, ...]` e dicionário confirmado.
- Produces: `RunMetadata(profile_id: str, profile_version: str, profile_sha256: str, source_sha256: str, generated_at: datetime, fictitious: bool, methods: tuple[str, ...], score_source: str, seed: int, package_versions: dict[str, str], code_version: str, source_options: dict)`; `ReportTables(descriptive: tuple[pd.DataFrame, ...], bivariate: tuple[pd.DataFrame, ...], notes: tuple[str, ...], narrative: tuple[str, ...])`; `PdfResult(path: Path | None, status: str, reason_pt: str | None)`.
- Produces: `build_tables(results: tuple[AnalysisResult, ...], summaries: tuple[SummaryResult, ...], profile: ResearchProfile) -> ReportTables`; `format_p(value: float | None) -> str`; `render_docx(tables: ReportTables, metadata: RunMetadata, output: Path) -> Path`; `convert_pdf(docx_path: Path, output_dir: Path) -> PdfResult`.

- [ ] **Passo 1: Escrever testes do conteúdo de relatório.**

```python
def test_p_format_does_not_round_into_threshold():
    assert format_p(0.0009) == "<0,001"
    assert format_p(0.001) == "0,001"
    assert format_p(None) == "Não calculado"
```

`test_three_descriptive_tables` exige grupos sociodemográfico/clínico/instrumentos, média 37,4, PSQI 4/26 e Zarit 2/8/16/4 calculados da fixture. `test_reports_include_provenance_and_warnings` exige n efetivo, método, pressupostos, IC ou motivo, p não arredondado nos dados, missing e multiplicidade. `test_fictitious_notice` exige “Dados fictícios para teste; não representam resultados da pesquisa.” em prévia e DOCX. `test_no_causal_templates` exige frase associativa conhecida, sem “causou”/“efeito independente”. `test_pdf_unavailable_keeps_docx` exige status `unavailable`, `path is None` e DOCX legível quando conversor ausente; falha de conversão usa status `failed`.

- [ ] **Passo 2: Confirmar vermelho.** `python -m pytest tests/test_reports.py -v`.
- [ ] **Passo 3: Implementar tabelas e DOCX.** Usar os mesmos `ReportTables` na tela e no documento; recalcular a AV2, sem copiar números históricos. Redação determinística em PT-BR, vírgula decimal, DP amostral, rodapé de resposta múltipla e limitações transversais/amostra pequena. Tabelas não incluem linhas individuais ou campos livres. Acrescentar proveniência dos escores fornecidos/recalculados e divergências sem expor participantes.
- [ ] **Passo 4: Implementar PDF local verificável.** Converter apenas o DOCX gerado, por subprocesso sem shell, com timeout e perfil temporário LibreOffice exclusivo por trabalho. Não abrir uploads DOCX nem enviar nada a conversor remoto. Sem conversor, manter exportação DOCX e explicar a ausência do PDF.
- [ ] **Passo 5: Confirmar verde e revisar visualmente.** Mesmo comando; renderizar DOCX e PDF disponíveis, inspecionar todas as páginas e corrigir cortes/quebras/cabeçalhos. Aplicar a skill `documents:documents` para a revisão do artefato e `pdf:pdf` quando houver PDF. Salvar em `docs/acceptance.md` conversor/versão e resultado, sem dados reais ou capturas identificáveis.
- [ ] **Passo 6: Commit.** `git add src/tcc_analyzer/reporting src/tcc_analyzer/models.py tests/test_reports.py docs/acceptance.md`; `git commit -m "feat: render reproducible Portuguese academic reports"`.

## Tarefa 8: Exportações, dicionário, manifesto e auditoria

**Files:** Create `src/tcc_analyzer/exports/{__init__,epiinfo}.py`, `src/tcc_analyzer/audit.py`, `tests/test_epi_export.py`, `tests/test_audit.py`, `docs/epiinfo-import.md`; Modify `models.py`.

**Interfaces:**

- Consumes: dados preparados, `ResearchProfile`, `ReportTables`, `RunMetadata`, comparações congeladas e transformações.
- Produces: `CsvFormat(encoding: str="utf-8-sig", separator: str=";", decimal: str=",")`; `ExportManifest(files: dict[str, str], sha256: dict[str, str], csv_format: CsvFormat, excluded_fields: tuple[str, ...], text_escapes: tuple[tuple[int, str], ...])` com nomes relativos, não caminhos internos.
- Produces: `export_epiinfo(df: pd.DataFrame, profile: ResearchProfile, output_dir: Path, csv_format: CsvFormat) -> ExportManifest`; `export_tables(tables: ReportTables, output: Path) -> Path`; `export_dictionary(profile: ResearchProfile, output: Path) -> Path`; `write_manifest(metadata: RunMetadata, comparisons: tuple[ComparisonSpec, ...], exports: ExportManifest, output: Path) -> Path`; `write_audit(transformations: tuple[Transformation, ...], profile: ResearchProfile, output: Path) -> Path`.

- [ ] **Passo 1: Escrever os testes de round-trip e privacidade.**

```python
def test_csv_xlsx_preserve_numeric_codes_and_hours(fictitious_df, confirmed_profile, tmp_path):
    manifest = export_epiinfo(fictitious_df, confirmed_profile, tmp_path, CsvFormat())
    csv_df = pd.read_csv(tmp_path / manifest.files["csv"], sep=";", decimal=",", encoding="utf-8-sig")
    xlsx_df = pd.read_excel(tmp_path / manifest.files["xlsx"])
    assert len(csv_df) == len(xlsx_df) == 30
    assert csv_df["ID"].tolist() == list(range(1, 31))
    assert csv_df["H_DEIT"].tolist() == fictitious_df["H_DEIT"].tolist()
    assert csv_df["PSQI_G"].tolist() == xlsx_df["PSQI_G"].tolist()
    assert "OCUP" not in csv_df and "OUTRA" not in csv_df
```

`test_missing_round_trip` preserva missing sem texto literal `nan`; `test_accents_and_delimiters` cobre rótulos com “ação”, `;`, aspas e quebras de linha em coluna artificial autorizada. `test_formula_like_text` exige XLSX como célula texto e CSV com escape reversível registrado para texto começando por `=`, `+`, `-`, `@`, tab/CR; números negativos continuam numéricos. `test_export_audit_redacts_identifiers` exige ausência de ID bruto, texto livre, token de sessão e caminho absoluto na auditoria exportada. `test_manifest_replays_decisions` exige hash da fonte/perfil, versões de pacotes, opções CSV, seed, família, método, origem do escore e transformações sem valores sensíveis. `test_tables_xlsx_numeric` exige p e estimativas numéricas em abas de dados, separadas da formatação da apresentação.

- [ ] **Passo 2: Confirmar vermelho.** `python -m pytest tests/test_epi_export.py tests/test_audit.py -v`.
- [ ] **Passo 3: Implementar os arquivos.** Produzir `tabelas.xlsx`, `epiinfo_dados.xlsx` (aba `Banco_EpiInfo`), `epiinfo_dados.csv`, `dicionario.xlsx`, `manifesto.json`, `auditoria.json`. Preservar nomes/códigos das colunas autorizadas e ordem original, com derivados ao final; ID sequencial explícito no dicionário. Para CSV, definir `escape_csv_text(value: str) -> tuple[str, bool]` (prefixar apóstrofo apenas quando necessário) e `unescape_csv_text(value: str, was_escaped: bool) -> str`; registrar coordenadas sequenciais em `text_escapes` para distinguir apóstrofos originais. XLSX grava tais valores como texto, nunca fórmula. Manifesto lista hashes dos demais artefatos, excluindo a si próprio e o ZIP para evitar dependência circular. Auditoria pública contém contagem, campo, motivo e valores codificados não sensíveis; histórico completo para desfazer não integra ZIP. Manifesto usa JSON padrão, sem NaN/Infinity.
- [ ] **Passo 4: Documentar a importação no Epi Info.** Em `docs/epiinfo-import.md`, escrever passos para XLSX no Classic Analysis/Visual Dashboard e CSV com encoding/delimitador/decimal explícitos, alternativa CSV UTF-8/comma/ponto se requerida pela versão local e conferência de tipos. Usar o [guia oficial histórico](https://stacks.cdc.gov/view/cdc/23495) como referência. Estado inicial da compatibilidade: `pendente de teste real no Windows`; a aplicação funciona sem Epi Info.
- [ ] **Passo 5: Confirmar verde.** Mesmo comando; todos passam, incluindo reimportação da versão escapada por decodificador documentado e manutenção dos valores originais na memória privada.
- [ ] **Passo 6: Commit.** `git add src/tcc_analyzer/exports src/tcc_analyzer/audit.py src/tcc_analyzer/models.py tests/test_epi_export.py tests/test_audit.py docs/epiinfo-import.md`; `git commit -m "feat: export research tables and auditable Epi Info datasets"`.

## Tarefa 9: Trabalhos privados, expiração e pipeline completo

**Files:** Create `src/tcc_analyzer/{jobs,pipeline}.py`, `scripts/cleanup_jobs.py`, `tests/test_sessions.py`, `tests/test_pipeline.py`; Modify `models.py`, `settings.py`, `.gitignore`.

**Interfaces:**

- Consumes: APIs puras das Tarefas 1–8, relógio UTC injetável e diretório `runtime/jobs/` fora de qualquer área pública.
- Produces: `SessionContext(token: str)` com `secrets.token_urlsafe(32)`; `JobContext(id: str, owner_token: str, directory: Path, created_at: datetime, expires_at: datetime, status: str)` com ID aleatório independente de token/nome/IP; `RunOptions(comparisons: tuple[ComparisonSpec, ...], score_source: str, fictitious: bool, csv_format: CsvFormat)`; `RunArtifacts(files: dict[str, Path], pdf_status: str)`; `CleanupSummary(deleted: int, active_skipped: int, failed: int)`.
- Produces: `JobManager(root: Path, settings: Settings, clock: Callable[[], datetime])` com `create_job(session: SessionContext) -> JobContext`, `store_upload(session: SessionContext, job: JobContext, filename: str, payload: bytes) -> Path`, `read_artifact(session: SessionContext, job: JobContext, artifact_key: str) -> bytes`, `bundle_results(session: SessionContext, job: JobContext, artifacts: RunArtifacts) -> Path`, `purge_expired_jobs() -> CleanupSummary`, `close() -> None`.
- Produces: `run_pipeline(*, manager: JobManager, session: SessionContext, job: JobContext, source_path: Path, prepared: PreparedDataset, profile: ResearchProfile, options: RunOptions, progress: Callable[[str], None]) -> RunArtifacts`. `Settings(import_limits: ImportLimits, max_heavy_runs: int=2, retention_minutes: int=60, cleanup_interval_seconds: int=300, max_artifact_bytes: int=67108864)` reúne os limites. A orquestração autoriza os caminhos antes de chamar os escritores das Tarefas 7–8.

- [ ] **Passo 1: Escrever testes de acesso cruzado e ciclo de vida.**

```python
def test_other_session_cannot_read_even_with_known_job(manager):
    owner, other = SessionContext(secrets.token_urlsafe(32)), SessionContext(secrets.token_urlsafe(32))
    job = manager.create_job(owner)
    with pytest.raises(DomainError, match="Acesso não permitido"):
        manager.read_artifact(other, job, "zip")

def test_upload_filename_cannot_escape_job(manager, session):
    job = manager.create_job(session)
    with pytest.raises(DomainError):
        manager.store_upload(session, job, "../dados.csv", b"ID\n1\n")
```

Definir fixtures `manager`, `session`, `fake_clock` neste arquivo: raiz `tmp_path`, tokens novos e relógio controlável. `test_two_parallel_runs_never_mix` exige sentinelas diferentes em resultados/ZIP; `test_third_heavy_run_is_busy` exige duas análises admitidas e terceira recusada, e vaga liberada mesmo após exceção. `test_completed_job_expiry` aceita leitura em 59m59s e nega em 60m; `test_active_job_not_purged`, `test_abandoned_upload_expiry`, `test_restart_sweeps_orphans` e `test_symlink_outside_root_not_followed` fixam a limpeza segura. `test_zip_allowlist` exige exatamente `relatorio.docx`, `tabelas.xlsx`, `epiinfo_dados.xlsx`, `epiinfo_dados.csv`, `dicionario.xlsx`, `manifesto.json`, `auditoria.json` e `relatorio.pdf` somente se disponível; nunca fonte, token, histórico privado ou ZIP recursivo. `test_pipeline_fictitious` exige todos os artefatos, 4/26, 2/8/16/4 e aviso de divergência em uma cópia alterada; perfil pendente deve bloquear o pipeline.

- [ ] **Passo 2: Confirmar vermelho.** `python -m pytest tests/test_sessions.py tests/test_pipeline.py -v`.
- [ ] **Passo 3: Implementar propriedade, contenção e concorrência.** Cada operação verifica token, registro interno do trabalho e prazo antes de tocar nos bytes. Rejeitar caminhos absolutos, `..`, barras, nomes reservados Windows, ADS com `:` e reparse points; resolver e conferir contenção na raiz. Caminhos e nomes de artefato são do servidor; a UI fornece apenas chave de allowlist. Usar semáforo/locks de processo, sem DataFrames ou resultados em caches globais. Manifesto de trabalho privado é gravado atomicamente; token não vai para JSON exportado nem URL. Erros mostram códigos PT-BR e não conteúdo/caminhos.
- [ ] **Passo 4: Implementar pipeline e limpeza.** O pipeline verifica que `source_path` é o upload registrado do trabalho e que seu hash coincide com `prepared.source_meta.source_sha256`; usa a cópia preparada com correções confirmadas, valida, calcula, aplica comparações congeladas, monta tabelas/relatórios/exportações e empacota apenas arquivos registrados. Cada `finally` libera vaga e estado ativo. Expiração é marcada depois da geração; remover também buffers de sessão na próxima interação e negar novos downloads vencidos. Limpador periódico usa locks e não segue links; `close()` tenta limpeza sem prometer exclusão ao fechar aba. No reinício, remover órfãos do processo anterior antes de aceitar sessões; impedir duas instâncias sobre a mesma raiz. A CLI de limpeza usa a mesma API e lock, nunca uma implementação paralela de exclusão.
- [ ] **Passo 5: Confirmar verde.** Mesmo comando; todos passam. Inspecionar ZIP em teste por lista exata, hashes e sentinelas, não apenas existência. Verificar que o pipeline opera sem importar Streamlit e que o arquivo de entrada mantém seu hash.
- [ ] **Passo 6: Commit.** `git add src/tcc_analyzer scripts/cleanup_jobs.py tests/test_sessions.py tests/test_pipeline.py .gitignore`; `git commit -m "feat: isolate analysis jobs and expire private artifacts"`.

## Tarefa 10: Interface em cinco passos e downloads pela sessão

**Files:** Create `app.py`, `src/tcc_analyzer/ui/{__init__,state,pages,downloads}.py`, `.streamlit/config.toml`, `tests/ui/test_wizard.py`, `tests/ui/test_browser_sessions.py`; Modify `README.md`, `docs/acceptance.md`.

**Interfaces:**

- Consumes: `JobManager`, `SessionContext`, pipeline e tabelas da Tarefa 9.
- Produces: `WorkflowState(session: SessionContext, job: JobContext | None, step: int, prepared: PreparedDataset | None, options: RunOptions | None, artifacts: RunArtifacts | None, reviewed: bool)`; `invalidate_after_change(state: WorkflowState) -> WorkflowState` invalida resultados/revisão ao alterar fonte, correção, regra ou comparação.
- Produces: `render_import(state: WorkflowState, manager: JobManager) -> None`, `render_validation(...) -> None`, `render_comparisons(...) -> None`, `render_results(...) -> None`, `render_exports(...) -> None`, todos com os mesmos dois parâmetros. `build_download_anchor(payload: bytes, *, filename: str, mime: str) -> str` aceita somente nomes/MIME de allowlist e escapa HTML.

Direção visual com **frontend-design** instalada, conforme AGENTS.md: bancada de análise acadêmica, com tabela de resultados como elemento principal. Paleta local: fundo `#F7FAFC`, texto `#173441`, ação `#1F6675`, divisórias `#CBD8DE`, atenção `#8A4B00`, erro `#AC2430`; Segoe UI/Segoe UI Semibold do Windows, números tabulares. Conteúdo alinhado à esquerda, um painel de trabalho, tabelas largas com rolagem horizontal e cinco passos reais; sem fontes/CDNs, telemetria, imagens ou componentes buscados na internet. Conferir contraste, foco, zoom 200%, teclado e tela de 360 px.

```text
Análise bivariada do TCC
Importar | Dicionário e validações | Configurar cruzamentos | Resultados | Exportar
[Orientação e estado do passo]
[Tabela / configuração / prévia do relatório]
[Avisos concretos e como corrigir]
[Voltar]                                  [Ação do próximo passo]
```

- [ ] **Passo 1: Escrever testes de estado e fluxo.** `test_no_analysis_before_validation` exige bloqueio com perfil pendente; `test_edit_requires_confirmation` mantém dados até confirmar e oferece desfazer; `test_change_invalidates_review` exige `reviewed is False` e artefatos anteriores indisponíveis; `test_export_requires_preview` exige revisão explícita antes de preparar download. Usar AppTest para estados/widget e Playwright em dois contextos isolados para upload e downloads reais.
- [ ] **Passo 2: Confirmar vermelho.** `python -m pytest tests/ui/test_wizard.py -v` e, com servidor local de teste iniciado pela fixture, `python -m pytest tests/ui/test_browser_sessions.py -v`.
- [ ] **Passo 3: Implementar os cinco passos.** (1) Importar e visualizar, seleção de aba/CSV; (2) Dicionário e validações, valores originais/preparados e correções confirmadas; (3) Configurar cruzamentos, estimando, método, orientação, família e origem PSQI; (4) Resultados com n, métodos, avisos e prévia integral do relatório; (5) Exportar individualmente ou ZIP. Estado somente em `st.session_state`; progresso por execução; erro legível e retorno ao passo corrigível. Nenhuma listagem de outros trabalhos. Avisar que recarregar pode exigir novo processamento.
- [ ] **Passo 4: Implementar downloads sem URL global de relatório.** Não presumir que `st.download_button` autoriza por dono em cada GET. Neste MVP, preparar os bytes por `read_artifact` e transmitir ao navegador da sessão um link `data:` de download, base64, com nome/MIME fixos, após revisão e verificação de expiração. Não registrar dados privados no gerenciador global `/media/`, em `st.static`, nem em rotas por `job_id`. O HTML contém apenas marcação controlada e bytes codificados, nunca texto HTML do upload. Preparar um arquivo por vez e respeitar 64 MiB; se o navegador suportado não cumprir esse fluxo, registrar o problema e revisar o transporte antes de liberar dados reais, sem relaxar o requisito de isolamento.
- [ ] **Passo 5: Verificar dois navegadores e rede HTTP.** `test_browser_sessions_download_only_own_bytes` usa duas bases com sentinelas, verifica os downloads reais e tenta usar job conhecido alheio; exige negação. `test_no_private_media_endpoint` intercepta tráfego, exige ausência de URL `/media/` para relatórios e GET em caminhos adivinhados `/runtime/jobs/...` com 404/negação sem conteúdo. `test_expired_download_not_prepared` avança o relógio antes de pedir novos bytes. Links já recebidos são cópias locais e não podem ser revogados; documentar essa limitação junto da retenção do servidor. Conferir que uma reconexão não apresenta o estado de outro cliente.
- [ ] **Passo 6: Confirmar verde e revisar a interface.** Rodar os dois comandos acima; revisar os cinco passos em 360/1366 px, teclado, foco e contraste. Conferir console/requisições e ausência de rede pública, incluindo estatísticas de uso do Streamlit desativadas. Configurar `server.enableXsrfProtection=true`, `server.enableCORS=true`, `server.enableStaticServing=false`, `server.maxUploadSize=20`, `browser.gatherUsageStats=false`; revalidar as chaves contra a versão fixada. Registrar capturas somente com dados fictícios.
- [ ] **Passo 7: Commit.** `git add app.py src/tcc_analyzer/ui .streamlit tests/ui README.md docs/acceptance.md`; `git commit -m "feat: add private five-step research analysis interface"`.

## Tarefa 11: Operação Windows/Hamachi e aceites externos

**Files:** Create `scripts/start_hamachi.ps1`, `scripts/configure_firewall.ps1`, `tests/windows/network.Tests.ps1`, `docs/hamachi-setup.md`; Modify `README.md`, `docs/acceptance.md`, `docs/epiinfo-import.md`.

**Interfaces:**

- Consumes: instalação fixada Python 3.12, aplicação da Tarefa 10, IPv4 Hamachi do anfitrião e IPs dos clientes autorizados fornecidos pelo administrador.
- Produces: `start_hamachi.ps1 -HamachiAddress <IPv4> -AllowedPeerAddresses <IPv4[]> [-AllowAnyBind]`; `configure_firewall.ps1 -HamachiAddress <IPv4> -AllowedPeerAddresses <IPv4[]>`. Porta fixa 8501; validar tipos de IP e existência do endereço na interface Hamachi, sem comandos construídos com strings.

- [ ] **Passo 1: Escrever testes PowerShell.** Em Pester, mockar cmdlets de rede/firewall e o início do processo: `BindsOnlyProvidedHamachiIPv4`, `RefusesMissingHamachiInterface`, `RefusesBroadFirewallRule`, `AnyBindRequiresRestrictedRule`, `DoesNotDisableXsrf`, `NoPortForwardOrPublicTunnel`. Asserções exigem `LocalAddress` do Hamachi, TCP/8501, lista de peers e interface correspondente na regra. Falta de privilégio administrativo deve explicar o comando manual necessário, sem alterar regras de terceiros.
- [ ] **Passo 2: Confirmar vermelho.** `Invoke-Pester -Path tests/windows/network.Tests.ps1 -Output Detailed`; esperado: falhas por scripts ausentes.
- [ ] **Passo 3: Implementar configuração e início restritos.** O configurador cria/atualiza somente a regra nomeada `TCC Analyzer Hamachi 8501`, registra parâmetros e exige execução administrativa. O launcher verifica a interface e a política restritiva antes de iniciar `python -m streamlit run app.py --server.address <IP_HAMACHI> --server.port 8501`. `0.0.0.0` só com `-AllowAnyBind` explícito e regra efetivamente restrita já verificada; caso contrário abortar. Conferir regras amplas preexistentes que possam liberar o processo/porta e orientar resolução, sem removê-las automaticamente. Não abrir janelas auxiliares visíveis: se usar `Start-Process`, passar `-WindowStyle Hidden`, manter logs sem dados e documentar como parar.
- [ ] **Passo 4: Documentar a operação.** Incluir admissão/remoção de membros Hamachi, ausência de senha na aplicação, IP:8501, pré-requisitos e instalação offline a partir de wheelhouse/locks, início/parada, retenção e órfãos, diagnóstico de WebSocket/reconexão sem desabilitar XSRF/CORS, PDF opcional e gestão separada de backups/logs do Windows. A VPN e a aprovação ética exigem avaliação do administrador antes de dados reais; não afirmar confidencialidade comprovada só pela instalação do Hamachi.
- [ ] **Passo 5: Confirmar a suíte automatizada completa.** Executar `python -m pytest -q`, `python -m compileall -q src app.py`, `python -m pip check` e o comando Pester; esperado: todos os testes automatizados passam, compilação sem erros, dependências consistentes e Pester sem falhas. Ausência de confirmação científica, browser de teste ou Pester é pendência explícita, não um skip convertido em aprovação. Uma revisão de código final deve conferir segurança, métodos e contratos, sem enfraquecer testes para obter verde.
- [ ] **Passo 6: Executar aceite Hamachi com cliente Windows remoto.** Em `docs/acceptance.md`, registrar data/versões e evidência fictícia: cliente autorizado abre IP Hamachi:8501, envia arquivo, analisa e baixa ZIP próprio; dois clientes simultâneos não misturam resultados; terceira análise recebe ocupado; após expiração novos downloads são negados. De máquina fora da rede virtual, testar o IP físico/LAN e o IP público do servidor na porta 8501: não acessíveis. Conferir listener com `Get-NetTCPConnection` e filtros de endereço/interface do Firewall. Anotar a origem de cada teste; teste negativo apenas de dentro do servidor não comprova restrição externa.
- [ ] **Passo 7: Executar aceite no Epi Info instalado.** Importar ambos XLSX/CSV em Windows, registrar versão do Epi Info/driver e os parâmetros aceitos; conferir 30 linhas, IDs, tipos, acentos, missing de uma microbase, `23.5`/`0.25`, uma descritiva e a 2×2 `[[8,2],[1,5]]`. Comparar p bilateral e RP/OR conforme convenções documentadas, sem exigir igualdade de ICs calculados por métodos diferentes. Corrigir o formato/guias se necessário e repetir só os checks afetados. Sem Epi Info disponível, manter compatibilidade como `não verificada`, preservando o funcionamento independente da aplicação.
- [ ] **Passo 8: Commit e registrar o estado de entrega.** `git add scripts/start_hamachi.ps1 scripts/configure_firewall.ps1 tests/windows docs README.md`; `git commit -m "feat: restrict Windows hosting to the authorized Hamachi network"`. Relatar arquivos alterados, resultados exatos dos comandos, confirmações científicas e aceites externos; não declarar o MVP pronto para dados reais com qualquer um desses gates pendente.

## Marcos, cobertura e revisão deste plano

| Marco | Tarefas | Entrega verificável |
| --- | --- | --- |
| M1 Dados | 1–2 | Importação preservada e perfil de 75 campos com pendências visíveis |
| M2 Instrumentos | 3 | Zarit/horários e PSQI confrontado com manual aprovado |
| M3 Estatística | 4–6 | Descritivas, família congelada, categóricas e numéricas com métodos/limites |
| M4 Artefatos | 7–8 | Prévia, DOCX/PDF disponível, tabelas, dicionário, auditoria e round-trip |
| M5 Aplicação privada | 9–11 | Sessões/ZIP/expiração, interface e aceites Windows/Hamachi/Epi Info |

Auto-revisão do plano executada contra a especificação e os arquivos: requisitos de importação/perfil/instrumentos em 1–3; métodos/multiplicidade em 4–6; relatórios/manifesto/exportação em 7–8; segurança multiusuário/retenção em 9–10; operação e provas externas em 11. Os cinco focos de revisão têm testes atribuídos. As interfaces de vizinhos usam os mesmos contratos; valores não definidos na fonte foram identificados como propostas ou dependências científicas. Nenhum teste, implementação, configuração de rede ou importação real no Epi Info foi executado nesta etapa de planejamento.

Execução sugerida: **native**, nesta sessão com `superpowers:executing-plans`. Conforme a orientação posterior do usuário, usar agentes/subagentes somente quando uma revisão ou tarefa independente trouxer economia concreta de tempo; não criar um implementador e um revisor novos por tarefa. Uma revisão independente focada em estatística/isolamento pode ser útil ao final. Solicitar a revisão deste documento antes de implementar, conforme `superpowers:writing-plans`.
