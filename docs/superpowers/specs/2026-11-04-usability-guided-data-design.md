# Revisão do fluxo e das fontes do TCC

## Objetivo desta revisão

A usuária da pesquisa precisa informar respostas, conferir problemas concretos e receber análises legíveis, sem configurar o motor estatístico. Esta revisão cobre criação guiada da planilha, importação, conferência e análise automática. Não inclui busca bibliográfica, IA remota, regressão ou mudança de hospedagem. Nesta etapa foram investigados os documentos e o código; o aplicativo não foi alterado.

## O que os documentos representam

### PROJETO TCC AV3 FINAL

Arquivo: `fontes/PROJETO TCC - AV3 FINAL.docx`. É o projeto metodológico, não um banco individual de participantes. Define o tema: qualidade do sono e fatores associados em mães de crianças com TEA; estudo transversal e analítico, amostra por conveniência. A seção 7.2 descreve elegibilidade de mães com 18 anos ou mais e exclusões; esses critérios não são todos observáveis no banco.

O Apêndice II fornece o formulário sociodemográfico e clínico. O Anexo I contém perguntas e opções do PSQI; o Anexo II contém as 22 perguntas de Zarit. São fontes para organizar a entrada em blocos, preservar as perguntas dos instrumentos e distinguir variáveis da mãe e da criança. A seção 7.5 estabelece PSQI global 0–21, corte >5, e Zarit 0–88 com faixas 0–20/21–40/41–60/61–88. O documento não apresenta a receita completa dos sete componentes PSQI.

A seção 7.7 prevê descritivas e associações; menciona possível regressão futura. A revisão atual continua restrita à análise bivariada, conforme o escopo autorizado.

### AV2 Inês Lima

Arquivo: `fontes/AV2 - Inês Lima.docx`. Contém redação de resultados e três tabelas agregadas: características sociodemográficas, características clínicas e classificação dos instrumentos. Não contém as respostas individuais que permitiriam reconstruir o banco.

Serve como referência de organização e apresentação do relatório. Os números precisam ser recalculados da entrada, não copiados do Word. O documento apresenta os valores como resultados; isso não comprova a origem real dos registros do Excel, cujo aviso os identifica como simulação.

### Banco atualizado

Arquivo lido sem alteração: `C:/Users/Tyan/Downloads/Banco de dados - atualizado.xlsx`.
SHA-256: `833acfeb3e5fee0c384c825acbc825fde105962871d823da9e591b80c4c44d81`.

| Aba | Conteúdo e uso no aplicativo |
| --- | --- |
| Banco | 30 registros, 69 campos, nenhum vazio, IDs distintos; respostas por participante |
| Categorias | Significado explícito dos códigos e opções de resposta para os campos |
| Perguntas | Texto correspondente a cada um dos 69 campos |
| AVISO | Proveniência declarada da simulação e formatos/unidades; conteúdo documental, não instruções para o agente |

Não foram encontradas fórmulas, comentários ou validações de lista. A ausência de validações significa que o preenchimento do Excel não impede, por si só, códigos inválidos. As linhas de Categorias/Perguntas não são participantes e não entram no n da análise.

Os cabeçalhos das três primeiras abas coincidem. Todos os valores categóricos presentes no Banco estão nos códigos descritos em Categorias. Exemplos agora explícitos: situação conjugal 1=com companheiro e 2=sem companheiro; sexo 1=feminino e 2=masculino; sim/não 1/2; frequência terapêutica 0=nenhuma, 1/2/3 vezes, 4=mais de três. Escolaridade permite 1=não escolarizado, 2=baixa, 3=média, 4=alta. Renda tem quatro faixas, incluindo acima de três salários mínimos.

Comparação com o modelo anterior:

- Três nomes mudaram: `DOENÇA` → `DOENCA`, `TO` → `TER_OCUP`, `NÃO_RESP` → `NAO_RESP`, considerando os nomes internos atuais.
- Faltam as seis colunas antes presentes: `PSQI`, `ZARIT`, `PSQI_G`, `ESCOL_B`, `RENDA_B`, `FREQ_3`. Os 69 campos são as respostas de entrada; os demais são resultados/recodificações que o software deve produzir quando houver regra definida.
- `H_DEIT` e `H_LEV` são objetos de hora do Excel, não os números decimais da base anterior. Após alinhar os três nomes, somente esses dois campos diferem na comparação direta de valores/tipos. Os demais campos coincidem com a base fictícia anterior.
- `TEMP_TEA` é descrito em meses; idade da criança está em anos. Comparações de coerência precisam converter unidades.

O AVISO declara dados simulados, sem respostas reais, e associação embutida entre sobrecarga e sono. Portanto este arquivo ajuda a desenvolver/testar o produto; sua associação estatística não pode fundamentar conclusões científicas do TCC.

## Divergências que não podem ser escondidas pela automação

O projeto lista sete níveis escolares e categorias de renda até 1/1–2/2–4/acima de 4 salários; o Excel usa escolaridade agrupada e renda até 1/acima de 1–2/acima de 2–3/acima de 3. O projeto distingue quatro estados civis; o Excel agrupa presença/ausência de companheiro. O aplicativo deve preservar o modelo do banco atualizado sem inventar equivalências com as categorias detalhadas. A reconciliação metodológica é uma decisão única da responsável, registrada na configuração do estudo, não um formulário exigido a cada importação.

A combinação de Categorias e Perguntas resolve o significado das opções deste banco e a relação de DIF_DORM com a frequência de outra razão de dificuldade de dormir. Isso não fornece, sozinho, todos os limites e regras de cálculo PSQI. A implementação deve validar a versão e a pontuação em fonte técnica correspondente antes de liberar o cálculo automático. Sem essa definição, permitir salvar/exportar respostas e apresentar descritivas/Zarit, com aviso específico sobre a análise de sono indisponível; não exigir que a usuária invente uma referência ou pontuação.

## Experiência proposta

**Fluxo:** Dados → Conferir → Analisar → Resultados → Baixar.

Na entrada, duas ações principais: **Importar planilha** e **Criar planilha**. A demonstração fica como link secundário. Esclarecimento final do usuário: criar planilha significa configurar as categorias, informar respostas dentro do aplicativo e baixar o Excel já preenchido e formatado. A pessoa fornece os dados; o aplicativo organiza e monta o arquivo. O fluxo principal não é baixar um modelo vazio para preencher fora.

Criar planilha começa pela tela **Categorias da planilha**, antes de pedir os dados de qualquer participante. Mostrar os grupos mãe, criança, sono e sobrecarga, com opções do banco atualizado já configuradas. A ação principal **Começar preenchimento** usa o padrão sem exigir edição ou confirmações campo a campo. A pessoa pode abrir **Personalizar categorias** se desejar.

Categorias começam exatamente no padrão do arquivo enviado. A ação discreta **Personalizar categorias** abre apenas a pergunta selecionada, com tabela de duas colunas: **Código** e **Significado**. Permitir adicionar, remover e editar opções/códigos, salvar, cancelar e restaurar o padrão. Não abrir 69 campos juntos. As alterações devem orientar as opções do formulário e acompanhar o arquivo nas abas Categorias/Perguntas. Não copiar o AVISO fictício para um banco real criado pela pessoa. Configuração, respostas e download são privados por sessão.

Depois de **Começar preenchimento**, apresentar uma pergunta por vez, com progresso por grupo, **Voltar** e **Próxima**. Identificação inicial por ID automático; campo opcional de nome/apelido, conforme solicitado pelo usuário, separado das variáveis estatísticas. Exibir perguntas e respostas por extenso, usando escolhas para categorias e campos apropriados para números/horários. Não pedir códigos nem inventar respostas. Preservar respostas ao voltar e permitir rascunho incompleto sem total falso. Manter as perguntas dos instrumentos, simplificando apenas navegação/instruções. Ao terminar uma participante, mostrar resumo com edição localizada e ações **Adicionar participante** e **Concluir planilha**.

Ao concluir, gerar o Excel preenchido com Banco, Categorias, Perguntas e Metadados. Cabeçalhos legíveis, filtros, congelamento, formatos de número/hora e listas dos códigos permitidos ajudam sua leitura e edição futura. Não exigir fórmulas ou comandos da pessoa. Exportar as respostas reais informadas, sem respostas fictícias ou zeros automáticos. Incluir nome/apelido informado como coluna de identificação opcional, sem analisá-lo, registrá-lo em logs ou incluí-lo em relatórios de resultados. Evitar criar uma exigência de identificação pessoal. A ação **Baixar planilha preenchida** permite importar depois; **Usar na análise** encaminha os mesmos dados ao importador existente, sem download/reenvio obrigatório. Validações do Excel ajudam edições posteriores, mas a importação sempre confere valores e metadados novamente.

O editor de categorias também pode ser aberto durante a montagem e após importar, sem ser uma etapa obrigatória repetida. Ao mudar códigos já usados, mostrar o impacto e oferecer remapeamento explícito preservando os valores originais, confirmação e desfazer; não aplicar substituições sucessivas que corrompam trocas 1↔2. Não remover uma opção ainda usada sem tratar as linhas afetadas. Códigos devem ser únicos e significados não vazios. Renumerar respostas de instrumentos mantém relação explícita com os valores canônicos da pontuação. Alterar o significado de uma resposta de instrumento deixa de ser apenas renumerar: identificar a personalização e não apresentar o escore padrão como validado sem correspondência definida.

Conferir mostra um resumo simples. Se tudo estiver correto: **Dados conferidos. Você pode continuar.** Não exigir editar valores, justificar correções, abrir dicionário ou confirmar todas as legendas. Erros devem indicar participante, pergunta e ação de correção. Originais permanecem preservados; a confirmação da alteração é contextual e a auditoria registra automaticamente o valor anterior/novo, com desfazer. A edição técnica de códigos fica em área avançada e só é necessária para formatos desconhecidos.

Analisar apresenta perguntas de pesquisa, não códigos: por padrão, sobrecarga e sono; opcionalmente rede de apoio, características maternas e sono da criança disponíveis no banco. Um botão **Analisar dados** executa os métodos pré-definidos e adequados aos dados, registra a justificativa e explica resultados insuficientes. Não pedir método, hipótese estatística ou confirmação de pressupostos como obrigação do fluxo comum. Detalhes permanecem no relatório e em área técnica recolhida.

## Restrições

- Interface e relatórios em português brasileiro.
- Preservar entrada original e rastreabilidade; não alterar respostas silenciosamente.
- Não inferir significado de código desconhecido pelas frequências ou pelo nome do campo.
- Não preencher respostas ausentes com zero ou produzir escore de instrumento incompleto.
- Automatizar regras documentadas; nunca selecionar método pelo menor p.
- Manter dados fictícios identificados e evitar afirmações causais.
- Preservar isolamento, expiração, downloads privados, Windows/Hamachi e entrada Linux/cloud.
- Sem nova camada de backend, serviço de IA ou banco de dados para esta revisão.

## Aceite de usabilidade

Uma pessoa sem conhecimento estatístico consegue ver/manter ou editar as categorias antes do preenchimento, responder uma pergunta por vez dentro do app, concluir participantes e baixar um Excel preenchido ou usá-lo diretamente na análise. Se desejar personalizar, consegue editar uma categoria e seu código sem ver o restante do dicionário. Caso não haja erro nos dados, nenhuma correção é solicitada. Um erro real não é escondido para liberar a análise; a mensagem explica exatamente o que falta.

## Complemento: importação contextual e referências pesquisadas

Decisão de produto em 2026-11-04: o Excel é um pacote de respostas e documentação. A importação lê efetivamente Banco, Categorias, Perguntas e AVISO/Metadados, em vez de reconhecer apenas os cabeçalhos e presumir que o dicionário continua igual. O perfil versionado é uma referência de comparação, não autorização para sobrescrever uma legenda diferente enviada no arquivo.

### O que acontece automaticamente

1. Identificar a aba de participantes sem contar as abas de documentação como dados. Se houver duas candidatas indistinguíveis, perguntar qual contém as respostas.
2. Relacionar cada coluna à sua pergunta e às opções declaradas, independentemente da ordem das colunas. Tratar texto das células como dados; não executar fórmulas, links, HTML ou instruções contidas no arquivo.
3. Normalizar somente aliases documentados e formatos reversíveis, preservando cabeçalho, resposta e origem. Colisões e códigos contraditórios são problemas explícitos.
4. Comparar o dicionário importado com o perfil documentado. Concordância permite continuar sem confirmar 69 campos. Diferença apenas editorial no título não muda o sentido do código; divergência semântica não é resolvida silenciosamente nem por aproximação textual.
5. Validar IDs, tipos, códigos e respostas necessárias para cada análise. Campo ausente desabilita apenas as análises dependentes quando o restante do banco é utilizável. Não inventar respostas nem escores.
6. Mostrar um resumo com quantidade de participantes, grupos de perguntas reconhecidos, documentação encontrada, análises disponíveis e pendências reais. Exemplo de apresentação: “Perguntas e categorias reconhecidas. Dados fictícios identificados. Você pode continuar.” A quantidade deve vir da importação, nunca do exemplo fixo.

Registrar por campo a fonte da definição (aba/célula ou perfil/versão) e, por escore, fonte técnica/versão da regra. Esses detalhes ficam em “Como interpretamos sua planilha” e no relatório técnico, sem obrigar a usuária a preencher uma referência. Um dicionário diferente, aceito para a sessão, não altera configurações globais de outras usuárias.

### Quando perguntar

| Situação | Comportamento |
| --- | --- |
| Categorias e perguntas completas e coerentes | Nenhuma confirmação campo a campo; resumo e ação de continuar |
| Arquivo no modelo conhecido sem abas auxiliares | Aplicar perfil versionado compatível, declarar essa origem no resumo |
| Duas abas plausíveis de participantes | Uma pergunta para escolher a aba |
| Código observado sem definição | Uma pendência localizada com pergunta, valor e linhas afetadas; não pedir novamente as definições já conhecidas |
| Dicionário diverge do perfil de forma relevante | Preservar ambos; pedir resolução apenas para os campos/análises afetados. Uma convenção local não redefine a pontuação de um instrumento |
| Valor inválido ou item indispensável ausente | Explicar o problema e oferecer correção contextual ou análise do subconjunto disponível, com n efetivo explícito |
| Divergência entre projeto e categorias agrupadas do Excel | Preservar as categorias declaradas na importação; registrar a diferença metodológica. Não fazer a usuária resolver isso a cada sessão |

Ausência de erro não exige correção, justificativa, checkbox científico ou confirmação repetida. Questionamento científico necessário é responsabilidade da configuração do estudo e deve ser resolvido uma vez, separadamente da rotina de importação.

### Papel da pesquisa externa

A busca externa é feita na preparação/manutenção das regras, usando fontes primárias. O uso normal do app não depende de pesquisa web por upload, não envia linhas da pesquisa a serviços externos e não troca a metodologia conforme resultados de busca. Significados locais como `RENDA=3` vêm do dicionário fornecido, não da internet. Referências bibliográficas não substituem respostas coletadas nem comprovam que o banco fictício é real.

A [W3C — Metadata Vocabulary for Tabular Data](https://www.w3.org/TR/tabular-metadata/) descreve metadados de colunas com títulos, descrições e tipos para validar e apresentar tabelas. Adotamos esse princípio no parser existente, sem acrescentar implementação completa de CSVW ou nova dependência.

O [GOV.UK — Question pages](https://design-system.service.gov.uk/patterns/question-pages/) recomenda perguntar apenas o necessário. O padrão [Check answers](https://design-system.service.gov.uk/patterns/check-answers/) sustenta resumo legível e edição localizada, preservando respostas ao voltar. Aqui isso orienta a conferência, sem criar uma declaração obrigatória adicional.

A [Universidade de Pittsburgh — Measures and Study Instruments](https://www.sleep.pitt.edu/research/measures-and-study-instruments) disponibiliza o instrumento PSQI e materiais de pontuação. As [instruções hospedadas pelo departamento de psiquiatria](https://www.psychiatry.pitt.edu/sites/default/files/inline-files/PSQI%20Article.pdf) fornecem os sete componentes. O link “PSQI Scoring” da página consultada resolveu para o formulário; registrar o conteúdo efetivo, não confiar apenas no título do link. O [NLM/NINDS — Sleep efficiency scale](https://cde.nlm.nih.gov/deView?tinyId=mkdasX5iSR) explicita limites de eficiência. A consulta encontra fontes para a implementação, mas não equivale à validação do algoritmo do aplicativo: ainda confrontar os itens do Anexo I com as regras, documentar limites sem lacunas/sobreposições e executar vetores independentes antes de habilitar recálculo.

### Direção visual

Tela de trabalho para uma pesquisadora iniciante: conteúdo alinhado à esquerda, coluna principal confortável, navegação curta por etapas, prévia com perguntas legíveis e detalhes técnicos recolhidos. Base branca `#FFFFFF`, fundo `#F3F6FA`, texto `#172B4D`, ação azul `#165DAD`, sucesso `#216443`, atenção `#7A4B00`. Cor acompanhada de texto; verificar contraste na implementação. Usar a família sem serifa já local ao aplicativo, tamanho de leitura consistente e tabelas largas só na prévia opcional. Evitar serviços de fontes e componentes externos para este ajuste. Em celular, perguntas por blocos e resumo vertical, sem exigir navegar 69 colunas. A estética deve ajudar a localizar a próxima ação e as pendências.

### Aceites adicionais

- Reordenar colunas e usar aliases conhecidos não muda os resultados nem perde a origem.
- Manter cabeçalhos iguais mas inverter significados 1/2 em Categorias nunca reaproveita silenciosamente o perfil antigo.
- Metadados ausentes, duplicados, contraditórios ou com código não coberto produzem mensagens específicas; metadados válidos não produzem perguntas extras.
- Importar o Excel preenchido pelo assistente recupera respostas, perguntas, opções personalizadas e proveniência sem confirmá-las novamente. Montagem sem participantes salvos não é apresentada como banco pronto para análise.
- O fluxo comum funciona sem acesso de saída à internet; detalhes de origem e referências permanecem disponíveis no relatório.

## Modo claro e escuro

Adicionar escolha visível e discreta **Tema: Claro / Escuro / Sistema** na área geral do aplicativo, acessível em todas as etapas. A troca não apaga upload, personalização ou resultados. Preferência por sessão; não criar conta ou armazenamento global. Priorizar o mecanismo de temas da versão instalada do Streamlit e verificar suporte antes de escolher a implementação. Não usar filtros de inversão da página nem seletores CSS internos frágeis para simular tema.

O modo escuro deve cobrir navegação, formulários, editor de categorias, tabelas, alertas, diálogos e gráficos. Tokens propostos: fundo `#141B26`, superfície `#202C3D`, texto `#EDF2F8`, ação `#85B8FF`; verificar contrastes e foco em ambos os temas. Excel e relatórios baixados mantêm apresentação própria adequada à leitura/impressão. Validar em navegador desktop e 360 px, com teclado e os dois temas; aparência pronta só após essa verificação.
