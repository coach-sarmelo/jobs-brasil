import math

# 97.5o percentil da normal padrao — usado para IC 95% (estimate +/- Z_95*SE).
Z_95 = 1.959963984540054


def weighted_mean(w_sum, wsum_x):
    """Media ponderada: Sigma(w*x)/Sigma(w)."""
    if w_sum <= 0:
        return None
    return wsum_x / w_sum


def weighted_variance(w_sum, wsum_x, wsum_x_sq):
    """Variancia ponderada via forma computacional: Sigma(w*x^2)/Sigma(w) - media^2."""
    if w_sum <= 0:
        return None
    mean = wsum_x / w_sum
    variance = (wsum_x_sq / w_sum) - mean ** 2
    return max(variance, 0.0)  # evita negativo por erro de ponto flutuante


def effective_n(w_sum, w_sq_sum):
    """Tamanho amostral efetivo via efeito de desenho de Kish: n_eff = Sigma(w)^2/Sigma(w^2).

    Aproximacao padrao de erro padrao ponderado quando so se tem os pesos
    finais (sem UPA/Estrato), cf. Kish, Survey Sampling (1965); Lohr,
    Sampling: Design and Analysis.
    """
    if w_sq_sum <= 0:
        return 0.0
    return (w_sum ** 2) / w_sq_sum


def standard_error_mean(w_sum, wsum_x, wsum_x_sq, w_sq_sum):
    """Erro padrao da media ponderada: SE = s_w/sqrt(n_eff), cf. Lohr, Sampling: Design and Analysis."""
    n_eff = effective_n(w_sum, w_sq_sum)
    if n_eff <= 1:
        return None
    variance = weighted_variance(w_sum, wsum_x, wsum_x_sq)
    if variance is None:
        return None
    return math.sqrt(variance / n_eff)


def weighted_proportion(w_sum, w_numerator):
    """Proporcao ponderada: Sigma(w em que evento ocorre)/Sigma(w)."""
    if w_sum <= 0:
        return None
    return w_numerator / w_sum


def standard_error_proportion(w_sum, w_numerator, w_sq_sum):
    """Erro padrao de proporcao ponderada: SE = sqrt(p*(1-p)/n_eff), cf. Lohr, Sampling: Design and Analysis."""
    n_eff = effective_n(w_sum, w_sq_sum)
    if n_eff <= 1:
        return None
    p = weighted_proportion(w_sum, w_numerator)
    if p is None:
        return None
    return math.sqrt(p * (1 - p) / n_eff)


def ci_95(estimate, se):
    """Intervalo de confianca de 95% via aproximacao normal: estimate +/- Z_95*SE."""
    if estimate is None or se is None:
        return None
    margin = Z_95 * se
    return (estimate - margin, estimate + margin)
