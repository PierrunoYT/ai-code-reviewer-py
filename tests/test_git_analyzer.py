import pytest
from datetime import datetime
import git # Import for git.InvalidGitRepositoryError
import tarfile
import io
from ai_code_reviewer_py.git_analyzer import GitAnalyzer, CommitInfo


@pytest.fixture
def mock_repo(mocker):
    return mocker.patch("ai_code_reviewer_py.git_analyzer.git.Repo")


def test_git_analyzer_init_success(mock_repo):
    analyzer = GitAnalyzer()
    mock_repo.assert_called_once_with('.', search_parent_directories=True) # Analyzer should init


def test_git_analyzer_init_invalid_repo(mock_repo):
    mock_repo.side_effect = git.InvalidGitRepositoryError("Invalid repo")
    
    with pytest.raises(ValueError, match="Invalid Git repository at ."):
        GitAnalyzer('.')


def test_get_commits_single_commit(mock_repo, mocker):
    mock_commit = mocker.MagicMock()
    mock_commit.hexsha = "abc123"
    mock_commit.message = "Test commit\n\nLonger description"
    mock_commit.author.name = "Test Author"
    mock_commit.author.email = "test@example.com"
    mock_commit.authored_date = 1640995200  # 2022-01-01 00:00:00 UTC
    
    mock_repo_instance = mocker.MagicMock()
    mock_repo.return_value = mock_repo_instance
    mock_repo_instance.commit.return_value = mock_commit
    
    analyzer = GitAnalyzer()
    commits = analyzer.get_commits("abc123")
    
    assert len(commits) == 1
    commit = commits[0]
    assert commit['hash'] == "abc123"
    assert commit['message'] == "Test commit"
    assert commit['author_name'] == "Test Author"
    assert commit['author_email'] == "test@example.com"
    assert isinstance(commit['date'], datetime)
    assert commit['body'] == "Test commit\n\nLonger description"


def test_get_commit_diff(mock_repo, mocker):
    mock_repo_instance = mocker.MagicMock()
    mock_commit_obj = mocker.MagicMock()
    mock_parent_commit_obj = mocker.MagicMock()

    # Setup the commit object
    mock_commit_obj.hexsha = "abc123"
    mock_commit_obj.parents = [mock_parent_commit_obj] # Assume it has parents

    mock_repo.return_value = mock_repo_instance
    mock_repo_instance.commit.return_value = mock_commit_obj # repo.commit(hash) returns our mock commit
    mock_repo_instance.git.show.return_value = "diff content"
    
    analyzer = GitAnalyzer()
    diff = analyzer.get_commit_diff("abc123")
    
    assert diff == "diff content"
    # Called with the hexsha of the commit object
    mock_repo_instance.git.show.assert_called_once_with(mock_commit_obj.hexsha, "--unified=3", "--pretty=format:")


def test_get_tracked_files(mock_repo, mocker):
    mock_repo_instance = mocker.MagicMock()
    mock_repo.return_value = mock_repo_instance
    mock_repo_instance.git.ls_files.return_value = "file1.py\nsrc/file2.py\nREADME.md"

    analyzer = GitAnalyzer()
    tracked_files = analyzer.get_tracked_files()

    assert len(tracked_files) == 3
    assert "file1.py" in tracked_files
    assert "src/file2.py" in tracked_files
    mock_repo_instance.git.ls_files.assert_called_once_with()


def test_get_files_from_remote_archive_success(mocker):
    mock_git_instance = mocker.MagicMock()
    
    # Create a dummy tar archive in memory
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
        # Add file1.py
        file1_content = "print('hello world')".encode('utf-8')
        file1_info = tarfile.TarInfo(name="src/file1.py")
        file1_info.size = len(file1_content)
        tar.addfile(file1_info, io.BytesIO(file1_content))
        
        # Add file2.txt
        file2_content = "Test content".encode('utf-8')
        file2_info = tarfile.TarInfo(name="docs/file2.txt")
        file2_info.size = len(file2_content)
        tar.addfile(file2_info, io.BytesIO(file2_content))
    tar_buffer.seek(0)
    
    mock_git_instance.archive.return_value = tar_buffer.getvalue()
    mocker.patch("ai_code_reviewer_py.git_analyzer.Git", return_value=mock_git_instance)

    analyzer = GitAnalyzer() # Not used for this static method, but good practice
    files_data = analyzer.get_files_from_remote_archive("https://example.com/repo.git", "main")

    assert len(files_data) == 2
    assert {"path": "src/file1.py", "content": "print('hello world')"} in files_data
    assert {"path": "docs/file2.txt", "content": "Test content"} in files_data
    mock_git_instance.archive.assert_called_once_with(
        remote="https://example.com/repo.git",
        format='tar',
        ref='main',
        kill_after_timeout=120,
        stdout_as_bytes=True
    )


def test_get_files_from_remote_archive_git_command_error(mocker):
    mock_git_instance = mocker.MagicMock()
    mock_git_instance.archive.side_effect = git.GitCommandError("archive", "fatal: error", stderr="fatal: error")
    mocker.patch("ai_code_reviewer_py.git_analyzer.Git", return_value=mock_git_instance)

    analyzer = GitAnalyzer()
    with pytest.raises(RuntimeError, match=r"Failed to fetch archive from 'https://example.com/repo.git' \(ref: main\)\. Git command failed: \s*stderr: 'fatal: error'"):
        analyzer.get_files_from_remote_archive("https://example.com/repo.git", "main")