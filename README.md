# Análise bivariada do TCC

Aplicativo local em português para importar Excel/CSV, conferir variáveis e instrumentos, executar cruzamentos e baixar relatórios Word/PDF, tabelas Excel e bancos para Epi Info.

## Abrir

No Windows, execute `Iniciar aplicativo.cmd` ou, no PowerShell:

```powershell
.\scripts\start_local.ps1
```

Abra **http://127.0.0.1:8501**. O servidor local escuta somente no computador anfitrião. O launcher remoto e as regras Hamachi estão em [docs/hamachi-setup.md](docs/hamachi-setup.md).

## Usar

1. Clique em **Experimentar dados fictícios** ou envie XLSX/XLS/CSV (até 20 MiB).
2. Confira os valores, dicionário, totais dos instrumentos e avisos. Correções exigem confirmação e podem ser desfeitas.
3. Selecione cruzamentos, confira os métodos e os pressupostos e execute.
4. Revise tabelas, estimativas, n efetivo, IC e limitações; confirme a revisão.
5. Prepare um arquivo individual ou o ZIP completo e clique no link de download.

A demonstração inclui 30 registros fictícios. Dados reais exigem confirmação da legenda numérica no próprio aplicativo. Códigos ausentes no exemplo podem ser acrescentados no editor do dicionário; nunca inferimos significado pelas frequências.

O PSQI fornecido é validado quanto à faixa e classificação; o recálculo dos sete componentes permanece bloqueado até confirmação da versão/manual do instrumento. Zarit é conferido pela soma dos 22 itens. O aplicativo não gera regressão ou conclusões causais.

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
