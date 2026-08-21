import numpy as np
import pytest

from scripts.stats.logit import wls_logit

def test_wls_logit_basic():
    # Simple case where logistic regression should work
    np.random.seed(42)
    n = 100
    X = np.random.randn(n, 2)
    X[:, 0] = 1.0 # intercept
    true_beta = np.array([-0.5, 1.5])
    eta = X @ true_beta
    p = 1.0 / (1.0 + np.exp(-eta))
    y = (np.random.rand(n) < p).astype(float)
    w = np.ones(n)
    
    result = wls_logit(X, y, w)
    
    # Check that beta is estimated
    assert len(result['beta']) == 2
    assert len(result['se']) == 2
    assert result['n'] == 100
    assert result['iterations'] > 0
    assert "COMPOSIÇÃO" in result['disclaimer']
    
def test_wls_logit_weighted():
    # Test with weights
    X = np.array([[1, 0], [1, 1], [1, 2], [1, 3]])
    y = np.array([0, 1, 0, 1])
    w = np.array([10, 20, 20, 10])
    
    result = wls_logit(X, y, w)
    
    assert len(result['beta']) == 2
    assert result['beta'][1] > 0  # Slope should be positive since y increases with X

def test_wls_logit_perfect_separation():
    # Perfect separation case
    X = np.array([[1, -10], [1, -5], [1, 5], [1, 10]])
    y = np.array([0, 0, 1, 1])
    w = np.ones(4)
    
    with pytest.raises(ValueError, match="perfect separation"):
        wls_logit(X, y, w, max_iter=50)

def test_wls_logit_empty_cells():
    X = np.array([[1, 1]])
    y = np.array([1])
    w = np.array([0])
    
    with pytest.raises(ValueError, match="No observations with positive weights"):
        wls_logit(X, y, w)

def test_wls_logit_divergence():
    # Extreme collinearity
    X = np.array([[1, 2, 4], [1, 2, 4], [1, 3, 6], [1, 3, 6]])
    y = np.array([0, 1, 0, 1])
    w = np.ones(4)
    
    with pytest.raises(ValueError, match="rank-deficient"):
        wls_logit(X, y, w)
