import pandas as pd
from tcc_analyzer.analysis_plan import build_default_plan,question_groups
from tcc_analyzer.profiles import load_updated_profile

def test_av3_catalog_and_deduplication():
    p=load_updated_profile();df=pd.DataFrame([{v.name:1 for v in p.variables}]);df['ZARIT_CLASS']=1
    plan=build_default_plan(df,p,('burden','factor_IDADE_M','support','support'))
    assert len(plan)==5
    assert len({c.id for c in plan})==5
    assert len(question_groups(p)['crianca'])==14
    assert all(c.predictor not in ('QUA_SONO','N_MIN') for c in plan)
    assert len(build_default_plan(df,p))==3
