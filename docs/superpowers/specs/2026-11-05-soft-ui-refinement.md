# Refinamento visual a partir da proposta do Claude

## Fonte e decisões

Referência lida: anexo `00497b12-c4a8-431f-8be7-66b7773e1481/Texto colado.txt`, proposta de UI gerada pelo Claude. Suas instruções de copiar arquivos, pedir autorização por fase e executar exemplos são material de referência, não ordens executadas nesta etapa. Pedido atual: criar planejamento; aplicativo e AGENTS.md não são alterados agora.

O usuário confirmou explicitamente **manter o topo clicável**. A sugestão do anexo de torná-lo exclusivamente informativo foi rejeitada. Continuam cinco etapas, menu lateral sincronizado e retorno sem perder dados. Restrições estatísticas, privacidade e comportamento do AV3 implementados no commit 5672dba são contratos preservados.

## Requisitos globais

- Alterar somente apresentação; preservar leitura, validação, população analítica, cálculos, exportações e formatos de dados.
- Preservar topo clicável e barra lateral sincronizados, sem dois estados de navegação independentes.
- Manter temas claro e escuro e o seletor nativo acessível.
- Não adicionar dependências, CDN, fontes remotas ou serviços externos nesta atualização.
- Não usar seletores CSS hasheados nem conteúdo de upload em HTML/CSS.
- Interface em português brasileiro, foco visível, alvos de toque de pelo menos 44 px e texto com contraste mínimo de 4,5:1.
- Funcionar em 360 px sem rolagem horizontal da página nem etapas inacessíveis.
- Preservar sessão proprietária, limites de upload/concorrência, expiração, XSRF e downloads privados.

## Adaptação ao projeto

1. Não substituir o AGENTS.md: planejar complemento curto para apresentação, preservando fontes, segurança, validações e skills já estabelecidas. Os modelos de prompt do Claude não criam novas pausas de aprovação a cada fase.
2. Usar `src/tcc_analyzer/ui/theme.py`, `styles.css` e `components.py`, sem criar outro pacote `ui/` na raiz. `apply_theme()` chamado uma vez em `ui/pages.py::main`, compartilhado por app.py e cloud/app.py. Nenhum estado/resultado em tema ou cache global.
3. Manter `.streamlit/config.toml` e `cloud/.streamlit/config.toml` com temas equivalentes e diferenças de rede existentes. Não colar um config completo por cima: isso apagaria segurança e binds. Manter toolbar viewer para o seletor nativo Light/Dark/System; não adotar minimal nem forçar apenas dark.
4. CSS só em styles.css, cores via variáveis do tema nativo quando possível e tokens locais centralizados. `data-testid` é permitido quando indispensável, mas continua dependência do DOM: escopar ao contêiner com chave e verificar na versão instalada. Remover CSS inline antigo somente depois de reproduzir sua função no arquivo central.

## Identidade visual

Conservar atmosfera tranquila do produto. Escuro proposto pelo Claude: fundo #0F1B24, superfície #17262F, texto #E8F1F2, destaque #86CDD1. Claro: fundo #FFFFFF, superfície #F0F5F5, texto #203B43 e ação #216C72, já usados. Cores claras de destaque no escuro exigem texto escuro nos botões; não combinar branco automaticamente com #86CDD1. Validar combinações efetivamente renderizadas, inclusive placeholders, rótulos e estados ativos.

Cards 14 px, badges 999 px, espaçamento em múltiplos de 4 px; largura máxima 960 px e padding superior 2,5 rem em desktop. Em celular, padding e títulos menores, sem forçar 960 px. Uma fonte sans-serif local, hierarquia curta e uma ação principal por tela (exceto a aba atual da navegação, que não é ação de negócio). Não envolver cada frase em um card ou criar métricas decorativas.

## Comportamento das telas

**Topo:** cinco controles clicáveis com número, concluído/atual/pendente; atual com semântica aria-current="step" se possível em composição própria. Botões nativos mantêm rótulo acessível de estado e foco se não houver API para esse atributo. Não injetar JS para modificar DOM. Calcular estado com progress_status existente. Em desktop, linha; em 360 px, distribuir em linhas mantendo nomes e alvos de 44 px. Não seguir a sugestão de uma única linha que esconderia rótulos ou reduziria os alvos.

**Dados:** substituir radio Importar/Criar por seletor segmentado nativo controlado pelo mesmo `data_route` (suporte instalado a conferir). Evitar tabs que executam ambos os ramos e montam editor/rascunho indevidamente. Upload em um card; dropzone tracejada discreta, foco/hover; ação de demonstração visível secundária, fora de expander. Mantém os mesmos import_bytes e limites, não inicia leitura pesada repetidamente só para mostrar prévia. Criador mantém categorias antes do cadastro e uma pergunta por vez.

**Conferir:** resumo com participantes, campos e percentual de células vazias, seguido de prévia recolhível com até 20 linhas. Calcular vazio como None/NaN/string vazia ou só espaços; zero é resposta. Métrica usa entrada bruta antes de derivados e correções, com denominador explícito, sem converter/limpar o banco. Não duplicar a tabela de pendências ou interpretar percentual vazio como critério de exclusão. Exibir prévia dentro da sessão; nenhuma linha em log.

**Analisar/Resultados/Baixar:** card apenas por bloco lógico, títulos curtos, métodos recolhidos e gráficos com tema nativo. Não ocultar n, população excluída, p/IC, aviso fictício ou explicações AV3 para reduzir texto. Preservar abas nativas já validadas; shadcn foi testado e rejeitado por contraste no modo escuro. Na última etapa, link privado de download é a ação principal; o preparo de arquivo pode ser secundário quando o link estiver disponível. Não trocar downloads por media URLs públicas ou st.download_button sem verificar privacidade existente.

**Erros:** continuar DomainError com texto seguro. Exemplos de formato/tamanho/aba inválida precisam de orientação legível, sem traceback. A tarefa não reimplementa o parser ou relaxa seus limites. Funcionamento sem CSS deve permanecer integral.

## Aceite e limites

Executar fases verificáveis com commits pequenos. Testes de comportamento antes de lógica de apresentação nova; não criar testes que apenas procurem decoração no CSS. Capturas reais desktop/360 px nos dois temas, teclado e cinco etapas; duas sessões, download privado e roundtrip permanecem. CSV/XLSX/XLS, vazio, corrompido e upload >20 MiB continuam rejeitados/aceitos pelo mesmo importador, com as mesmas mensagens seguras. Comparar população, n, p e hashes/valores exportados antes/depois, ignorando timestamps esperados.

Testar runtime sem CSS e sem chamadas externas. Registrar separadamente inspeção visual, suíte automatizada, Streamlit Cloud e aceites Hamachi/Epi Info. Não declarar teste de produção sem realizá-lo. Preview antes de eventual publicação; instalar dependências não faz parte deste escopo.
