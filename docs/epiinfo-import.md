# Importação dos dados exportados no Epi Info 7

O aplicativo funciona sem Epi Info instalado. A exportação gera dados tabulares e dicionário; não cria um projeto `.prj`, não altera formulários Epi Info e não usa suas tabelas internas como armazenamento.

**Estado da compatibilidade:** round-trip dos arquivos pode ser verificado pelos testes Python; importação real na instalação Windows do Epi Info permanece **não verificada** até executar o roteiro abaixo. Não confundir os dois aceites.

## Arquivo Excel

1. Baixar `epiinfo_dados.xlsx` e `dicionario.xlsx` da própria sessão.
2. No Epi Info 7, abrir **Classic Analysis** e escolher **Data → Read (Import)**.
3. Selecionar o formato Excel 2007 (`.xlsx`), escolher o arquivo e marcar a primeira linha como nomes dos campos.
4. Selecionar a aba de dados apresentada pelo arquivo. Conferir nomes e quantidade de registros.
5. No **Visual Dashboard**, selecionar a fonte de dados Excel e a mesma aba; conferir contagem e tipos novamente.

Se o driver Excel exigido pela versão instalada não estiver disponível, usar o CSV; não concluir que o arquivo está compatível apenas porque o Python o reabre.

## Arquivo CSV

O padrão de exportação é UTF-8 com BOM, delimitador ponto e vírgula (`;`) e decimal vírgula. Conferir os parâmetros no `manifesto.json` da execução. No **Read (Import)**, selecionar texto delimitado, indicar o delimitador real, qualificador de texto aspas duplas e os tipos das variáveis de acordo com o dicionário.

O driver de texto do Epi Info pode depender da versão e da configuração regional do Windows. Se essa instalação exigir CSV com vírgula e decimal ponto, registrar a exigência e gerar essa variante localmente, preservando a fonte e registrando a conversão; não alterar silenciosamente o CSV original. Números, códigos e horários devem continuar numéricos. Campos ausentes são ausentes, não zero nem texto `nan`.

Texto que possa ser interpretado como fórmula de planilha é tratado de forma segura pelo exportador. Conferir no manifesto eventuais escapes. Texto livre e identificadores da entrada não são exportados por padrão. O ID exportado é sequencial por execução, sem promessa de anonimização absoluta.

## Roteiro de aceite real

Usar somente os registros fictícios e uma microbase artificial com missing/acentos. Registrar data, versão Epi Info, arquitetura/driver e parâmetros regionais aceitos, sem capturas de participantes reais.

- Importar tanto XLSX como CSV e conferir 30 registros, IDs sequenciais distintos e ordem/códigos dos campos autorizados.
- Conferir os horários decimais: 23.5 é 23h30 e 0.25 é 00h15; não interpretar como número de dias Excel.
- Conferir acentos, delimitador, aspas, missing e tipos em uma microbase artificial.
- Calcular a média de `IDADE_M` no banco fictício: 37,4, com DP amostral aproximadamente 6,392883974955386.
- Comparar a tabela 2×2 artificial `[[8,2],[1,5]]`: Fisher bilateral 0,034965034965034975, OR amostral 20 e razão de prevalências 4,8, respeitando a orientação exposição/desfecho.
- Comparar métodos de IC e definições do p bilateral antes de interpretar divergências; métodos diferentes não garantem ICs idênticos.

Registrar sucesso ou falha no documento de aceitação do aplicativo. Disponibilidade de um arquivo para download não comprova interoperabilidade.

Referência: [guia oficial histórico Epi Info 7 do CDC](https://stacks.cdc.gov/view/cdc/23495). O suporte oficial foi encerrado; o aplicativo mantém seu cálculo e exportações independentes do programa.
