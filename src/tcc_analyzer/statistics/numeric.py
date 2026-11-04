import math
import numpy as np
from scipy import stats
from statsmodels.stats.oneway import anova_oneway
from ..models import DomainError, EffectEstimate, TestResult

def _bootstrap_ci(a, b, *, paired, statistic, seed):
    rng = np.random.default_rng(seed)
    estimates = []
    for start in range(0,1999,32):
        size = min(32,1999-start)
        ai = rng.integers(len(a), size=(size,len(a)))
        bi = ai if paired else rng.integers(len(b), size=(size,len(b)))
        vals = np.asarray(statistic(a[ai], b[bi]))
        estimates.extend(vals[np.isfinite(vals)].tolist())
    if len(estimates) < 1900 or np.ptp(estimates) == 0:
        return None
    lo,hi = np.percentile(estimates,[2.5,97.5])
    return float(lo),float(hi)

def _superiority(a,b):
    return stats.mannwhitneyu(a,b,axis=-1,method='asymptotic').statistic/(a.shape[-1]*b.shape[-1])

def _rho_batch(a,b):
    ra,rb = stats.rankdata(a,axis=-1),stats.rankdata(b,axis=-1)
    da,db = ra-ra.mean(axis=-1,keepdims=True),rb-rb.mean(axis=-1,keepdims=True)
    denominator = np.sqrt(np.sum(da*da,axis=-1)*np.sum(db*db,axis=-1))
    return np.divide(np.sum(da*db,axis=-1),denominator,out=np.full(denominator.shape,np.nan),where=denominator>0)

def compare_groups(groups, *, method, seed=20261104):
    if method not in ('welch_t','mann_whitney','welch_anova','kruskal'):
        raise DomainError('method', 'Método de comparação numérica inválido.')
    try:
        arrays = tuple(np.asarray(g,dtype=float).ravel() for g in groups)
    except (ValueError,TypeError):
        raise DomainError('numeric', 'A comparação exige valores numéricos válidos.') from None
    if len(arrays) < 2 or (method in ('welch_t','mann_whitney') and len(arrays)!=2):
        raise DomainError('groups', 'O método selecionado não corresponde ao número de grupos.')
    missing = sum(np.isnan(g).sum() for g in arrays)
    arrays = tuple(g[~np.isnan(g)] for g in arrays)
    if any(not np.isfinite(g).all() for g in arrays):
        raise DomainError('numeric', 'Valores infinitos não podem ser analisados.')
    result = TestResult(method,sum(len(g) for g in arrays),int(missing),seed=seed,
                        assumptions=('Grupos independentes; escolha do estimando e pressupostos confirmados antes da execução.',))
    if any(len(g)<2 for g in arrays):
        result.warnings = ('Cada grupo necessita de pelo menos duas observações válidas.',)
        return result
    all_values = np.concatenate(arrays)
    if np.ptp(all_values)==0 or (method in ('welch_t','welch_anova') and any(np.var(g,ddof=1)==0 for g in arrays)):
        result.warnings = ('Variância nula: inferência não calculada; apresentar descrição dos grupos.',)
        return result
    if method == 'welch_t':
        a,b=arrays
        answer=stats.ttest_ind(a,b,equal_var=False,alternative='two-sided')
        interval=answer.confidence_interval(confidence_level=.95)
        result.statistic,result.p_value,result.p_kind=float(answer.statistic),float(answer.pvalue),'parametric'
        result.effects['mean_difference']=EffectEstimate(float(a.mean()-b.mean()),(float(interval.low),float(interval.high)),f'Diferença média do primeiro grupo menos o segundo; Welch t, gl={answer.df:.6g}')
    elif method == 'welch_anova':
        answer=anova_oneway(arrays,use_var='unequal')
        result.statistic,result.p_value,result.p_kind=float(answer.statistic),float(answer.pvalue),'parametric'
        result.effects['omnibus']=EffectEstimate(None,None,f'Welch ANOVA; gl={tuple(float(v) for v in answer.df)}','Sem efeito/IC global validado neste MVP; conferir médias por grupo.')
    elif method == 'kruskal':
        answer=stats.kruskal(*arrays)
        result.statistic,result.p_value,result.p_kind=float(answer.statistic),float(answer.pvalue),'asymptotic'
        if any(len(g)<5 for g in arrays):result.warnings+=('Aproximação Kruskal–Wallis com grupo menor que cinco; interpretar com cautela.',)
        result.effects['omnibus']=EffectEstimate(None,None,'Kruskal–Wallis','Sem efeito/IC global validado neste MVP; conferir medianas e distribuições.')
    else:
        a,b=arrays
        tied=len(np.unique(all_values))!=len(all_values)
        if not tied and min(len(a),len(b))<=8:
            answer=stats.mannwhitneyu(a,b,alternative='two-sided',method='exact')
            p_kind='exact'
        elif tied and math.comb(len(all_values),len(a))<=10000:
            def statistic(x,y):return stats.mannwhitneyu(x,y,method='asymptotic').statistic
            answer=stats.permutation_test((a,b),statistic,permutation_type='independent',n_resamples=np.inf,alternative='two-sided',vectorized=False)
            p_kind='permutation_exact'
        else:
            answer=stats.mannwhitneyu(a,b,alternative='two-sided',method='asymptotic',use_continuity=True)
            p_kind='asymptotic'
            result.warnings+=('Mann–Whitney com p assintótico e correção de empates/continuidade.',)
        result.statistic,result.p_value,result.p_kind=float(answer.statistic),float(answer.pvalue),p_kind
        estimate=result.statistic/(len(a)*len(b))
        ci=_bootstrap_ci(a,b,paired=False,statistic=_superiority,seed=seed) if min(len(a),len(b))>=5 else None
        result.effects['probability_superiority']=EffectEstimate(estimate,ci,'P(primeiro > segundo) + 0,5 P(empate); IC95% bootstrap percentil, 1.999 reamostragens',None if ci else 'IC indisponível: amostra menor que cinco ou reamostragem degenerada.')
    return result

def correlate(x,y, *, method, seed=20261104):
    if method not in ('pearson','spearman'):
        raise DomainError('method','Método de correlação inválido.')
    try:a,b=np.asarray(x,dtype=float).ravel(),np.asarray(y,dtype=float).ravel()
    except (ValueError,TypeError):raise DomainError('numeric','A correlação exige valores numéricos válidos.') from None
    if len(a)!=len(b):raise DomainError('pairs','Os vetores devem conter os mesmos pares de observações.')
    mask=~(np.isnan(a)|np.isnan(b));missing=int((~mask).sum());a,b=a[mask],b[mask]
    if not np.isfinite(a).all() or not np.isfinite(b).all():raise DomainError('numeric','Valores infinitos não podem ser analisados.')
    result=TestResult(method,len(a),missing,seed=seed,assumptions=('Pares de observações independentes; Pearson requer relação linear e pressupostos paramétricos; Spearman avalia monotonicidade.',))
    if len(a)<3 or np.ptp(a)==0 or np.ptp(b)==0:
        result.warnings=('São necessários ao menos três pares válidos e duas variáveis não constantes.',)
        return result
    if method=='pearson':
        answer=stats.pearsonr(a,b)
        value=float(answer.statistic);p=float(answer.pvalue);kind='parametric'
        ci=None
        if len(a)>3:
            interval=answer.confidence_interval(confidence_level=.95)
            ci=(float(interval.low),float(interval.high))
        effect=EffectEstimate(value,ci,'r de Pearson; IC95% pela transformação Fisher-z',None if ci else 'IC Fisher-z requer mais de três pares.')
    else:
        value=float(stats.spearmanr(a,b).statistic)
        if len(a)<=8:
            rank_a=stats.rankdata(a)
            def statistic(permuted):return float(stats.pearsonr(rank_a,stats.rankdata(permuted)).statistic)
            answer=stats.permutation_test((b,),statistic,permutation_type='pairings',n_resamples=np.inf,alternative='two-sided',vectorized=False)
            p,kind=float(answer.pvalue),'permutation_exact'
        else:
            p,kind=float(stats.spearmanr(a,b).pvalue),'asymptotic'
            result.warnings+=('Spearman com p assintótico; não é teste exato.',)
        ci=_bootstrap_ci(a,b,paired=True,statistic=_rho_batch,seed=seed) if len(a)>=5 else None
        effect=EffectEstimate(value,ci,'rho de Spearman; IC95% bootstrap pareado percentil, 1.999 reamostragens',None if ci else 'IC indisponível: menos de cinco pares ou reamostragem degenerada.')
    result.statistic,result.p_value,result.p_kind=value,p,kind
    result.effects['correlation']=effect
    return result
