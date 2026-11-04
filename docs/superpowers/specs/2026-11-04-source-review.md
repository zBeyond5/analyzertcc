# Conferência das fontes para o plano de implementação

Data: 2026-11-04. Leitura local, sem modificar os três arquivos. A pasta ainda não contém código de aplicação nem repositório Git.

## Inventário

| Arquivo em `fontes/` | SHA-256 |
| --- | --- |
| AV2 - Inês Lima.docx | `53d38d6487e4be57394ba3c3742c9b008f63d93214c56e081566848ee30a6149` |
| Banco para Epi Info dados ficticios.xlsx | `e2a2fb48502e3a31b06af7c421417afc3819465a59c54127a1805fab3c137f3c` |
| PROJETO TCC - AV3 FINAL.docx | `dc5079a2adc669e6f64ca6f616ffabf526dbeee3fb9872ca138179df89e84660` |

Os originais devem ser copiados pelo implementador para `fixtures/source/`, com os mesmos hashes. Essas cópias e `fontes/` ficam fora do Git. Apenas uma cópia verificada do banco declarado fictício pode integrar `tests/fixtures/synthetic_tcc.xlsx`. Não copiar os DOCX para o conjunto público de testes.

## Verificações do banco fictício

- Uma aba: `Banco_EpiInfo`; 31 linhas incluindo cabeçalho; 30 registros e 75 colunas.
- Nenhuma célula vazia no bloco de dados; nenhuma fórmula; IDs 1 a 30, sem repetição.
- `ZARIT` coincide com a soma dos 22 campos de `TEMP_VOC` a `UNIC_RESP` em 30/30 registros.
- `PSQI_G` coincide com `1` para `PSQI <= 5` e `2` para `PSQI > 5` em 30/30 registros: 4 boas e 26 más.
- Idade materna: média 37,4; DP amostral 6,392883974955386, apresentado como 6,4.
- Faixas Zarit 0–20 / 21–40 / 41–60 / 61–88: 2 / 8 / 16 / 4.
- Todas as horas de sono informadas cabem no intervalo de deitar a levantar calculado com travessia de meia-noite.
- Estes números servem como referências de teste, nunca como achados de pesquisa.

## Evidências e confirmações necessárias

1. O DOCX AV3, seção 7.5 e Anexo I, fornece as perguntas PSQI e as amplitudes 0–3 e 0–21, mas não o algoritmo completo de componentes. Confirmar a versão e o manual de pontuação, os limites de duração/eficiência e a correspondência de `DIF_DORM` à frequência da questão 5j antes de implementar o recálculo. `PARCEIRO` corresponde à questão 10 e não deve entrar automaticamente no global.
2. Não há aba de dicionário nem legenda dos códigos. Frequências iguais às tabelas não provam o sentido de códigos. Confirmar, em especial, `SIT_CONJ`, `SEXO`, `ESCOL`, `RENDA`, `ESCOL_B`, `RENDA_B`, `FREQ_3` e a convenção sim/não dos campos 1/2.
3. O Apêndice II lista sete níveis de escolaridade; a AV2 resume baixa/média/alta; o banco contém `ESCOL` 2/3/4. O formulário lista renda até 1 / 1 a 2 / 2 a 4 / acima de 4 salários; a AV2 usa até 1 / acima de 1 a 2 / acima de 2 a 3; o banco contém `RENDA` 1/2/3. Exigir decisão da responsável, sem adaptar silenciosamente o formulário à tabela.
4. A AV3 prevê possível regressão em 7.7; a especificação atual a exclui expressamente do MVP. Prevalece o escopo atual de análises bivariadas.
5. Não existe campo que comprove diagnóstico prévio de distúrbio do sono ou TCLE. A aplicação pode apontar idade materna menor que 18 e questionários incompletos, mas não pode certificar todos os critérios de elegibilidade usando apenas este banco.
6. A AV2 é referência das três tabelas e da redação. Recalcular todos os números a partir do banco; terapias são respostas múltiplas, com denominador total explicitado.
7. Validação matemática da soma Zarit não substitui confirmação da versão do questionário e dos códigos pelo responsável científico.

## Estrutura observada das 75 colunas

A tabela registra domínio **observado**, não valores permitidos nem legenda clínica aprovada. `a..b` representa somente mínimo/máximo observados. Não expor os textos livres individuais no documento ou nos logs.

| Ordem | Campo original | Tipo observado | Domínio observado |
| --- | --- | --- | --- |
| 1 | `ID` | inteiro | 1..30 (30 valores distintos) |
| 2 | `IDADE_M` | inteiro | 27..50 (23 valores distintos) |
| 3 | `SIT_CONJ` | inteiro | 1, 2 |
| 4 | `ESCOL` | inteiro | 2, 3, 4 |
| 5 | `OCUP` | texto | 17 textos distintos; potencialmente identificável |
| 6 | `RENDA` | inteiro | 1, 2, 3 |
| 7 | `RED_APO` | inteiro | 1, 2 |
| 8 | `FILHOS` | inteiro | 1, 2, 3 |
| 9 | `TRAB_NOT` | inteiro | 1, 2 |
| 10 | `DOENCA` | inteiro | 1, 2 |
| 11 | `ANTIDEP` | inteiro | 1, 2 |
| 12 | `ANSIED` | inteiro | 1, 2 |
| 13 | `DEPRE` | inteiro | 1, 2 |
| 14 | `IDADE_C` | inteiro | 3..12 (10 valores distintos) |
| 15 | `SEXO` | inteiro | 1, 2 |
| 16 | `TEMP_TEA` | inteiro | 6..105 (26 valores distintos) |
| 17 | `ACOMP_TEP` | inteiro | 1, 2 |
| 18 | `FISIO` | inteiro | 1, 2 |
| 19 | `FONO` | inteiro | 1, 2 |
| 20 | `TER_OCUP` | inteiro | 1, 2 |
| 21 | `PSI` | inteiro | 1, 2 |
| 22 | `PSICOP` | inteiro | 1, 2 |
| 23 | `OUTRA` | texto | 4 textos distintos; potencialmente identificável |
| 24 | `FREQ_TEP` | inteiro | 0, 1, 2, 3, 4 |
| 25 | `ALT_SONO` | inteiro | 1, 2 |
| 26 | `DESP_NOT` | inteiro | 0, 1, 2, 3, 4, 5 |
| 27 | `CHORO` | inteiro | 1, 2 |
| 28 | `SUPERV` | inteiro | 1, 2 |
| 29 | `H_DEIT` | número | 0.25..23.75 |
| 30 | `N_MIN` | inteiro | 10..55 (9 valores distintos) |
| 31 | `H_LEV` | número | 5..8 |
| 32 | `H_SONO` | inteiro | 3, 4, 5, 6, 7, 8 |
| 33 | `NAO_CONS` | inteiro | 0, 1, 2 |
| 34 | `ACORD` | inteiro | 0, 1, 2, 3 |
| 35 | `PREC_LEV` | inteiro | 0, 1, 2, 3 |
| 36 | `NAO_RESP` | inteiro | 0, 1 |
| 37 | `TOS_RONC` | inteiro | 0, 1 |
| 38 | `FRIO` | inteiro | 0, 1 |
| 39 | `CALOR` | inteiro | 0, 1, 2, 3 |
| 40 | `SONHOS` | inteiro | 0, 1, 2, 3 |
| 41 | `DOR` | inteiro | 0, 1, 2, 3 |
| 42 | `DIF_DORM` | inteiro | 0, 1, 2, 3 |
| 43 | `QUA_SONO` | inteiro | 0, 1, 2, 3 |
| 44 | `FREQ_MED` | inteiro | 0, 1 |
| 45 | `DIF_ACOR` | inteiro | 0, 1, 2 |
| 46 | `ANIMO` | inteiro | 0, 1, 2, 3 |
| 47 | `PARCEIRO` | inteiro | 0, 1, 3 |
| 48 | `TEMP_VOC` | inteiro | 0, 1, 2, 3, 4 |
| 49 | `ESTRES` | inteiro | 0, 2, 3, 4 |
| 50 | `IRRIT` | inteiro | 0, 1, 2, 3, 4 |
| 51 | `AFET_REL` | inteiro | 0, 1, 2, 3, 4 |
| 52 | `MEDO` | inteiro | 1, 2, 3, 4 |
| 53 | `DEPENDE` | inteiro | 0, 1, 2, 3, 4 |
| 54 | `TENSO` | inteiro | 0, 1, 2, 3, 4 |
| 55 | `SAU_FIS` | inteiro | 0, 1, 2, 3, 4 |
| 56 | `PRIV` | inteiro | 1, 2, 3, 4 |
| 57 | `VID_SOC` | inteiro | 1, 2, 3, 4 |
| 58 | `DESCONF` | inteiro | 0, 1, 2, 3 |
| 59 | `UNICA_P` | inteiro | 0, 1, 2, 3, 4 |
| 60 | `DINHEIRO` | inteiro | 1, 2, 3, 4 |
| 61 | `CAP_CUI` | inteiro | 0, 1, 2, 3 |
| 62 | `CONTROLE` | inteiro | 0, 1, 2, 3, 4 |
| 63 | `INCAPAZ` | inteiro | 0, 1, 2, 3, 4 |
| 64 | `FAZ_MAIS` | inteiro | 0, 1, 2, 3, 4 |
| 65 | `CUID_MEL` | inteiro | 1, 2, 3, 4 |
| 66 | `MAIS_AJUD` | inteiro | 0, 1, 2, 3, 4 |
| 67 | `EXAUSTO` | inteiro | 0, 1, 2, 3, 4 |
| 68 | `CONST` | inteiro | 0, 1, 2, 3 |
| 69 | `UNIC_RESP` | inteiro | 1, 2, 3, 4 |
| 70 | `PSQI` | inteiro | 4..14 (11 valores distintos) |
| 71 | `ZARIT` | inteiro | 17..72 (26 valores distintos) |
| 72 | `PSQI_G` | inteiro | 1, 2 |
| 73 | `ESCOL_B` | inteiro | 1, 2 |
| 74 | `RENDA_B` | inteiro | 1, 2 |
| 75 | `FREQ_3` | inteiro | 1, 2 |

## Referências técnicas consultadas

Fontes oficiais consultadas em 2026-11-04; referências de planejamento, sem instalar pacotes nem executar serviços externos sobre o banco. A execução futura deve fixar versões e confirmar as APIs na documentação correspondente ao lock.

- [University of Pittsburgh: PSQI e materiais de pontuação](https://www.sleep.pitt.edu/research/measures-and-study-instruments). Não presume que o algoritmo externo já foi aprovado para o instrumento do projeto.
- [SciPy: Fisher exato](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.fisher_exact.html) e [Welch via ttest_ind](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_ind.html).
- [statsmodels: Table2x2](https://www.statsmodels.org/stable/generated/statsmodels.stats.contingency_tables.Table2x2.html): impedir a correção automática de zeros pelo parâmetro `shift_zeros`.
- [Streamlit: estado por sessão](https://docs.streamlit.io/develop/concepts/architecture/session-state), [configuração](https://docs.streamlit.io/develop/api-reference/configuration/config.toml) e [downloads](https://docs.streamlit.io/develop/api-reference/widgets/st.download_button). Estado por sessão, sozinho, não comprova autorização de cada requisição de download.
- [Código oficial do gerenciador de mídia Streamlit](https://github.com/streamlit/streamlit/blob/develop/lib/streamlit/runtime/media_file_manager.py): registro de mídia global. O plano evita registrar relatórios privados em URLs de mídia compartilhadas e exige teste HTTP e com dois navegadores.
- [CDC: guia oficial histórico do Epi Info 7](https://stacks.cdc.gov/view/cdc/23495) e [comando READ](https://www.cdc.gov/epiinfo/user-guide/command-reference/analysis-commands-read.html). As páginas históricas podem estar indisponíveis; usar o guia arquivado e registrar a versão efetivamente testada.
- [CDC: encerramento de suporte e alternativas](https://www.cdc.gov/epiinfo/pdfs/userguide/20250722_Cleared-Epi-Info-Sunset-Alt.pdf). O aplicativo não depende de Epi Info instalado.
