import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock
from ai_code_reviewer_py.config_models import AppConfig
from ai_code_reviewer_py.app_service import AppService
from ai_code_reviewer_py.enums import AIProvider

@pytest.fixture
def integration_config():
    return AppConfig(
        ai_provider=AIProvider.OPENAI,
        api_key="test-key",
        save_to_markdown=True,
        markdown_output_dir="test_reviews"
    )

@pytest.fixture
def integration_service(integration_config):
    return AppService(integration_config)

@pytest.mark.asyncio
async def test_full_commit_review_workflow(integration_service):
    """Test the complete workflow of reviewing commits"""
    mock_commits = [
        {
            "hash": "abc123",
            "message": "Add new feature",
            "author_name": "Test Author",
            "author_email": "test@example.com",
            "date": datetime(2024, 1, 1, 10, 0, 0),
            "body": "Add new feature\n\nDetailed description"
        }
    ]
    
    mock_diff = "--- a/file.py\n+++ b/file.py\n@@ -1,1 +1,2 @@\n print('hello')\n+print('world')"
    
    mock_review = {
        "score": 8,
        "summary": "Good changes",
        "confidence": 9,
        "issues": [],
        "suggestions": [],
        "security": [],
        "performance": [],
        "dependencies": [],
        "accessibility": [],
        "sources": []
    }
    
    with patch.object(integration_service.git_analyzer, 'get_commits', return_value=mock_commits), \
         patch.object(integration_service.git_analyzer, 'get_commit_diff', return_value=mock_diff), \
         patch.object(integration_service.ai_reviewer, 'review_multiple_commits', new_callable=AsyncMock) as mock_review_multiple:
        
        mock_review_multiple.return_value = [mock_review]
        
        await integration_service.review_commits_in_range("HEAD~1..HEAD")
        
        mock_review_multiple.assert_called_once()
        args = mock_review_multiple.call_args[0]
        assert len(args[0]) == 1  # commits
        assert len(args[1]) == 1  # diffs
        assert args[0][0]["hash"] == "abc123"
        assert args[1][0] == mock_diff

@pytest.mark.asyncio
async def test_full_repository_review_workflow(integration_service):
    """Test the complete workflow of reviewing repository files"""
    mock_files = ["src/main.py", "src/utils.py", "README.md"]
    mock_repo_summary = {
        "overall_score": 8,
        "executive_summary": "Good repository structure",
        "architecture_assessment": {},
        "security_assessment": {"risk_level": "low"},
        "code_quality": {},
        "dependencies": {},
        "key_findings": [],
        "immediate_actions": [],
        "long_term_recommendations": [],
        "sources": [],
        "confidence": 9
    }
    
    with patch.object(integration_service.git_analyzer, 'get_tracked_files', return_value=mock_files), \
         patch.object(integration_service.ai_reviewer, 'review_entire_repository_with_retry', new_callable=AsyncMock) as mock_repo_review, \
         patch('pathlib.Path.read_text', return_value="test content"):
        
        mock_repo_review.return_value = mock_repo_summary
        integration_service.git_analyzer.repo.working_dir = "/test/repo"
        
        await integration_service.review_repository_files(
            include_patterns=["**/*.py"],
            exclude_patterns=["tests/**"],
            max_files=None
        )
        
        mock_repo_review.assert_called_once()
        args = mock_repo_review.call_args[0]
        assert len(args[0]) == 2  # Should have 2 Python files after filtering
        assert args[1] == "Local Repository (/test/repo)"