# Análise bivariada do TCC

Aplicativo local em português para importar Excel/CSV, conferir variáveis e instrumentos, executar cruzamentos e baixar relatórios Word/PDF, tabelas Excel e bancos para Epi Info.

## Abrir

No Windows, execute `Iniciar aplicativo.cmd` ou, no PowerShell:

```powershell
.\scripts\start_local.ps1
```

Abra **http://127.0.0.1:8501**. O servidor local escuta somente no computador anfitrião. O launcher remoto e as regras Hamachi estão em [docs/hamachi-setup.md](docs/hamachi-setup.md).

## Usar

1. **Importar planilha** lê as respostas e as abas Perguntas/Categorias automaticamente.
2. **Criar planilha** permite manter ou ajustar categorias, responder uma pergunta por vez e baixar o Excel preenchido. É possível salvar um rascunho e importá-lo para continuar depois.
3. **Conferir** mostra pendências reais; edição de categorias e correções ficam recolhidas. Um banco válido não exige preencher referências ou justificar alterações inexistentes.
4. **Analisar** apresenta perguntas de pesquisa, com métodos definidos pelo programa.
5. **Resultados → Baixar** entrega Word, PDF, tabelas e pacote ZIP privado.

Em Dados, escolha **Importar planilha** ou **Criar planilha** no seletor. Na conferência, o resumo mostra participantes, campos e células vazias do arquivo original; a prévia fica recolhida. Zero não conta como vazio.

Use o passo a passo no topo ou as abas do projeto à esquerda para navegar. Etapas concluídas mostram ✓ e permitem voltar; modificar respostas invalida os resultados dependentes. Em Resultados, as abas Resumo/Tabelas/Detalhes incluem gráficos interativos com os mesmos dados da análise.

Para alternar claro/escuro/sistema, abra o menu **⋮ → Light (claro) / Dark (escuro) / System (sistema)**. A escolha é nativa do navegador e não apaga respostas.

O perfil atualizado usa as 69 respostas documentadas e calcula PSQI/Zarit com regras e limites registrados em docs/methods.md. O formato legado continua aceito com seus totais fornecidos. Perguntas/códigos desconhecidos não recebem significados inventados. Dados fictícios permanecem identificados ao exportar e retomar no assistente. Nenhuma IA ou consulta web é usada na execução.

## Instalar em outro ambiente

Python 3.12, Windows 11:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.lock
```

As versões testadas estão fixadas no lock. A instalação requer acesso aos pacotes ou uma pasta local de wheels preparada pelo administrador; o processamento do banco não usa serviços remotos.

## Testar

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-dev.lock
npx --yes agent-browser install
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m compileall -q src app.py
.venv\Scripts\python.exe -m pip check
```

O teste de navegador inicia um servidor em porta local livre, abre dois contextos e compara seus downloads. O Chrome instalado pelo agent-browser deve estar disponível no perfil do usuário. Scripts de rede são testados sem alterar o Firewall.

## Privacidade e limites

Sem login adicional: só permita membros autorizados na rede Hamachi. XSRF e CORS permanecem ativos; sem diretório estático, histórico global ou cache compartilhado de bancos. Arquivos temporários são privados por execução e expiram 60 minutos após a geração; limpeza periódica a cada 5 minutos. Downloads vencidos são recusados imediatamente; trabalhos ativos não são removidos. Reinício remove trabalhos órfãos. Cópias baixadas, buffers do navegador e backups/logs do sistema operacional exigem gestão separada.

Dados de entrada não são sobrescritos. Texto livre fica fora das exportações por padrão; ID exportado é sequencial por trabalho. Isso não garante anonimização. Verifique autorização ética antes de usar dados reais.

## Validação

Resultados e limites: [docs/acceptance.md](docs/acceptance.md). Métodos: [docs/methods.md](docs/methods.md). Importação Epi Info: [docs/epiinfo-import.md](docs/epiinfo-import.md). O aplicativo não depende de Epi Info instalado; a compatibilidade na instalação Windows de destino só é comprovada após teste real.


## Análises conforme AV3

Escolha sobrecarga/sono e, se precisar, abra outros fatores da mãe/criança. Cada comparação mostra p, interpretação pelo critério de 5%, método, pares completos e estimativas. p não é desvio padrão nem prova de causa. Se houver questionários incompletos ou participantes fora do critério observável, o aplicativo mostra a contagem e pede confirmação apenas para analisar o grupo elegível; o Excel original continua integral.
