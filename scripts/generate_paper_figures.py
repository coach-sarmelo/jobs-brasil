#!/usr/bin/env python3
"""
generate_paper_figures.py
Gera figuras de qualidade para publicação acadêmica (PDF e PNG) em paper/figures/
usando os dados reais calculados pelo pipeline em data/output/.
"""

import json
import os
import numpy as np
import matplotlib.pyplot as plt

# Configuração de estilo Tufte / JEP
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Helvetica', 'Arial'],
    'font.size': 9,
    'axes.labelsize': 10,
    'axes.titlesize': 11,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 8.5,
    'figure.titlesize': 12,
    'axes.linewidth': 0.8,
    'axes.edgecolor': '#333333',
    'grid.color': '#E5E5E5',
    'grid.linestyle': '-',
    'grid.linewidth': 0.6,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'pdf.fonttype': 42,
    'ps.fonttype': 42
})

OUTPUT_DIR = "paper/figures"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def generate_fig1_gradient():
    """Figura 1: Dispersão ponderada e gradiente Escolaridade x Exposição."""
    panel = load_json("data/output/regional_panel.json")["data"]
    econ = load_json("data/output/econometrics.json")["specifications"]["S1"]
    res = econ.get("results_clustered_occupation") or econ["results"]
    
    escolaridade = np.array([d["avg_anos_estudo"] for d in panel])
    exposicao = np.array([d["exposure"] for d in panel])
    emprego = np.array([d["jobs"] for d in panel])
    
    # Coeficiente individual (nível de trabalhador, com controles mincerianos) para anotação
    b1_ind = res["beta"][1]
    se1_ind = res["se"][1]
    
    # Ajuste no nível de célula (WLS ponderado por emprego) para a linha passar pela nuvem
    w = emprego / emprego.sum()
    W = np.diag(w)
    X = np.column_stack([np.ones_like(escolaridade), escolaridade])
    b_cell = np.linalg.inv(X.T @ W @ X) @ (X.T @ W @ exposicao)
    b0_cell, b1_cell = b_cell[0], b_cell[1]
    
    fig, ax = plt.subplots(figsize=(6.5, 4.3))
    
    sizes = 12 + 180 * (emprego - emprego.min()) / (emprego.max() - emprego.min())
    
    ax.scatter(
        escolaridade, exposicao, s=sizes,
        color="#2B5C8F", alpha=0.45, edgecolors="#1B3A5B", linewidth=0.5, zorder=2,
        label="Célula ocupação × região (área = emprego)"
    )

    # Reta ajustada apenas na faixa observada de escolaridade (sem extrapolar abaixo de θ = 0)
    x_grid = np.linspace(escolaridade.min(), escolaridade.max(), 100)
    y_fit = b0_cell + b1_cell * x_grid

    ax.plot(x_grid, y_fit, color="#C0392B", linewidth=2.0, zorder=3,
            label=f"Ajuste de célula (WLS): $\\hat{{\\beta}}_1 = {b1_cell:.2f}$")
    # Anotação com o coeficiente individual (S1, controles mincerianos, erros agrupados por ocupação)
    ci_lo = b1_ind - 1.959964 * se1_ind
    ci_hi = b1_ind + 1.959964 * se1_ind
    ax.text(0.99, 0.02,
            f"Coef. individual (S1): $\\hat{{\\beta}}_1 = {b1_ind:.2f}$ (EP ${se1_ind:.2f}$)\n"
            f"IC 95%: [{ci_lo:.2f}; {ci_hi:.2f}], N = 227.629, "
            f"erros agrupados por ocupação",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=8,
            color="#333333", bbox=dict(facecolor="white", alpha=0.9, edgecolor="#BBBBBB"),
            zorder=5)

    annotations = [
        ("Trabalho doméstico\n(θ = 0,1)", 9.0, 0.1, (22, 12)),
        ("Construção estrutural\n(θ = 0,9)", 8.3, 0.9, (18, -28)),
        ("Escriturários gerais\n(θ = 5,8)", 13.5, 5.8, (-70, 14)),
        ("Desenvolvedores\n(θ = 7,5)", 15.7, 7.5, (-75, -22)),
        ("Comerciantes e vendedores\n(θ = 4,1)", 11.7, 4.1, (18, -18))
    ]

    for text, x_pos, y_pos, offset in annotations:
        ax.annotate(
            text, xy=(x_pos, y_pos), xytext=offset, textcoords="offset points",
            fontsize=8.5, fontweight="bold", color="#1A1A1A", zorder=4,
            arrowprops=dict(arrowstyle="->", color="#444444", lw=0.8, shrinkB=4,
                            connectionstyle="arc3,rad=0.12")
        )

    ax.set_xlabel("Escolaridade Média da Célula (Anos de Estudo)", fontsize=11)
    ax.set_ylabel(r"Índice de Exposição à IA ($\theta_j$)", fontsize=11)
    ax.set_xlim(5.0, 16.8)
    ax.set_ylim(-1.0, 8.8)
    ax.tick_params(labelsize=9.5)
    ax.grid(True, alpha=0.45, linewidth=0.6)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.legend(frameon=True, facecolor="white", edgecolor="#DDDDDD", loc="upper left",
              framealpha=0.9, fontsize=9)
    
    plt.tight_layout()
    pdf_path = os.path.join(OUTPUT_DIR, "fig1_gradiente.pdf")
    png_path = os.path.join(OUTPUT_DIR, "fig1_gradiente.png")
    plt.savefig(pdf_path)
    plt.savefig(png_path)
    plt.close()
    print(f"Gerado: {pdf_path}")


def generate_fig2_mediation():
    """Figura 2: Associação bruta vs. parcial entre Exposição e Informalidade (Mediação)."""
    panel = load_json("data/output/regional_panel.json")["data"]
    econ = load_json("data/output/econometrics.json")["specifications"]
    
    exposicao = np.array([d["exposure"] for d in panel])
    informalidade = np.array([d["informality"] for d in panel])
    escolaridade = np.array([d["avg_anos_estudo"] for d in panel])
    emprego = np.array([d["jobs"] for d in panel])
    
    s3a = econ["S3a"].get("results_clustered_occupation") or econ["S3a"]["results"]
    s3b = econ["S3"].get("results_clustered_occupation") or econ["S3"]["results"]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.0, 4.0))
    
    sizes = 10 + 130 * (emprego - emprego.min()) / (emprego.max() - emprego.min())
    
    # Painel A: Bruta
    ax1.scatter(exposicao, informalidade, s=sizes, color="#2E7D32", alpha=0.35, edgecolors="#1B5E20", linewidth=0.5)
    # Ajuste no nível de célula (WLS ponderado por emprego) para a linha passar pela nuvem
    w = emprego / emprego.sum()
    W = np.diag(w)
    X_a = np.column_stack([np.ones_like(exposicao), exposicao])
    b_a_cell = np.linalg.inv(X_a.T @ W @ X_a) @ (X_a.T @ W @ informalidade)
    x_grid_a = np.linspace(0.1, 7.8, 100)
    y_fit_a = b_a_cell[0] + b_a_cell[1] * x_grid_a
    # Anotação com o coeficiente individual (S3a, controles mincerianos)
    lbl_a = f"Ajuste de célula (WLS): $\\hat{{\\gamma}}_1 = {b_a_cell[1]:.2f}$ p.p."
    ax1.plot(x_grid_a, y_fit_a, color="#C0392B", linewidth=1.8, label=lbl_a)
    ax1.text(0.99, 0.02,
            f"Coef. individual (S3a): $\\hat{{\\gamma}}_1 = {s3a['beta'][1]:.2f}$ p.p. "
            f"(EP ${s3a['se'][1]:.2f}$)***",
            transform=ax1.transAxes, ha="right", va="bottom", fontsize=7.5,
            color="#333333", bbox=dict(facecolor="white", alpha=0.85, edgecolor="#DDDDDD"))
    
    ax1.set_title(f"A. Relação Bruta (S3a: $R^2 = {s3a['r_squared']:.2f}$)", fontsize=10, fontweight="bold", pad=8)
    ax1.set_xlabel(r"Exposição à IA ($\theta_j$)")
    ax1.set_ylabel("Taxa de Informalidade (%)")
    ax1.set_xlim(-0.2, 8.2)
    ax1.set_ylim(-5, 105)
    ax1.grid(True)
    ax1.spines['top'].set_visible(False)
    ax1.spines['right'].set_visible(False)
    ax1.legend(frameon=True, facecolor="white", edgecolor="#DDDDDD", loc="upper right")
    
    # Painel B: Resíduos parciais (controlando por escolaridade)
    w = emprego / emprego.sum()
    W = np.diag(w)
    X_e = np.column_stack([np.ones_like(escolaridade), escolaridade])
    
    beta_inf = np.linalg.inv(X_e.T @ W @ X_e) @ (X_e.T @ W @ informalidade)
    res_inf = informalidade - X_e @ beta_inf
    
    beta_exp = np.linalg.inv(X_e.T @ W @ X_e) @ (X_e.T @ W @ exposicao)
    res_exp = exposicao - X_e @ beta_exp
    
    ax2.scatter(res_exp, res_inf, s=sizes, color="#455A64", alpha=0.35, edgecolors="#263238", linewidth=0.5)
    # Inclinação parcial no nível de célula (WLS dos resíduos, sem intercepto)
    b_partial = np.sum(w * res_exp * res_inf) / np.sum(w * res_exp**2)
    x_grid_b = np.linspace(res_exp.min(), res_exp.max(), 100)
    y_fit_b = b_partial * x_grid_b
    # Teste de significancia: z = |beta/se|
    z_b = abs(s3b["beta"][1] / s3b["se"][1])
    stars_b = "***" if z_b > 2.576 else ("**" if z_b > 1.96 else "")
    lbl_b = f"Ajuste de célula (WLS): $\\hat{{\\gamma}}_1 = {b_partial:.2f}$ p.p."
    ax2.plot(x_grid_b, y_fit_b, color="#C0392B", linewidth=1.8, linestyle="--", label=lbl_b)
    ax2.text(0.99, 0.02,
            f"Coef. individual (S3): $\\hat{{\\gamma}}_1 = {s3b['beta'][1]:.2f}$ p.p. "
            f"(EP ${s3b['se'][1]:.2f}$){stars_b}",
            transform=ax2.transAxes, ha="right", va="bottom", fontsize=7.5,
            color="#333333", bbox=dict(facecolor="white", alpha=0.85, edgecolor="#DDDDDD"))
    
    ax2.set_title(f"B. Regressão Parcial / Resíduos (S3: $R^2 = {s3b['r_squared']:.2f}$)", fontsize=10, fontweight="bold", pad=8)
    ax2.set_xlabel(r"Exposição Residual ($\theta_j \mid \text{escolaridade}$)")
    ax2.set_ylabel(r"Informalidade Residual (% $\mid \text{escolaridade}$)")
    ax2.grid(True)
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.legend(frameon=True, facecolor="white", edgecolor="#DDDDDD", loc="upper right")
    
    plt.tight_layout()
    pdf_path = os.path.join(OUTPUT_DIR, "fig2_mediacao.pdf")
    png_path = os.path.join(OUTPUT_DIR, "fig2_mediacao.png")
    plt.savefig(pdf_path)
    plt.savefig(png_path)
    plt.close()
    print(f"Gerado: {pdf_path}")


def generate_fig3_regional_slopes():
    """Figura 3: Inclinação do gradiente por Grande Região."""
    panel = load_json("data/output/regional_panel.json")["data"]
    
    regioes = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
    cores = {
        "Norte": "#E67E22",
        "Nordeste": "#D35400",
        "Centro-Oeste": "#27AE60",
        "Sudeste": "#2980B9",
        "Sul": "#8E44AD"
    }
    
    # Calcula formalidade regional a partir dos dados (ponderado por emprego)
    formality_map = {}
    for reg in regioes:
        sub = [d for d in panel if d["region"] == reg]
        total_emp = sum(d["jobs"] for d in sub)
        weighted_inf = sum(d["jobs"] * d["informality"] / total_emp for d in sub)
        formality_map[reg] = (100.0 - weighted_inf) / 100.0
    
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    
    for reg in regioes:
        sub = [d for d in panel if d["region"] == reg]
        esc = np.array([d["avg_anos_estudo"] for d in sub])
        exp = np.array([d["exposure"] for d in sub])
        emp = np.array([d["jobs"] for d in sub])
        
        ax.scatter(esc, exp, s=15 + 60*(emp/emp.max()), color=cores[reg], alpha=0.3, edgecolors="none")
        
        w = emp / emp.sum()
        X = np.column_stack([np.ones_like(esc), esc])
        b = np.linalg.inv(X.T @ np.diag(w) @ X) @ (X.T @ np.diag(w) @ exp)
        
        x_line = np.linspace(esc.min(), esc.max(), 50)
        lbl = f"{reg} (form.: {formality_map[reg]*100:.0f}%, slope = {b[1]:.2f})"
        ax.plot(x_line, b[0] + b[1]*x_line, color=cores[reg], linewidth=1.8, label=lbl)
    
    ax.set_xlabel("Escolaridade Média da Célula (Anos de Estudo)")
    ax.set_ylabel(r"Índice de Exposição à IA ($\theta_j$)")
    ax.set_title("Heterogeneidade Regional: Gradiente mais íngreme onde a formalidade é profunda", fontsize=10.5, pad=10)
    ax.set_xlim(5.0, 16.5)
    ax.set_ylim(0.0, 8.5)
    ax.grid(True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.legend(frameon=True, facecolor="white", edgecolor="#DDDDDD", loc="upper left", fontsize=8)
    
    plt.tight_layout()
    pdf_path = os.path.join(OUTPUT_DIR, "fig3_regional_slopes.pdf")
    png_path = os.path.join(OUTPUT_DIR, "fig3_regional_slopes.png")
    plt.savefig(pdf_path)
    plt.savefig(png_path)
    plt.close()
    print(f"Gerado: {pdf_path}")


def generate_fig5_forest_robustness():
    """Figura 5: Forest plot / coefficient plot de robustez (Tabela A1)."""
    rob = load_json("data/output/robustness.json")
    
    labels = [
        "Linha de Base (Amostra Completa)",
        "Sem Dirigentes e gerentes",
        "Sem Profissionais das ciências",
        "Sem Técnicos de nível médio",
        "Sem Apoio administrativo",
        "Sem Serviços e vendedores",
        "Sem Agropecuária e pesca",
        "Sem Indústria e construção",
        "Sem Operadores e montadores",
        "Sem Ocupações elementares",
        "Sem Ponderação (OLS não-ponderado)",
        "Exposição Winsorizada (1%/99%)",
        "Sem Outliers (exclui p > 99)"
    ]
    
    baseline_b = rob["R1_weighting"]["weighted"]["beta"][1]
    baseline_se = rob["R1_weighting"]["weighted"]["se"][1]
    
    betas = [baseline_b]
    ses = [baseline_se]
    
    # 9 grupos
    for g in range(1, 10):
        b = rob["R3_drop_major_group"]["by_group"][str(g)]["beta"][1]
        se = rob["R3_drop_major_group"]["by_group"][str(g)]["se"][1]
        betas.append(b)
        ses.append(se)
        
    # Unweighted
    betas.append(rob["R1_weighting"]["unweighted"]["beta"][1])
    ses.append(rob["R1_weighting"]["unweighted"]["se"][1])
    
    # Winsorized
    betas.append(rob["R5_outliers"]["winsorized_1_99"]["beta"][1])
    ses.append(rob["R5_outliers"]["winsorized_1_99"]["se"][1])
    
    # Trimming
    betas.append(rob["R5_outliers"]["dropped_above_p99"]["beta"][1])
    ses.append(rob["R5_outliers"]["dropped_above_p99"]["se"][1])
    
    betas = np.array(betas)
    ses = np.array(ses)
    ci_low = betas - 1.96 * ses
    ci_high = betas + 1.96 * ses
    
    M = len(betas)
    y_pos = np.arange(M, 0, -1)
    
    fig, ax = plt.subplots(figsize=(6.8, 4.8))
    
    ax.axvline(baseline_b, color="#B0BEC5", linestyle="--", linewidth=1.2, label=f"Linha de Base ({baseline_b:.2f})")
    
    for i in range(M):
        if i == 0:
            col = "#C0392B"
            marker = "s"
            ms = 6.5
        elif i >= 10:
            col = "#2E7D32"
            marker = "D"
            ms = 5.5
        else:
            col = "#1F4E78"
            marker = "o"
            ms = 5.5
            
        ax.plot([ci_low[i], ci_high[i]], [y_pos[i], y_pos[i]], color=col, linewidth=1.4)
        ax.plot(betas[i], y_pos[i], marker=marker, markersize=ms, color=col, markeredgecolor=col)
        
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=8.5)
    ax.set_xlabel(r"Coeficiente da Escolaridade ($\hat{\beta}_1$) $\pm$ IC 95%")
    ax.set_title("Estabilidade do Gradiente sob Variações de Amostra e Ponderação", fontsize=10.5, pad=10)
    ax.set_xlim(min(ci_low) - 0.05, max(ci_high) + 0.05)
    ax.set_ylim(0.4, M + 0.6)
    ax.grid(True)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.legend(frameon=True, facecolor="white", edgecolor="#DDDDDD", loc="upper right")
    
    plt.tight_layout()
    pdf_path = os.path.join(OUTPUT_DIR, "fig5_robustez_forest.pdf")
    png_path = os.path.join(OUTPUT_DIR, "fig5_robustez_forest.png")
    plt.savefig(pdf_path)
    plt.savefig(png_path)
    plt.close()
    print(f"Gerado: {pdf_path}")


if __name__ == "__main__":
    print("Gerando figuras do artigo...")
    generate_fig1_gradient()
    generate_fig2_mediation()
    generate_fig3_regional_slopes()
    generate_fig5_forest_robustness()
    print("Todas as figuras geradas com sucesso em paper/figures/.")
