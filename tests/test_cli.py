import pytest
from unittest.mock import patch, AsyncMock
from click.testing import CliRunner
import click
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
import json
from ai_code_reviewer_py.cli import cli
from ai_code_reviewer_py import __version__
from ai_code_reviewer_py.config_models import AppConfig, AIProvider


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_version(runner):
    result = runner.invoke(cli, ["--version"], prog_name="ai-code-reviewer-py")
    assert result.exit_code == 0
    assert f"ai-code-reviewer-py, version {__version__}" in result.output


def test_cli_help(runner):
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "AI Code Reviewer CLI" in result.output


def test_review_command_help(runner):
    result = runner.invoke(cli, ["review", "--help"])
    assert result.exit_code == 0
    assert "Review commits in the specified range" in result.output


def test_review_command_with_mocked_service(runner, mocker):
    mock_load_config = mocker.patch("ai_code_reviewer_py.cli.load_base_config")
    mocker.patch("ai_code_reviewer_py.cli.validate_final_config", return_value=True)
    
    mock_app_service_constructor = mocker.patch("ai_code_reviewer_py.cli.AppService")
    mock_service_instance = mock_app_service_constructor.return_value
    mock_service_instance.review_commits_in_range = mocker.AsyncMock()
    
    mock_config = mocker.MagicMock(spec=AppConfig)
    mock_load_config.return_value = mock_config
    
    result = runner.invoke(cli, ["review", "HEAD~1..HEAD"])
    
    assert result.exit_code == 0
    mock_load_config.assert_called_once()
    mock_app_service_constructor.assert_called_once_with(mock_config)
    mock_service_instance.review_commits_in_range.assert_called_once_with("HEAD~1..HEAD")


@pytest.fixture
def mock_global_config_paths(mocker, tmp_path):
    # Using a shorter, simpler directory name to avoid complex wrapping by Rich
    mock_config_dir = tmp_path / "aicr_test_config" 
    mock_config_file = mock_config_dir / "config.json"
    
    mocker.patch("ai_code_reviewer_py.constants.GLOBAL_CONFIG_FILE", mock_config_file)
    mocker.patch("ai_code_reviewer_py.constants.GLOBAL_CONFIG_DIR", mock_config_dir)
    # Also need to mock for app_service if it imports directly
    mocker.patch("ai_code_reviewer_py.app_service.GLOBAL_CONFIG_FILE", mock_config_file)
    mocker.patch("ai_code_reviewer_py.app_service.GLOBAL_CONFIG_DIR", mock_config_dir)
    # Mock for cli.py's direct import of GLOBAL_CONFIG_FILE
    mocker.patch("ai_code_reviewer_py.cli.GLOBAL_CONFIG_FILE", mock_config_file)
    return mock_config_file, mock_config_dir


def test_config_set_api_key_new_file(runner, mocker, mock_global_config_paths):
    mock_config_file, _ = mock_global_config_paths
    # Ensure AppConfig() can be instantiated correctly with mocked constants
    # The mock_global_config_paths fixture should handle the constants.GLOBAL_CONFIG_DIR mocking
    mocker.patch("ai_code_reviewer_py.cli.load_base_config", return_value=AppConfig()) 

    result = runner.invoke(cli, ["config", "set", "api_key", "test_api_123"], catch_exceptions=False)
    
    assert result.exit_code == 0
    assert "✅ Global configuration file created at:" in result.output
    assert str(mock_config_file) in result.output.replace("\n", "")
    assert '   Set api_key to ***HIDDEN***.' in result.output
    
    assert mock_config_file.exists()
    with open(mock_config_file, "r") as f:
        data = json.load(f)
    assert data["api_key"] == "test_api_123"
    # Create a new AppConfig instance to get its default max_tokens
    # This AppConfig() will also use the mocked GLOBAL_CONFIG_DIR due to the fixture
    assert data.get("max_tokens") == AppConfig().max_tokens # Check other defaults persist


def test_config_set_model_existing_file(runner, mocker, mock_global_config_paths):
    mock_config_file, mock_config_dir = mock_global_config_paths
    mock_config_dir.mkdir(parents=True, exist_ok=True)
    initial_config_data = {"model": "old_model", "max_tokens": 1000}
    with open(mock_config_file, "w") as f:
        json.dump(initial_config_data, f)

    mocker.patch("ai_code_reviewer_py.cli.load_base_config", return_value=AppConfig(**initial_config_data))

    result = runner.invoke(cli, ["config", "set", "model", "new_model_456"])
    
    assert result.exit_code == 0
    assert "✅ Global configuration file updated at:" in result.output
    assert str(mock_config_file) in result.output.replace("\n", "")
    assert '   Set model to "new_model_456".' in result.output
    
    with open(mock_config_file, "r") as f:
        data = json.load(f)
    assert data["model"] == "new_model_456"
    assert data["max_tokens"] == 1000 # Check other existing data persists


def test_config_show_no_file(runner, mocker, mock_global_config_paths):
    mock_config_file, _ = mock_global_config_paths
    # This mock is for the main cli group, not directly used by 'config show' logic itself
    mocker.patch("ai_code_reviewer_py.cli.load_base_config", return_value=AppConfig())
    result = runner.invoke(cli, ["config", "show"])
    assert result.exit_code == 0
    assert f"Global configuration file is expected at: {mock_config_file}" in result.output
    assert "Global configuration file does not exist yet" in result.output


def test_config_show_existing_file(runner, mocker, mock_global_config_paths):
    mock_config_file, mock_config_dir = mock_global_config_paths
    mock_config_dir.mkdir(parents=True, exist_ok=True)
    config_content = {"api_key": "fake_key_shown"}
    with open(mock_config_file, "w") as f:
        json.dump(config_content, f, indent=2)
    
    # This mock is for the main cli group
    mocker.patch("ai_code_reviewer_py.cli.load_base_config", return_value=AppConfig())
    result = runner.invoke(cli, ["config", "show"])
    assert result.exit_code == 0
    assert f"Global configuration file is expected at: {mock_config_file}" in result.output
    assert '"api_key": "fake_key_shown"' in result.output


@pytest.mark.parametrize(
    "cli_option, cli_value, config_attr, expected_value",  # Ensure these names are used
    [
        ("--include", "**/*.py", "include_patterns", ["**/*.py"]),
        ("--exclude", "docs/**", "exclude_patterns", ["docs/**"]),
        ("--max-files", "10", "max_files", 10),
        ("--provider", "openai", "ai_provider", AIProvider.OPENAI),
        ("--web-search", None, "enable_anthropic_web_search", True),
        ("--no-citations", None, "enable_citations", False),
        ("--batch", None, "enable_batch_processing", True),
        ("--no-extended-thinking", None, "enable_extended_thinking", False),
        ("--save-markdown", None, "save_to_markdown", True),
        ("--markdown-dir", "my_repo_reviews", "markdown_output_dir", "my_repo_reviews"),
    ]
)
def test_review_repo_command_options(runner, mocker, cli_option, cli_value, config_attr, expected_value): # Ensure these names match above
    mock_load_config = mocker.patch("ai_code_reviewer_py.cli.load_base_config")
    mocker.patch("ai_code_reviewer_py.cli.validate_final_config", return_value=True)
    mock_app_service_constructor = mocker.patch("ai_code_reviewer_py.cli.AppService")
    mock_service_instance = mock_app_service_constructor.return_value
    mock_service_instance.review_repository_files = mocker.AsyncMock()

    initial_config_data = {"api_key": "dummy_key_for_provider_test"} if config_attr == "ai_provider" else {}
    mock_base_config = AppConfig(**initial_config_data)
    mock_load_config.return_value = mock_base_config

    cli_args = ["review-repo", cli_option]
    if cli_value is not None:
        cli_args.append(cli_value)
    
    result = runner.invoke(cli, cli_args)
    
    assert result.exit_code == 0, f"CLI failed with output: {result.output}"
    
    mock_app_service_constructor.assert_called_once()
    final_config_passed_to_service = mock_app_service_constructor.call_args[0][0]
    
    if config_attr in ["include_patterns", "exclude_patterns", "max_files"]:
        # These are passed as positional arguments to review_repository_files
        service_pos_args = mock_service_instance.review_repository_files.call_args[0]
        if config_attr == "include_patterns":
            actual_value = service_pos_args[0]
        elif config_attr == "exclude_patterns":
            actual_value = service_pos_args[1]
        elif config_attr == "max_files":
            actual_value = service_pos_args[2]
        else: # Should not happen based on the if condition
            actual_value = None 

        if isinstance(expected_value, list): 
            assert list(actual_value) == expected_value
        else:
            assert actual_value == expected_value
    else: 
        actual_config_value = getattr(final_config_passed_to_service, config_attr)
        assert actual_config_value == expected_value, \
            f"For option {cli_option}, expected {config_attr}={expected_value}, got {actual_config_value}" # Ensure cli_option is used here


@pytest.mark.parametrize(
    "option_name, option_value, expected_config_attr, expected_config_value",
    [
        ("--provider", "anthropic", "ai_provider", AIProvider.ANTHROPIC),
        ("--web-search", None, "enable_anthropic_web_search", True),
        ("--no-web-search", None, "enable_anthropic_web_search", False),
        ("--citations", None, "enable_citations", True),
        ("--no-citations", None, "enable_citations", False),
        ("--batch", None, "enable_batch_processing", True),
        ("--no-batch", None, "enable_batch_processing", False),
        ("--extended-thinking", None, "enable_extended_thinking", True),
        ("--no-extended-thinking", None, "enable_extended_thinking", False),
        ("--save-markdown", None, "save_to_markdown", True),
        ("--no-save-markdown", None, "save_to_markdown", False),
        ("--markdown-dir", "./custom_reviews", "markdown_output_dir", "./custom_reviews"),
        ("--include-diff", None, "include_diff_in_markdown", True), # Assuming True is the default for the option
        ("--no-include-diff", None, "include_diff_in_markdown", False),
    ]
)
def test_review_command_options(runner, mocker, option_name, option_value, expected_config_attr, expected_config_value):
    mock_load_config = mocker.patch("ai_code_reviewer_py.cli.load_base_config")
    mocker.patch("ai_code_reviewer_py.cli.validate_final_config", return_value=True)
    mock_app_service_constructor = mocker.patch("ai_code_reviewer_py.cli.AppService")
    mock_service_instance = mock_app_service_constructor.return_value
    mock_service_instance.review_commits_in_range = mocker.AsyncMock()

    # Create a base AppConfig instance to be returned by load_base_config
    # For provider, ensure api_key is set if provider is set, to pass validation
    initial_config_data = {"api_key": "dummy_key_for_provider_test"} if expected_config_attr == "ai_provider" else {}
    mock_base_config = AppConfig(**initial_config_data)
    mock_load_config.return_value = mock_base_config

    cli_args = ["review", "HEAD~1..HEAD", option_name]
    if option_value is not None:
        cli_args.append(option_value)
    
    result = runner.invoke(cli, cli_args)
    
    assert result.exit_code == 0, f"CLI failed with output: {result.output}"
    
    mock_app_service_constructor.assert_called_once()
    # The AppService is instantiated with the final config.
    # We need to check the config that was passed to its constructor.
    final_config_passed_to_service = mock_app_service_constructor.call_args[0][0]
    
    actual_value = getattr(final_config_passed_to_service, expected_config_attr)
    assert actual_value == expected_config_value, \
        f"For option {option_name}, expected {expected_config_attr}={expected_config_value}, got {actual_value}"


@pytest.mark.parametrize(
    "cli_args, expected_service_args",
    [
        (["review-remote", "https://example.com/repo.git"], 
         {"repo_url": "https://example.com/repo.git", "ref": "HEAD", "include_patterns": ["**/*"], "exclude_patterns": [], "max_files": None}),
        (["review-remote", "https://another.com/r.git", "--ref", "develop", "--include", "*.py", "--exclude", "tests/*", "--max-files", "5"],
         {"repo_url": "https://another.com/r.git", "ref": "develop", "include_patterns": ["*.py"], "exclude_patterns": ["tests/*"], "max_files": 5}),
    ]
)
def test_review_remote_command_options(runner, mocker, cli_args, expected_service_args):
    mock_load_config = mocker.patch("ai_code_reviewer_py.cli.load_base_config")
    mocker.patch("ai_code_reviewer_py.cli.validate_final_config", return_value=True)
    mock_app_service_constructor = mocker.patch("ai_code_reviewer_py.cli.AppService")
    mock_service_instance = mock_app_service_constructor.return_value
    mock_service_instance.review_external_repository = mocker.AsyncMock()

    # Base config for AppService instantiation
    mock_base_config = AppConfig(api_key="dummy_key") # Ensure api_key for validation
    mock_load_config.return_value = mock_base_config

    result = runner.invoke(cli, cli_args)
    
    assert result.exit_code == 0, f"CLI failed with output: {result.output}"
    
    mock_app_service_constructor.assert_called_once()
    final_config_passed_to_service = mock_app_service_constructor.call_args[0][0]
    assert isinstance(final_config_passed_to_service, AppConfig)

    mock_service_instance.review_external_repository.assert_called_once()
    call_args, _ = mock_service_instance.review_external_repository.call_args
    
    assert call_args[0] == expected_service_args["repo_url"]
    assert call_args[1] == expected_service_args["ref"]
    # Convert tuple from CLI (multiple=True) to list for comparison if necessary
    assert list(call_args[2]) == expected_service_args["include_patterns"]
    assert list(call_args[3]) == expected_service_args["exclude_patterns"]
    assert call_args[4] == expected_service_args["max_files"]


def test_summarize_command_help(runner):
    result = runner.invoke(cli, ["summarize", "--help"])
    assert result.exit_code == 0
    assert "Generate a summary of saved review markdown files" in result.output


def test_summarize_command_with_mocked_service(runner, mocker):
    mock_load_config = mocker.patch("ai_code_reviewer_py.cli.load_base_config")
    mock_app_service_constructor = mocker.patch("ai_code_reviewer_py.cli.AppService")
    mock_service_instance = mock_app_service_constructor.return_value
    mock_service_instance.generate_review_summary = mocker.AsyncMock()
    
    mock_config = AppConfig() # Default config
    mock_load_config.return_value = mock_config
    
    result = runner.invoke(cli, ["summarize", "--since", "2024-01-01", "--min-score", "7"])
    assert result.exit_code == 0
    mock_app_service_constructor.assert_called_once_with(mock_config)
    mock_service_instance.generate_review_summary.assert_called_once()
    # You could assert the datetime and int args if needed by inspecting call_args


@patch('ai_code_reviewer_py.cli.AppService')
@patch('ai_code_reviewer_py.cli.validate_final_config')
@patch('ai_code_reviewer_py.cli.asyncio.run')
def test_review_repo_command(mock_asyncio_run, mock_validate, mock_app_service_class):
    mock_service = MagicMock()
    mock_app_service_class.return_value = mock_service
    
    runner = CliRunner()
    result = runner.invoke(cli, [
        'review-repo', 
        '--include', '**/*.py',
        '--exclude', 'tests/**',
        '--max-files', '10'
    ])
    
    assert result.exit_code == 0
    mock_asyncio_run.assert_called_once()
    mock_app_service_class.assert_called_once()

@patch('ai_code_reviewer_py.cli.AppService')
@patch('ai_code_reviewer_py.cli.validate_final_config')
@patch('ai_code_reviewer_py.cli.asyncio.run')
def test_review_remote_command(mock_asyncio_run, mock_validate, mock_app_service_class):
    mock_service = MagicMock()
    mock_app_service_class.return_value = mock_service
    
    runner = CliRunner()
    result = runner.invoke(cli, [
        'review-remote',
        'https://github.com/example/repo.git',
        '--ref', 'main',
        '--include', '**/*.py',
        '--max-files', '5'
    ])
    
    assert result.exit_code == 0
    mock_asyncio_run.assert_called_once()
    mock_app_service_class.assert_called_once()

@patch('ai_code_reviewer_py.cli.AppService')
def test_config_set_command(mock_app_service_class):
    mock_service = MagicMock()
    mock_app_service_class.return_value = mock_service
    
    runner = CliRunner()
    result = runner.invoke(cli, ['config', 'set', 'api_key', 'test-key-123'])
    
    assert result.exit_code == 0
    mock_service.set_global_config_value.assert_called_once_with('api_key', 'test-key-123')

@patch('ai_code_reviewer_py.cli.GLOBAL_CONFIG_FILE')
@patch('builtins.open')
def test_config_show_command_exists(mock_open, mock_config_file):
    mock_config_file.exists.return_value = True
    mock_open.return_value.__enter__.return_value.read.return_value = '{"api_key": "***"}'
    
    runner = CliRunner()
    result = runner.invoke(cli, ['config', 'show'])
    
    assert result.exit_code == 0
    assert "Current content:" in result.output

@patch('ai_code_reviewer_py.cli.GLOBAL_CONFIG_FILE')
def test_config_show_command_not_exists(mock_config_file):
    mock_config_file.exists.return_value = False
    
    runner = CliRunner()
    result = runner.invoke(cli, ['config', 'show'])
    
    assert result.exit_code == 0
    assert "Global configuration file does not exist yet" in result.output

@patch('ai_code_reviewer_py.cli.AppService')
@patch('ai_code_reviewer_py.cli.asyncio.run')
def test_review_command_with_range(mock_asyncio_run, mock_app_service_class):
    mock_service = MagicMock()
    mock_app_service_class.return_value = mock_service
    
    runner = CliRunner()
    result = runner.invoke(cli, ['review', 'HEAD~3..HEAD'])
    
    assert result.exit_code == 0
    mock_asyncio_run.assert_called_once()
    mock_app_service_class.assert_called_once()

@patch('ai_code_reviewer_py.cli.AppService')
@patch('ai_code_reviewer_py.cli.asyncio.run')
def test_review_command_default_range(mock_asyncio_run, mock_app_service_class):
    mock_service = MagicMock()
    mock_app_service_class.return_value = mock_service
    
    runner = CliRunner()
    result = runner.invoke(cli, ['review'])
    
    assert result.exit_code == 0
    mock_asyncio_run.assert_called_once()
    mock_app_service_class.assert_called_once()