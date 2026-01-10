
import pytest
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime
import sys
import os
import json
from pathlib import Path

# Add scripts to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../scripts')))

from article_generator import (
    generate_daily_article,
    get_market_summary,
    get_sector_rotation,
    get_stock_analysis,
    save_to_json
)

@pytest.fixture
def mock_scan_results():
    return {
        "date": "2026-01-10",
        "criteria": {"lookbackDays": 20},
        "summary": {
            "total": 10,
            "counts": {"new": 2, "continued": 8, "removed": 1}
        },
        "changes": {
            "new": [{"ticker": "2330"}, {"ticker": "2454"}]
        },
        "stocks": [
            {
                "ticker": "2330", "name": "台積電", "sector": "半導體",
                "currentPrice": 1000, "changePct": 1.5, "consecutiveRed": 5,
                "signal": {"priority": 100}
            },
            {
                "ticker": "2454", "name": "聯發科", "sector": "半導體",
                "currentPrice": 900, "changePct": -0.5, "consecutiveRed": 2,
                "signal": {"priority": 90}
            },
            {
                "ticker": "2317", "name": "鴻海", "sector": "電子代工",
                "currentPrice": 200, "changePct": 2.0, "consecutiveRed": 3,
                "signal": {"priority": 80}
            }
        ]
    }

class TestArticleGenerator:
    
    def test_market_summary_content(self, mock_scan_results):
        """Test market summary text generation"""
        text = get_market_summary(mock_scan_results)
        assert "大盤與選股概要" in text
        assert "共篩選出 **10** 檔" in text
        
    def test_save_to_json(self, mock_scan_results, tmp_path):
        """Test JSON saving logic using temporary directory"""
        article = generate_daily_article(mock_scan_results)
        
        # Use pytest tmp_path fixture
        success = save_to_json(article, output_dir=tmp_path)
        
        assert success is True
        
        # Verify file exists
        expected_file = tmp_path / "articles" / "2026-01-10.json"
        assert expected_file.exists()
        
        # Verify content
        with open(expected_file, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
            assert saved_data['date'] == "2026-01-10"
            assert "content" in saved_data

