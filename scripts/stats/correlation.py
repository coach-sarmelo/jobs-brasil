import math

from . import hypothesis


def pearson_r(xs, ys):
    """Correlacao de Pearson entre duas series pareadas."""
    n = len(xs)
    if n < 2 or n != len(ys):
        return None

    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    if var_x == 0 or var_y == 0:
        return None

    return cov / math.sqrt(var_x * var_y)


def linear_regression(xs, ys):
    """Regressao linear simples via equacoes normais: y = intercept + slope*x."""
    n = len(xs)
    if n < 2 or n != len(ys):
        return None

    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    sxx = sum((x - mean_x) ** 2 for x in xs)
    if sxx == 0:
        return None

    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    slope = sxy / sxx
    intercept = mean_y - slope * mean_x
    return {"slope": slope, "intercept": intercept}


def correlation_significance(r, n, alpha=0.05):
    """Significancia de r via transformacao z de Fisher: z = atanh(r)*sqrt(n-3).

    Aproximacao assintoticamente normal, cf. Fisher (1921); valida para n
    moderado/grande. Para n pequeno (ex.: 10 grandes grupos), o resultado
    deve ser lido com cautela — ver ressalva na pagina de metodologia (F3).
    """
    if r is None or n < 4:
        return None

    if abs(r) >= 1:
        # z seria infinito (atanh(+-1)) — nao serializavel como JSON padrao
        # (JS JSON.parse rejeita o token `Infinity`). p ja e 0.0, entao nada
        # downstream precisa do z infinito.
        p_value = 0.0
        z_stat = None
    else:
        z_stat = math.atanh(r) * math.sqrt(n - 3)
        p_value = hypothesis.two_sided_p_value(z_stat)

    return {"z": z_stat, "p_value": p_value, "significant": p_value < alpha}
