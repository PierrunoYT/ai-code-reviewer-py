import pytest
import json
from pathlib import Path
from ai_code_reviewer_py.config_loader import load_base_config, validate_final_config
from ai_code_reviewer_py.config_models import AppConfig
from ai_code_reviewer_py.enums import AIProvider


@pytest.fixture
def mock_global_constants_for_config(mocker, tmp_path):
    mock_config_file = tmp_path / "ai-code-reviewer-py" / "config.json"
    mock_config_dir = tmp_path / "ai-code-reviewer-py"
    
    mocker.patch("ai_code_reviewer_py.constants.GLOBAL_CONFIG_FILE", mock_config_file)
    mocker.patch("ai_code_reviewer_py.constants.GLOBAL_CONFIG_DIR", mock_config_dir)
    return mock_config_file, mock_config_dir


def test_load_base_config_defaults(mocker, mock_global_constants_for_config):
    mocker.patch("ai_code_reviewer_py.config_loader._load_json_config_data", return_value={}) # Ensure no file is loaded
    mocker.patch("pathlib.Path.exists", return_value=False)
    
    config = load_base_config()
    
    assert isinstance(config, AppConfig)
    assert config.ai_provider is None
    assert config.max_tokens == 32000


def test_load_base_config_from_file(tmp_path, mocker, mock_global_constants_for_config):
    mock_config_file_path, _ = mock_global_constants_for_config
    config_file = tmp_path / "test-config.json"
    config_data = {
        "ai_provider": "openai",
        "model": "gpt-4",
        "max_tokens": 8000
    }
    config_file.write_text(json.dumps(config_data))
    
    # Mock _load_json_config_data to control what's "read"
    mocker.patch("ai_code_reviewer_py.config_loader._load_json_config_data", return_value=config_data)
    
    config = load_base_config(str(config_file))
    
    assert isinstance(config, AppConfig)
    assert config.ai_provider == AIProvider.OPENAI
    assert config.model == "gpt-4"
    assert config.max_tokens == 8000


def test_validate_final_config_valid(mocker, mock_global_constants_for_config):
    config = AppConfig(ai_provider=AIProvider.OPENAI, api_key="test-api-key")
    assert validate_final_config(config) is True


def test_validate_final_config_no_api_key(mocker, mock_global_constants_for_config):
    config = AppConfig()
    mocker.patch("os.getenv", return_value=None)
    
    with pytest.raises(ValueError, match="is required but not set"): # Match generic message part
        validate_final_config(config)