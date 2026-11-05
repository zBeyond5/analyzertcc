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
