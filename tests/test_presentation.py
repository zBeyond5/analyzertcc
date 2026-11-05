from dataclasses import replace
import pytest
from tcc_analyzer.models import VariableSpec
from tcc_analyzer.profiles import load_profile, load_updated_profile
from tcc_analyzer.presentation import field_title, category_title, term_definition


@pytest.mark.parametrize('profile', [load_profile(), load_updated_profile()])
def test_all_fields_have_readable_titles_without_changing_schema(profile):
    original=repr(profile)
    assert field_title('DEPRE',profile)=='Depressão (diagnóstico informado)'
    assert field_title('ESCOL',profile)=='Grau de escolaridade'
    assert field_title('ACOMP_TEP',profile)=='Acompanhamento terapêutico da criança'
    assert field_title('PSQI_G',profile)=='Classificação da qualidade do sono'
    assert field_title('PSI',profile)=='Psicologia'
    assert field_title('TO',profile)=='Terapia ocupacional'
    assert all(field_title(v.name,profile)!=v.name for v in profile.variables if v.kind!='text')
    assert repr(profile)==original
    assert 'variação' in term_definition('DP')


def test_custom_questions_categories_and_unknown_fields_are_not_guessed():
    p=load_updated_profile()
    variables=tuple(replace(v,label='Outra pergunta <>& PSI PSQI',labels={8:'Opção personalizada'}) if v.name=='DEPRE' else v for v in p.variables)
    p=replace(p,variables=variables+(VariableSpec('NEW','NEW','numeric'),))
    assert field_title('DEPRE',p)=='Outra pergunta <>& PSI PSQI'
    assert category_title('DEPRE',8,p)=='Opção personalizada'
    assert 'sem definição confirmada' in category_title('DEPRE',9,p)
    assert field_title('NEW',p)=='Variável sem descrição'
    assert 'sem definição confirmada' in category_title('ESCOL',1,load_profile())


def build_example(results, data=None):
    import pandas as pd
    from tcc_analyzer.presentation import build_document
    from tcc_analyzer.models import ReportTables
    if data is None:data=pd.DataFrame({'PSQI_G':[1,1,2,2], 'ZARIT':[10,20,30,40], 'PSQI':[2,3,8,9], 'NOME':['PRIVATE-NAME']*4})
    return build_document(results,ReportTables((),(),(),()),load_updated_profile(),data,{'n_source':6,'n_included':4,'score_origins':{'PSQI':'calculado a partir das respostas'}})


def test_each_question_has_its_own_p_estimate_and_group_direction():
    from tcc_analyzer.models import ComparisonSpec, AnalysisResult, TestResult, EffectEstimate
    a=AnalysisResult(ComparisonSpec('groups','PSQI_G','ZARIT',group_order=(2,1)),TestResult('welch_t',4,p_value=.096,p_kind='parametric',effects={'mean_difference':EffectEstimate(20,(5,35))}))
    b=AnalysisResult(ComparisonSpec('scores','PSQI','ZARIT','complementary'),TestResult('spearman',4,p_value=.002,p_kind='exact',effects={'correlation':EffectEstimate(-.8)}))
    d=build_example((a,b))
    assert [c.p_display for c in d.comparisons]==['0,096','0,002']
    assert d.comparisons[0].interpretation!=d.comparisons[1].interpretation
    assert 'PSQI_G' not in d.comparisons[0].reading
    assert 'PRIVATE-NAME' not in repr(d)
    assert 'primeiro menos o segundo' in ' '.join(d.comparisons[0].estimates)
    assert 'negativa' in d.comparisons[1].reading
    assert 'calculado a partir das respostas' in ' '.join(d.summary)
    assert any('6 registros' in x for x in d.summary)


@pytest.mark.parametrize('p,kind,status',[(0,'exact','significativa'),(.05,'parametric','não atingiu'),(None,'not_computed','não calculado'),(float('nan'),'asymptotic','não calculado')])
def test_p_explanations_and_unavailable_are_human_readable(p,kind,status):
    from tcc_analyzer.models import ComparisonSpec, AnalysisResult, TestResult
    a=AnalysisResult(ComparisonSpec('x','PSQI_G','ZARIT'),TestResult('welch_t',4,p_value=p,p_kind=kind,warnings=('Variância nula: inferência não calculada; apresentar descrição dos grupos.',) if p is None else ()))
    c=build_example((a,)).comparisons[0]
    assert status in c.interpretation.lower()
    assert 'Confira o método e os avisos' not in c.reading
    assert 'p=Não calculado' not in c.reading
    if p is None:assert 'variaram' in c.reading


def test_zero_pairs_and_sparse_tables_have_specific_reasons():
    import pandas as pd
    from tcc_analyzer.models import ComparisonSpec, AnalysisResult, TestResult
    a=AnalysisResult(ComparisonSpec('none','PSQI_G','ZARIT'),TestResult('descriptive',0))
    assert 'Não há respostas completas' in build_example((a,),pd.DataFrame({'PSQI_G':[], 'ZARIT':[]})).comparisons[0].reading
    a.result.n_effective=4;a.result.warnings=('Tabela RxC esparsa: somente descrição, sem p.',)
    assert 'poucas participantes' in build_example((a,)).comparisons[0].reading
