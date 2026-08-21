import os
import json
import pytest
import numpy as np
import sys

statsmodels = pytest.importorskip("statsmodels.api")

# Add scripts directory to path
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from scripts.stats.regression import wls_regression
from scripts.stats.logit import wls_logit

pytestmark = pytest.mark.crossval

@pytest.fixture(scope="module")
def panel_data():
    os.makedirs(os.path.join(base_dir, 'data/output'), exist_ok=True)
    panel_path = os.path.join(base_dir, 'data/output/regional_panel.json')
    with open(panel_path, 'r', encoding='utf-8') as f:
        panel_data = json.load(f)
    return panel_data.get('data', [])

def test_wls_regression_matches_statsmodels(panel_data):
    # Same filter as compute_econometrics.py
    valid_rows = []
    for row in panel_data:
        if (row.get('exposure') is not None and 
            row.get('avg_anos_estudo') is not None and 
            row.get('renda') is not None and 
            row.get('jobs') is not None and 
            row.get('jobs') > 0):
            valid_rows.append(row)
            
    assert len(valid_rows) > 0, "No valid rows found"
    
    y = np.array([r['exposure'] for r in valid_rows])
    w = np.array([r['jobs'] for r in valid_rows])
    
    # Specification 2: exposure on avg_anos_estudo and renda
    X = np.array([[1.0, r['avg_anos_estudo'], r['renda']] for r in valid_rows])
    
    # Custom WLS
    ours = wls_regression(X, y, w)
    
    # Statsmodels WLS
    sm_model = statsmodels.WLS(y, X, weights=w)
    sm_results = sm_model.fit(cov_type='HC1')
    
    np.testing.assert_allclose(ours["beta"], sm_results.params, rtol=1e-5, atol=1e-8)
    np.testing.assert_allclose(ours["se"], sm_results.bse, rtol=1e-5, atol=1e-8)
    np.testing.assert_allclose(ours["t"], sm_results.tvalues, rtol=1e-5, atol=1e-8)
    
    # p-values might have nan issues, but usually fine
    ours_p = np.array([p if p is not None else np.nan for p in ours["p_value"]])
    np.testing.assert_allclose(ours_p, sm_results.pvalues, rtol=1e-5, atol=1e-8)
    
    assert ours["r_squared"] == pytest.approx(sm_results.rsquared)

def test_wls_logit_matches_statsmodels(panel_data):
    # Same filter as logit.py
    valid_rows = []
    for row in panel_data:
        if (row.get('exposure') is not None and 
            row.get('informality') is not None and 
            row.get('jobs') is not None and 
            row.get('jobs') > 0):
            valid_rows.append(row)
            
    assert len(valid_rows) > 0, "No valid rows found"
    
    # P75 exposure
    sorted_rows = sorted(valid_rows, key=lambda r: r['exposure'])
    total_jobs = sum(r['jobs'] for r in sorted_rows)
    cum_jobs = 0
    p75_exposure = None
    for row in sorted_rows:
        cum_jobs += row['jobs']
        if cum_jobs >= 0.75 * total_jobs:
            p75_exposure = row['exposure']
            break
            
    y = np.array([1.0 if r['exposure'] > p75_exposure else 0.0 for r in valid_rows])
    w = np.array([r['jobs'] for r in valid_rows])
    
    regions = sorted(list(set(r['region'] for r in valid_rows)))
    reference_region = 'Sudeste' if 'Sudeste' in regions else regions[0]
    region_dummies = [reg for reg in regions if reg != reference_region]
    
    has_sector = any(r.get('sector') is not None for r in valid_rows)
    if has_sector:
        sectors = sorted(list(set(r['sector'] for r in valid_rows if r.get('sector') is not None)))
        reference_sector = sectors[0]
        sector_dummies = [sec for sec in sectors if sec != reference_sector]
    else:
        sector_dummies = []
        
    X_list = []
    for row in valid_rows:
        x_row = [1.0, row['informality']]
        for reg in region_dummies:
            x_row.append(1.0 if row['region'] == reg else 0.0)
        for sec in sector_dummies:
            x_row.append(1.0 if row.get('sector') == sec else 0.0)
        X_list.append(x_row)
        
    X = np.array(X_list)
    
    # Custom Logit
    ours = wls_logit(X, y, w)
    
    # Statsmodels GLM with Binomial family and var_weights
    sm_model = statsmodels.GLM(y, X, family=statsmodels.families.Binomial(), var_weights=w)
    sm_results = sm_model.fit(cov_type='HC1')
    
    n, k = X.shape
    correction = np.sqrt(n / (n - k))
    
    np.testing.assert_allclose(ours["beta"], sm_results.params, rtol=1e-5, atol=1e-5)
    np.testing.assert_allclose(ours["se"], sm_results.bse * correction, rtol=1e-5, atol=1e-5)
    np.testing.assert_allclose(ours["t"], sm_results.tvalues / correction, rtol=1e-5, atol=1e-5)
    
    ours_p = np.array([p if p is not None else np.nan for p in ours["p_value"]])
    scipy_stats = pytest.importorskip("scipy.stats")
    expected_p = 2 * scipy_stats.norm.sf(np.abs(ours["t"]))
    np.testing.assert_allclose(ours_p, expected_p, rtol=1e-5, atol=1e-5)
