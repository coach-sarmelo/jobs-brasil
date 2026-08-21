import json
import os
import tempfile

from scripts.compute_robustness import compute_robustness


def _mock_panel():
    rows = []
    specs = [
        # (region, code, exposure, schooling, income, informality, jobs)
        ("Norte", "211", 0.2, 9.0, 1400.0, 55.0, 1000),
        ("Norte", "411", 4.0, 12.0, 2600.0, 25.0, 900),
        ("Norte", "511", 0.5, 8.0, 1200.0, 60.0, 1500),
        ("Sul", "211", 0.3, 10.0, 1600.0, 45.0, 1200),
        ("Sul", "411", 4.5, 13.0, 3000.0, 20.0, 1100),
        ("Sul", "511", 0.4, 9.0, 1500.0, 50.0, 1300),
        ("Sul", "811", 2.0, 9.5, 1900.0, 40.0, 800),
    ]
    for region, code, exp, esc, renda, inf, jobs in specs:
        rows.append({
            "region": region, "occupation_code": code,
            "exposure": exp, "avg_anos_estudo": esc, "renda": renda,
            "informality": inf, "jobs": jobs,
        })
    # invalid row: missing informality -> filtered out
    rows.append({"region": "Norte", "occupation_code": "911",
                 "exposure": 1.0, "avg_anos_estudo": 9.0,
                 "renda": 1700.0, "jobs": 400})
    return {"metadata": {"decisions": []}, "data": rows}


def test_compute_robustness():
    with tempfile.TemporaryDirectory() as temp_dir:
        os.makedirs(os.path.join(temp_dir, 'data/output'), exist_ok=True)
        panel_path = os.path.join(temp_dir, 'data/output/regional_panel.json')
        output_path = os.path.join(temp_dir, 'data/output/robustness.json')
        with open(panel_path, 'w') as f:
            json.dump(_mock_panel(), f)

        out = compute_robustness(panel_path, output_path)

        assert os.path.exists(output_path)
        with open(output_path, 'r', encoding='utf-8') as f:
            saved = json.load(f)
        assert set(saved) == set(out)

        expected_keys = {'R1_weighting', 'R2_wild_bootstrap_s4',
                         'R3_drop_major_group', 'R4_log_outcome',
                         'R5_outliers', 'R6_oster', 'R7_mediation_stability'}
        assert set(out) == expected_keys

        # R1: same beta when weights are uniform? no — but both run
        assert out['R1_weighting']['unweighted']['n'] == 7
        assert out['R1_weighting']['weighted']['n'] == 7

        # R2: bootstrap p in (0, 1], exact enumeration by region
        boot = out['R2_wild_bootstrap_s4']['bootstrap_region']
        assert 0 < boot['p'] <= 1
        assert boot['n_draws'] == 2 ** boot['n_clusters']
        assert boot['n_clusters'] == 2  # duas regioes no mock
        assert boot['restricted'] is True

        # R3: one entry per major group present (2, 4, 5, 8)
        by_group = out['R3_drop_major_group']['by_group']
        assert set(by_group) == {'2', '4', '5', '8'}
        for res in by_group.values():
            assert res['n'] < 7

        # R4: log outcome runs and has 2 coefficients
        assert len(out['R4_log_outcome']['results']['beta']) == 2

        # R5: thresholds recorded
        assert out['R5_outliers']['thresholds']['p99'] >= \
            out['R5_outliers']['thresholds']['p1']

        # R6: oster bound computed or gracefully skipped
        for variant in ('rmax_1', 'rmax_1_3r2'):
            bound = out['R6_oster'][variant]
            assert 'delta_for_zero' in bound
            assert 'beta_star_delta1' in bound
            if bound['delta_for_zero'] is not None:
                assert abs(bound['beta_uncontrolled'] -
                           bound['beta_controlled']) > 1e-12

        # R7: same groups as R3, informalidade como dependente
        assert set(out['R7_mediation_stability']['by_group']) == \
            {'2', '4', '5', '8'}


def test_compute_robustness_empty_panel():
    with tempfile.TemporaryDirectory() as temp_dir:
        os.makedirs(os.path.join(temp_dir, 'data/output'), exist_ok=True)
        panel_path = os.path.join(temp_dir, 'data/output/regional_panel.json')
        output_path = os.path.join(temp_dir, 'data/output/robustness.json')
        with open(panel_path, 'w') as f:
            json.dump({"metadata": {}, "data": []}, f)

        try:
            compute_robustness(panel_path, output_path)
            assert False, "expected ValueError"
        except ValueError as exc:
            assert "No valid rows" in str(exc)
