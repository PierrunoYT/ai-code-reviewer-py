import pytest
from unittest.mock import MagicMock, patch, mock_open, AsyncMock
from pathlib import Path
from datetime import datetime, timezone

from ai_code_reviewer_py.app_service import AppService
from ai_code_reviewer_py.ai_reviewer import AIReviewer
from ai_code_reviewer_py.config_models import AppConfig
from ai_code_reviewer_py.models import AIReviewResponse, FileDetails, AIReviewIssue, RepositorySummaryResponse


@pytest.fixture
def mock_config():
    return AppConfig(markdown_output_dir="test_reviews")


@pytest.fixture
def app_service(mock_config):
    with patch("ai_code_reviewer_py.app_service.GitAnalyzer") as MockGitAnalyzer, \
         patch("ai_code_reviewer_py.app_service.AIReviewer") as MockAIReviewer:
        mock_git_analyzer_instance = MockGitAnalyzer.return_value
        mock_ai_reviewer_instance = MockAIReviewer.return_value
        service = AppService(mock_config)
        service.console = MagicMock() # Mock console to check output
        return service


def create_mock_md_file(name: str, content: str) -> MagicMock:
    mock_file = MagicMock(spec=Path)
    mock_file.name = name
    mock_file.read_text.return_value = content
    return mock_file


@pytest.mark.asyncio
async def test_generate_review_summary_no_dir(app_service, mock_config):
    with patch("pathlib.Path.exists", return_value=False):
        await app_service.generate_review_summary(None, None)
        app_service.console.print.assert_any_call(
            f"[yellow]Review directory '{mock_config.markdown_output_dir}' does not exist. No reviews to summarize.[/yellow]"
        )


@pytest.mark.asyncio
async def test_generate_review_summary_no_files(app_service):
    with patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.is_dir", return_value=True), \
         patch("pathlib.Path.glob", return_value=[]):
        await app_service.generate_review_summary(None, None)
        app_service.console.print.assert_any_call("[yellow]No review files found.[/yellow]")


@pytest.mark.asyncio
async def test_generate_review_summary_success(app_service):
    md_content_1 = """# Code Review for Commit 12345678
**Date:** 2024-01-15T10:00:00Z
- **Score:** 8/10
- **Summary:** Good work
"""
    md_content_2 = """# Code Review for Commit abcdef01
**Date:** 2024-01-10T12:00:00Z
- **Score:** 6/10
- **Summary:** Needs improvement
"""
    mock_files = [
        create_mock_md_file("review1.md", md_content_1),
        create_mock_md_file("review2.md", md_content_2),
    ]

    with patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.is_dir", return_value=True), \
         patch("pathlib.Path.glob", return_value=mock_files):
        await app_service.generate_review_summary(None, None)

        assert app_service.console.print.call_count > 2 # Initial, header, and per-summary prints
        output_str = " ".join(str(call_args) for call_args in app_service.console.print.call_args_list)
        assert "Review Summary (2 reviews matching criteria)" in output_str
        assert "review1.md" in output_str
        assert "Good work" in output_str
        assert "review2.md" in output_str
        assert "Needs improvement" in output_str


@pytest.mark.asyncio
async def test_generate_review_summary_with_since_filter(app_service):
    md_content_1 = """# Code Review for Commit 12345678
**Date:** 2024-03-15T10:00:00Z
- **Score:** 8/10
- **Summary:** Recent review
""" 
    md_content_2 = """# Code Review for Commit abcdef01
**Date:** 2024-01-10T12:00:00Z
- **Score:** 6/10
- **Summary:** Old review
""" 
    mock_files = [
        create_mock_md_file("review1.md", md_content_1),
        create_mock_md_file("review2.md", md_content_2),
    ]
    since_date = datetime(2024, 2, 1, tzinfo=timezone.utc)

    with patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.is_dir", return_value=True), \
         patch("pathlib.Path.glob", return_value=mock_files):
        await app_service.generate_review_summary(since_date, None)

        output_str = " ".join(str(call_args) for call_args in app_service.console.print.call_args_list)
        assert "Review Summary (1 reviews matching criteria)" in output_str
        assert "Recent review" in output_str
        assert "Old review" not in output_str


@pytest.mark.asyncio
async def test_generate_review_summary_with_min_score_filter(app_service):
    md_content_1 = """# Code Review for Commit 12345678
**Date:** 2024-01-15T10:00:00Z
- **Score:** 9/10
- **Summary:** High score review
""" 
    md_content_2 = """# Code Review for Commit abcdef01
**Date:** 2024-01-10T12:00:00Z
- **Score:** 5/10
- **Summary:** Low score review
""" 
    mock_files = [
        create_mock_md_file("review1.md", md_content_1),
        create_mock_md_file("review2.md", md_content_2),
    ]

    with patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.is_dir", return_value=True), \
         patch("pathlib.Path.glob", return_value=mock_files):
        await app_service.generate_review_summary(None, 7) 

        output_str = " ".join(str(call_args) for call_args in app_service.console.print.call_args_list)
        assert "Review Summary (1 reviews matching criteria)" in output_str
        assert "High score review" in output_str
        assert "Low score review" not in output_str


@pytest.mark.asyncio
async def test_generate_review_summary_malformed_file(app_service):
    md_content_malformed = """# Code Review
**Date:** 2024-01-15T10:00:00Z
- **Summary:** No score here
""" 
    mock_files = [create_mock_md_file("malformed.md", md_content_malformed)]

    with patch("pathlib.Path.exists", return_value=True), \
         patch("pathlib.Path.is_dir", return_value=True), \
         patch("pathlib.Path.glob", return_value=mock_files):
        await app_service.generate_review_summary(None, None)

        output_str = " ".join(str(call_args) for call_args in app_service.console.print.call_args_list)
        assert "Could not parse all required fields from 'malformed.md'" in output_str
        assert "No reviews match the specified criteria" in output_str # Because the only file was skipped


@pytest.mark.asyncio
async def test_review_file_details_list_and_report(app_service, mock_config):
    files_to_review: list[FileDetails] = [
        {"path": "file1.py", "content": "content1"},
        {"path": "file2.py", "content": "content2"},
    ]
    mock_review_1: AIReviewResponse = {"score": 8, "summary": "Review for file1", "confidence": 7, "issues": []}
    mock_review_2_error = ValueError("AI failed for file2")

    app_service.ai_reviewer.review_entire_repository_with_retry = AsyncMock(return_value=mock_review_1)
    app_service._display_repository_summary_to_console = MagicMock()
    app_service._save_repository_summary_to_markdown = MagicMock()
    mock_config.save_to_markdown = True

    await app_service._review_file_details_list_and_report(files_to_review, "Test Reviewing File", "test-repo")

    app_service.ai_reviewer.review_entire_repository_with_retry.assert_called_once_with(files_to_review, "test-repo")
    app_service._display_repository_summary_to_console.assert_called_once()


@pytest.mark.asyncio
async def test_review_file_details_list_and_report_no_files(app_service):
    await app_service._review_file_details_list_and_report([], "Test Reviewing File", "test-repo")
    app_service.console.print.assert_any_call("[yellow]No files to review.[/yellow]")


@pytest.mark.asyncio
async def test_review_repository_files_flow(app_service, mock_config):
    mock_file_contents = {
        "src/main.py": "def main(): pass",
        "src/sub/helper.py": "def helper(): pass",
        "README.md": "# Readme",
        "tests/test_main.py": "def test_main(): pass"
    }

    mock_review_response: AIReviewResponse = {"score": 8, "summary": "Great file!", "confidence": 9, "issues": []}
    app_service.ai_reviewer.review_entire_repository_with_retry = AsyncMock(return_value=mock_review_response)
    app_service._display_repository_summary_to_console = MagicMock()
    app_service._save_repository_summary_to_markdown = MagicMock()

    app_service.git_analyzer.repo.working_dir = "/fake/repo/root"
    app_service.git_analyzer.get_tracked_files = MagicMock(return_value=list(mock_file_contents.keys()))

    def mock_read_text_side_effect(self_path_obj, encoding='utf-8', errors='ignore'):
        relative_path_str = str(self_path_obj.relative_to(Path("/fake/repo/root")))
        return mock_file_contents.get(relative_path_str, "default content")

    with patch("pathlib.Path.read_text", side_effect=mock_read_text_side_effect, autospec=True):
        await app_service.review_repository_files(
            include_patterns=["src/**/*.py"],
            exclude_patterns=["**/test_*.py"],
            max_files=None
        )

    app_service.git_analyzer.get_tracked_files.assert_called_once()
    app_service.ai_reviewer.review_entire_repository_with_retry.assert_called_once()


@pytest.mark.asyncio
async def test_review_repository_files_max_files_limit(app_service):
    mock_tracked_files = ["file3.py", "file1.py", "file2.py"] 
    app_service.git_analyzer.get_tracked_files = MagicMock(return_value=mock_tracked_files)
    
    app_service.git_analyzer.repo.working_dir = "/fake/repo/root"
    
    mock_file_contents = {
        "file1.py": "content for file1",
        "file2.py": "content for file2",
        "file3.py": "content for file3",
    }

    app_service.ai_reviewer.review_entire_repository_with_retry = AsyncMock(return_value={"overall_score": 8})

    def mock_read_text_side_effect(self_path_obj, encoding='utf-8', errors='ignore'):
        relative_path_str = str(self_path_obj.relative_to(Path("/fake/repo/root")))
        return mock_file_contents.get(relative_path_str, "default content")

    with patch("pathlib.Path.read_text", side_effect=mock_read_text_side_effect, autospec=True):
        await app_service.review_repository_files(
            include_patterns=["**/*.py"], 
            exclude_patterns=[], 
            max_files=2
        )

    app_service.console.print.assert_any_call("[yellow]Limiting to 2 files out of 3 found.[/yellow]")
    
    app_service.ai_reviewer.review_entire_repository_with_retry.assert_called_once()


@pytest.mark.asyncio
async def test_review_external_repository(app_service, mock_config, mocker):
    mock_files_data = [
        FileDetails(path="src/main.py", content="content1"),
        FileDetails(path="README.md", content="content2")
    ]
    app_service.git_analyzer.get_files_from_remote_archive = MagicMock(return_value=sorted(mock_files_data, key=lambda x: x["path"]))
    
    mocker.patch.object(app_service, "_filter_and_limit_file_data", return_value=mock_files_data)

    mock_review_and_report_helper = mocker.patch.object(app_service, "_review_file_details_list_and_report", new_callable=AsyncMock)

    repo_url = "https://example.com/repo.git"
    ref = "main"
    include = ["**/*.py"]
    exclude = ["docs/**"]
    max_f = 10

    await app_service.review_external_repository(repo_url, ref, include, exclude, max_f)

    app_service.git_analyzer.get_files_from_remote_archive.assert_called_once_with(repo_url, ref)
    app_service._filter_and_limit_file_data.assert_called_once_with(
        sorted(mock_files_data, key=lambda x: x["path"]), 
        include, exclude, max_f
    )
    mock_review_and_report_helper.assert_called_once_with(mock_files_data, "Reviewing remote file", f"{repo_url} (ref: {ref})")