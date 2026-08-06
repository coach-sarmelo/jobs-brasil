import json
import os
import pytest

def test_site_data_json():
    data_path = os.path.join(os.path.dirname(__file__), '../site/data.json')
    assert os.path.exists(data_path), "site/data.json does not exist"
    
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    assert "meta" in data
    assert "occupations" in data
    assert data["meta"]["total_jobs"] > 50000000
    assert data["meta"]["weighted_ai_exposure"] > 0
    assert len(data["occupations"]) > 50
