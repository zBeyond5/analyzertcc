"""Portuguese reading vocabulary; analytical field names and values stay intact."""
from functools import lru_cache
from dataclasses import dataclass
import math
import numpy as np
import pandas as pd
from .interpretation import interpret_p
from .profiles import ALIASES, load_profile, load_updated_profile

FIELD_TITLES={
    'ID':'Identificação','IDADE_M':'Idade da mãe (anos)','SIT_CONJ':'Situação conjugal',
    'ESCOL':'Grau de escolaridade','OCUP':'Ocupação','RENDA':'Renda familiar mensal',
    'RED_APO':'Rede de apoio','FILHOS':'Número de filhos','TRAB_NOT':'Trabalho noturno',
    'DOENCA':'Doença crônica (diagnóstico informado)','ANTIDEP':'Uso de antidepressivos',
    'ANSIED':'Ansiedade (diagnóstico informado)','DEPRE':'Depressão (diagnóstico informado)',
    'IDADE_C':'Idade da criança (anos)','SEXO':'Sexo da criança','TEMP_TEA':'Tempo de diagnóstico do autismo (meses)',
    'ACOMP_TEP':'Acompanhamento terapêutico da criança','FISIO':'Fisioterapia','FONO':'Fonoaudiologia',
    'TER_OCUP':'Terapia ocupacional','PSI':'Psicologia','PSICOP':'Psicopedagogia','OUTRA':'Outra terapia',
    'FREQ_TEP':'Frequência das terapias','ALT_SONO':'Alterações no sono da criança',
    'DESP_NOT':'Despertares noturnos da criança','CHORO':'Choro intenso durante a noite',
    'SUPERV':'Necessidade de supervisão constante','H_DEIT':'Horário de deitar (hora decimal)',
    'N_MIN':'Tempo para adormecer (minutos)','H_LEV':'Horário de levantar (hora decimal)',
    'H_SONO':'Duração do sono (horas por noite)','NAO_CONS':'Dificuldade para adormecer em até 30 minutos',
    'ACORD':'Acordar durante a noite ou cedo demais','PREC_LEV':'Levantar para ir ao banheiro',
    'NAO_RESP':'Dificuldade para respirar durante o sono','TOS_RONC':'Tosse ou ronco forte',
    'FRIO':'Frio durante o sono','CALOR':'Calor durante o sono','SONHOS':'Sonhos ruins',
    'DOR':'Dor durante o sono','DIF_DORM':'Outras dificuldades para dormir',
    'QUA_SONO':'Qualidade do sono percebida','FREQ_MED':'Uso de medicamento para dormir',
    'DIF_ACOR':'Dificuldade para ficar acordada durante atividades','ANIMO':'Dificuldade para manter o ânimo',
    'PARCEIRO':'Parceiro ou colega de quarto','TEMP_VOC':'Tempo disponível para si',
    'ESTRES':'Estresse ao conciliar cuidados e responsabilidades','IRRIT':'Irritação durante os cuidados',
    'AFET_REL':'Impacto nos relacionamentos','MEDO':'Medo pelo futuro do familiar',
    'DEPENDE':'Dependência do familiar','TENSO':'Tensão durante os cuidados',
    'SAU_FIS':'Impacto dos cuidados na saúde física','PRIV':'Impacto na privacidade',
    'VID_SOC':'Impacto na vida social','DESCONF':'Desconforto ao receber visitas',
    'UNICA_P':'Expectativa de ser a única pessoa de apoio','DINHEIRO':'Recursos financeiros para os cuidados',
    'CAP_CUI':'Capacidade de continuar cuidando','CONTROLE':'Perda de controle da própria vida',
    'INCAPAZ':'Dificuldade para lidar com os problemas','FAZ_MAIS':'Sensação de que deveria fazer mais',
    'CUID_MEL':'Sensação de que poderia cuidar melhor','MAIS_AJUD':'Pedidos de ajuda do familiar',
    'EXAUSTO':'Exaustão durante os cuidados','CONST':'Constrangimento com o comportamento do familiar',
    'UNIC_RESP':'Expectativa de responsabilidade exclusiva pelos cuidados',
    'PSQI':'Pontuação da qualidade do sono','PSQI_G':'Classificação da qualidade do sono',
    'ZARIT':'Pontuação de sobrecarga','ZARIT_CLASS':'Nível de sobrecarga',
    'ESCOL_B':'Escolaridade agrupada','RENDA_B':'Renda agrupada','FREQ_3':'Frequência de terapias agrupada',
}
TERM_DEFINITIONS={
    'n':'Participantes com respostas completas nesta comparação; pode ser menor que o total do banco.',
    'p':'Valor de p: o projeto usa o critério menor que 0,05. Não é a probabilidade de a relação ser verdadeira; não demonstra causa ou importância prática.',
    'DP':'Desvio padrão: mostra a variação das respostas ao redor da média; não é o valor de p.',
    'Média':'Soma dos valores dividida pela quantidade de respostas válidas.',
    'Mediana':'Ponto central das respostas ordenadas.',
    'Q1/Q3':'Limites da faixa que contém os 50% centrais das respostas ordenadas.',
    'IC95%':'Intervalo de confiança de 95%: expressa a incerteza da estimativa sob o método usado; não contém necessariamente 95% das participantes.',
    'Correlação':'Grau e direção da associação entre duas pontuações; não demonstra causa.',
    'OR':'Razão de chances: compara chances entre grupos definidos; não é razão de riscos nem probabilidade.',
    'RP':'Razão de prevalências: compara a proporção do evento entre grupos definidos.',
    'PSQI':'Índice de Qualidade do Sono de Pittsburgh (PSQI): pontuação global de 0 a 21; valores acima de 5 indicam pior qualidade do sono pelo corte adotado, sem diagnóstico automático.',
    'Zarit':'Escala de Sobrecarga de Zarit: pontuação de 0 a 88 na versão de 22 itens adotada pelo projeto. Classificação não substitui avaliação clínica.',
}
METHOD_DESCRIPTIONS={
    'welch_t':('Teste t de Welch','Compara a média das respostas entre dois grupos.'),
    'welch_anova':('Análise de variância de Welch','Compara médias de três ou mais grupos.'),
    'mann_whitney':('Teste de Mann–Whitney','Compara a ordenação e a distribuição das respostas entre dois grupos; não é automaticamente um teste de medianas.'),
    'kruskal':('Teste de Kruskal–Wallis','Compara a ordenação das respostas de três ou mais grupos.'),
    'spearman':('Correlação de Spearman','Avalia se pontuações maiores de uma variável tendem a acompanhar pontuações maiores ou menores da outra.'),
    'pearson':('Correlação de Pearson','Avalia associação linear entre duas medidas numéricas.'),
    'chi_square':('Teste do qui-quadrado','Avalia a associação entre categorias pelas suas frequências.'),
    'fisher':('Teste exato de Fisher','Avalia a associação entre categorias em uma tabela de dois por dois.'),
    'descriptive':('Análise descritiva','Apresenta quantidades ou distribuições; não calcula significância estatística.'),
}
FAMILY_LABELS={'primary':'Pergunta central','complementary':'Análise complementar','exploratory':'Outro fator investigado'}


@lru_cache(maxsize=1)
def _standard_labels():
    # Only shipped schema definitions are cached; never uploaded data or results.
    labels={}
    for p in (load_profile(),load_updated_profile()):
        for v in p.variables:labels.setdefault(v.name,set()).add(v.label)
    return labels


def field_title(code,profile):
    code=ALIASES.get(code,code)
    variable=next((v for v in profile.variables if v.name==code),None)
    if variable and variable.label and variable.label!=code and variable.label not in _standard_labels().get(code,set()):
        return variable.label
    return FIELD_TITLES.get(code,'Variável sem descrição')


def category_title(code,value,profile):
    code=ALIASES.get(code,code)
    variable=next((v for v in profile.variables if v.name==code),None)
    labels=variable.labels if variable else {}
    if code=='ZARIT_CLASS':labels={1:'Ausente ou leve (0–20)',2:'Moderada (21–40)',3:'Moderada a severa (41–60)',4:'Severa (61–88)'}
    label=labels.get(value)
    if label and not any(token in str(label).casefold() for token in ('não confirmada','pendente')):return str(label)
    return 'Categoria sem definição confirmada'


def term_definition(key):
    return TERM_DEFINITIONS.get(key,'Termo sem definição documentada.')


def category_titles(code,values,profile):
    labels=tuple(category_title(code,value,profile) for value in values)
    return tuple(f'{label} (grupo {i+1})' if labels.count(label)>1 else label for i,label in enumerate(labels))


def readable_number(value,digits=1):
    if value is None:return 'Não disponível'
    try:return f'{float(value):.{digits}f}'.replace('.',',') if math.isfinite(float(value)) else 'Não disponível'
    except (TypeError,ValueError):return 'Não disponível'


@dataclass(frozen=True)
class ReportComparison:
    id: str
    title: str
    family_label: str
    n_effective: int
    n_missing: int
    method_label: str
    method_explanation: str
    p_display: str
    interpretation: str
    estimates: tuple[str,...]
    reading: str
    warnings: tuple[str,...]
    technical_notes: tuple[str,...]


@dataclass(frozen=True)
class ReportDocument:
    title: str
    summary: tuple[str,...]
    comparisons: tuple[ReportComparison,...]
    glossary: dict[str,str]
    limitations: tuple[str,...]
    technical_notes: tuple[str,...]


def complete_pairs(data,spec):
    fields=[spec.outcome,spec.predictor]
    return data.reindex(columns=fields).replace('',np.nan).dropna()


def _unavailable_reason(result,pair,categorical):
    messages=' '.join(result.warnings).casefold()
    if not len(pair):return 'Não há respostas completas para esta comparação.'
    if 'esparsa' in messages:return 'Há poucas participantes em algumas categorias para aplicar este teste com segurança; apresentamos as quantidades e os percentuais.'
    if 'variância nula' in messages:return 'As respostas de um grupo não variaram; este método não calculou significância.'
    if any(pair[c].nunique()<2 for c in pair):return 'Uma das variáveis apresenta apenas um valor ou categoria; não é possível avaliar associação por este método.'
    if len(pair)<3:return 'São necessárias ao menos três participantes com respostas completas para avaliar esta associação.'
    if categorical and pair.groupby(categorical[0],observed=True).size().min()<2:return 'Um dos grupos tem menos de duas participantes; apresentamos apenas a descrição.'
    return 'O método não forneceu um teste válido para estes dados. Apresentamos a descrição; os detalhes técnicos estão no relatório completo.'


def _warnings(result):
    messages=[]
    for warning in result.warnings:
        if warning=='zero_cell_no_automatic_correction':messages.append('Uma combinação de categorias não teve participantes. Nenhuma correção automática foi aplicada; algumas estimativas ou intervalos podem estar indisponíveis.')
        elif 'assintótico' in warning:messages.append('O valor de p usa uma aproximação estatística; não é um cálculo exato.')
        elif 'Kruskal' in warning:messages.append('Há grupo com menos de cinco participantes; a aproximação deste teste exige cautela.')
    return tuple(dict.fromkeys(messages))


def build_document(results,tables,profile,data,metadata):
    kinds={v.name:v.kind for v in profile.variables};kinds['ZARIT_CLASS']='categorical'
    comparisons=[]
    for analysis in results:
        spec,r=analysis.spec,analysis.result
        if any(kinds.get(c)=='text' for c in (spec.outcome,spec.predictor)):
            from .models import DomainError
            raise DomainError('private_variable','Identificação e campos de texto livre não podem integrar os resultados analíticos.')
        pair=complete_pairs(data,spec)
        categorical=[c for c in pair if kinds.get(c)=='categorical']
        order=spec.group_order or (tuple(sorted(pair[categorical[0]].unique())) if categorical else ())
        group_names=category_titles(categorical[0],order,profile) if categorical else ()
        answer=interpret_p(r.p_value,p_kind=r.p_kind)
        valid=answer['status']!='unavailable'
        status={'significant':'Associação estatisticamente significativa pelo critério do projeto.',
                'not_significant':'A comparação não atingiu o critério estatístico do projeto; isso não prova ausência de associação.',
                'unavailable':'Teste estatístico não calculado.'}[answer['status']]
        method,explanation=METHOD_DESCRIPTIONS.get(r.method,('Método documentado nos detalhes técnicos','Consulte os detalhes do método utilizado.'))
        estimates=[];descriptions=[]
        if len(categorical)==1:
            group=categorical[0];number=next(c for c in pair if c!=group)
            for code,name in zip(order,group_names):
                values=pd.to_numeric(pair.loc[pair[group]==code,number])
                descriptions.append(f'{name}: {len(values)} participantes; média {readable_number(values.mean())}; mediana {readable_number(values.median())}.')
        effect_names={'mean_difference':'Diferença entre médias','correlation':'Coeficiente de correlação',
                      'odds_ratio':'Razão de chances','prevalence_ratio':'Razão de prevalências',
                      'probability_superiority':'Probabilidade de superioridade','omnibus':'Estimativa global'}
        for name,effect in r.effects.items():
            text=f'{effect_names.get(name,"Estimativa")}: {readable_number(effect.value,3)}'
            if name in ('mean_difference','probability_superiority') and len(group_names)==2:
                text+=f'; grupos na ordem: {group_names[0]} e {group_names[1]}'
                if name=='mean_difference':text+='; primeiro menos o segundo'
                else:text+='; chance de uma resposta do primeiro grupo superar a do segundo, contando metade dos empates'
            if name in ('odds_ratio','prevalence_ratio'):
                event=category_title(spec.outcome,spec.event_value,profile)
                reference=category_title(spec.predictor,spec.group_order[1],profile) if len(spec.group_order)==2 else 'não declarada'
                exposed=category_title(spec.predictor,spec.group_order[0],profile) if len(spec.group_order)==2 else 'não declarado'
                text+=f'; evento: {event}; grupo comparado: {exposed}; referência: {reference}'
            if effect.ci95 and all(math.isfinite(x) for x in effect.ci95):text+=f'; intervalo de confiança de 95%: {readable_number(effect.ci95[0],3)} a {readable_number(effect.ci95[1],3)}'
            else:
                reason=effect.unavailable_reason or ''
                if 'célula zero' in reason:reason='uma combinação de categorias não teve respostas; este método não calculou intervalo'
                elif 'menor que cinco' in reason or 'menos de cinco' in reason:reason='não há respostas suficientes ou estáveis para estimar o intervalo por reamostragem'
                elif 'mais de três' in reason:reason='o intervalo deste método exige mais de três respostas completas'
                elif 'global' in reason:reason='este método não fornece um intervalo global nesta versão; confira as descrições por grupo'
                else:reason='não disponibilizado para este método/amostra'
                text+='; intervalo de confiança não disponível: '+reason
            estimates.append(text+'.')
            if name=='correlation' and effect.value is not None and math.isfinite(effect.value):
                direction='positiva' if effect.value>0 else 'negativa' if effect.value<0 else 'nula'
                descriptions.append(f'A associação observada entre as pontuações foi {direction}; isso não indica causa.')
        reading=f'Participaram desta comparação {r.n_effective} pessoas com respostas completas. {status}'
        if valid:reading+=f' Valor de p: {answer["p_display"]}; critério do projeto: menor que 0,05.'
        else:reading+=' '+_unavailable_reason(r,pair,categorical)
        if r.n_missing:reading+=f' {r.n_missing} participantes ficaram fora desta comparação por falta de respostas necessárias.'
        if descriptions:reading+=' '+' '.join(descriptions)
        warnings=_warnings(r)
        unknown=tuple(w for w in r.warnings if not any(t in w for t in ('esparsa','nula','observa','pares','assintótico','Kruskal','zero_cell','categoria')))
        if unknown:warnings+=('Há uma ressalva adicional do método nos detalhes técnicos do relatório completo.',)
        comparisons.append(ReportComparison(spec.id,f'{field_title(spec.outcome,profile)} e {field_title(spec.predictor,profile)}',
            FAMILY_LABELS.get(spec.family,'Outro fator investigado'),r.n_effective,r.n_missing,method,explanation,
            answer['p_display'] if valid else '',status,tuple(estimates),reading,warnings,tuple(r.assumptions)+tuple(r.warnings)))
    total=metadata.get('n_source',len(data));included=metadata.get('n_included',len(data))
    summary=[f'Base de análise: {total} registros na fonte; {included} participantes incluídas; {total-included} excluídas pelos critérios observáveis.',
             'Cada comparação utiliza apenas respostas completas, sem preencher respostas ausentes. Critérios não observáveis no banco não foram certificados.']
    origins=metadata.get('score_origins',profile.derived_rules.get('score_origins',{}))
    for code,label in (('PSQI','Qualidade do sono — Índice de Qualidade do Sono de Pittsburgh (PSQI), de 0 a 21 pontos'),('ZARIT','Sobrecarga — Escala de Sobrecarga de Zarit, versão de 22 itens, de 0 a 88 pontos')):
        origin=origins.get(code,'origem não registrada')
        summary.append(f'{label}: {origin}.')
    used={'n','p'}
    if tables.descriptive:used.update(('Média','Mediana','DP','Q1/Q3'))
    fields={c for a in results for c in (a.spec.outcome,a.spec.predictor)}
    if fields&{'PSQI','PSQI_G'}:used.add('PSQI')
    if fields&{'ZARIT','ZARIT_CLASS'}:used.add('Zarit')
    if any(a.result.effects for a in results):used.add('IC95%')
    for name,term in (('correlation','Correlação'),('odds_ratio','OR'),('prevalence_ratio','RP')):
        if any(name in a.result.effects for a in results):used.add(term)
    glossary={k:v for k,v in TERM_DEFINITIONS.items() if k in used}
    technical=[f'{v.name}: {field_title(v.name,profile)}' for v in profile.variables if v.kind!='text' and v.name in data]
    technical+=['ZARIT_CLASS: '+field_title('ZARIT_CLASS',profile)]
    for a in results:
        technical.append(f'{a.spec.id}: {a.spec.outcome} × {a.spec.predictor}; família {a.spec.family}; método {a.result.method}; tipo de p {a.result.p_kind}.')
        technical.extend(a.result.assumptions+a.result.warnings)
        technical.extend(f'{name}: {e.method}; {e.unavailable_reason}' for name,e in a.result.effects.items() if e.unavailable_reason)
    technical.append('As notas de pressupostos descrevem condições do método; não certificam que o desenho do estudo as cumpriu.')
    limitations=('Estudo transversal: associação não demonstra causa.',
                 'Valores de p bilaterais sem ajuste por múltiplas comparações. A interpretação exige cautela, especialmente nas análises exploratórias.',
                 'Significância estatística não determina importância clínica. Resultados não significativos não provam ausência de associação.',
                 'Análises bivariadas, sem ajuste por confundidores. Categorias e cortes seguem o dicionário efetivamente utilizado.')
    return ReportDocument('Resultados da análise bivariada',tuple(summary),tuple(comparisons),glossary,limitations,tuple(technical))
