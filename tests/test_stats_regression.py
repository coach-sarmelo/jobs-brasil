import numpy as np

from scripts.stats.regression import wls_regression


def test_wls_regression():
    X = np.array([[1, 2], [1, 3], [1, 4], [1, 5]])
    y = np.array([2, 4, 5, 4])
    w = np.array([1, 2, 3, 4])
    
    res = wls_regression(X, y, w)
    
    assert res["n"] == 4
    assert np.allclose(res["beta"], [2.5, 0.4])
    assert np.allclose(res["se"], [1.94514781, 0.47159304])
    assert np.allclose(res["t"], [1.28524937, 0.84818893])
    assert np.allclose(res["p_value"], [0.19870516, 0.39633276])
    assert np.isclose(res["r_squared"], 0.2318840579710142)


def test_ols_fallback():
    X = np.array([[1, 2], [1, 3], [1, 4], [1, 5]])
    y = np.array([2, 4, 5, 4])
    
    res = wls_regression(X, y)
    
    assert res["n"] == 4
    assert len(res["beta"]) == 2
    assert len(res["se"]) == 2
    assert len(res["p_value"]) == 2


def test_perfect_fit_r_squared():
    X = np.array([[1, 2], [1, 3]])
    y = np.array([4, 6])
    res = wls_regression(X, y)
    
    assert np.isclose(res["r_squared"], 1.0)
