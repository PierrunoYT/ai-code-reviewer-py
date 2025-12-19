from typing import List, Dict, Optional, Union
from pydantic import BaseModel, Field, ConfigDict


from ai_code_reviewer_py.enums import AIProvider, IssueSeverity, AIModel
from ai_code_reviewer_py.constants import GLOBAL_CONFIG_DIR

class AlternativeConfig(BaseModel):
    ai_provider: AIProvider = Field(...)
    model: Union[str, AIModel]
    max_tokens: int = Field(...)
    enable_extended_thinking: Optional[bool] = Field(None)
    enable_citations: Optional[bool] = Field(None)

    model_config = ConfigDict(extra="ignore", validate_assignment=True, revalidate_instances="always")

class AppConfig(BaseModel):
    ai_provider: Optional[AIProvider] = Field(None)
    model: Optional[Union[str, AIModel]] = Field(None)
    max_tokens: int = Field(32000)
    api_key: str = Field("")

    review_criteria: List[str] = Field([
        "code quality",
        "security vulnerabilities",
        "performance issues",
        "naming conventions",
        "code complexity",
        "test coverage",
        "documentation",
        "accessibility",
        "dependency security"
    ])

    blocking_issues: List[IssueSeverity] = Field([IssueSeverity.CRITICAL, IssueSeverity.HIGH])
    minimum_score: int = Field(6)

    save_to_markdown: bool = Field(True)
    markdown_output_dir: str = Field(default_factory=lambda: str(GLOBAL_CONFIG_DIR / "code-reviews"))
    include_diff_in_markdown: bool = Field(True)

    enable_extended_thinking: bool = Field(False)
    enable_citations: bool = Field(False)
    enable_batch_processing: bool = Field(True)
    enable_anthropic_web_search: bool = Field(False)

    retry_attempts: int = Field(3)
    batch_size: int = Field(5)

    alternative_configs: Optional[Dict[str, AlternativeConfig]] = Field(None)

    model_config = ConfigDict(extra="ignore", validate_assignment=True, revalidate_instances="always")

    def get_required_api_key_name(self) -> str:
        if not self.ai_provider:
            return "API Key"
        if self.ai_provider == AIProvider.OPENAI:
            return "OpenAI API Key"
        elif self.ai_provider == AIProvider.ANTHROPIC:
            return "Anthropic API Key"
        elif self.ai_provider == AIProvider.GOOGLE:
            return "Google API Key"
        return "API Key"

    def get_default_model(self) -> Union[str, AIModel]:
        if not self.ai_provider:
            return AIModel.GPT_4_1
        if self.ai_provider == AIProvider.OPENAI:
            return AIModel.GPT_4_1
        elif self.ai_provider == AIProvider.ANTHROPIC:
            return AIModel.CLAUDE_SONNET_4_20250514
        elif self.ai_provider == AIProvider.GOOGLE:
            return AIModel.GEMINI_2_5_FLASH_PREVIEW_05_20
        return AIModel.GPT_4_1