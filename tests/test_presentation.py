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
