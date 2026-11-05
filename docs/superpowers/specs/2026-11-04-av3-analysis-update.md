# Atualização das análises conforme o AV3

## Objetivo

Completar as perguntas bivariadas disponíveis e explicar seus resultados em linguagem simples, respeitando o AV3 e a auditoria em `docs/2026-11-04-av3-coverage.md`. A interface atual e o motor estatístico são preservados. Este pedido é de planejamento, sem implementação/publicação.

## Requisitos globais

- Interface e relatórios em português brasileiro.
- Significância definida por p < 0,05; comparar o valor numérico original, nunca o texto arredondado.
- Sem IA, buscas web ou envio de respostas a serviços externos durante o uso.
- Não escolher testes ou variáveis pelo menor p nem ocultar resultados não significativos.
- Preservar entrada original, auditoria, desfazer, isolamento por sessão e downloads privados.
- Sem regressão múltipla, backend adicional, reconstrução de categorias perdidas ou imputação de respostas.

## Significância compreensível

O AV3, seção 7.7, adota 5% (p < 0,05). Desvio padrão descreve dispersão das respostas; não decide significância. Uma pergunta como sono/sobrecarga pode produzir comparações de médias, classificações e correlação, cada qual com seu p. Não produzir um “p da variável” ou escolher um único resultado dentre eles por ser significativo.

Estados exibidos por comparação: **Significativa pelo critério de 5%**, **Não atingiu o critério de 5%**, **Inferência não disponível**. Para o primeiro: “A comparação apresentou associação estatisticamente significativa pelo critério do projeto (p < 0,05). Isso não demonstra causa nem, por si só, importância prática.” Para o segundo: “A comparação não atingiu o critério de significância de 5%. Isso não prova ausência de associação.” O terceiro apresenta a razão já fornecida pelo motor, como tabela esparsa ou amostra insuficiente.

Exibir juntos pergunta, n efetivo/ausentes, método, p, estimativa e IC95% quando disponíveis. Direção e tamanho dependem da estimativa/orientação, nunca do p. Não gerar semáforo de variável relevante/irrelevante nem frase causal. Preservar aviso fictício em toda apresentação e exportação. Manter todas as comparações selecionadas no relatório, com famílias principal/complementar/exploratória e aviso de multiplicidade; limiar por comparação, sem declarar ajuste ou controle global inexistente.

Valores exatamente 0,05 não atendem ao critério estrito. Valores 0,04996 e 0,05004 não podem aparecer ambos somente como 0,050 ao lado de classificações distintas: usar precisão adicional nesses casos. p ausente em análise descritiva não vira zero; p inválido/não finito não recebe classificação. Não apresentar p como probabilidade da hipótese ser verdadeira ou de o resultado ser “por acaso”.

Referências: AV3 7.7 e [declaração da American Statistical Association](https://www.amstat.org/asa/files/pdfs/p-valuestatement.pdf). A ASA distingue significância de tamanho/importância do efeito e recomenda contexto e relato completo. Essa fonte orienta a explicação, sem alterar o critério escolhido no projeto.

## Catálogo e método

Manter sono/sobrecarga como pergunta principal e as três comparações existentes. Complementos agrupados, recolhidos por padrão:

- Mãe: IDADE_M, SIT_CONJ, ESCOL, RENDA, RED_APO, FILHOS, TRAB_NOT, DOENCA, ANTIDEP, ANSIED, DEPRE.
- Criança: IDADE_C, SEXO, TEMP_TEA, ACOMP_TEP, FISIO, FONO, TER_OCUP, PSI, PSICOP, FREQ_TEP, ALT_SONO, DESP_NOT, CHORO, SUPERV.

Cada fator adicional gera uma comparação com PSQI_G, pelo tipo documentado do perfil, como exploratória; não gerar ambos PSQI/PSQI_G para cada fator. Reutilizar IDs atuais de rede de apoio e sono infantil para evitar duplicação. Rótulos humanos derivados das perguntas, sem exibir códigos no caminho comum. Nenhum fator adicional pré-selecionado; não selecionar automaticamente todos nem filtrar por p. Itens individuais PSQI/Zarit não entram como preditores de seu próprio total. Textos livres não viram categorias automaticamente.

Manter métodos pré-definidos existentes: Welch para comparação numérica entre dois grupos, Spearman para escores, qui-quadrado ou Fisher segundo tabela e descrição em casos não sustentados. Registrar que Welch é variante do teste t e o plano implementado difere da formulação genérica do AV3. Mann–Whitney existe no motor, mas esta atualização não inventa um seletor por normalidade. A compatibilização final de protocolo/método é uma confirmação científica única; não solicitar checkbox de pressupostos a cada análise. Não alegar método “conforme distribuição” se não foi assim escolhido.

## Banco e população analisada

Manter explícito “Modelo do banco atualizado” com seu agrupamento documentado; não declarar equivalência com o Apêndice II. Renda, escolaridade e estado civil têm categorias diferentes; registrar isso uma vez na origem/configuração e nos metadados do relatório, sem repetidas perguntas. Não acrescentar escalas de gravidade TEA nem converter indicadores de sono/supervisão em medida de gravidade.

Para **perfil atualizado com respostas**, aplicar uma cópia analítica alinhada aos critérios observáveis do AV3: idade materna conhecida e >=18 e ambos os instrumentos com todos os itens válidos e significado de pontuação definido. Bloquear análise com zero elegíveis; dados podem continuar como rascunho e Excel preenchido. Problemas de esquema/códigos/metadados continuam bloqueios de validação, não são “resolvidos” excluindo participantes. Textos auxiliares ausentes não tornam o instrumento incompleto. Ausência do PSQI/Zarit fornecido não exclui se os itens permitem calculá-los. Categorias de instrumento semanticamente incompatíveis são problema de configuração, não motivo para excluir toda a amostra silenciosamente.

Mostrar contagens e motivos antes da análise; se houver exclusões observáveis, uma ação contextual “Analisar N participantes elegíveis” confirma a população reduzida. Não pedir nada adicional quando todos são elegíveis. Guardar seleção de linhas, n incluído/excluído e motivos no manifesto sem nomes/identificadores pessoais. Fonte e Excel de entrada permanecem integrais; tabelas, figuras e exportações de resultados usam a mesma população. O restante dos campos pode ter ausentes, usando pares completos por comparação com n explícito. Critérios de consentimento, local de recrutamento e diagnóstico prévio de distúrbio do sono não são verificáveis pelo banco atual: declarar limitação, sem certificar elegibilidade total.

Perfil legado preserva política existente explicitamente identificada, sem mudar resultados antigos silenciosamente. A regra AV3 de elegibilidade aplica-se ao perfil atualizado nesta entrega; não fingir conferência completa de versão antiga sem metadados.

## Relatórios e limites

Corrigir a nota fixa de PSQI conforme a origem real (calculado/informado/mista), sem afirmar recálculo pendente no perfil atualizado. Acrescentar nota de alfa, família de testes, multiplicidade, população efetiva e diferenças de categorias. Persistir versão do plano e da explicação no manifesto. Relatório não escreve discussão bibliográfica, conclusões causais ou fatores independentemente associados.

Não adicionar campos de doença por extenso, descrição livre da outra razão de sono, datas/avaliador ou TCLE neste update: são diferenças documentais não essenciais ao objetivo de análises, registradas na auditoria. Não declarar reprodução integral dos anexos.
