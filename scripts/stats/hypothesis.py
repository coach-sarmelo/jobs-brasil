import math


def normal_cdf(z):
    """CDF da normal padrao via funcao erro (stdlib): Phi(z) = 0.5*(1+erf(z/sqrt(2)))."""
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def two_sided_p_value(z):
    """p-valor bicaudal para estatistica z: 2*(1-Phi(|z|))."""
    return 2 * (1 - normal_cdf(abs(z)))


def z_test_diff(mean_a, se_a, mean_b, se_b, alpha=0.05):
    """Teste z de diferenca entre duas medias/proporcoes ponderadas independentes.

    z = (a-b)/sqrt(se_a^2+se_b^2), assumindo subpopulacoes disjuntas (ex.:
    homens vs mulheres) e portanto independentes. Usado para os gaps de
    genero/raca (SPEC.md F4) — sinaliza quando um gap nao e estatisticamente
    distinguivel de zero.
    """
    if mean_a is None or mean_b is None or se_a is None or se_b is None:
        return None

    se_diff = math.sqrt(se_a ** 2 + se_b ** 2)
    if se_diff == 0:
        return None

    z = (mean_a - mean_b) / se_diff
    p_value = two_sided_p_value(z)
    return {"z": z, "p_value": p_value, "significant": p_value < alpha}
