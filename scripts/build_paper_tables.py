"""Gera as tabelas LaTeX do artigo a partir dos artefatos em data/output.

Uso: python3 scripts/build_paper_tables.py
Saidas: paper/tables/tab_descritivas.tex, tab_maiores.tex,
        tab_gradiente.tex, tab_s3.tex, tab_s4.tex,
        tab_robustez.tex, tab_robustez_grupos.tex

Cada tabela e um tabular (booktabs) puro; o \\begin{table} e a legenda
ficam nas secoes do artigo.
"""
import json
import os

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(base_dir, 'paper', 'tables')


def fmt(x, dec=2):
    """Formata numero no padrao pt-BR (virgula decimal)."""
    s = f"{x:,.{dec}f}"
    return s.replace(',', 'X').replace('.', ',').replace('X', '.')


def stars(p):
    if p is None:
        return ''
    if p < 0.01:
        return '***'
    if p < 0.05:
        return '**'
    if p < 0.10:
        return '*'
    return ''


def coef_row(label, specs, idx, scale=1.0, dec=2):
    """Duas linhas fisicas: coeficientes com estrelas; erros-padrao abaixo."""
    coefs, ses = [], []
    for res in specs:
        if res is None:
            coefs.append('--')
            ses.append('')
            continue
        b = res['beta'][idx] * scale
        se = res['se'][idx] * scale
        coefs.append(f"{fmt(b, dec)}{stars(res['p_value'][idx])}")
        ses.append(f"({fmt(se, dec)})")
    return (f"{label} & " + " & ".join(coefs) + r" \\" + "\n" +
            " & " + " & ".join(ses) + r" \\")


def stat_row(label, specs, key):
    cells = []
    for res in specs:
        if res is None:
            cells.append('--')
        elif key == 'r_squared':
            cells.append(f"{res[key]:.3f}".replace('.', ','))
        elif key == 'n' and isinstance(res[key], (int, float)):
            cells.append(fmt(int(res[key]), 0))
        else:
            cells.append(str(res[key]))
    return f"{label} & " + " & ".join(cells) + r" \\"



def load(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    os.makedirs(OUT, exist_ok=True)

    econ = load(os.path.join(base_dir, 'data/output/econometrics.json'))['specifications']
    panel = load(os.path.join(base_dir, 'data/output/regional_panel.json'))['data']
    scores = {k: v for k, v in load(os.path.join(base_dir, 'data/output/scores.json')).items()}
    national_raw = load(os.path.join(base_dir, 'data/output/cod_subgroups.json'))
    # Fix 1 (scripts/process_microdata.py): aceita lista (antigo) ou dict com `meta` + `occupations`.
    national = national_raw.get("occupations") if isinstance(national_raw, dict) else national_raw

    def res(name):
        s = econ[name]
        return s['results_clustered_occupation'] if 'results_clustered_occupation' in s else s['results']

    # ---------------- Tabela 1: gradiente (S1, S2) ----------------
    s1, s2 = res('S1'), res('S2')
    rows = [
        coef_row(r"Anos de escolaridade", [s1, s2], 1),
        coef_row(r"Rendimento habitual (por R\$ 1.000)", [None, s2], 2, scale=1e3, dec=3),
        coef_row(r"Constante", [s1, s2], 0),
        r"\midrule",
        stat_row(r"$R^2$", [s1, s2], 'r_squared'),
        stat_row(r"$N$ (indiv\'iduos)", [s1, s2], 'n'),
        stat_row(r"Grupos (ocupa\c c\~oes)", [s1, s2], 'n_clusters'),
    ]
    write_tab('tab_gradiente.tex', rows)

    # ---------------- Tabela 2: informalidade (S3a, S3) ----------------
    s3a, s3 = res('S3a'), res('S3')
    rows = [
        coef_row(r"Exposi\c c\~ao \`a IA (0--10)", [s3a, s3], 1),
        coef_row(r"Anos de escolaridade", [None, s3], 2),
        coef_row(r"Constante", [s3a, s3], 0),
        r"\midrule",
        stat_row(r"$R^2$", [s3a, s3], 'r_squared'),
        stat_row(r"$N$ (indiv\'iduos)", [s3a, s3], 'n'),
        stat_row(r"Grupos (ocupa\c c\~oes)", [s3a, s3], 'n_clusters'),
    ]
    write_tab('tab_s3.tex', rows)

    # ---------------- Tabela 3: interacao regional (S4) ----------------
    s4 = res('S4')
    rows = [
        coef_row(r"Anos de escolaridade", [s4], 1),
        coef_row(r"Escolaridade $\times$ formalidade regional", [s4], 2),
        coef_row(r"Formalidade regional (0--1)", [s4], 3),
        coef_row(r"Constante", [s4], 0),
        r"\midrule",
        stat_row(r"$R^2$", [s4], 'r_squared'),
        stat_row(r"$N$ (indiv\'iduos)", [s4], 'n'),
        stat_row(r"Grupos (ocupa\c c\~oes)", [s4], 'n_clusters'),
    ]
    write_tab('tab_s4.tex', rows)

    # ---------------- Tabela 4: descritivas (individuos, ponderadas) ----------------
    # A amostra econométrica e no nivel do individuo (Seção 5); as descritivas
    # acompanham: medias e desvios ponderados pelos pesos amostrais (V1028).
    import csv as _csv
    exp_map = {code: (v.get('exposure') if isinstance(v, dict) else None)
               for code, v in scores.items()}
    rows_e, rows_s, rows_i, rows_r = [], [], [], []
    with open(os.path.join(base_dir, 'data/output/individual_microdata.csv'),
              newline='', encoding='utf-8') as f:
        for rec in _csv.DictReader(f):
            e = exp_map.get(rec['occupation'])
            if e is None:
                continue
            w = float(rec['weight'])
            rows_e.append((w, e))
            rows_s.append((w, float(rec['years_of_study'])))
            rows_i.append((w, 100.0 * int(rec['informal'])))
            rows_r.append((w, float(rec['income'])))

    def wstats(pairs, dec):
        tot = sum(w for w, _ in pairs)
        mu = sum(w * v for w, v in pairs) / tot
        sd = (sum(w * (v - mu) ** 2 for w, v in pairs) / tot) ** 0.5
        vs = [v for _, v in pairs]
        return (len(pairs), fmt(mu, dec), fmt(sd, dec),
                fmt(min(vs), dec), fmt(max(vs), dec))

    rows = []
    for label, pairs, dec in [
        (r"Exposi\c c\~ao \`a IA (0--10)", rows_e, 2),
        (r"Escolaridade (anos)", rows_s, 2),
        (r"Informalidade (\%)", rows_i, 1),
        (r"Rendimento habitual (R\$)", rows_r, 0),
    ]:
        n_, mu, sd, lo, hi = wstats(pairs, dec)
        rows.append(f"{label} & {fmt(n_, 0)} & {mu} & {sd} & {lo} & {hi} \\\\")
    write_tab('tab_descritivas.tex', rows)

    # ---------------- Tabela 5: dez maiores ocupacoes ----------------
    # escolaridade nacional = media ponderada por emprego das celulas regionais
    esc = {}
    for r in panel:
        if r.get('avg_anos_estudo') is None:
            continue
        c = r['occupation_code']
        t, e = esc.get(c, (0.0, 0.0))
        esc[c] = (t + r['jobs'], e + r['jobs'] * r['avg_anos_estudo'])
    top = sorted(national, key=lambda o: -o['total_workers'])[:10]
    rows = []
    for o in top:
        code = o['code']
        exp = scores.get(code, {}).get('exposure')
        esc_n = esc[code][1] / esc[code][0] if code in esc and esc[code][0] > 0 else None
        rows.append(
            f"{tex_escape(truncate(o['name'], 52))} & {fmt(o['total_workers'] / 1e6, 1)} & "
            f"{fmt(exp, 1) if exp is not None else '--'} & "
            f"{fmt(esc_n, 1) if esc_n is not None else '--'} & "
            f"{fmt(o['informality_rate'], 1)} & {fmt(o['avg_income'], 0)} \\\\"
        )
    write_tab('tab_maiores.tex', rows)

    # ---------------- Tabela 6: robustez do gradiente (S1) ----------------
    rob = load(os.path.join(base_dir, 'data/output/robustness.json'))
    specs = [s1,
             rob['R1_weighting']['unweighted'],
             rob['R5_outliers']['winsorized_1_99'],
             rob['R5_outliers']['dropped_above_p99'],
             rob['R4_log_outcome']['results']]
    rows = [
        coef_row(r"Anos de escolaridade", specs, 1),
        coef_row(r"Constante", specs, 0),
        r"\midrule",
        stat_row(r"$R^2$", specs, 'r_squared'),
        stat_row(r"$N$ (indiv\'iduos)", specs, 'n'),
    ]
    write_tab('tab_robustez.tex', rows)

    # ---------------- Tabela A1: robustez por grande grupo ---------------
    # Nomes condensados dos grandes grupos (COD e compativel com ISCO-08).
    GROUP_LABELS = {
        '1': r"Dirigentes e gerentes",
        '2': r"Profissionais das ci\^encias e intelectuais",
        '3': r"T\'ecnicos de n\'ivel m\'edio",
        '4': r"Apoio administrativo",
        '5': r"Servi\c cos e vendedores",
        '6': r"Agropecu\'aria e pesca",
        '7': r"Ind\'ustria, constru\c c\~ao e artes",
        '8': r"Operadores e montadores",
        '9': r"Ocupa\c c\~oes elementares",
    }
    r3 = rob['R3_drop_major_group']['by_group']
    r7 = rob['R7_mediation_stability']['by_group']
    rows = []
    for grp in sorted(r3):
        a, b = r3[grp], r7[grp]
        rows.append(
            f"{GROUP_LABELS[grp]} & "
            f"{fmt(a['beta'][1], 2)}{stars(a['p_value'][1])} ({fmt(a['se'][1], 2)}) & "
            f"{fmt(b['beta'][1], 2)}{stars(b['p_value'][1])} ({fmt(b['se'][1], 2)}) \\\\"
        )
    write_tab('tab_robustez_grupos.tex', rows)

    print(f"Created tables in {OUT}")


def truncate(s, n):
    return s if len(s) <= n else s[:n - 3].rstrip() + '...'


def tex_escape(s):
    return s.replace('&', r'\&').replace('%', r'\%').replace('_', r'\_')


def write_tab(name, rows):
    # A ultima linha NAO pode terminar em "\\": quando o arquivo e lido via
    # \input dentro de um tabular, o "\\" no fim do arquivo quebra o
    # \bottomrule ("Misplaced \noalign"). O "\\" da ultima linha fica no
    # wrapper da secao (\input{...} \\).
    rows = list(rows)
    last = rows[-1].rstrip()
    if last.endswith('\\\\'):
        last = last[:-2].rstrip()
    rows[-1] = last
    with open(os.path.join(OUT, name), 'w', encoding='utf-8') as f:
        f.write("% AUTO-GERADO por scripts/build_paper_tables.py — nao editar a mao\n")
        f.write("\n".join(rows) + "\n")


if __name__ == '__main__':
    main()
