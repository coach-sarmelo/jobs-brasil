import json
import os
import pytest

def test_cod_subgroups_extraction():
    json_path = os.path.join(os.path.dirname(__file__), '../cod_subgroups.json')
    assert os.path.exists(json_path), "cod_subgroups.json does not exist"
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    assert isinstance(data, list)
    assert len(data) >= 80 and len(data) <= 120, f"Expected ~96 subgroups, found {len(data)}"
    
    item = data[0]
    assert "code" in item
    assert "name" in item
    assert "section" in item
    assert "total_workers" in item
    assert "avg_income" in item
    assert item["total_workers"] > 0
    assert item["avg_income"] > 0
