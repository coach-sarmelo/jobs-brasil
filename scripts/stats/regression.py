import itertools

import numpy as np

from . import hypothesis


def wls_regression(X, y, w=None):
    """Regressao OLS/WLS multivariada com erros padrao robustos (White/HC1)."""
    if w is None:
        w = np.ones_like(y)
        
    n, k = X.shape
    
    XWX_inv = np.linalg.pinv(X.T @ (w[:, None] * X))
    beta = XWX_inv @ X.T @ (w * y)
    
    e = y - X @ beta
    
    X_tilde = np.sqrt(w)[:, None] * X
    e_tilde = np.sqrt(w) * e
    meat = X_tilde.T @ ((e_tilde**2)[:, None] * X_tilde)
    
    if n <= k:
        V = np.full((k, k), np.nan)
    else:
        V = (n / (n - k)) * XWX_inv @ meat @ XWX_inv
        
    se = np.sqrt(np.diag(V))
    
    with np.errstate(invalid='ignore'):
        t = beta / se
    p_values = [hypothesis.two_sided_p_value(t_val) if not np.isnan(t_val) else None for t_val in t]
    
    y_mean_w = np.sum(w * y) / np.sum(w)
    ss_res = np.sum(w * e**2)
    ss_tot = np.sum(w * (y - y_mean_w)**2)
    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    
    return {
        "beta": beta.tolist(),
        "se": se.tolist(),
        "t": t.tolist(),
        "p_value": p_values,
        "r_squared": float(r_squared),
        "n": int(n)
    }


def wls_regression_clustered(X, y, w=None, clusters=None):
    """Regressao WLS com erros padrao agrupados (cluster-robust, CR3-assimptotico).

    Segue Cameron, Gelbach e Miller (2008): estimador sandwich com a "carne"
    somada por grupo. Para WLS, o sanduiche e montado sobre as variaveis
    ponderadas (X_tilde = sqrt(w)*X; e_tilde = sqrt(w)*e), de modo que a
    ponderacao por emprego nao elimina a correlacao intra-grupo.
    """
    if w is None:
        w = np.ones_like(y)
    if clusters is None:
        raise ValueError("clusters e obrigatorio (use wls_regression para HC1).")

    n, k = X.shape

    XWX_inv = np.linalg.pinv(X.T @ (w[:, None] * X))
    beta = XWX_inv @ X.T @ (w * y)
    e = y - X @ beta

    X_tilde = np.sqrt(w)[:, None] * X
    e_tilde = np.sqrt(w) * e

    clusters = np.asarray(clusters)
    unique = np.unique(clusters)
    g = len(unique)

    meat = np.zeros((k, k))
    for cl in unique:
        idx = clusters == cl
        s = X_tilde[idx].T @ e_tilde[idx]
        meat += np.outer(s, s)

    if g > 1 and n > k:
        corr = (g / (g - 1)) * ((n - 1) / (n - k))
        V = corr * XWX_inv @ meat @ XWX_inv
    else:
        V = np.full((k, k), np.nan)

    se = np.sqrt(np.diag(V))

    with np.errstate(invalid='ignore'):
        t = beta / se
    p_values = [hypothesis.two_sided_p_value(t_val) if not np.isnan(t_val) else None for t_val in t]

    y_mean_w = np.sum(w * y) / np.sum(w)
    ss_res = np.sum(w * e**2)
    ss_tot = np.sum(w * (y - y_mean_w)**2)
    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    return {
        "beta": beta.tolist(),
        "se": se.tolist(),
        "t": t.tolist(),
        "p_value": p_values,
        "r_squared": float(r_squared),
        "n": int(n),
        "n_clusters": int(g)
    }


def wild_cluster_bootstrap_p(X, y, w, clusters, idx, restricted=True):
    """p-valor do wild cluster bootstrap (Rademacher) para o coeficiente idx.

    Com poucos grupos (G <= 12) enumeramos exaustivamente os 2^G vetores de
    sinais — sem aleatoriedade, resultado exato e reproduzivel. Versao
    "restricted" (WCR): a hipotese nula e imposta ao gerar y*, como em
    Cameron, Gelbach e Miller (2008); residuos da regressao restrita.
    """
    clusters = np.asarray(clusters)
    unique = np.unique(clusters)
    g = len(unique)
    if g < 2:
        raise ValueError("wild bootstrap precisa de >= 2 grupos.")
    if g > 12:
        raise ValueError("enumeracao exaustiva exige G <= 12.")

    full = wls_regression_clustered(X, y, w, clusters)
    t_hat = full['t'][idx]

    if restricted:
        X0 = np.delete(X, idx, axis=1)
        beta0 = np.array(wls_regression(X0, y, w)['beta'])
        center = X0 @ beta0
        resid = y - center
    else:
        beta = np.array(full['beta'])
        center = X @ beta
        resid = y - center

    count = 0
    total = 0
    for signs in itertools.product((1.0, -1.0), repeat=g):
        v = np.empty(len(y))
        for s, cl in zip(signs, unique):
            v[clusters == cl] = s
        y_star = center + v * resid
        t_star = wls_regression_clustered(X, y_star, w, clusters)['t'][idx]
        total += 1
        if np.isfinite(t_star) and abs(t_star) >= abs(t_hat):
            count += 1

    return {
        "p": (count + 1) / (total + 1),
        "t_stat": float(t_hat),
        "n_draws": total,
        "n_clusters": int(g),
        "restricted": restricted
    }
