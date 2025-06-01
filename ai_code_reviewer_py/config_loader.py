import json
from pathlib import Path
from typing import Optional, Dict, Any
import os

from pydantic import ValidationError

from ai_code_reviewer_py.config_models import AppConfig
from ai_code_reviewer_py.enums import AIProvider
from ai_code_reviewer_py.constants import GLOBAL_CONFIG_FILE

def _load_json_config_data(config_path: Path) -> Dict[str, Any]:
    if config_path.exists() and config_path.is_file():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"⚠️ Warning: Could not parse config file {config_path}. Invalid JSON.")
        except Exception as e:
            print(f"⚠️ Warning: Error loading config file {config_path}: {e}")
    return {}

def load_base_config(config_path_override: Optional[str] = None) -> AppConfig:

    file_config_data = {}
    loaded_config_source_description = "defaults"

    potential_config_sources: list[tuple[Path, str]] = []

    if config_path_override:
        potential_config_sources.append(
            (Path(config_path_override), f"CLI option '{config_path_override}'")
        )

    potential_config_sources.append(
        (GLOBAL_CONFIG_FILE, f"global file '{GLOBAL_CONFIG_FILE}'")
    )

    for config_path_to_check, description in potential_config_sources:
        if config_path_to_check.exists() and config_path_to_check.is_file():
            data = _load_json_config_data(config_path_to_check)
            if data:
                file_config_data = data
                loaded_config_source_description = description
                break

    try:
        config = AppConfig(**file_config_data)
    except ValidationError as e:
        print(f"⚠️ Warning: Invalid configuration data found in {loaded_config_source_description}: {e}")
        print("    Falling back to complete default configuration.")
        config = AppConfig()

    # Populate API key from environment if not set in config and provider is known
    if not config.api_key and config.ai_provider:
        if config.ai_provider == AIProvider.OPENAI:
            config.api_key = os.getenv("OPENAI_API_KEY", "")
        elif config.ai_provider == AIProvider.ANTHROPIC:
            config.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        elif config.ai_provider == AIProvider.GOOGLE:
            config.api_key = os.getenv("GOOGLE_API_KEY", "")

    return config

def validate_required_fields(config: AppConfig) -> bool:
    if not config.ai_provider:
        raise ValueError(
            f"❌ AI provider is required but not set.\n\n"
            f"Set it with: ai-code-reviewer config set ai_provider 'openai|anthropic|google'"
        )
    
    if not config.api_key.strip():
        api_key_name = config.get_required_api_key_name()
        raise ValueError(
            f"❌ {api_key_name} is required but not set.\n\n"
            f"Set it with: ai-code-reviewer config set api_key 'your_api_key'"
        )
    return True

def validate_final_config(config: AppConfig) -> bool:
    return validate_required_fields(config)