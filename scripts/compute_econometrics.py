import json
import os
import sys
import numpy as np
import pandas as pd
import statsmodels.api as sm

# Adjust PYTHONPATH so we can import from scripts
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from scripts.stats.regression import wls_regression, wls_regression_clustered


def _region_formality_loo(valid_rows):
    """Taxa de formalidade regional excluindo a propria ocupacao (leave-one-out)."""
    sums = {}
    for row in valid_rows:
        r = row['region']
        formal_jobs = row['jobs'] * (1.0 - row['informality'] / 100.0)
        tot, form = sums.get(r, (0.0, 0.0))
        sums[r] = (tot + row['jobs'], form + formal_jobs)

    loo = []
    for row in valid_rows:
        r = row['region']
        formal_jobs = row['jobs'] * (1.0 - row['informality'] / 100.0)
        tot_loo = sums[r][0] - row['jobs']
        form_loo = sums[r][1] - formal_jobs
        loo.append(form_loo / tot_loo if tot_loo > 0 else None)
    return loo


def _uf_formality_loo(df):
    """Calcula formalidade regional leave-one-out por UF."""
    uf_totals = df.groupby('uf')['weight'].sum()
    df['formal_weight'] = df['weight'] * (1 - df['informal'])
    uf_formals = df.groupby('uf')['formal_weight'].sum()
    
    tot_uf = df['uf'].map(uf_totals)
    form_uf = df['uf'].map(uf_formals)
    
    tot_loo = tot_uf - df['weight']
    form_loo = form_uf - df['formal_weight']
    
    loo = np.where(tot_loo > 0, form_loo / tot_loo, np.nan)
    return loo


def extract_results(model_result, n_clusters):
    return {
        "beta": model_result.params.tolist(),
        "se": model_result.bse.tolist(),
        "p_value": model_result.pvalues.tolist(),
        "r_squared": float(model_result.rsquared),
        "n": int(model_result.nobs),
        "n_clusters": int(n_clusters)
    }


def compute_econometrics(input_path, output_path, scores_path=None):
    if input_path.endswith('.csv'):
        # Individual-level microdata estimation with Mincerian controls
        print("Loading individual microdata...")
        df = pd.read_csv(input_path)
        
        if scores_path is None:
            scores_path = os.path.join(base_dir, 'data/output/scores.json')
            
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
        clusters = df['occupation']
        n_clusters = df['occupation'].nunique()
        weights = df['weight']
        
        output = {"specifications": {}, "disclaimers": []}
        
        # S1: exposure ~ years_of_study + Mincerian
        y1 = df['exposure']
        X1_cols = ['years_of_study'] + mincerian_cols
        X1 = sm.add_constant(df[X1_cols])
        model_s1 = sm.WLS(y1, X1, weights=weights).fit(cov_type='cluster', cov_kwds={'groups': clusters})
        output["specifications"]["S1"] = {
            "description": "Regressão de exposição sobre escolaridade com controles mincerianos (individual-level)",
            "results_clustered_occupation": extract_results(model_s1, n_clusters)
        }

        # S2: exposure ~ years_of_study + income + Mincerian
        X2_cols = ['years_of_study', 'income'] + mincerian_cols
        X2 = sm.add_constant(df[X2_cols])
        model_s2 = sm.WLS(y1, X2, weights=weights).fit(cov_type='cluster', cov_kwds={'groups': clusters})
        output["specifications"]["S2"] = {
            "description": "Regressão de exposição sobre escolaridade, renda e mincerianos",
            "results_clustered_occupation": extract_results(model_s2, n_clusters)
        }

        # S3: informality ~ exposure + years_of_study + Mincerian
        y3 = df['informal'] * 100.0
        X3_cols = ['exposure', 'years_of_study'] + mincerian_cols
        X3 = sm.add_constant(df[X3_cols])
        model_s3 = sm.WLS(y3, X3, weights=weights).fit(cov_type='cluster', cov_kwds={'groups': clusters})
        output["specifications"]["S3"] = {
            "description": "Regressão da taxa de informalidade sobre exposição, escolaridade e mincerianos",
            "results_clustered_occupation": extract_results(model_s3, n_clusters)
        }

        # S3a: informality ~ exposure + Mincerian
        X3a_cols = ['exposure'] + mincerian_cols
        X3a = sm.add_constant(df[X3a_cols])
        model_s3a = sm.WLS(y3, X3a, weights=weights).fit(cov_type='cluster', cov_kwds={'groups': clusters})
        output["specifications"]["S3a"] = {
            "description": "Regressão da taxa de informalidade sobre exposição e mincerianos (incondicional escolaridade)",
            "results_clustered_occupation": extract_results(model_s3a, n_clusters)
        }

        # S4: regional heterogeneity at 27-UF level
        df['formality_loo'] = _uf_formality_loo(df)
        df_s4 = df.dropna(subset=['formality_loo']).copy()
        df_s4['years_x_formality'] = df_s4['years_of_study'] * df_s4['formality_loo']
        
        y4 = df_s4['exposure']
        w4 = df_s4['weight']
        clusters_s4 = df_s4['occupation']
        n_clusters_s4 = df_s4['occupation'].nunique()
        
        X4_cols = ['years_of_study', 'years_x_formality', 'formality_loo'] + mincerian_cols
        X4 = sm.add_constant(df_s4[X4_cols])
        model_s4 = sm.WLS(y4, X4, weights=w4).fit(cov_type='cluster', cov_kwds={'groups': clusters_s4})
        
        output["specifications"]["S4"] = {
            "description": "Gradiente interagido com formalidade regional 27-UF leave-one-out",
            "results_clustered_occupation": extract_results(model_s4, n_clusters_s4)
        }
        
        disclaimers = [
            "A unidade de análise é o indivíduo com controles mincerianos (idade, sexo, raça), rodado nos microdados completos.",
            "β1 mede sorting com variância individual, controlando para fatores demográficos estruturais do mercado de trabalho brasileiro.",
            "Erros-padrão são agrupados por ocupação.",
            "Em S4 a formalidade regional varia entre as 27 Unidades da Federação (UFs), resolvendo a fragilidade estatística da estimação original em 5 regiões."
        ]
        output["disclaimers"] = disclaimers

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
            
    else:
        # Cell-level JSON panel fallback for unit tests and backwards compatibility
        with open(input_path, 'r', encoding='utf-8') as f:
            panel_data = json.load(f)

        data = panel_data.get('data', [])
        valid_rows = []
        for row in data:
            if (row.get('exposure') is not None and
                row.get('avg_anos_estudo') is not None and
                row.get('renda') is not None and
                row.get('informality') is not None and
                row.get('region') is not None and
                row.get('occupation_code') is not None and
                row.get('jobs') is not None and
                row.get('jobs') > 0):
                valid_rows.append(row)

        if not valid_rows:
            raise ValueError("No valid rows found in the regional panel after filtering.")

        y = np.array([r['exposure'] for r in valid_rows])
        w = np.array([r['jobs'] for r in valid_rows])
        clusters_occ = [r['occupation_code'] for r in valid_rows]

        X1 = np.array([[1.0, r['avg_anos_estudo']] for r in valid_rows])
        s1_res = wls_regression(X1, y, w)
        s1_cl = wls_regression_clustered(X1, y, w, clusters_occ)

        X2 = np.array([[1.0, r['avg_anos_estudo'], r['renda']] for r in valid_rows])
        s2_res = wls_regression(X2, y, w)
        s2_cl = wls_regression_clustered(X2, y, w, clusters_occ)

        y3 = np.array([r['informality'] for r in valid_rows])
        X3 = np.array([[1.0, r['exposure'], r['avg_anos_estudo']] for r in valid_rows])
        s3_res = wls_regression_clustered(X3, y3, w, clusters_occ)

        X3a = np.array([[1.0, r['exposure']] for r in valid_rows])
        s3a_res = wls_regression_clustered(X3a, y3, w, clusters_occ)

        formality_loo = _region_formality_loo(valid_rows)
        s4_rows, s4_loo = [], []
        for row, f in zip(valid_rows, formality_loo):
            if f is not None:
                s4_rows.append(row)
                s4_loo.append(f)
        if not s4_rows:
            raise ValueError("No valid rows for S4 (all regions have a single occupation).")
        y4 = np.array([r['exposure'] for r in s4_rows])
        w4 = np.array([r['jobs'] for r in s4_rows])
        cl4 = [r['occupation_code'] for r in s4_rows]
        X4 = np.array([[1.0,
                        r['avg_anos_estudo'],
                        r['avg_anos_estudo'] * f,
                        f]
                       for r, f in zip(s4_rows, s4_loo)])
        s4_res = wls_regression_clustered(X4, y4, w4, cl4)

        disclaimers = [
            "A unidade de análise é a célula ocupação×região (grande região IBGE), não a pessoa — nenhuma inferência sobre indivíduos deve ser sugerida no texto.",
            "β1 mede sorting — como a exposição da ocupação varia com a escolaridade média de quem a exerce naquela região — e um β1>0 diz que hoje ocupações mais escolarizadas tendem a estar mais expostas ao índice de Eloundou et al., não que a IA vai atingir mais os escolarizados.",
            "S3 e S4 são associações de equilíbrio (sorting ocupacional), não efeitos causais da exposição sobre a informalidade; a exposição é constante dentro da ocupação, então os erros-padrão são agrupados por ocupação (~124 grupos).",
            "Em S4 a formalidade regional varia apenas entre 5 grandes regiões — a interação é grosseira e deve ser lida como sugestiva."
        ]

        output = {
            "specifications": {
                "S1": {
                    "description": "Regressão de exposição sobre escolaridade (gradiente bruto)",
                    "variables": ["intercept", "avg_anos_estudo"],
                    "results": s1_res,
                    "results_clustered_occupation": s1_cl
                },
                "S2": {
                    "description": "Regressão de exposição sobre escolaridade e renda (condicional)",
                    "variables": ["intercept", "avg_anos_estudo", "renda"],
                    "results": s2_res,
                    "results_clustered_occupation": s2_cl
                },
                "S3": {
                    "description": "Regressão da taxa de informalidade sobre exposição e escolaridade (Proposição 2)",
                    "variables": ["intercept", "exposure", "avg_anos_estudo"],
                    "clustering": "occupation_code",
                    "results": s3_res
                },
                "S3a": {
                    "description": "Regressão da taxa de informalidade sobre exposição, incondicional (bruta)",
                    "variables": ["intercept", "exposure"],
                    "clustering": "occupation_code",
                    "results": s3a_res
                },
                "S4": {
                    "description": "Gradiente escolaridade-exposição interagido com formalidade regional leave-one-out (Proposição 3)",
                    "variables": ["intercept", "avg_anos_estudo", "avg_anos_estudo_x_formality_loo", "formality_loo"],
                    "clustering": "occupation_code",
                    "results": s4_res
                }
            },
            "disclaimers": disclaimers
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    microdata_file = os.path.join(base_dir, 'data/output/individual_microdata.csv')
    scores_file = os.path.join(base_dir, 'data/output/scores.json')
    output_file = os.path.join(base_dir, 'data/output/econometrics.json')
    compute_econometrics(microdata_file, output_file, scores_file)
    print(f"Created {output_file}")
