from dataclasses import replace
import numpy as np
import pandas as pd
import pytest
from tcc_analyzer.models import ComparisonSpec, DomainError, ResearchProfile, VariableSpec
from tcc_analyzer.profiles import load_profile
from tcc_analyzer.statistics.descriptive import describe
from tcc_analyzer.statistics.selection import recommend_test, freeze_comparisons, default_comparisons
from tcc_analyzer.statistics.categorical import analyze_contingency
from tcc_analyzer.statistics.numeric import compare_groups, correlate

SEED = 20261104

def profile(*variables):
    return ResearchProfile('test','1',tuple(VariableSpec(name, name, kind, mapping_status='confirmed') for name,kind in variables))

def test_age_descriptive_sample_sd(fictitious_df):
    result,=describe(fictitious_df,('IDADE_M',),load_profile())
    assert result.n_valid==30
    assert result.metrics['mean']==pytest.approx(37.4)
    assert result.metrics['sd']==pytest.approx(6.392883974955386)

def test_missing_and_therapy_denominators(fictitious_df):
    result,=describe(pd.DataFrame({'ALT_SONO':[1,2,None]}),('ALT_SONO',),load_profile())
    assert (result.n_total,result.n_valid,result.n_missing)==(3,2,1)
    assert result.metrics['percentages'][1]==50
    therapy,=describe(fictitious_df,('FONO',),load_profile())
    assert therapy.metrics['percentages'][1]==80
    assert therapy.n_total==30

def test_empty_description():
    result,=describe(pd.DataFrame({'x':[None,None]}),('x',),profile(('x','numeric')))
    assert result.n_valid==0 and result.metrics['mean'] is None
    assert result.metrics['sd'] is None

def test_primary_family_prespecified():
    items=default_comparisons()
    assert [(x.outcome,x.predictor) for x in items if x.family=='primary']==[('PSQI_G','ZARIT'),('PSQI_G','ZARIT_CLASS')]

def test_freeze_validates_rationale_and_names():
    p=profile(('outcome','numeric'),('predictor','numeric'))
    s=ComparisonSpec('a','outcome','predictor',method='pearson')
    assert freeze_comparisons((s,),p)==(s,)
    with pytest.raises(DomainError):freeze_comparisons((replace(s,rationale=''),),p)
    with pytest.raises(DomainError):freeze_comparisons((replace(s,outcome='missing'),),p)
    with pytest.raises(DomainError):freeze_comparisons((s,s),p)

def test_selection_shape_and_kind():
    p=profile(('outcome','categorical'),('predictor','numeric'))
    df=pd.DataFrame({'outcome':[1,1,1,2,2,2],'predictor':[1,2,3,4,5,6]})
    c=ComparisonSpec('a','outcome','predictor')
    rec=recommend_test(df,c,p)
    assert rec.method=='welch_t' and not rec.blocked
    assert 'mann_whitney' in rec.alternatives
    # A column named shapiro_p is irrelevant to selection.
    assert recommend_test(df.assign(shapiro_p=0.00001),c,p).method==rec.method
    ordp=profile(('outcome','ordinal'),('predictor','numeric'))
    assert recommend_test(df,c,ordp).method=='spearman'

def test_categorical_recommendation_sparse():
    df=pd.DataFrame({'y':[1,1,1,2],'x':[1,1,2,2]})
    rec=recommend_test(df,ComparisonSpec('a','y','x'),profile(('y','categorical'),('x','categorical')))
    assert rec.method=='fisher'

def test_fisher_reference_and_orientation():
    result=analyze_contingency(np.array([[8,2],[1,5]]),method='fisher',event_column=0,exposed_row=0)
    assert result.p_value==pytest.approx(0.034965034965034975)
    assert result.n_effective==16 and result.p_kind=='exact'
    assert result.effects['odds_ratio'].value==pytest.approx(20)
    assert result.effects['prevalence_ratio'].value==pytest.approx(4.8)
    reverse=analyze_contingency(np.array([[8,2],[1,5]]),method='fisher',event_column=0,exposed_row=1)
    assert reverse.effects['prevalence_ratio'].value==pytest.approx(1/4.8)

def test_dense_chi_square():
    r=analyze_contingency(np.array([[10,10],[10,10]]),method='chi_square',event_column=None,exposed_row=None)
    assert r.statistic==0 and r.p_value==1 and r.effects=={}

def test_zero_cells_do_not_add_half():
    r=analyze_contingency(np.array([[0,5],[4,1]]),method='fisher',event_column=0,exposed_row=0)
    assert 0<=r.p_value<=1
    assert r.effects['prevalence_ratio'].value==0
    assert r.effects['prevalence_ratio'].ci95 is None
    assert 'zero_cell_no_automatic_correction' in r.warnings

def test_sparse_rxc_and_zero_margin():
    r=analyze_contingency(np.array([[1,0,0],[0,1,1]]),method='auto',event_column=None,exposed_row=None)
    assert r.p_value is None and r.warnings
    z=analyze_contingency(np.array([[0,0],[1,3]]),method='fisher',event_column=0,exposed_row=0)
    assert z.p_value is None and z.warnings

@pytest.mark.parametrize('table',[[],[[-1,1],[2,3]],[[0.5,1],[2,3]],[[np.nan,1],[2,3]]])
def test_invalid_counts(table):
    with pytest.raises(DomainError):analyze_contingency(np.array(table),method='auto',event_column=None,exposed_row=None)

def test_sparse_requested_chi_square_is_blocked():
    r=analyze_contingency(np.array([[1,0],[0,1]]),method='chi_square',event_column=None,exposed_row=None)
    assert r.p_value is None

def test_welch_mean_difference_reference():
    r=compare_groups((np.array([1.,2.,3.]),np.array([4.,5.,6.])),method='welch_t',seed=SEED)
    assert r.effects['mean_difference'].value==-3
    assert r.effects['mean_difference'].ci95[1]<0
    assert r.p_value==pytest.approx(0.021311641128756727)

def test_mann_whitney_estimand():
    r=compare_groups((np.array([1.,2.,3.]),np.array([4.,5.,6.])),method='mann_whitney',seed=SEED)
    assert r.statistic==0 and r.p_value==pytest.approx(0.1)
    assert r.effects['probability_superiority'].value==0
    assert r.effects['probability_superiority'].ci95 is None
    assert 'median_difference' not in r.effects

def test_three_group_references():
    groups=tuple(np.array(g,dtype=float) for g in ([1,2,3],[4,5,6],[7,8,9]))
    w=compare_groups(groups,method='welch_anova',seed=SEED)
    k=compare_groups(groups,method='kruskal',seed=SEED)
    assert w.n_effective==k.n_effective==9
    # Welch inclui correção finita: F = 27/(1+1/6), gl=(2,4).
    assert w.statistic==pytest.approx(162/7) and w.p_value==pytest.approx((7/88)**2)
    assert k.statistic==pytest.approx(7.2) and k.p_value==pytest.approx(0.02732372244729256)

def test_small_tied_mann_whitney_is_exact_permutation():
    r=compare_groups((np.array([1,1,2]),np.array([2,3,3])),method='mann_whitney',seed=SEED)
    assert r.p_kind=='permutation_exact' and 0<=r.p_value<=1

@pytest.mark.parametrize('method',['welch_t','mann_whitney','welch_anova','kruskal'])
def test_minimum_groups_and_constants(method):
    small=compare_groups((np.array([1]),np.array([2,3])),method=method,seed=SEED)
    assert small.p_value is None and small.warnings
    constant=compare_groups((np.array([1,1]),np.array([1,1])),method=method,seed=SEED)
    assert constant.p_value is None and constant.warnings

def test_pearson_reference():
    r=correlate(np.array([1,2,3,4]),np.array([1,3,2,4]),method='pearson',seed=SEED)
    assert r.effects['correlation'].value==pytest.approx(.8)
    assert r.p_value==pytest.approx(.2)
    assert r.effects['correlation'].ci95 is not None

def test_spearman_exact_monotonic():
    r=correlate(np.array([1,2,3,4,5]),np.array([1,4,9,16,25]),method='spearman',seed=SEED)
    assert r.effects['correlation'].value==pytest.approx(1)
    assert r.p_kind=='permutation_exact'
    assert r.effects['correlation'].ci95 is None

def test_correlation_joint_missing_and_constants():
    r=correlate(np.array([1,2,np.nan,4,5]),np.array([1,np.nan,9,16,25]),method='pearson',seed=SEED)
    assert r.n_effective==3 and r.n_missing==2
    c=correlate(np.ones(5),np.arange(5),method='spearman',seed=SEED)
    assert c.p_value is None and c.warnings

def test_seed_reproducible():
    x=np.array([1,2,3,4,5,6.]);y=np.array([1,4,2,6,3,5.])
    a=correlate(x,y,method='spearman',seed=SEED)
    b=correlate(x,y,method='spearman',seed=SEED)
    assert a.p_value==b.p_value
    assert a.effects['correlation'].ci95==b.effects['correlation'].ci95
