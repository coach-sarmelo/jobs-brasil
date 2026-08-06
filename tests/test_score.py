import json
import os
import pytest

def test_scores_json_structure():
    scores_path = os.path.join(os.path.dirname(__file__), '../scores.json')
    assert os.path.exists(scores_path), "scores.json does not exist"
    
    with open(scores_path, 'r', encoding='utf-8') as f:
        scores = json.load(f)
        
    assert isinstance(scores, dict)
    assert len(scores) > 50
    
    sample_key = list(scores.keys())[0]
    entry = scores[sample_key]
    assert "score" in entry
    assert "rationale" in entry
    assert 0 <= entry["score"] <= 10
    assert len(entry["rationale"]) > 10
