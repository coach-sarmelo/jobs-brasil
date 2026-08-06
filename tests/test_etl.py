import json
import os
import pytest

def test_jobs_br_json_structure():
    json_path = os.path.join(os.path.dirname(__file__), '../src/data/jobs_br.json')
    assert os.path.exists(json_path), "jobs_br.json output does not exist"
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    assert "totals" in data
    assert "items" in data
    assert "sections" in data
    assert len(data["items"]) > 50
    
    first_item = data["items"][0]
    assert "id" in first_item
    assert "name" in first_item
    assert "code" in first_item
    assert "section" in first_item
    assert "avg_income" in first_item
    assert "total_workers" in first_item
    assert "wage_bill" in first_item
    assert "ai_exposure_score" in first_item
