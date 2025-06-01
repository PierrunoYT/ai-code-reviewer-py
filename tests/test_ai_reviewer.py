import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch
from ai_code_reviewer_py.git_analyzer import CommitInfo
from ai_code_reviewer_py.ai_reviewer import AIReviewer
from ai_code_reviewer_py.config_models import AppConfig
from ai_code_reviewer_py.enums import AIProvider, AIModel


@pytest.fixture
def sample_commit():
    return CommitInfo(
        hash="abc123",
        message="Test commit",
        author_name="Test Author",
        author_email="test@example.com",
        date=datetime.now(),
        body="Test commit\n\nLonger description"
    )


@pytest.fixture
def ai_reviewer():
    config = AppConfig(ai_provider="openai", api_key="test-key")
    return AIReviewer(config)


@pytest.fixture
def config():
    return AppConfig(
        ai_provider=AIProvider.ANTHROPIC,
        model="claude-sonnet-4-20250514",
        api_key="test-key"
    )


def test_ai_reviewer_init(config):
    reviewer = AIReviewer(config)
    
    assert reviewer.config == config
    assert reviewer.provider == AIProvider.ANTHROPIC
    assert reviewer.model == "claude-sonnet-4-20250514"


def test_get_default_model():
    config_openai = AppConfig(ai_provider=AIProvider.OPENAI)
    reviewer = AIReviewer(config_openai)
    assert reviewer._get_default_model() == AIModel.GPT_4_1_MINI.value
    
    config_anthropic = AppConfig(ai_provider=AIProvider.ANTHROPIC)
    reviewer = AIReviewer(config_anthropic)
    assert reviewer._get_default_model() == AIModel.CLAUDE_SONNET_4_20250514.value

    config_none = AppConfig(ai_provider=None)
    reviewer = AIReviewer(config_none)
    assert reviewer._get_default_model() == AIModel.GPT_4_1_MINI.value


def test_build_prompt(config, sample_commit):
    reviewer = AIReviewer(config)
    diff = "- old line\n+ new line"
    
    prompt = reviewer._build_prompt(diff, sample_commit)
    
    assert "Test commit" in prompt
    assert "Test Author" in prompt
    assert "- old line\n+ new line" in prompt
    assert "code quality" in prompt.lower()


@pytest.mark.asyncio
async def test_review_code_with_retry_success(ai_reviewer):
    diff = "- old line\n+ new line"
    commit = CommitInfo(
        hash="abc123",
        message="Test commit",
        author_name="Test Author", 
        author_email="test@example.com",
        date=datetime.now(),
        body="Test commit body"
    )
    
    with patch.object(ai_reviewer, 'review_code', new_callable=AsyncMock) as mock_review:
        mock_response = {"score": 8, "summary": "Good changes", "confidence": 9, "issues": []}
        mock_review.return_value = mock_response
        
        result = await ai_reviewer.review_code_with_retry(diff, commit)
        
        assert result == mock_response
        mock_review.assert_called_once_with(diff, commit)

@pytest.mark.asyncio
async def test_review_entire_repository_with_retry_success(ai_reviewer):
    files_data = [{"path": "test.py", "content": "print('hello')"}]
    repo_info = "test-repo"
    
    with patch.object(ai_reviewer, 'review_entire_repository', new_callable=AsyncMock) as mock_review:
        mock_response = {"overall_score": 8, "executive_summary": "Good repo", "confidence": 9}
        mock_review.return_value = mock_response
        
        result = await ai_reviewer.review_entire_repository_with_retry(files_data, repo_info)
        
        assert result == mock_response
        mock_review.assert_called_once_with(files_data, repo_info)