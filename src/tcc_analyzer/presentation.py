"""Portuguese reading vocabulary; analytical field names and values stay intact."""
from functools import lru_cache
import math
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


def readable_number(value,digits=1):
    if value is None:return 'Não disponível'
    try:return f'{float(value):.{digits}f}'.replace('.',',') if math.isfinite(float(value)) else 'Não disponível'
    except (TypeError,ValueError):return 'Não disponível'
