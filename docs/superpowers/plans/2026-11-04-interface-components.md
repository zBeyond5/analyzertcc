# Interface: navegação do projeto, componentes e gráficos

## Objetivo e escopo

Planejamento solicitado antes de alterar o aplicativo. Enriquecer a experiência existente sem acrescentar configurações estatísticas, serviços, projetos persistentes ou etapas obrigatórias. A barra esquerda permanece e passa a navegar pelas abas do projeto, conforme esclarecimento do usuário; remover o título redundante “Análise do TCC”. Não transformar a barra apenas em botão para iniciar outra análise.

## Decisão sobre bibliotecas

| Recurso | Decisão | Uso concreto |
| --- | --- | --- |
| Streamlit nativo 1.66.1 instalado | Manter como base | Upload, formulário de respostas, editor de categorias, tabelas e seletor nativo de tema |
| streamlit-shadcn-ui | Prototipar e adotar seletivamente após aceite técnico | Navegação lateral, escolha Importar/Criar e abas de resultados, com estados claros |
| Plotly | Adotar para gráficos de resultados | Visualizar distribuição de sobrecarga por sono, proporções por categoria e relação entre escores |
| streamlit-elements | Não adicionar nesta revisão | Material UI e dashboards arrastáveis não resolvem uma necessidade atual; evitar dois sistemas visuais de componentes |

Nenhuma das três bibliotecas adicionais está instalada no ambiente atual. Não instalar nesta etapa de planejamento. Verificar uma versão publicada compatível, fixar versões e atualizar locks somente na implementação. Não adotar a API da branch main como se já fosse a versão publicada. Se um controle shadcn não atender teclado, tema ou estado por sessão, manter seu equivalente nativo.

## Fontes consultadas

- [streamlit-shadcn-ui, documentação do projeto](https://github.com/ObservedObserver/streamlit-shadcn-ui): componentes e integração; validar a versão distribuída contra Streamlit instalado.
- [streamlit-elements, documentação do projeto](https://github.com/okld/streamlit-elements): Material UI, Monaco, Nivo e composição de dashboards. Recursos considerados, sem aplicação necessária neste escopo.
- [Streamlit st.plotly_chart](https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart): integração nativa, tema Streamlit e eventos de seleção. Não usar Chart Studio ou serviço remoto.
- [Plotly: hover e formatação](https://plotly.com/python/hover-text-and-formatting/): limitar dados enviados à figura; ocultar tooltip não equivale a remover dados da figura. Não incluir nomes, IDs ou texto livre na estrutura do gráfico.

## Direção visual

Conservar a identidade suave já aprovada: branco #FFFFFF, superfície #F0F5F5, texto #203B43, ação #216C72; escuro com fundo #141F29 e texto #EBF2F4. Uma família sem serifa local, títulos menores, respiro, bordas suaves e sombra discreta somente onde houver hierarquia real. Sem multiplicar cartões, números decorativos ou animações automáticas. Gráficos são o destaque visual na tela de resultados; formulários permanecem calmos e focados.

```text
Barra do projeto            ✓ Dados ━ ✓ Conferir ━ ③ Analisar ─ ④ Resultados ─ ⑤ Baixar
                           Etapa 3 de 5

                           Conteúdo da aba atual
  Dados                    Título curto
  Conferir                 Próxima ação / conteúdo
  Analisar                 ...
  Resultados
  Arquivos

  Nova análise
```

No celular, a barra lateral recolhe usando o comportamento nativo. Conforme ajuste posterior do usuário, manter o topo como passo a passo visual em vez de remover sua navegação: substituir os rádios pequenos por etapas numeradas conectadas, com botões de área confortável. A lateral dá acesso às abas do projeto e o topo mostra avanço; ambos refletem a mesma etapa e o mesmo estado. “Abas do projeto” significa seções do trabalho da sessão atual; não criar catálogo persistente de pesquisas ou contas. No fluxo superior, usar o rótulo direto “Baixar” na quinta etapa.

### Comportamento do passo a passo

- **Concluída:** número acompanhado/substituído por ✓, conexão preenchida e rótulo legível; clicável para retornar.
- **Atual:** número em destaque e identificação “Etapa X de 5”; não usar apenas cor para distingui-la.
- **Próxima:** número e nome visíveis, com ligação discreta. Só liberar avanço quando seus pré-requisitos estiverem atendidos; não pular a execução da análise.
- **Futuras:** visual neutro e indicação acessível de indisponibilidade quando aplicável, com desabilitação funcional.
- Exemplo na etapa 3: Dados e Conferir concluídos; Analisar ativo; Resultados e Baixar à frente. Pode voltar ao 1/2 e retornar ao 3 sem perder respostas.
- Visitar uma etapa não a conclui. Dados conclui após preparação/importação; Conferir depende dos bloqueios reais; Analisar depende dos artefatos gerados; Resultados conduz ao download. Arquivo preparado não prova que o usuário terminou de baixá-lo.
- Voltar apenas para olhar preserva resultados. Alterar respostas, categorias ou plano invalida resultados/arquivos dependentes e atualiza os estados do topo e da lateral juntos.
- Em 360 px, preservar nomes, ordem e área de toque com quebra organizada ou apresentação compacta da etapa atual e suas vizinhas; não deixar os passos virarem cinco rádios minúsculos ou criar rolagem horizontal da página.
- Foco visível, operação por teclado e indicação semântica de etapa atual/concluída; testar contraste claro/escuro.

## Etapas de implementação

### 1. Navegação lateral e redução de ruído

Arquivos: `ui/pages.py`, `ui/state.py`, `tests/test_ui.py`, `tests/test_browser.py`.

- [ ] Testar primeiro que Dados → Conferir → Analisar → Resultados → Arquivos preserva upload, respostas, categorias e resultados. Acesso a uma seção ainda indisponível explica a próxima ação sem erro genérico.
- [ ] Implementar navegação lateral e substituir os rádios do topo pelo passo a passo descrito acima, com etapas concluídas, atual e próximas. Usar uma única fonte de estado, sem dois índices de navegação independentes. Não simular desabilitação por CSS.
- [ ] Testar na etapa 3: 1/2 concluídos e clicáveis, 3 destacado, próximas identificadas; voltar sem editar não perde dados nem relatórios; editar invalida as conclusões dependentes; passos não são concluídos por simples visita.
- [ ] Remover título redundante “Análise do TCC” e textos técnicos permanentes. “Nova análise” fica separada ao final e pede confirmação se houver trabalho na sessão.
- [ ] Evitar os três títulos empilhados no criador: um título de contexto e a pergunta atual são suficientes. Ajuda permanece disponível sob demanda.
- [ ] Rodar os testes focados e conferir desktop/360 px antes de seguir.

### 2. Protótipo shadcn pequeno e verificável

Arquivos: `ui/pages.py`, pequeno módulo `ui/components.py` apenas se necessário para callbacks compartilhados; manifests/locks de dependências e testes de UI.

- [ ] Confirmar API da versão publicada com documentação correspondente; instalar versão fixa compatível e atualizar locks existentes de forma consistente.
- [ ] Testar navegação/retorno antes de substituir controles: chaves estáveis, reruns e duas sessões não podem trocar estado nem repetir ações.
- [ ] Aplicar shadcn à navegação e às abas de apresentação somente onde seu comportamento passar os testes. Preservar widgets nativos no preenchimento e na edição de categorias; não reescrever o assistente inteiro para mudar aparência.
- [ ] Conferir temas claro/escuro, herança do tema em componentes, foco visível e teclado. Não criar um segundo seletor de tema independente.
- [ ] Confirmar que os componentes não requisitam recursos externos em execução nem criam URLs públicas de arquivos privados. Se falhar, usar controle nativo para aquele ponto.

### 3. Resultados com Plotly

Arquivos: novo `ui/charts.py`, `ui/pages.py`, testes de gráficos; manifests/locks de dependências.

- [ ] Criar testes com microbases artificiais: n/denominadores e categorias devem coincidir com tabelas; ausentes e categoria única devem receber tratamento explícito. A estrutura da figura não pode conter nome, ID ou texto livre.
- [ ] Construir figuras com somente colunas necessárias, da cópia privada da sessão; nunca usar cache global. Reutilizar o mesmo subconjunto completo de cada comparação e explicitar n.
- [ ] Pergunta principal: distribuição da sobrecarga por qualidade do sono. Proporções de categorias com denominador explícito e dispersão PSQI/Zarit ficam em visualizações complementares. Sem tendência de regressão ou novo cálculo de significância.
- [ ] Mostrar um gráfico principal por vez, títulos e legendas em português, detalhes ao passar o mouse e resumo textual acessível. Configuração de gráfico não muda o plano de análise nem os testes científicos.
- [ ] Organizar resultados em “Resumo”, “Tabelas” e “Detalhes”, mantendo acesso claro aos arquivos. Não acrescentar filtro que mude silenciosamente os números exportados.
- [ ] Usar `st.plotly_chart` e tema alinhado ao aplicativo. Relatórios Word/PDF mantêm seus dados e formatação; exportar novos gráficos científicos é outro requisito, não adicionar dependência de renderização nesta revisão.

### 4. Integração e aceite

- [ ] Browser real: importar banco atualizado → conferir → analisar → alternar abas de resultados → baixar; criar planilha → voltar pelas abas → retomar sem perdas.
- [ ] Tema claro/escuro e 360 px: barra recolhível, componentes legíveis, gráficos responsivos, sem rolagem horizontal na página. Demonstrar por capturas reais.
- [ ] Duas sessões com dados diferentes, downloads privados, expiração e invalidação após alteração continuam cobertos. Nomes/IDs não aparecem no JSON das figuras.
- [ ] Comparar números de tabelas/relatórios com o motor anterior para entradas idênticas. Rodar testes focados primeiro e suíte completa, compileall e pip check na integração.
- [ ] Registrar dependências efetivas e eventuais controles mantidos nativos. Entregar preview local antes de qualquer publicação.

## Estado da execução

Implementado em 2026-11-04. Navegação lateral sincronizada com passo a passo por botões nativos, retorno sem perda e bloqueios reais. Em 360 px os cinco botões quebram em linhas, sem corte horizontal. Plotly 7.1.0 adotado, com gráficos apenas das comparações executadas e sem identificadores pessoais.

Protótipo real de streamlit-shadcn-ui 1.4.0 passou interações, mas as abas ficaram com baixo contraste no tema escuro. Aplicada a alternativa prevista: abas nativas Resumo/Tabelas/Detalhes, sem incluir shadcn nas dependências do projeto. Streamlit Elements continua sem necessidade neste escopo.

Preview local aberto antes do commit/push; capturas reais em test-results/interface (fora do Git). Navegador validou desktop/celular, claro/escuro, abas, dados de gráficos, retorno, invalidação, isolamento e downloads. Regras científicas e backend permanecem os mesmos desta versão.

Validação final integrada: 146 testes passaram em 111,06 s, incluindo navegador. Compilação e dependências verificadas.
