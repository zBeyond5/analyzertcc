# Análise Bivariada

Aplicação local Python 3.12 + Streamlit para o TCC, hospedada em Windows 11 e acessível por Hamachi. Interface e relatórios em português brasileiro.

## Antes de trabalhar

- Ler a tarefa pertinente em `docs/superpowers/plans/2026-11-04-tcc-statistical-analyzer.md` e a conferência em `docs/superpowers/specs/2026-11-04-source-review.md`. Não reler o plano inteiro em cada alteração pequena.
- Preservar `fontes/` e `fixtures/source/`. O banco de 30 registros é fictício; não apresentar seus números como resultados científicos.
- Confirmar legenda dos códigos e versão/pontuação PSQI antes de implementar interpretações dependentes. Não adivinhar pelas frequências das tabelas.

## Skills e economia

- Usar **ponytail** nas tarefas de código: menor solução completa, reutilizando bibliotecas existentes e funções diretas.
- Usar **context7:context7-mcp** para a API/configuração de biblioteca em dúvida; consultar documentação oficial da versão usada e reaproveitar a consulta na tarefa. Nunca enviar dados da pesquisa.
- Em frontend, sempre usar **frontend-design** instalada de **anthropics/skills**, respeitando as instruções explícitas do usuário e os contratos existentes do projeto.
- Usar **find-skills** quando faltar uma capacidade; conferir primeiro as skills instaladas. Não instalar nem atualizar pacotes de skills sem necessidade da tarefa.
- Execução nativa por padrão. Agentes/subagentes somente se uma tarefa independente ou revisão específica economizar tempo; não delegar automaticamente cada tarefa nem duplicar investigação.
- Abrir o `SKILL.md` instalado apenas das skills pertinentes. Não empilhar workflows que não ajudem a entrega atual.

## Implementação e usabilidade

- Um processo Streamlit e núcleo estatístico sem dependência da UI. Sem serviços, filas distribuídas, banco de dados ou abstrações para usos futuros.
- Priorizar o fluxo: importar → validar → configurar cruzamentos → conferir resultados → exportar. Mostrar próxima ação, progresso, n efetivo, método e avisos compreensíveis.
- Preferir widgets nativos acessíveis, foco visível, tabelas legíveis e funcionamento por teclado. Aparência deve facilitar a análise.
- Não sobrescrever entrada: correções exigem confirmação, desfazer e auditoria. Não imputar respostas nem escolher teste só por normalidade; sem regressão no MVP.
- Preservar isolamento por sessão, limites de upload/concorrência, expiração, XSRF e acesso somente por Hamachi. Simplificar não permite remover essas proteções.
- Sem dados reais no Git/logs, cache global de resultados, histórico compartilhado ou serviços externos. Artefatos só podem ser obtidos pela sessão proprietária.

## Verificação e entrega

- Testar o comportamento alterado; para lógica nova, demonstrar falha antes da correção. Não criar testes que apenas repitam implementação ou decoração.
- Rodar os testes focados primeiro; suíte completa na integração. Não repetir checks já verdes sem nova mudança ou motivo.
- Registrar separadamente confirmações científicas, testes automatizados e aceites reais Windows/Hamachi/Epi Info. Não declarar compatibilidade ou isolamento externo sem a prova correspondente.
- Responder brevemente com o que mudou, verificação e pendências concretas. Não expandir o escopo sem necessidade.
