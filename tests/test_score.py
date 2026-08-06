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

    for entry in scores.values():
        assert "score" in entry
        assert "rationale" in entry
        assert 0 <= entry["score"] <= 10
        assert len(entry["rationale"]) > 10
        assert entry.get("method") in ("llm", "heuristic-keyword-v1"), (
            f"Missing or unknown scoring method for '{entry.get('name')}': {entry.get('method')!r}"
        )
        assert "generated_at" in entry
