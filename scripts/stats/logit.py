import os
import json
import numpy as np

# `make refresh` executa este arquivo diretamente (python scripts/stats/logit.py),
# quando o import relativo falha (__package__=None); como modulo
# (python -m scripts.stats.logit) o relativo e o correto.
try:
    from . import hypothesis
except ImportError:
    import hypothesis

def wls_logit(X, y, w=None, max_iter=100, tol=1e-8):
    """
    Regressão logística ponderada usando Iteratively Reweighted Least Squares (IRLS).
    Erro-padrão robusto à heterocedasticidade (Sandwich/HC1).
    """
    # Converter para numpy arrays
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    if w is None:
        w = np.ones_like(y, dtype=float)
    else:
        w = np.asarray(w, dtype=float)
        
    n, k = X.shape
    
    # Check for empty cells or no positive weights
    if n == 0 or np.sum(w) <= 0:
        raise ValueError("No observations with positive weights.")
        
    beta = np.zeros(k)
    
    for iteration in range(max_iter):
        eta = X @ beta
        # Prevent overflow in exp
        eta = np.clip(eta, -250, 250)
        mu = 1.0 / (1.0 + np.exp(-eta))
        
        # Prevent mu from being exactly 0 or 1 to avoid S=0 globally
        mu = np.clip(mu, 1e-15, 1.0 - 1e-15)
        
        S = w * mu * (1.0 - mu)
        H = X.T @ (S[:, None] * X)
        
        # Check if Hessian is singular or ill-conditioned
        # which can happen with perfect separation or multicollinearity
        try:
            cond = np.linalg.cond(H)
        except np.linalg.LinAlgError:
            cond = np.inf
            
        if cond > 1e12:
            raise ValueError("Design matrix is rank-deficient or perfect separation occurred.")
            
        gradient = X.T @ (w * (y - mu))
        
        # Update beta
        delta = np.linalg.solve(H, gradient)
        beta += delta
        
        if np.max(np.abs(delta)) < tol:
            break
        if np.max(np.abs(beta)) > 100:
            raise ValueError("Perfect separation detected: coefficients diverged.")
    else:
        raise ValueError("IRLS failed to converge within max_iter. Possible perfect separation.")
        
    # Standard Errors (Sandwich / HC1)
    # H is the Fisher Information Matrix (already computed)
    H_inv = np.linalg.pinv(H)
    
    # Meat matrix
    meat = X.T @ ( (w**2 * (y - mu)**2)[:, None] * X )
    
    if n <= k:
        V = np.full((k, k), np.nan)
    else:
        V = (n / (n - k)) * H_inv @ meat @ H_inv
        
    # Handle negative variances in diagonal (rare but possible due to numerical issues)
    diag_V = np.diag(V)
    se = np.full(k, np.nan)
    valid = diag_V > 0
    se[valid] = np.sqrt(diag_V[valid])
    
    with np.errstate(invalid='ignore'):
        t = beta / se
    p_values = [hypothesis.two_sided_p_value(t_val) if not np.isnan(t_val) else None for t_val in t]
    
    return {
        "beta": beta.tolist(),
        "se": se.tolist(),
        "t": t.tolist(),
        "p_value": p_values,
        "n": int(n),
        "iterations": iteration + 1,
        "disclaimer": "O coeficiente de informalidade descreve COMPOSIÇÃO (células mais informais estão mais ou menos presentes em ocupações substituíveis), não risco individual de substituição."
    }

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    panel_file = os.path.join(base_dir, 'data/output/regional_panel.json')
    output_file = os.path.join(base_dir, 'data/output/logit_results.json')
    
    with open(panel_file, 'r', encoding='utf-8') as f:
        panel_data = json.load(f)
        
    data = panel_data.get('data', [])
    
    # Filter valid rows
    valid_rows = []
    for row in data:
        if (row.get('exposure') is not None and 
            row.get('informality') is not None and 
            row.get('jobs') is not None and 
            row.get('jobs') > 0):
            valid_rows.append(row)
            
    if not valid_rows:
        raise ValueError("No valid rows found in the regional panel.")
        
    # Calculate 75th percentile of exposure weighted by jobs
    # First, sort by exposure
    valid_rows.sort(key=lambda r: r['exposure'])
    total_jobs = sum(r['jobs'] for r in valid_rows)
    
    cum_jobs = 0
    p75_exposure = None
    for row in valid_rows:
        cum_jobs += row['jobs']
        if cum_jobs >= 0.75 * total_jobs:
            p75_exposure = row['exposure']
            break
            
    # Prepare dependent variable
    y = np.array([1.0 if r['exposure'] > p75_exposure else 0.0 for r in valid_rows])
    w = np.array([r['jobs'] for r in valid_rows])
    
    # Build design matrix X
    # Variables: Intercept, Informality, Region Dummies (excluding reference), Sector Dummies (if available)
    
    # Find unique regions
    regions = sorted(list(set(r['region'] for r in valid_rows)))
    # Use the first one alphabetically as reference (e.g. Centro-Oeste) or Sudeste
    if 'Sudeste' in regions:
        reference_region = 'Sudeste'
    else:
        reference_region = regions[0]
        
    region_dummies = [reg for reg in regions if reg != reference_region]
    
    # Check if we have sector dummies (Task 11)
    has_sector = any(r.get('sector') is not None for r in valid_rows)
    if has_sector:
        sectors = sorted(list(set(r['sector'] for r in valid_rows if r.get('sector') is not None)))
        reference_sector = sectors[0]
        sector_dummies = [sec for sec in sectors if sec != reference_sector]
    else:
        sector_dummies = []
        
    variables = ["intercept", "informality"] + [f"region_{reg}" for reg in region_dummies] + [f"sector_{sec}" for sec in sector_dummies]
    
    X = []
    for row in valid_rows:
        x_row = [1.0, row['informality']]
        for reg in region_dummies:
            x_row.append(1.0 if row['region'] == reg else 0.0)
        for sec in sector_dummies:
            x_row.append(1.0 if row.get('sector') == sec else 0.0)
        X.append(x_row)
        
    X = np.array(X)
    
    print(f"Running logit regression (N={len(valid_rows)}, target exposure > {p75_exposure})")
    
    res = wls_logit(X, y, w)
    
    output = {
        "description": "Logit ponderado da probabilidade de estar em ocupação de alta exposição (acima do percentil 75).",
        "p75_exposure_threshold": p75_exposure,
        "variables": variables,
        "results": res
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        
    print(f"Results saved to {output_file}")

if __name__ == '__main__':
    main()
