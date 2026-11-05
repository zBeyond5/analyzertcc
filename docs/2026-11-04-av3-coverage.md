# Cobertura do projeto AV3 pelo aplicativo

Leitura em 2026-11-04 de `fontes/PROJETO TCC - AV3 FINAL.docx`, comparada ao código do commit cec8706. Auditoria documental e de código, sem alterar o programa ou os originais. Não confundir os 146 testes da entrega anterior com novo aceite científico de conformidade com o projeto.

## Conclusão

O aplicativo cobre a organização do banco, os instrumentos e o núcleo da comparação sobrecarga/sono. Ainda não cobre todas as associações previstas no AV3. Principal ajuste de escopo necessário: ampliar o catálogo simples de perguntas para os fatores já coletados, sem pedir configuração estatística ao usuário.

| Exigência e localização no AV3 | Cobertura atual | Limite verificado |
| --- | --- | --- |
| Objetivo, seção 5: qualidade do sono e fatores associados | Parcial | Sono/sobrecarga cobertos; demais fatores restritos no catálogo |
| Banco digital numericamente codificado, 7.6 | Coberto | Excel/CSV, dicionário, perguntas, cadastro e códigos editáveis por sessão |
| Formulário materno e da criança, 7.5 e Apêndice II | Parcial | Principais campos presentes; modelo segue Excel atualizado, com diferenças do formulário original |
| PSQI: sete componentes, total 0–21, corte >5, 7.5 | Implementado | Regras/fontes/limites documentados em methods.md, testes; aprovação da versão pelo responsável científico é distinta de validação matemática |
| Zarit: 22 itens, total 0–88 e quatro faixas, 7.5 | Implementado | Códigos renumerados preservam correspondência canônica; significado alterado não deve gerar escore padrão |
| PSQI como contínuo e boa/má qualidade, 7.6 | Coberto | Escore, classificação e comparações principais em ambos os formatos |
| Frequências absolutas/relativas, média, mediana e dispersão, 7.6–7.7 | Ampla, não integral | Tabelas de perfil, clínica e instrumentos; alguns textos livres e itens individuais não aparecem nas tabelas prontas |
| Qualidade do sono × sobrecarga, 7.7 | Coberto | Média por grupo, associação entre classificações e correlação entre escores |
| Qualidade do sono × demais variáveis independentes, 7.6–7.7 | Parcial importante | UI oferece apenas sobrecarga, rede de apoio e alteração do sono infantil; idade, renda, escolaridade, filhos, trabalho noturno, doenças, ansiedade/depressão, terapias, despertares e supervisão não têm perguntas disponíveis nessa tela |
| Qui-quadrado, t de Student ou Mann–Whitney, 7.7 | Parcialmente alinhado | Motor tem qui-quadrado/Fisher, Welch e Mann–Whitney; UI simplificada não ativa Mann–Whitney conforme uma regra de distribuição. Comparação principal usa Welch, variante do teste t, e não t com variância combinada |
| Nível de significância de 5%, 7.7 | Parcialmente explícito | Valores de p são calculados/exibidos; relatório não declara sistematicamente o limiar 0,05. Não chamar método pelo menor p; deixar a convenção documentada |
| Possível regressão múltipla, 7.7 | Não implementado, fora do MVP autorizado | Texto diz “poderão”; não adicionar automaticamente. Sem regressão, não afirmar fatores independentemente associados |
| Conferência de instrumentos completos, 7.2 e 7.4 | Parcial | Rascunhos e respostas ausentes são preservados; sem imputação e sem escore incompleto. A política por pares completos não equivale à exclusão de questionários incompletos prevista no projeto |
| Elegibilidade, 7.2 | Parcial | Aviso para idade materna <18; banco não comprova diagnóstico prévio de distúrbio do sono, consentimento ou todas as condições de recrutamento |
| TCLE, CEP, recrutamento presencial e confidencialidade, 7.4 e 7.8 | Fora da automação científica | Isolamento e downloads privados ajudam proteção; não comprovam consentimento, aprovação ética ou regularidade da coleta |

## Divergências concretas de formulário

- Estado civil: AV3 distingue solteira/casada ou união estável/divorciada/viúva; Excel atualizado agrupa com/sem companheiro. Não é possível reconstruir quatro estados a partir desses dois grupos.
- Escolaridade: AV3 tem sete níveis; Excel usa não escolarizado/baixa/média/alta. A equivalência detalhada não foi declarada.
- Renda: AV3 usa até 1 / 1–2 / 2–4 / acima de 4 salários; Excel usa até 1 / acima de 1–2 / acima de 2–3 / acima de 3. Não recodificar automaticamente como se fossem faixas iguais.
- Apêndice II pergunta qual doença crônica após Sim. O modelo69 possui apenas indicador de doença, sem campo específico para seu nome.
- Anexo I tem descrição textual de “outra razão” para dormir mal; banco registra DIF_DORM como frequência, sem esse texto. O item PARCEIRO não participa do escore global. Esses limites não devem ser confundidos com fórmula incorreta do escore.
- Datas administrativas/avaliador do formulário não compõem o modelo analítico atual. Não são necessários ao cálculo, mas a planilha não representa reprodução documental integral dos anexos.

## Limites da hipótese

A hipótese (seção 6) fala em pior sono e maior gravidade das características clínicas/comportamentais. O banco permite investigar associações com os indicadores que realmente contém; não possui uma escala específica de gravidade do TEA. Não chamar esses indicadores de medida validada de gravidade. Não existe grupo de mães sem filhos com TEA neste banco; portanto a análise interna não demonstra diferença frente à população geral. O desenho transversal não comprova causa ou direção da associação.

## Ajustes pequenos prioritários

1. Ampliar perguntas de análise para os fatores de 7.6 já presentes, agrupados em mãe/criança. Preservar seleção consciente e registrar comparações exploratórias, sem executar dezenas silenciosamente ou selecionar por significância.
2. Alinhar uma vez o dicionário do banco com o Apêndice II e registrar a versão adotada; não pedir confirmação repetida em toda importação. Dados já agrupados não recuperam detalhe perdido.
3. Explicitar a política de elegibilidade/questionários incompletos antes de resultados científicos. Rascunhos continuam permitidos; uma exclusão analítica nunca deve apagar linhas nem ocorrer silenciosamente. Ausência em campo auxiliar não deve ser confundida com instrumento incompleto.
4. Documentar o plano de testes efetivamente usado (incluindo Welch, Fisher quando necessário e tratamento de tabelas esparsas), o limiar 0,05 e limites de inferência. Isso é diferente de implementar um seletor automático por normalidade.
5. Corrigir a nota fixa em `reporting.build_tables`: ainda diz “PSQI informado: recálculo ... pendente” mesmo no perfil atualizado que calcula PSQI. Manifesto e tela já reconhecem a nova origem, mas essa nota do relatório precisa acompanhar o perfil.

## Evidência de código

- `analysis_plan.py`: três perguntas disponíveis e construção das comparações.
- `statistics/selection.py` e `statistics/numeric.py`: recomendação de métodos, limites e cálculo.
- `scales.py`, `validation.py` e perfil `tea_maternal_sleep_updated_v1.yaml`: instrumentos, origem e consistência.
- `reporting.py`: grupos de tabelas, estatísticas e nota fixa de PSQI.
- `ui/create_sheet.py` e `data_entry.py`: entrada guiada, Excel preenchido e dicionário.

Nenhuma correção de código foi feita nesta auditoria. As lacunas acima não exigem trocar o backend nem transformar o aplicativo numa plataforma de pesquisa.
