import json
import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.build_regional_panel import build_regional_panel

def test_build_regional_panel():
    uf_codes = {
        "11": {"sigla": "RO", "regiao": "Norte"},
        "35": {"sigla": "SP", "regiao": "Sudeste"},
        "33": {"sigla": "RJ", "regiao": "Sudeste"}
    }
    
    subgroups = {
        "RO": [
            {
                "code": "111", "name": "Occ 1", "sample_size": 25, "total_workers": 100,
                "avg_age": 40, "avg_study_years": 10, "informal_weight_numerator": 50, "informal_weight_sum": 100,
                "predominant_sector": "A"
            },
            {
                "code": "222", "name": "Occ 2 (low sample)", "sample_size": 5, "total_workers": 10
            }
        ],
        "SP": [
            {
                "code": "111", "name": "Occ 1", "sample_size": 30, "total_workers": 200,
                "avg_age": 43, "avg_study_years": 11, "informal_weight_numerator": 80, "informal_weight_sum": 200,
                "predominant_sector": "B"
            },
            {
                "code": "11", "name": "Occ 4 (subgroup)", "sample_size": 16, "total_workers": 50,
                "avg_age": 30, "avg_study_years": 8, "informality_rate": 50.0
            }
        ],
        "RJ": [
            {
                "code": "111", "name": "Occ 1", "sample_size": 10, "total_workers": 100,
                "informal_weight_numerator": 20, "informal_weight_sum": 100,
                "predominant_sector": "B"
            },
            {
                "code": "333", "name": "Occ 3 (no exposure)", "sample_size": 50, "total_workers": 500
            },
            {
                "code": "11", "name": "Occ 4 (subgroup)", "sample_size": 0, "total_workers": 50
            }
        ]
    }
    
    scores = {
        "11": {"exposure": 2.0},
        "111": {"exposure": 5.0, "tier": 2},
        "222": {"exposure": 4.0},
        "333": {"exposure": None}
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        uf_path = os.path.join(tmpdir, "uf.json")
        sub_path = os.path.join(tmpdir, "sub.json")
        scores_path = os.path.join(tmpdir, "scores.json")
        out_path = os.path.join(tmpdir, "out.json")
        
        with open(uf_path, 'w') as f: json.dump(uf_codes, f)
        with open(sub_path, 'w') as f: json.dump(subgroups, f)
        with open(scores_path, 'w') as f: json.dump(scores, f)
        
        build_regional_panel(uf_path, sub_path, scores_path, out_path)
        
        with open(out_path, 'r') as f:
            output = json.load(f)
            
        assert "metadata" in output
        assert "decisions" in output["metadata"]
        panel = output["data"]
            
        assert len(panel) == 3, f"Expected 3 rows, got {len(panel)}"
        
        # Check Norte / 111
        norte = next(r for r in panel if r["region"] == "Norte" and r["occupation_code"] == "111")
        assert norte["jobs"] == 100
        assert norte["sample_size"] == 25
        assert norte["avg_anos_estudo"] == 10.0
        assert norte["informality"] == 50.0
        assert norte["predominant_sector"] == "A"
        
        # Check Sudeste / 111 (SP + RJ aggregated, RJ is missing demographics)
        sudeste = next(r for r in panel if r["region"] == "Sudeste" and r["occupation_code"] == "111")
        assert sudeste["jobs"] == 300
        assert sudeste["sample_size"] == 40
        # Age: only SP has it -> 200*43 / 200 = 43.0
        assert sudeste["avg_idade"] == 43.0
        # Study: only SP has it -> 200*11 / 200 = 11.0
        assert sudeste["avg_anos_estudo"] == 11.0
        # Informality: (80+20)/(200+100) = 100/300 = 33.3
        assert sudeste["informality"] == 33.3
        assert sudeste["predominant_sector"] == "B"
        
        # Check Sudeste / 11 (Subgroup with sample size 16 >= 15)
        subgroup = next(r for r in panel if r["region"] == "Sudeste" and r["occupation_code"] == "11")
        assert subgroup["jobs"] == 100
        assert subgroup["sample_size"] == 16
        # Demographics missing in RJ, should use only SP's denominator
        assert subgroup["avg_idade"] == 30.0
        assert subgroup["avg_anos_estudo"] == 8.0
        # Informality rate fallback, missing in RJ
        assert subgroup["informality"] == 50.0
        
        # Check low sample excluded (Occ 2)
        assert not any(r["occupation_code"] == "222" for r in panel)
        
        # Check null exposure excluded (Occ 3)
        assert not any(r["occupation_code"] == "333" for r in panel)
