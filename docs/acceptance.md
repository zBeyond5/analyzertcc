# Validação do aplicativo

## Revisão de usabilidade — 2026-11-04

Esta seção atualiza os estados históricos abaixo para o perfil do banco atualizado. O formato legado permanece preservado.

- Entrada com importar/criar; criação começa pelas categorias e segue uma pergunta por vez. Excel preenchido privado, rascunho exportável/reimportável e nome opcional fora de estatísticas/relatórios.
- Dicionário e perguntas lidos das abas do arquivo. Conferência sem referência manual, sem correção obrigatória e sem checkbox de pressupostos. Perguntas de pesquisa com plano automático; download acessível após resultados.
- Perfil de 69 respostas com PSQI/Zarit calculados por funções Python; regras, fontes e fronteiras em methods.md. O aceite local do arquivo fornecido (simulado) gerou relatórios e exportações. Isso não substitui aceite científico pela responsável.
- Tema nativo Claro/Escuro/Sistema pelo menu ⋮ → Light / Dark / System; sem CSS de inversão e sem configuração global mutável por sessão. A implementação usa toolbar viewer para manter esse controle disponível.
- Revisão independente corrigiu atualização de escores após mudanças, preservação do aviso fictício ao retomar e cache de categorias ao reimportar.
- Evidências de navegador ficam em test-results/usability (ignorado pelo Git); suíte completa: **134 testes passaram em 57,93 s**, incluindo navegador real. Compilação sem erros e pip check sem dependências quebradas.
- Não foram realizados novos testes em cliente remoto Hamachi, Epi Info nem publicação desta revisão no Streamlit Cloud.

## Navegação e visualização — 2026-11-04

Validação final: `python -m pytest -q` → **146 passed in 111.06s**; `compileall` sem erros e `pip check` sem dependências quebradas. Preview local exibido antes do commit/push.

- Passo a passo com etapas concluídas, atual e próximas; atalhos laterais sincronizados. Retorno 3 → 2 → 1 → 3 preserva dados; alteração invalida resultados imediatamente.
- Cinco etapas dentro de 360 px, distribuídas em linhas. Sem título redundante na lateral; Nova análise pede confirmação contextual.
- Gráficos Plotly com n/denominadores dos mesmos pares da análise, somente variáveis necessárias e sem nomes/IDs no payload. Testes cobrem correspondência dos dados e ausência de identificadores.
- Abas nativas Resumo/Tabelas/Detalhes adotadas após o protótipo shadcn reprovar contraste no modo escuro. Plotly 7.1.0 fixado no projeto e lock.
- Navegador real: retorno, tabelas/detalhes/resumo, gráfico com dados, claro/escuro/celular, downloads privados, sentinelas por sessão, retomada do Excel e invalidação. Capturas em test-results/interface.
- Revisão corrigiu importação parcialmente aplicada após falha e alinhou liberação da navegação às demonstrações reconhecidas pelo pipeline.

## Registro histórico da primeira entrega

Verificação em Windows, Python 3.12.10, em 2026-11-04. A aplicação está instalada em `.venv`; versões exatas em `requirements.lock` e `requirements-dev.lock`.

## Evidência automatizada

Comando final executado:

```powershell
.venv/Scripts/python.exe -m pytest -q --tb=short --basetemp runtime/final-qa-2 -p no:cacheprovider
```

**Resultado: 95 passed in 43.62s.** Sem testes pulados. A pasta temporária explícita evita conflito de ACL entre o usuário de automação e a conta Windows. Em uma instalação normal, `python -m pytest -q` é suficiente.

Também executados: `python -m compileall -q src app.py` (sem erros) e `python -m pip check` (`No broken requirements found`).

Cobertura:

- Excel/CSV, estrutura real, tamanho/descompactação, cabeçalhos, fórmulas e preservação dos originais.
- Perfil com 75 campos, legenda pendente, novos códigos confirmados, alterações reversíveis e limites dos instrumentos.
- Banco fictício: 30×75, zero vazios, IDs distintos, PSQI_G 4/26, Zarit somado em 30/30 e faixas 2/8/16/4; idade média 37,4.
- Descritivas, métodos, zeros, tabelas esparsas, missing, grupos mínimos, constantes, correlações, IC e reamostragem reproduzível.
- DOCX/PDF legíveis, tabelas numéricas, CSV/XLSX round-trip, acentos e texto potencialmente interpretável como fórmula.
- Tokens independentes, tentativa de leitura com outro proprietário, caminhos inválidos, duas análises simultâneas, recusa de terceira, expiração e recuperação de órfãos.
- Scripts PowerShell: configuração local, proposta de Firewall sem aplicação, rejeição de IP/caminhos inválidos, interface ausente e sintaxe.
- Servidor HTTP local real e Chrome 157: duas sessões independentes processam bases distintas e baixam ZIPs; primeira mantém IDADE_M=34, segunda recebe a alteração fictícia para 99. Cada ZIP contém somente os oito artefatos da própria execução. Links são dados locais, sem endpoint compartilhado de relatório. Alterar configuração invalida a revisão/exportação anterior.

## Conferência visual

Interface conferida também em 360 px, sem rolagem horizontal da página. Revisadas as telas no navegador e as três páginas do PDF fictício renderizadas em imagem: tabelas legíveis, cabeçalhos repetidos, sem cortes ou sobreposição. DOCX validado estruturalmente e reaberto por python-docx; sua paginação específica no Microsoft Word não foi inspecionada. PDF é gerado localmente com ReportLab, dispensando LibreOffice.

## Condições científicas e de implantação

O aplicativo está funcional para demonstração e para bancos cujas legendas sejam conferidas explicitamente no editor. Não confundir os seguintes itens com os testes automatizados:

| Item | Estado |
| --- | --- |
| Uso local em localhost, cinco passos e exportações | Verificado |
| Soma Zarit, faixa PSQI e ponto de corte informado | Verificados com a base fictícia |
| Significado dos códigos de renda/escolaridade e outros campos | Não inferido; exige confirmação documentada no aplicativo |
| Recálculo dos sete componentes PSQI | Bloqueado: versão/manual não confirmado nas fontes |
| Compatibilidade CSV/XLSX por reimportação Python | Verificada |
| Importação em Epi Info instalado no Windows de destino | Não executada; roteiro em epiinfo-import.md |
| Acesso por cliente Hamachi Windows remoto | Não executado; exige o cliente e a rede de implantação |
| Restrição efetiva do Firewall e teste negativo de rede externa | Não executados; nenhuma regra do sistema foi alterada |

O servidor disponibilizado nesta entrega escuta apenas em **127.0.0.1:8501**. A implantação remota usa os scripts restritivos documentados em `hamachi-setup.md`. Não foram configurados túneis públicos, nuvem ou port forwarding.

## Decisões de implementação

- Streamlit nativo, funções Python e um gerenciador de trabalhos: sem backend adicional, banco de dados ou fila distribuída.
- Perfil original permanece em rascunho científico; a demonstração usa códigos neutros e não presume uma legenda a partir das frequências.
- PSQI informado é a origem explícita do desfecho; nenhum algoritmo clínico desconhecido foi inventado.
- PDF local direto em vez de conversão Word/LibreOffice. Os dois formatos partilham as mesmas tabelas e números.
- Welch ANOVA mantém a correção padrão: F=162/7 na microbase de teste, corrigindo a referência F=27 do plano.
- Limpeza integrada ao processo e ao reinício: não foi criado um segundo mecanismo independente de descarte.
- Revisão independente dos módulos de integração identificou limites numéricos, escores incompletos, denominador de terapias, direção/n dos grupos, edição de códigos e invalidação de resultados; corrigidos e cobertos por testes.

Os números fictícios são referências funcionais e não conclusões científicas. A liberação para dados reais depende das confirmações científicas, éticas e de implantação descritas acima.


## AV3 — 2026-11-05

Implementado: catálogo materno/infantil agrupado, interpretação estrita de p <0,05 por comparação, estimativas/IC/n junto do resultado e notas coerentes com a origem efetiva PSQI/Zarit. Legado preservado. Perfil atualizado usa critérios observáveis de idade e instrumentos completos com exclusão contextual confirmada, fonte integral e população única em figuras/tabelas/exportações. Nenhuma exclusão resolve erro de esquema/código.

Verificação final: **166 passed in 93.36s**, incluindo navegador desktop/360px, temas, navegação, relatórios e isolamento. Compilação passou; pip check sem dependências quebradas. Novas regressões cobrem fronteiras de p (inclusive floats adjacentes), método na população elegível, origem mista/informada e questionário incompleto com total informado. DOCX/PDF e banco exportado conferidos por leitura automática. Revisão independente identificou quatro falhas e todas foram corrigidas com regressões.

Não houve nova aprovação científica da responsável, teste externo Hamachi/Epi Info ou publicação no Streamlit Cloud. Welch/métodos e categorias agrupadas continuam exigindo alinhamento metodológico único com o AV3. Nenhuma conclusão causal ou regressão foi acrescentada. Preview local em 127.0.0.1:8503; a coleta ética não é certificada pelo software.


## Refinamento visual suave — 2026-11-05

Tema/CSS centralizados no pacote UI; topo clicável e menu lateral mantidos. Importar/Criar usa seletor segmentado nativo, demonstração secundária visível, upload em card e resumo da entrada bruta com percentual de células vazias. Zero permanece resposta e a métrica não modifica o banco nem define exclusões. Download mantém mecanismo privado e ganha destaque quando pronto. CSS integra o pacote distribuível; a ausência do arquivo de estilos não impede chegar ao ZIP.

Validação final: **170 passed in 121.11s**, incluindo navegador real. Compileall passou e pip check não encontrou dependências quebradas. Matriz visual: cinco etapas × claro/escuro ×1366/360px; capturas em test-results/soft-ui (ignoradas no Git). Confirmados alvos de etapa >=44px, ausência de rolagem horizontal, foco por Tab/Shift+Tab e contraste computado >=4,5:1 em títulos, etapa ativa e opções selecionadas. A revisão independente encontrou contraste insuficiente no escuro; corrigido com cores de texto estáticas por tema e regressão de navegador. Dropzone tracejada validada na versão instalada.

Regressões conferem alternância de modo preservando rascunho/dono, retorno entre etapas, atualização e exportação de sentinelas separadas (34/99), downloads data-URL sem /media público, roundtrip do Excel preenchido e execução até o download com CSS ausente. As suítes existentes de parser, critérios AV3, p/estimativas, relatórios e segurança permaneceram verdes. Diff confirma ausência de alterações nos módulos de cálculo, população, parsing, jobs ou exportadores.

Limites desta rodada: não foi realizado novo upload de um arquivo XLS binário válido nem novo aceite de produção Streamlit Cloud/Hamachi/Epi Info. CSV/XLSX, erros e limites seguem testes existentes; não houve instalação de dependências ou publicação. Não se declara auditoria WCAG completa de cada célula/estado desabilitado: foram verificados controles, foco, pares de cores e telas mencionados. Preview local em 127.0.0.1:8504.

## Relatórios compreensíveis — 2026-11-05

Vocabulário compartilhado nos resultados, gráficos, perguntas e tabelas, preservando perguntas personalizadas e códigos de máquina. PDF/Word ilustrados; Excel de resultados com glossário e dicionário com nome de leitura. Relatório completo com sumário/páginas reais e links internos, listas de tabelas/figuras e siglas usadas; material parcial para artigo sem sumário/estrutura de monografia. Nenhuma promessa de conformidade UNEB/ABNT.

Evidência automatizada antes da revisão final: suíte completa com 192 testes verdes; regressão adicional de fonte Unicode compartilhada com dois PDFs simultâneos, RED (duas renderizações concorrentes) → GREEN (renderização serial da fonte). Erro de contraste das legendas ao mudar o tema foi reproduzido no navegador (1,305:1) e corrigido preservando o estilo nativo. Novo teste também reproduziu e corrigiu título separado da tabela. Expectativa antiga de texto de inferência foi atualizada para a explicação atual, sem mudar a condição científica testada.

Navegador real via Playwright/Chrome já instalado: fluxo completo, ZIP nos dois modelos, duas sessões com sentinelas distintas, 360/1366px, claro/escuro, foco/contraste e retorno às etapas. URLs de dados pessoais não foram publicadas; downloads continuam pela sessão. Troca de modelo preservou resultados, expiração, hashes/ZIP; falha simulada de geração preservou os arquivos anteriores. Agent-browser CLI não está disponível neste ambiente; não se instalou ferramenta nova para repetir a capacidade existente.

PDFs reais: ambos os bancos declarados fictícios, todos os 28 cruzamentos disponíveis, nos dois modelos. Conferidos limites da página, destinos do sumário, imagens e páginas renderizadas: legado completo50/artigo33; atualizado completo49/artigo32. Folhas de contato de todas as páginas e inspeções em tamanho legível em test-results/readable-reports/qa-final. Teste separado com 100 comparações não omite seções e fica dentro de64MiB. Preview padrão atualizado:18 páginas no completo (inclui mapa técnico de categorias) e7 no material para artigo. Números são demonstrações, não achados científicos.

Limitação concreta: DOCX foi conferido por conteúdo/OOXML, imagens, cabeçalhos de tabelas e campos nativos, mas o renderizador local falhou por ausência de LibreOffice. Não se declara inspeção visual do Word; sumário/listas exigem atualização dos campos no Word. Normas específicas do curso/periódico, aceite científico, produção Streamlit Cloud e clientes externos Hamachi/Epi Info continuam sem novo aceite nesta rodada. Originais e alteração independente em scripts/start_hamachi.ps1 foram preservados.


Revisão independente final concluída: três achados importantes reproduzidos antes da correção e cobertos por regressões. Identidade de grupos neutros agora deriva do domínio declarado do perfil e é preservada mesmo quando faltam pares; o apêndice contém código ↔ identificação de categoria. Rótulos de gráficos são texto literal, sem MathText. Categorias longas têm espaço por linhas efetivas e teste de ausência de sobreposição, com pelo menos9pt no caso de quatro rótulos de aproximadamente300caracteres no tamanho final. Sumário longo também recebeu regressão para começar na primeira página, sem capa quase vazia. Nenhum achado menor foi adiado.

Pontos que a revisão independente não certifica: renderização visual/atualização dos campos do Word sem renderizador; validação científica/normativa e clientes externos; alteração independente do Hamachi. A revisão leu código e executou reproduções focadas; não repetiu toda a suíte ou a inspeção das páginas, cujas evidências são da execução principal.

Verificação final após todas as correções: **197 testes aprovados em180,27s**, incluindo navegador real; compileall e pip check sem erros. Aplicativo iniciado com o código atual em127.0.0.1:8505, saúde HTTP200. Commits locais; nenhuma publicação ou push nesta rodada.
