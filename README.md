# AI Code Reviewer (Python)

An intelligent code review system for Python projects that analyzes your git commits using AI. It provides detailed feedback on code quality, security, performance, and best practices.

## Features

- 🤖 **Latest AI Models**: Supports models from Anthropic (Claude Sonnet, Claude 3.7 Sonnet, Claude 3.5 Sonnet), OpenAI (GPT-4.1, GPT-4.1 Mini), and Google (Gemini 2.5 Pro/Flash).
- 🔍 **Comprehensive Analysis**: Reviews code focusing on quality, security vulnerabilities, performance issues, naming conventions, complexity, test coverage, documentation, accessibility, and dependency security.
- 🌐 **Web Search Integration**: (Anthropic) Can leverage web search for up-to-date information if the model supports it.
- 🧠 **Extended Thinking**: (Anthropic) Enables deeper analysis for more thorough reviews if the model supports it.
- 📚 **Citations**: Can include citations for recommendations and best practices if the model supports it.
- ⚡ **Batch Processing**: Efficiently reviews multiple commits or files simultaneously.
- 🔄 **Retry Logic**: Robust error handling with exponential backoff for API calls.
- 📄 **Markdown Reports**: Automatically saves detailed review reports in markdown format.
- 📁 **Repository-Wide Analysis**: Generates comprehensive security and architecture assessments of your entire repository.
- 🌍 **Remote Repository Analysis**: Fetches and analyzes complete remote repositories for security, architecture, and code quality.
- 📊 **Review Summarization**: Generates a summary of previously saved markdown review files.
- ⚙️ **Highly Configurable**: Customize AI provider, model, review criteria, output directories, and more via a global configuration file or CLI options.
- ⌨️ **CLI Interface**: Easy-to-use command-line interface powered by Click.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/anywaifu/ai-code-reviewer-py.git
    cd ai-code-reviewer-py
    ```
2.  **Install in editable mode**:

    This is recommended for development or if you want to use the CLI from anywhere while easily pulling updates.
    ```bash
    pip install -e .
    ```
    Ensure your Python scripts directory is in your system's PATH to use the `ai-code-reviewer` command directly.

## Setup

1.  **Set API Keys**:
    The application requires API keys for the AI provider you intend to use. You can set these as environment variables:

    ```bash
    # For Anthropic/Claude (recommended):
    export ANTHROPIC_API_KEY="your-anthropic-api-key"

    # For OpenAI:
    export OPENAI_API_KEY="your-openai-api-key"

    # For Google/Gemini:
    export GOOGLE_API_KEY="your-google-api-key"
    ```
    It's good practice to add these to your shell's configuration file (e.g., `~/.bashrc`, `~/.zshrc`).

2.  **Global Configuration (Recommended)**:
    You can set global configuration values, including your API key, using the CLI. This creates a configuration file at `~/.ai-code-reviewer-py/config.json`.

    First, set your preferred AI provider:
    ```bash
    ai-code-reviewer config set ai_provider anthropic # or openai, google
    ```

    Then, set your API key:
    ```bash
    ai-code-reviewer config set api_key "your-api-key"
    ```

    You can view your current global configuration anytime:
    ```bash
    ai-code-reviewer config show
    ```

## Usage

The primary way to use the tool is through its Command Line Interface (CLI).

### General Help
```bash
ai-code-reviewer --help
ai-code-reviewer <command> --help # For help on a specific command
```
## Review the last commit
```bash
ai-code-reviewer review
```
## Review a specific commit range (e.g., last 3 commits)
```bash
ai-code-reviewer review HEAD~3..HEAD
```
## Review a specific commit
```bash
ai-code-reviewer review <commit_hash>
```
## Review a range between two branches or commits
```bash
ai-code-reviewer review main..my-feature-branch
```
**Common Options for `review`:**
-   `--provider <name>`: Override AI provider (e.g., `openai`).
-   `--web-search` / `--no-web-search`: Enable/disable Anthropic web search.
-   `--citations` / `--no-citations`: Enable/disable review citations.
-   `--batch` / `--no-batch`: Enable/disable batch processing for multiple commits.
-   `--extended-thinking` / `--no-extended-thinking`: Enable/disable Anthropic extended thinking.
-   `--save-markdown` / `--no-save-markdown`: Enable/disable saving reviews to Markdown.
-   `--markdown-dir <path>`: Directory to save Markdown files.
-   `--include-diff` / `--no-include-diff`: Include diff in Markdown reports.

### Review Repository Files (Local)

Generate a comprehensive analysis of your local repository including security assessment, architecture review, and code quality evaluation.
```bash
# Analyze the entire current repository
ai-code-reviewer review-repo
#
# Include only Python files
ai-code-reviewer review-repo --include "**/*.py"
#
# Exclude test files and limit to 10 files
ai-code-reviewer review-repo --exclude "tests/**" --exclude "**/test_*.py" --max-files 10
```

**Common Options for `review-repo`:**
-   `--include <pattern>`: Glob pattern for files to include (can be used multiple times). Default: `**/*`.
-   `--exclude <pattern>`: Glob pattern for files to exclude (can be used multiple times).
-   `--max-files <number>`: Maximum number of files to review.
-   Plus most options available for the `review` command (provider, web-search, etc.).

### Review Remote Repository Files

Fetch and generate a comprehensive analysis of a remote Git repository.
```bash
# Analyze a remote repository from HEAD of default branch
ai-code-reviewer review-remote https://github.com/user/repo.git
#
# Review files from a specific branch or tag
ai-code-reviewer review-remote https://github.com/user/repo.git --ref my-branch
#
# Include only Python files from the remote repository
ai-code-reviewer review-remote https://github.com/user/repo.git --include "**/*.py"
```

**Common Options for `review-remote`:**
-   `repo_url`: The URL of the remote repository.
-   `--ref <ref>`: Git ref (branch, tag, commit hash) to archive from. Default: `HEAD`.
-   `--include <pattern>`, `--exclude <pattern>`, `--max-files <number>`: Same as `review-repo`.
-   Plus most options available for the `review` command.

### Manage Global Configuration
```bash
# Set a global configuration value (e.g., default model)
ai-code-reviewer config set model "claude-3-5-sonnet-20240620"
#
# Show the current global configuration path and content
ai-code-reviewer config show
```

### Summarize Saved Reviews

Generate a summary from previously saved Markdown review files.
```bash
# Summarize all reviews in the default markdown directory
ai-code-reviewer summarize
#
# Summarize reviews since a specific date
ai-code-reviewer summarize --since 2024-01-01
#
# Summarize reviews with a minimum score of 7
ai-code-reviewer summarize --min-score 7
```

**Common Options for `summarize`:**
-   `--since <YYYY-MM-DD>`: Only include reviews from this date.
-   `--min-score <number>`: Minimum review score to include.

## Configuration

The application uses a global configuration file located at `~/.ai-code-reviewer-py/config.json`. You can manage this file using `ai-code-reviewer config set` / `ai-code-reviewer config show` commands, or by editing it directly.

CLI options will override settings from the global configuration file. If a config file path is provided via the main `--config` option, it will take precedence over the global file.

**Example `config.json` structure (based on `AppConfig`):**
```json
{
  "ai_provider": "anthropic",
  "model": "claude-3-5-sonnet-20240620",
  "max_tokens": 32000,
  "api_key": "your_api_key_here_if_not_using_env_vars",
  "review_criteria": [
    "code quality",
    "security vulnerabilities",
    "performance issues",
    "naming conventions",
    "code complexity",
    "test coverage",
    "documentation",
    "accessibility",
    "dependency security"
  ],
  "blocking_issues": ["critical", "high"],
  "minimum_score": 6,
  "save_to_markdown": true,
  "markdown_output_dir": "/home/user/.ai-code-reviewer-py/code-reviews",
  "include_diff_in_markdown": true,
  "enable_extended_thinking": false,
  "enable_citations": false,
  "enable_batch_processing": true,
  "enable_anthropic_web_search": false,
  "retry_attempts": 3,
  "batch_size": 5
}
```

**Key Configuration Options:**

-   `ai_provider`: `anthropic`, `openai`, or `google`.
-   `model`: Specific model name (e.g., `claude-3-5-sonnet-20240620`, `gpt-4.1-mini`).
-   `max_tokens`: Maximum tokens for the AI response.
-   `api_key`: Your API key for the selected provider.
-   `review_criteria`: List of aspects the AI should focus on.
-   `save_to_markdown`: Boolean, whether to save reviews as Markdown files.
-   `markdown_output_dir`: Directory where Markdown reviews are saved. Default: `~/.ai-code-reviewer-py/code-reviews`.
-   `include_diff_in_markdown`: Boolean, whether to include the code diff in Markdown reports.
-   `enable_extended_thinking`: (Anthropic) Boolean for deeper analysis.
-   `enable_citations`: Boolean for including sources in AI responses.
-   `enable_batch_processing`: Boolean for parallel processing of multiple items.
-   `enable_anthropic_web_search`: (Anthropic) Boolean for web search capabilities.
-   `retry_attempts`: Number of retries for failed API calls.

## Supported AI Providers

Ensure you have the respective API key set as an environment variable or in the configuration file.

### Anthropic Claude

-   Environment Variable: `ANTHROPIC_API_KEY`
-   Supported Models (examples):
    -   `claude-sonnet-4-20250514`
    -   `claude-3-7-sonnet-20250219`
    -   `claude-3-5-sonnet-20240620` (Often a good balance of capability and cost)
-   Features: Extended thinking, citations, web search (model-dependent).

### OpenAI

-   Environment Variable: `OPENAI_API_KEY`
-   Supported Models (examples):
    -   `gpt-4.1`
    -   `gpt-4.1-mini` (Often faster and more cost-effective for smaller tasks)

### Google AI (Gemini)

-   Environment Variable: `GOOGLE_API_KEY`
-   Supported Models (examples):
    -   `gemini-2.5-pro-preview-05-06`
    -   `gemini-2.5-flash-preview-05-20`

## How Code Analysis Works

### Repository Analysis
1. **File Collection**: Gathers all tracked files (local) or downloads repository archive (remote)
2. **Comprehensive Analysis**: Sends entire repository content to AI for holistic review
3. **Security Assessment**: Identifies potential backdoors, vulnerabilities, and security risks
4. **Architecture Review**: Evaluates design patterns, structure quality, and modularity
5. **Repository Summary**: Generates detailed markdown report with findings and recommendations

### Commit Analysis
1. **Git Data Extraction**:
    - For commit reviews, `GitAnalyzer` extracts commit details (hash, message, author, date) and the diff.
-   For repository reviews, it lists tracked files or fetches files from a remote archive.

2.  **AI Prompt Construction**:
    -   A structured prompt is built including commit details (if applicable), the code diff or file content, and the configured `review_criteria`.
    -   The prompt instructs the AI to return a JSON formatted response.

3.  **AI Interaction**:
    -   The prompt is sent to the selected AI model via LiteLLM.
    -   Features like extended thinking or web search are enabled based on configuration and provider support.

4.  **Response Parsing**:
    -   The AI's JSON response is parsed into a structured `AIReviewResponse` format.
    -   This includes a score, summary, list of issues (severity, description, suggestion, category), and other notes.

5.  **Output and Reporting**:
    -   The review is displayed on the console.
    -   If `save_to_markdown` is enabled, a detailed Markdown report is saved.

## Markdown Review Reports

When enabled, reviews are saved as Markdown files.

-   **Directory**: Defined by `markdown_output_dir` in the configuration (default: `~/.ai-code-reviewer-py/code-reviews`).
-   **Filename Format**:
    -   For commits: `YYYYMMDD-HHMMSS-<short_hash>-<sanitized_commit_message_summary>.md`
    -   For files: `file-YYYYMMDD-HHMMSS-<sanitized_file_path>.md`

**Report Structure Example (Commit Review):**
```markdown
# Code Review for Commit <short_hash>

**Message:** Original commit message
**Author:** Author Name <author@example.com>
**Date:** YYYY-MM-DDTHH:MM:SS

## AI Review Summary
- **Score:** 8/10
- **Confidence:** 9/10
- **Summary:** A brief summary from the AI.

## Issues Found
- **[CRITICAL]** Description of a critical issue.
  - Suggestion: How to fix it.
  - Citation: (If provided)

## Code Diff
--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
def old_function():
    pass
+def new_function():
+    # This is a new line
```
## Development

### Running Tests

Tests are written using `pytest`.
```bash
pytest
```

## GitHub Actions for Tests

To automatically run tests on push and pull requests, you can add a GitHub Actions workflow. Create a file named `.github/workflows/python-tests.yml`:
```yaml
name: Python Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.13"] # required for blob patterns

    steps:
    - uses: actions/checkout@v4
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .[dev] # Installs main + dev dependencies
    - name: Run tests
      run: |
        pytest
```