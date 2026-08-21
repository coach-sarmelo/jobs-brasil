import json
import os
import tempfile
import pytest

from scripts.compute_econometrics import compute_econometrics

def test_compute_econometrics():
    # Create mock regional panel data
    mock_panel = {
        "metadata": {"decisions": []},
        "data": [
            {
                "region": "Norte",
                "occupation_code": "911",
                "exposure": 0.1,
                "avg_anos_estudo": 9.5,
                "renda": 1500.0,
                "informality": 60.0,
                "jobs": 1000
            },
            {
                "region": "Norte",
                "occupation_code": "915",
                "exposure": 0.3,
                "avg_anos_estudo": 10.5,
                "renda": 1800.0,
                "informality": 45.0,
                "jobs": 800
            },
            {
                "region": "Sul",
                "occupation_code": "912",
                "exposure": 0.5,
                "avg_anos_estudo": 12.0,
                "renda": 2500.0,
                "informality": 30.0,
                "jobs": 2000
            },
            {
                "region": "Sudeste",
                "occupation_code": "913",
                "exposure": 0.8,
                "avg_anos_estudo": 15.0,
                "renda": 4000.0,
                "informality": 15.0,
                "jobs": 5000
            },
            # This row should be skipped due to missing renda
            {
                "region": "Nordeste",
                "occupation_code": "914",
                "exposure": 0.2,
                "avg_anos_estudo": 8.0,
                "jobs": 500
            }
        ]
    }

    with tempfile.TemporaryDirectory() as temp_dir:
        os.makedirs(os.path.join(temp_dir, 'data/output'), exist_ok=True)
        panel_path = os.path.join(temp_dir, 'data/output/regional_panel.json')
        output_path = os.path.join(temp_dir, 'data/output/econometrics.json')

        with open(panel_path, 'w') as f:
            json.dump(mock_panel, f)

        compute_econometrics(panel_path, output_path)

        assert os.path.exists(output_path)

        with open(output_path, 'r', encoding='utf-8') as f:
            output = json.load(f)

        # Check structure
        assert "specifications" in output
        assert "disclaimers" in output

        specs = output["specifications"]
        assert "S1" in specs
        assert "S2" in specs

        # Check S1
        s1 = specs["S1"]
        assert s1["variables"] == ["intercept", "avg_anos_estudo"]
        assert "beta" in s1["results"]
        assert len(s1["results"]["beta"]) == 2
        assert s1["results"]["n"] == 4

        # Check S2
        s2 = specs["S2"]
        assert s2["variables"] == ["intercept", "avg_anos_estudo", "renda"]
        assert "beta" in s2["results"]
        assert len(s2["results"]["beta"]) == 3

        # Check S3 (conditional), S3a (raw) and S4 (interaction)
        s3 = specs["S3"]
        assert s3["variables"] == ["intercept", "exposure", "avg_anos_estudo"]
        assert s3["clustering"] == "occupation_code"
        assert len(s3["results"]["beta"]) == 3
        assert s3["results"]["n"] == 4

        s3a = specs["S3a"]
        assert s3a["variables"] == ["intercept", "exposure"]
        assert len(s3a["results"]["beta"]) == 2

        s4 = specs["S4"]
        assert s4["variables"] == [
            "intercept", "avg_anos_estudo",
            "avg_anos_estudo_x_formality_loo", "formality_loo"
        ]
        assert len(s4["results"]["beta"]) == 4
        # apenas as duas celulas do Norte tem LOO definido (912 e 913
        # sao unicas em suas regioes e saem de S4)
        assert s4["results"]["n"] == 2

        # Check disclaimers length and content
        disclaimers = output["disclaimers"]
        assert len(disclaimers) == 4
        assert "A unidade de análise é a célula ocupação×região" in disclaimers[0]
        assert "β1 mede sorting" in disclaimers[1]

def test_compute_econometrics_empty_panel():
    mock_panel = {
        "metadata": {"decisions": []},
        "data": []
    }
    with tempfile.TemporaryDirectory() as temp_dir:
        os.makedirs(os.path.join(temp_dir, 'data/output'), exist_ok=True)
        panel_path = os.path.join(temp_dir, 'data/output/regional_panel.json')
        output_path = os.path.join(temp_dir, 'data/output/econometrics.json')
        
        with open(panel_path, 'w') as f:
            json.dump(mock_panel, f)
            
        with pytest.raises(ValueError, match="No valid rows found in the regional panel after filtering."):
            compute_econometrics(panel_path, output_path)
