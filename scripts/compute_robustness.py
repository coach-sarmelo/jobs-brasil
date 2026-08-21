"""Bateria de robustez R1-R7 para as especificacoes S1-S4 do artigo.

Uso: python scripts/compute_robustness.py
Saida: data/output/robustness.json
"""
import json
import os
import sys
import numpy as np
import pandas as pd
import statsmodels.api as sm

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from scripts.compute_econometrics import _region_formality_loo, _uf_formality_loo
from scripts.stats.regression import (
    wls_regression,
    wls_regression_clustered,
    wild_cluster_bootstrap_p,
)

REQUIRED_FIELDS = ('exposure', 'avg_anos_estudo', 'renda', 'informality',
                   'region', 'occupation_code', 'jobs')


def _filter_valid(data):
    return [r for r in data
            if all(r.get(k) is not None for k in REQUIRED_FIELDS)
            and r['jobs'] > 0]


def _s4_matrices(rows):
    """Matrizes de S4 (interacao com formalidade regional LOO)."""
    loo = _region_formality_loo(rows)
    keep = [(r, f) for r, f in zip(rows, loo) if f is not None]
    y = np.array([r['exposure'] for r, _ in keep])
    w = np.array([r['jobs'] for r, _ in keep])
    cl = [r['occupation_code'] for r, _ in keep]
    rg = [r['region'] for r, _ in keep]
    X = np.array([[1.0, r['avg_anos_estudo'], r['avg_anos_estudo'] * f, f]
                  for r, f in keep])
    return X, y, w, cl, rg


def extract_results(model_result, n_clusters):
    return {
        "beta": model_result.params.tolist(),
        "se": model_result.bse.tolist(),
        "p_value": model_result.pvalues.tolist(),
        "r_squared": float(model_result.rsquared),
        "n": int(model_result.nobs),
        "n_clusters": int(n_clusters)
    }


def oster_bound(res_uncon, res_con, r_max):
    """Limite de Oster (2019): delta que zera o efeito e beta*(delta=1)."""
    b1 = res_uncon['beta'][1]
    b2 = res_con['beta'][1]
    r2u = res_uncon['r_squared']
    r2c = res_con['r_squared']
    base = {
        'beta_uncontrolled': float(b1),
        'beta_controlled': float(b2),
        'r_squared_uncontrolled': float(r2u),
        'r_squared_controlled': float(r2c),
        'r_max': float(r_max),
    }
    denom = (b1 - b2) * (r_max - r2u)
    if abs(b1 - b2) < 1e-12 or abs(r2c - r2u) < 1e-12 or abs(denom) < 1e-12:
        base.update({
            'delta_for_zero': None,
            'beta_star_delta1': None,
            'note': 'movimento insuficiente entre especificacoes (beta ou R2 nao mudam)',
        })
        return base
    delta = b2 * (r2c - r2u) / denom
    bstar = b2 - (b1 - b2) * (r_max - r2u) / (r2c - r2u)
    base.update({
        'delta_for_zero': float(delta),
        'beta_star_delta1': float(bstar),
    })
    return base


def fast_wild_bootstrap_mc(y, X, w, clusters, idx=2, n_draws=1000, seed=42):
    """Fast vectorized Wild Cluster Bootstrap (Monte Carlo) em NumPy."""
    np.random.seed(seed)
    n, k = X.shape
    w = np.asarray(w, dtype=float)
    y = np.asarray(y, dtype=float)
    X = np.asarray(X, dtype=float)
    clusters = np.asarray(clusters)
    
    unique_clusters = np.unique(clusters)
    g = len(unique_clusters)
    
    w_sqrt = np.sqrt(w)
    X_tilde = w_sqrt[:, None] * X
    XWX = X_tilde.T @ X_tilde
    XWX_inv = np.linalg.pinv(XWX)
    
    beta_hat = XWX_inv @ (X_tilde.T @ (w_sqrt * y))
    e_tilde_hat = w_sqrt * (y - X @ beta_hat)
    
    cluster_indices = [np.where(clusters == c)[0] for c in unique_clusters]
    
    meat = np.zeros((k, k))
    for c_idx in cluster_indices:
        s = X_tilde[c_idx].T @ e_tilde_hat[c_idx]
        meat += np.outer(s, s)
    corr = (g / (g - 1)) * ((n - 1) / (n - k))
    V_hat = corr * XWX_inv @ meat @ XWX_inv
    t_hat = beta_hat[idx] / np.sqrt(V_hat[idx, idx])
    
    X0 = np.delete(X, idx, axis=1)
    X0_tilde = w_sqrt[:, None] * X0
    X0WX0_inv = np.linalg.pinv(X0_tilde.T @ X0_tilde)
    beta0 = X0WX0_inv @ (X0_tilde.T @ (w_sqrt * y))
    center = X0 @ beta0
    resid = y - center
    
    y_star = np.empty(n, dtype=float)
    count = 0
    
    for _ in range(n_draws):
        signs = np.random.choice([1.0, -1.0], size=g)
        for s, c_idx in zip(signs, cluster_indices):
            y_star[c_idx] = center[c_idx] + s * resid[c_idx]
            
        beta_b = XWX_inv @ (X_tilde.T @ (w_sqrt * y_star))
        e_tilde_b = w_sqrt * (y_star - X @ beta_b)
        
        meat_b = np.zeros((k, k))
        for c_idx in cluster_indices:
            s_b = X_tilde[c_idx].T @ e_tilde_b[c_idx]
            meat_b += np.outer(s_b, s_b)
            
        V_b = corr * XWX_inv @ meat_b @ XWX_inv
        se_b = np.sqrt(V_b[idx, idx])
        t_b = beta_b[idx] / se_b if se_b > 0 else 0.0
        
        if np.isfinite(t_b) and abs(t_b) >= abs(t_hat):
            count += 1
            
    p_val = (count + 1) / (n_draws + 1)
    return {
        "p": float(p_val),
        "t_stat": float(t_hat),
        "n_draws": int(n_draws),
        "n_clusters": int(g),
        "restricted": True
    }


def compute_robustness(input_path, output_path, scores_path=None, econometrics_path=None):
    if input_path.endswith('.csv'):
        # Individual-level microdata estimation with Mincerian controls
        print("Loading microdata for robustness analysis...")
        df = pd.read_csv(input_path)
        
        if scores_path is None:
            scores_path = os.path.join(base_dir, 'data/output/scores.json')
        if econometrics_path is None:
            econometrics_path = os.path.join(base_dir, 'data/output/econometrics.json')
            
        with open(scores_path, 'r', encoding='utf-8') as f:
            scores = json.load(f)
        exposure_map = {k: v.get('exposure') for k, v in scores.items() if k != '_meta' and v.get('exposure') is not None}
        
        df['occupation'] = df['occupation'].astype(str)
        df['exposure'] = df['occupation'].map(exposure_map)
        df = df.dropna(subset=['exposure', 'years_of_study', 'income', 'informal', 'uf', 'occupation', 'weight', 'age', 'sex', 'race'])
        
        df['age'] = df['age'].astype(float)
        df['age_sq'] = df['age'] ** 2
        df['is_female'] = (df['sex'] == 2).astype(float)
        race_dummies = pd.get_dummies(df['race'], prefix='race', drop_first=True).astype(float)
        df = pd.concat([df, race_dummies], axis=1)
        
        mincerian_cols = ['age', 'age_sq', 'is_female'] + list(race_dummies.columns)
        
        y = df['exposure']
        w = df['weight']
        clusters = df['occupation']
        n_clusters = df['occupation'].nunique()
        
        X1_cols = ['years_of_study'] + mincerian_cols
        X1 = sm.add_constant(df[X1_cols])
        
        out = {}
        
        # R1: Weighting
        m_unweighted = sm.OLS(y, X1).fit(cov_type='cluster', cov_kwds={'groups': clusters})
        m_weighted = sm.WLS(y, X1, weights=w).fit(cov_type='cluster', cov_kwds={'groups': clusters})
        out['R1_weighting'] = {
            'description': 'S1 sem ponderacao por emprego (OLS) vs baseline ponderado (WLS), erros agrupados por ocupacao',
            'unweighted': extract_results(m_unweighted, n_clusters),
            'weighted': extract_results(m_weighted, n_clusters),
        }
        
        # R2: Wild bootstrap for S4 interaction
        df['formality_loo'] = _uf_formality_loo(df)
        df_s4 = df.dropna(subset=['formality_loo']).copy()
        df_s4['years_x_formality'] = df_s4['years_of_study'] * df_s4['formality_loo']
        
        y4 = df_s4['exposure'].values
        w4 = df_s4['weight'].values
        cl4 = df_s4['occupation'].values
        uf4 = df_s4['uf'].values
        X4_cols = ['years_of_study', 'years_x_formality', 'formality_loo'] + mincerian_cols
        X4 = sm.add_constant(df_s4[X4_cols]).values
        
        m_s4 = sm.WLS(y4, X4, weights=w4).fit(cov_type='cluster', cov_kwds={'groups': cl4})
        boot_res = fast_wild_bootstrap_mc(y4, X4, w4, clusters=uf4, idx=2, n_draws=1000)
        out['R2_wild_bootstrap_s4'] = {
            'description': 'Wild cluster bootstrap (Monte Carlo, grupos = 27 UFs) para a interacao de S4',
            'coefficient': 'years_x_formality',
            'baseline_occupation_clustered': extract_results(m_s4, df_s4['occupation'].nunique()),
            'bootstrap_region': boot_res,
        }
        
        # R3: Drop each major group COD
        df['major_group'] = df['occupation'].str[0]
        groups = sorted(df['major_group'].unique())
        by_group = {}
        for grp in groups:
            sub = df[df['major_group'] != grp]
            X_sub = sm.add_constant(sub[X1_cols])
            m_sub = sm.WLS(sub['exposure'], X_sub, weights=sub['weight']).fit(cov_type='cluster', cov_kwds={'groups': sub['occupation']})
            by_group[grp] = extract_results(m_sub, sub['occupation'].nunique())
        out['R3_drop_major_group'] = {
            'description': 'S1 reestimado excluindo cada grande grupo COD (primeiro digito) um a um',
            'n_groups': len(groups),
            'by_group': by_group,
        }
        
        # R4: Functional form log(exposure + 1)
        y_log = np.log(y + 1.0)
        m_log = sm.WLS(y_log, X1, weights=w).fit(cov_type='cluster', cov_kwds={'groups': clusters})
        out['R4_log_outcome'] = {
            'description': 'S1 com log(exposicao + 1) como variavel dependente',
            'results': extract_results(m_log, n_clusters),
        }
        
        # R5: Outliers
        lo, hi = np.percentile(y, [1.0, 99.0])
        y_win = np.clip(y, lo, hi)
        m_win = sm.WLS(y_win, X1, weights=w).fit(cov_type='cluster', cov_kwds={'groups': clusters})
        
        keep_p99 = y <= hi
        df_p99 = df[keep_p99]
        X_p99 = sm.add_constant(df_p99[X1_cols])
        m_p99 = sm.WLS(df_p99['exposure'], X_p99, weights=df_p99['weight']).fit(cov_type='cluster', cov_kwds={'groups': df_p99['occupation']})
        out['R5_outliers'] = {
            'description': 'S1 sob tratamento de valores extremos de exposicao',
            'winsorized_1_99': extract_results(m_win, n_clusters),
            'dropped_above_p99': extract_results(m_p99, df_p99['occupation'].nunique()),
            'thresholds': {'p1': float(lo), 'p99': float(hi)},
        }
        
        # R6: Oster bound
        with open(econometrics_path, 'r', encoding='utf-8') as f:
            econ = json.load(f)['specifications']
        s1_res = econ['S1']['results_clustered_occupation']
        s2_res = econ['S2']['results_clustered_occupation']
        out['R6_oster'] = {
            'description': 'Limite de Oster (2019) para o gradiente: quanto o coeficiente se move ao adicionar renda (S1 -> S2)',
            'rmax_1': oster_bound(s1_res, s2_res, r_max=1.0),
            'rmax_1_3r2': oster_bound(s1_res, s2_res, r_max=min(1.0, 1.3 * s2_res['r_squared'])),
        }
        
        # R7: Mediation stability on R3 subsamples
        X3_cols = ['exposure', 'years_of_study'] + mincerian_cols
        med = {}
        for grp in groups:
            sub = df[df['major_group'] != grp]
            X3_sub = sm.add_constant(sub[X3_cols])
            m_med = sm.WLS(sub['informal'] * 100.0, X3_sub, weights=sub['weight']).fit(cov_type='cluster', cov_kwds={'groups': sub['occupation']})
            med[grp] = extract_results(m_med, sub['occupation'].nunique())
        out['R7_mediation_stability'] = {
            'description': 'S3 (informalidade ~ exposicao + escolaridade) nas subamostras de R3',
            'by_group': med,
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        return out
        
    else:
        # Cell-level JSON panel fallback for unit tests
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f).get('data', [])
        rows = _filter_valid(data)
        if not rows:
            raise ValueError("No valid rows in the regional panel after filtering.")

        y = np.array([r['exposure'] for r in rows])
        w = np.array([r['jobs'] for r in rows])
        cl_occ = [r['occupation_code'] for r in rows]
        X1 = np.array([[1.0, r['avg_anos_estudo']] for r in rows])
        X2 = np.array([[1.0, r['avg_anos_estudo'], r['renda']] for r in rows])

        s1 = wls_regression(X1, y, w)
        s2 = wls_regression(X2, y, w)
        out = {}

        out['R1_weighting'] = {
            'description': 'S1 sem ponderacao por emprego (OLS) vs baseline ponderado (WLS), erros agrupados por ocupacao',
            'unweighted': wls_regression_clustered(X1, y, np.ones_like(y), cl_occ),
            'weighted': wls_regression_clustered(X1, y, w, cl_occ),
        }

        X4, y4, w4, cl4, rg4 = _s4_matrices(rows)
        out['R2_wild_bootstrap_s4'] = {
            'description': 'Wild cluster bootstrap de Rademacher (enumeracao exaustiva, grupos = grande regiao) para a interacao de S4',
            'coefficient': 'avg_anos_estudo_x_formality_loo',
            'baseline_occupation_clustered': wls_regression_clustered(X4, y4, w4, cl4),
            'bootstrap_region': wild_cluster_bootstrap_p(X4, y4, w4, rg4, idx=2,
                                                         restricted=True),
        }

        groups = sorted({r['occupation_code'][0] for r in rows})
        by_group = {}
        for grp in groups:
            sub = [r for r in rows if r['occupation_code'][0] != grp]
            Xg = np.array([[1.0, r['avg_anos_estudo']] for r in sub])
            yg = np.array([r['exposure'] for r in sub])
            wg = np.array([r['jobs'] for r in sub])
            clg = [r['occupation_code'] for r in sub]
            by_group[grp] = wls_regression_clustered(Xg, yg, wg, clg)
        out['R3_drop_major_group'] = {
            'description': 'S1 reestimado excluindo cada grande grupo COD (primeiro digito) um a um',
            'n_groups': len(groups),
            'by_group': by_group,
        }

        y_log = np.log(y + 1.0)
        out['R4_log_outcome'] = {
            'description': 'S1 com log(exposicao + 1) como variavel dependente',
            'results': wls_regression_clustered(X1, y_log, w, cl_occ),
        }

        lo, hi = np.percentile(y, [1.0, 99.0])
        keep = y <= hi
        cld = [c for c, k in zip(cl_occ, keep) if k]
        out['R5_outliers'] = {
            'description': 'S1 sob tratamento de valores extremos de exposicao',
            'winsorized_1_99': wls_regression_clustered(
                X1, np.clip(y, lo, hi), w, cl_occ),
            'dropped_above_p99': wls_regression_clustered(
                X1[keep], y[keep], w[keep], cld),
            'thresholds': {'p1': float(lo), 'p99': float(hi)},
        }

        out['R6_oster'] = {
            'description': 'Limite de Oster (2019) para o gradiente: quanto o coeficiente se move ao adicionar renda (S1 -> S2)',
            'rmax_1': oster_bound(s1, s2, r_max=1.0),
            'rmax_1_3r2': oster_bound(s1, s2, r_max=min(1.0, 1.3 * s2['r_squared'])),
        }

        med = {}
        for grp in groups:
            sub = [r for r in rows if r['occupation_code'][0] != grp]
            X3g = np.array([[1.0, r['exposure'], r['avg_anos_estudo']] for r in sub])
            y3g = np.array([r['informality'] for r in sub])
            wg = np.array([r['jobs'] for r in sub])
            clg = [r['occupation_code'] for r in sub]
            med[grp] = wls_regression_clustered(X3g, y3g, wg, clg)
        out['R7_mediation_stability'] = {
            'description': 'S3 (informalidade ~ exposicao + escolaridade) nas subamostras de R3',
            'by_group': med,
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        return out


if __name__ == '__main__':
    microdata_file = os.path.join(base_dir, 'data/output/individual_microdata.csv')
    scores_file = os.path.join(base_dir, 'data/output/scores.json')
    econometrics_file = os.path.join(base_dir, 'data/output/econometrics.json')
    output_file = os.path.join(base_dir, 'data/output/robustness.json')
    compute_robustness(microdata_file, output_file, scores_file, econometrics_file)
    print(f"Created {output_file}")
