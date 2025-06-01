from enum import Enum

class AIProvider(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"

class IssueSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class IssueCategory(str, Enum):
    SECURITY = "security"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    STYLE = "style"
    TESTING = "testing"
    DOCUMENTATION = "documentation"
    ACCESSIBILITY = "accessibility"
    DEPENDENCIES = "dependency_security"

class AIModel(str, Enum):
    CLAUDE_SONNET_4_20250514 = "claude-sonnet-4-20250514"
    CLAUDE_3_7_SONNET_20250219 = "claude-3-7-sonnet-20250219"
    GPT_4_1 = "gpt-4.1"
    GPT_4_1_MINI = "gpt-4.1-mini"
    GPT_4_1_NANO = "gpt-4.1-nano"
    GEMINI_2_5_PRO_PREVIEW_05_06 = "gemini-2.5-pro-preview-05-06"
    GEMINI_2_5_FLASH_PREVIEW_05_20 = "gemini-2.5-flash-preview-05-20"
    CLAUDE_3_5_SONNET_LATEST = "claude-3.5-sonnet-20240620"
