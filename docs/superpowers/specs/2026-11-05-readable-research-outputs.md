# Resultados e relatórios compreensíveis

## Problema observado e escopo

Fonte: trecho fornecido em `6645046e-beca-484a-be71-880c61dd4aa0/Texto colado.txt`, com PSQI_G, ZARIT_CLASS, ESCOL, DEPRE, ACOMP_TEP, n/p e notas repetidas. Comparado ao código da versão da0f66a. O anexo é exemplo de saída, não instrução nem evidência científica; seus números pertencem à demonstração fictícia e não são resultados reais do TCC.

Planejar apresentação editorial do relatório e dos resultados, não novos testes estatísticos, interpretação clínica por IA, discussão bibliográfica ou alteração de dados. Cálculos AV3, população elegível, pares completos, p estrito e proteção por sessão permanecem. Sem dependências novas: ReportLab, python-docx, Matplotlib e Plotly existentes são suficientes. Não usar serviços externos ou conversão remota de arquivos.

## Requisitos globais

- Apresentação em português brasileiro, com nomes compreensíveis e termos explicados no contexto.
- Não alterar dados, testes, população, valores de p, estimativas, intervalos ou orientação das comparações.
- Não inferir significado de categoria desconhecida ou personalização clínica pelo código/frequência.
- Não afirmar causalidade, importância prática pelo p, elegibilidade total ou aprovação científica inexistente.
- Preservar aviso de dados fictícios, resultados não significativos, análises indisponíveis e limitações relevantes.
- Sem IA em execução, novas dependências, serviços externos ou cache global de dados/figuras.
- Preservar sessão proprietária, limites de trabalho/artefatos, expiração e downloads privados.
- Códigos internos e cabeçalhos de arquivos de reimportação permanecem estáveis; traduzir a apresentação, não o banco.

## Vocabulário único

Usar um título curto para leitura e a pergunta/definição completa do perfil como contexto. Cobrir todos os campos dos perfis antigo/atual, aliases, derivados, categorias, métodos, medidas, famílias, motivos de indisponibilidade e avisos. Exemplos: DEPRE → Depressão (diagnóstico informado); ESCOL → Grau de escolaridade; ACOMP_TEP → Acompanhamento terapêutico da criança; PSI → Psicologia; PSQI → Pontuação da qualidade do sono; PSQI_G → Classificação da qualidade do sono; ZARIT → Pontuação de sobrecarga; ZARIT_CLASS → Nível de sobrecarga. Primeira ocorrência/glossário nomeia o instrumento completo e sua sigla. Não reescrever as perguntas validadas do formulário de coleta.

Os títulos curtos conhecidos não podem apagar perguntas/categorias personalizadas: quando a pergunta não corresponde à definição conhecida, usar sua descrição declarada, com quebra de linha, e indicar personalização quando relevante. Categorias 1/2 aparecem como seus significados efetivos apenas se documentados. Perfil legado sem legenda mostra “Categoria sem definição confirmada” com código no apêndice técnico, jamais supõe Sim/Não. Campo desconhecido sem descrição recebe “Variável sem descrição” e referência técnica, sem inventar doença, escala ou unidade. ID/nome/apelido/ocupação e outros textos identificáveis não entram nas narrativas ou nas imagens.

Não fazer substituição global de strings no PDF pronto: reconstruir a apresentação a partir de objetos estruturados. Tokens como PSI dentro de PSQI ou TO dentro de texto não são unidades de substituição. Notas científicas livres do motor não devem ser analisadas por regex para recuperar médias ou estimativas; gerar frases a partir de resultados/dados declarados. Notas originais podem ser preservadas em apêndice técnico, claramente identificado e secundário.

## Termos e casos numéricos

| Termo técnico | Apresentação e cuidado |
| --- | --- |
| n | Participantes com respostas completas nesta comparação; separar total da fonte, elegíveis e pares efetivos |
| p | Valor de p (critério estatístico do projeto); ajuda explica limite <0,05, sem dizer probabilidade de a relação ser verdadeira |
| DP | Desvio padrão: variação das respostas ao redor da média; não confundir com significância |
| Média/mediana | Valor médio/ponto central das respostas ordenadas; identificar qual foi calculado |
| Q1/Q3 | Faixa que contém os 50% centrais das respostas, com limites por extenso |
| IC95% | Intervalo de confiança de 95%: incerteza da estimativa sob o método; não faixa contendo 95% das participantes nem probabilidade de 95% sobre parâmetro fixo |
| Diferença de médias | Mostrar grupos e ordem explícitos, unidade correta; sinal não determina relevância clínica |
| Correlação | Grau e direção de associação entre escores; só afirmar positiva/negativa quando coeficiente válido; não implica causa |
| RP/OR | Razão de prevalências/razão de chances, com evento, grupo comparado e referência declarados; não chamar OR de risco ou probabilidade |
| Welch, Fisher, qui-quadrado, Spearman, Mann–Whitney, Kruskal, ANOVA/Pearson | Nome técnico em detalhes, frase curta do que a comparação avalia, sem alegar método executado quando resultado foi apenas descritivo |
| Principal/complementar/exploratória | Pergunta central/análise complementar/outro fator investigado, preservando família técnica no apêndice |
| Ausentes/sem inferência | Quantidade sem respostas necessárias ou motivo específico, não zero ou “sem relação” |

Exemplo de texto, com os números do anexo somente como demonstração: “Participaram desta comparação 30 pessoas com respostas completas. A comparação da sobrecarga média entre os grupos de qualidade do sono não atingiu o critério estatístico do projeto (valor de p: 0,096). Isso não prova ausência de associação.” O resultado complementar p=0,002 refere-se a outra comparação (associação entre escores): não fundir seus p, selecionar o menor ou declarar uma conclusão universal para sono/sobrecarga. Mostrar coeficiente/estimativa e intervalo quando existirem; não inventar os que o trecho não fornece.

Uma razão concreta substitui “confira os avisos”: “Há poucas participantes em algumas categorias para aplicar este teste com segurança; apresentamos as quantidades e os percentuais.” Para variância nula: “As respostas de um grupo não variaram; este método não calculou significância.” Com zero pares: “Não há respostas completas para esta comparação.” Comparação descritiva não ganha inferência pelo gráfico.

Usar números em pt-BR, unidades documentadas (idade em anos; tempo de diagnóstico em meses; horas/minutos de sono), precisão coerente, sem NaN/None/inf nos textos. p usa interpret_p existente, incluindo fronteira 0,05 e valores adjacentes, sem converter indisponível em 0. Não exibir “p=Não calculado”; escrever “Teste estatístico não calculado” com motivo. Evitar repetição da mesma limitação após cada linha: uma nota geral e avisos locais específicos bastam.

## Estrutura editorial dos relatórios

PDF e Word devem compartilhar conteúdo e figuras, em layout próprio para leitura/impressão clara (não copiar tema escuro do app):

1. Abertura concisa: título da pesquisa, data, natureza do relatório e aviso fictício quando aplicável. Sem nome de participante, capa vazia ou identidade institucional inventada.
2. Resumo da base: fonte total, elegíveis, excluídos por critérios observáveis, respostas faltantes por comparação e escores calculados/informados. Não rotular hash ou profile_id como introdução principal.
3. Caracterização: três blocos atuais com títulos por extenso; frequências, percentuais e medidas com denominadores/unidades. Totais de terapias múltiplas não precisam somar 100%; explicar.
4. Perguntas centrais: um bloco por comparação com título compreensível, gráfico, legenda explicativa, leitura curta, participantes, estimativa/IC e valor de p explicado. Descrição dos instrumentos/cortes sem diagnóstico ou julgamento de gravidade TEA.
5. Outros fatores: resumo organizado por mãe/criança e, para todas as comparações executadas, bloco compacto com resultado, gráfico aplicável e motivo quando não houver inferência. Não omitir resultados não significativos nem criar ranking pelo menor p.
6. Limitações e “Como ler este relatório”: desenho transversal, multiplicidade, amostra/ausências, categorias agrupadas e instrumentos; glossário curto dos termos realmente usados.
7. Apêndice técnico: código ↔ nome, famílias/métodos/fontes/versões, orientação de grupos, detalhes/avisos não traduzíveis, hash/manifesto. Códigos aqui são intencionais, não vazamento para leitura principal.

Não apresentar médias por grupo como prova de diferença, nem exibir marca de significância sem teste. Não incluir bibliografia não consultada ou conclusões geradas por IA. Texto determinístico e rastreável aos dados.

## Gráficos estáticos

Figuras do PDF/Word são geradas com Matplotlib Agg a partir dos mesmos dados elegíveis e pares completos usados na comparação, sem Kaleido/Chrome novo/CDN. Plotly permanece interativo na tela. Ambos consomem dados estruturados comuns, não imagens de tela. Não alterar medidas para conseguir um gráfico mais bonito.

- Categórica × numérica: distribuição por grupo com legenda simples explicando mediana/faixa central, número em cada grupo; com observações insuficientes, mostrar pontos/descritiva e avisar, sem caixa enganosa.
- Categórica × categórica: barras com contagens e/ou percentuais, denominadores explícitos e categorias rotuladas; múltiplas categorias com cor e padrão/posição, legíveis em escala de cinza.
- Numérica × numérica: dispersão dos pares, eixos com unidades, sem nomes/IDs e sem reta de regressão ou novo teste.
- Sem pares/variância constante/tabela esparsa: gráfico descritivo se sustentado, aviso específico; vazio não gera imagem branca ou layout quebrado.

Uma figura por comparação executada quando há pares representáveis, em ordem estável, sem duplicar figura igual por página. Até 100 comparações (limite atual): renderização sequencial, fechar figuras, PNGs em memória por vez e nenhuma persistência pública/cache. Validar orçamento de artefatos/concorrência e falhar com orientação clara se não couber; não truncar silenciosamente o relatório.

## Formatos cobertos

| Saída | Tratamento |
| --- | --- |
| Tela: perguntas, resumo, tabelas, detalhes e gráficos | Mesmo vocabulário e leitura; códigos só em área técnica recolhida |
| PDF e Word | Relatório editorial com figuras, legendas, resumo e apêndice |
| Tabelas Excel | Abas legíveis, cabeçalhos e medidas explicados; incluir glossário sem alterar números |
| Banco Excel/CSV para reimportação/Epi Info e Excel preenchido | Preservar cabeçalhos/códigos, acrescentar/remeter ao dicionário conforme contrato atual, sem renomear campos destrutivamente |
| Dicionário | Código, nome de leitura, pergunta, opções e unidade/proveniência; manter versão compatível |
| Manifesto/auditoria/ZIP | Chaves técnicas estáveis e privacidade preservadas; apontar versão de apresentação. ZIP contém as saídas com mesmo significado |

## Qualidade visual e segurança

A4, margens de 50 pt, coluna útil calculada da página; corpo 11 pt, tabelas/legendas >=9 pt, títulos claros, cores sóbrias e contraste suficiente em branco e cinza. Contagem de larguras igual ao número real de colunas e soma dentro da área útil. Hoje a tabela bivariada tem seis colunas e render_pdf fornece cinco larguras: corrigir especificamente esse caso, sem encolher tudo até ficar ilegível. No Word, repetir cabeçalhos de tabela e impedir que títulos/legendas fiquem sozinhos na página. Dividir tabelas longas sem cortar células; não manter tabela inteira num bloco indivisível.

Escapar texto em Paragraph ReportLab e rótulos HTML Plotly; títulos personalizados não são markup executável. Fonte Unicode incorporada usando uma fonte local já distribuída com Matplotlib (licença e disponibilidade conferidas), sem depender de Arial/Calibri do Windows. Mesmo conteúdo no Windows/Linux. PNGs privados em memória, sem nomes/campos identificáveis em metadados de imagem. Sem novos artefatos públicos ou necessidade de alterar isolamento de jobs.

Aceite exige PDFs reais renderizados e páginas inspecionadas, não apenas extração de texto; Word também deve ser renderizado/verificado com ferramenta local disponível, com limitação explicitada se não houver. Testar títulos enormes, categorias longas/personalizadas, acentos, <>&, 1/0/100 comparações, grupos desbalanceados, efeito/p/IC ausentes e dados fictícios. O conjunto padrão e todos os fatores do AV3 devem gerar arquivos legíveis. Não declarar padrão ABNT sem requisitos específicos nem “trabalho científico final” sem revisão da pesquisadora.

## Complemento solicitado: sumário e apresentação acadêmica

Incluir sumário automático com títulos, níveis e páginas reais, além de listas de tabelas e figuras quando houver esses elementos. Sumário não é resumo dos resultados. PDF deve resolver paginação em múltiplas passagens e incluir links internos; DOCX usa estilos de títulos e campos nativos atualizáveis, com limitação de atualização no Word explicitada. Números de página do PDF e do Word podem diferir; cada arquivo usa sua paginação, nunca uma lista de páginas fixa compartilhada.

Incluir seções numeradas, títulos/legendas/fontes de tabelas e figuras, lista de siglas usadas e paginação consistente. Em figuras, fonte “Elaboração do aplicativo a partir do banco informado”, identificando simulação quando aplicável; não inventar autoria humana, coleta ou instituição.

Oferecer duas opções: “Relatório completo” (`editorial`) e “Material para o artigo” (`article`). O relatório completo contém a estrutura explicativa acima e sumário/listas. O material para o artigo contém procedimentos estatísticos efetivamente executados e resultados, tabelas/figuras numeradas e respectivas notas essenciais, sem capa de monografia, sumário ou apêndice técnico. A leitura didática e a rastreabilidade continuam disponíveis no relatório completo. Rotular o material como conteúdo parcial para integrar o artigo, sem inventar introdução, discussão ou alegação de que o TCC está concluído.

Ambos usam inicialmente o layout editorial documentado (A4, margens de50pt, corpo11pt e tabelas/legendas >=9pt), identificado como escolha de apresentação, sem selo ABNT/UNEB. Fonte, margens, espaçamentos e numeração permanecem separados dos dados e cálculos. Um futuro template institucional ou de periódico exige valores e fonte efetivamente conferidos; não é motivo para bloquear a exportação legível atual nem criar um terceiro modo não validado. Não instalar editor de templates complexo nem expor dezenas de configurações.

Referência consultada em2026-11-05: [normalização da Biblioteca da UFES](https://biblioteca.ufes.br/normalizacao). Edições identificadas e limites dessa evidência constam da [conferência de fontes UNEB/Fisioterapia](2026-11-05-uneb-physiotherapy-source-review.md). Identificação de edição não equivale à leitura integral de norma ou comprovação de adequação institucional.

O entregável permanece um relatório de análise pronto para leitura/inclusão no TCC, não um TCC completo: não criar revisão de literatura, resumo científico do trabalho inteiro, discussão, conclusões gerais, folha de aprovação ou referências não usadas. Capa/folha de identificação somente quando previstas no modelo escolhido e com dados fornecidos da pesquisa/autora; nunca exigir nome das participantes. Modelos de artigo e monografia têm estruturas diferentes. Registrar essa distinção, sem acrescentar um gerador completo de trabalhos acadêmicos.

## Instituição confirmada pelo usuário

Curso: Fisioterapia; instituição: Universidade do Estado da Bahia (UNEB). O AV3 situa a pesquisa no Campus I, Salvador; não generalizar regras de outros cursos/campi.

Pesquisa oficial em2026-11-05 encontrou a modalidade artigo tanto no regulamento do PPC anterior quanto nos trechos indexados do [PPC atual de Fisioterapia](https://dcv.salvador.uneb.br/projeto-pedagogico-fisio). A conferência vinculada registra exatamente como cada evidência foi obtida. Não foi possível ler integralmente os documentos UNEB por erros403/502/conexão; não afirmar leitura integral ou vigência específica da turma. O regulamento geral, Resolução CONSEPE2.212/2023, atribui regras internas aos colegiados; o PPC atual o referencia. Não foi localizado template de Fisioterapia com valores exatos de formatação.

Portanto: implementar os dois destinos acima, sem exigir da usuária decisões de normalização a cada análise. Exigências específicas do colegiado ou de um periódico escolhido permanecem uma adaptação documental futura, sem perguntas adicionais para permitir o fluxo básico. Nenhuma informação de periódico, aprovação ética, autoria ou coleta é inferida da planilha.

Usar o checklist STROBE de estudos transversais como apoio à completude dos resultados: população efetiva, ausências, limites de categorias e estimativas/intervalos existentes. O aplicativo não controla o estudo inteiro; não declarar conformidade integral com STROBE, ajuste por confundidores inexistente ou confirmação científica. Não acrescentar novos testes estatísticos para preencher itens do checklist. Pesquisa de referências acontece no desenvolvimento; nenhuma chamada à internet/IA é necessária para gerar os relatórios.
