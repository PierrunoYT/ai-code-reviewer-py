import click
from typing import Optional
import asyncio
from datetime import datetime
import os

from ai_code_reviewer_py import __version__
from ai_code_reviewer_py.config_loader import (
    load_base_config,
    validate_final_config
)
from ai_code_reviewer_py.app_service import AppService
from ai_code_reviewer_py.constants import GLOBAL_CONFIG_FILE
from ai_code_reviewer_py.enums import AIProvider
from ai_code_reviewer_py.config_models import AppConfig


@click.group(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--config', 'config_file_path', type=click.Path(exists=True, dir_okay=False), help='Path to config file.')
@click.version_option(__version__, package_name="ai-code-reviewer-py")
@click.pass_context
def cli(ctx, config_file_path: Optional[str]):
    """AI Code Reviewer CLI"""
    ctx.ensure_object(dict)
    base_app_config = load_base_config(config_file_path)
    ctx.obj['base_config'] = base_app_config


def _apply_common_config_overrides(
    final_config: AppConfig,
    ai_provider_override: Optional[str],
    enable_anthropic_web_search_override: Optional[bool],
    enable_citations_override: Optional[bool],
    enable_batch_processing_override: Optional[bool],
    enable_extended_thinking_override: Optional[bool],
    save_to_markdown_override: Optional[bool],
    markdown_output_dir_override: Optional[str],
    include_diff_in_markdown_override: Optional[bool] = None,
):
    if ai_provider_override is not None:
        final_config.ai_provider = AIProvider(ai_provider_override)
        if not final_config.api_key:
            if final_config.ai_provider == AIProvider.OPENAI:
                final_config.api_key = os.getenv("OPENAI_API_KEY", "")
            elif final_config.ai_provider == AIProvider.ANTHROPIC:
                final_config.api_key = os.getenv("ANTHROPIC_API_KEY", "")
            elif final_config.ai_provider == AIProvider.GOOGLE:
                final_config.api_key = os.getenv("GOOGLE_API_KEY", "")
    if enable_anthropic_web_search_override is not None:
        final_config.enable_anthropic_web_search = enable_anthropic_web_search_override
    if enable_citations_override is not None:
        final_config.enable_citations = enable_citations_override
    if enable_batch_processing_override is not None:
        final_config.enable_batch_processing = enable_batch_processing_override
    if enable_extended_thinking_override is not None:
        final_config.enable_extended_thinking = enable_extended_thinking_override
    if save_to_markdown_override is not None:
        final_config.save_to_markdown = save_to_markdown_override
    if markdown_output_dir_override is not None:
        final_config.markdown_output_dir = markdown_output_dir_override
    if include_diff_in_markdown_override is not None:
        final_config.include_diff_in_markdown = include_diff_in_markdown_override


@cli.command()
@click.argument('commit_range', default='HEAD~1..HEAD')
@click.option('--provider', 'ai_provider_override', type=click.Choice([p.value for p in AIProvider], case_sensitive=False), help='Override AI provider.')
@click.option('--web-search/--no-web-search', 'enable_anthropic_web_search_override', default=None, help="Enable/disable Anthropic web search (Anthropic only).")
@click.option('--citations/--no-citations', 'enable_citations_override', default=None, help="Enable/disable review citations in output.")
@click.option('--batch/--no-batch', 'enable_batch_processing_override', default=None, help="Enable/disable batch processing of commits.")
@click.option('--extended-thinking/--no-extended-thinking', 'enable_extended_thinking_override', default=None, help="Enable/disable extended thinking (Anthropic only).")
@click.option('--save-markdown/--no-save-markdown', 'save_to_markdown', default=None, help="Enable/disable saving reviews to markdown.")
@click.option('--markdown-dir', 'markdown_output_dir', help="Directory to save markdown files.")
@click.option('--include-diff/--no-include-diff', 'include_diff_in_markdown', default=None, help="Include/exclude diff in markdown.")
@click.pass_context
def review(
    ctx,
    commit_range: str,
    ai_provider_override: Optional[str],
    enable_anthropic_web_search_override: Optional[bool],
    enable_citations_override: Optional[bool],
    enable_batch_processing_override: Optional[bool],
    enable_extended_thinking_override: Optional[bool],
    save_to_markdown: Optional[bool],
    markdown_output_dir: Optional[str],
    include_diff_in_markdown: Optional[bool]
):
    """Review commits in the specified range (e.g., 'HEAD~3..HEAD', 'main..my-branch', 'abc123ef')."""
    try:
        final_config = ctx.obj['base_config'] # Start with base config

        _apply_common_config_overrides(
            final_config=final_config,
            ai_provider_override=ai_provider_override,
            enable_anthropic_web_search_override=enable_anthropic_web_search_override,
            enable_citations_override=enable_citations_override,
            enable_batch_processing_override=enable_batch_processing_override,
            enable_extended_thinking_override=enable_extended_thinking_override,
            save_to_markdown_override=save_to_markdown,
            markdown_output_dir_override=markdown_output_dir,
            include_diff_in_markdown_override=include_diff_in_markdown
        )

        validate_final_config(final_config)
        service = AppService(final_config)
        asyncio.run(service.review_commits_in_range(commit_range))
    except (ValueError, Exception) as e:
        click.echo(click.style(f"{e}", fg="red"), err=True)
        raise click.Abort()


@cli.command(name="review-repo")
@click.option('--include', 'include_patterns', help='Glob patterns for files to include (e.g., "**/*.py"). Can be used multiple times.', multiple=True, default=["**/*"])
@click.option('--exclude', 'exclude_patterns', help='Glob patterns for files to exclude (e.g., "tests/**", "*.min.js"). Can be used multiple times.', multiple=True, default=[])
@click.option('--max-files', type=int, help='Maximum number of files to review.')
@click.option('--provider', 'ai_provider_override', type=click.Choice([p.value for p in AIProvider], case_sensitive=False), help='Override AI provider.')
@click.option('--web-search/--no-web-search', 'enable_anthropic_web_search_override', default=None, help="Enable/disable Anthropic web search (Anthropic only).")
@click.option('--citations/--no-citations', 'enable_citations_override', default=None, help="Enable/disable review citations in output.")
@click.option('--batch/--no-batch', 'enable_batch_processing_override', default=None, help="Enable/disable batch processing of files.")
@click.option('--extended-thinking/--no-extended-thinking', 'enable_extended_thinking_override', default=None, help="Enable/disable extended thinking (Anthropic only).")
@click.option('--save-markdown/--no-save-markdown', 'save_to_markdown_override', default=None, help="Enable/disable saving reviews to markdown.")
@click.option('--markdown-dir', 'markdown_output_dir_override', help="Directory to save markdown files.")
@click.pass_context
def review_repo(
    ctx,
    include_patterns: list[str],
    exclude_patterns: list[str],
    max_files: Optional[int],
    ai_provider_override: Optional[str],
    enable_anthropic_web_search_override: Optional[bool],
    enable_citations_override: Optional[bool],
    enable_batch_processing_override: Optional[bool],
    enable_extended_thinking_override: Optional[bool],
    save_to_markdown_override: Optional[bool],
    markdown_output_dir_override: Optional[str]
):
    """Review all (or a subset of) tracked files in the repository."""
    try:
        final_config = ctx.obj['base_config']

        _apply_common_config_overrides(
            final_config=final_config,
            ai_provider_override=ai_provider_override,
            enable_anthropic_web_search_override=enable_anthropic_web_search_override,
            enable_citations_override=enable_citations_override,
            enable_batch_processing_override=enable_batch_processing_override,
            enable_extended_thinking_override=enable_extended_thinking_override,
            save_to_markdown_override=save_to_markdown_override,
            markdown_output_dir_override=markdown_output_dir_override,
            # No include_diff_in_markdown_override for review-repo
        )
        
        validate_final_config(final_config)
        service = AppService(final_config)
        asyncio.run(service.review_repository_files(list(include_patterns), list(exclude_patterns), max_files))
    except (ValueError, Exception) as e:
        click.echo(click.style(f"{e}", fg="red"), err=True)
        raise click.Abort()


@cli.command(name="review-remote")
@click.argument('repo_url', type=str)
@click.option('--ref', default='HEAD', help='Git ref (branch, tag, commit hash) to archive from the remote repository.')
@click.option('--include', 'include_patterns', help='Glob patterns for files to include (e.g., "**/*.py"). Can be used multiple times.', multiple=True, default=["**/*"])
@click.option('--exclude', 'exclude_patterns', help='Glob patterns for files to exclude (e.g., "tests/**", "*.min.js"). Can be used multiple times.', multiple=True, default=[])
@click.option('--max-files', type=int, help='Maximum number of files to review from the remote repository.')
@click.option('--provider', 'ai_provider_override', type=click.Choice([p.value for p in AIProvider], case_sensitive=False), help='Override AI provider.')
@click.option('--web-search/--no-web-search', 'enable_anthropic_web_search_override', default=None, help="Enable/disable Anthropic web search (Anthropic only).")
@click.option('--citations/--no-citations', 'enable_citations_override', default=None, help="Enable/disable review citations in output.")
@click.option('--batch/--no-batch', 'enable_batch_processing_override', default=None, help="Enable/disable batch processing of files.")
@click.option('--extended-thinking/--no-extended-thinking', 'enable_extended_thinking_override', default=None, help="Enable/disable extended thinking (Anthropic only).")
@click.option('--save-markdown/--no-save-markdown', 'save_to_markdown_override', default=None, help="Enable/disable saving reviews to markdown.")
@click.option('--markdown-dir', 'markdown_output_dir_override', help="Directory to save markdown files.")
@click.pass_context
def review_remote(
    ctx,
    repo_url: str,
    ref: str,
    include_patterns: list[str],
    exclude_patterns: list[str],
    max_files: Optional[int],
    ai_provider_override: Optional[str],
    enable_anthropic_web_search_override: Optional[bool],
    enable_citations_override: Optional[bool],
    enable_batch_processing_override: Optional[bool],
    enable_extended_thinking_override: Optional[bool],
    save_to_markdown_override: Optional[bool],
    markdown_output_dir_override: Optional[str]
):
    """Review files from a remote git repository archive."""
    try:
        final_config: AppConfig = ctx.obj['base_config']
        _apply_common_config_overrides(
            final_config=final_config,
            ai_provider_override=ai_provider_override,
            enable_anthropic_web_search_override=enable_anthropic_web_search_override,
            enable_citations_override=enable_citations_override,
            enable_batch_processing_override=enable_batch_processing_override,
            enable_extended_thinking_override=enable_extended_thinking_override,
            save_to_markdown_override=save_to_markdown_override,
            markdown_output_dir_override=markdown_output_dir_override,
            include_diff_in_markdown_override=None
        )
        validate_final_config(final_config)
        service = AppService(final_config)
        asyncio.run(service.review_external_repository(repo_url, ref, list(include_patterns), list(exclude_patterns), max_files))
    except (ValueError, RuntimeError, Exception) as e:
        click.echo(click.style(f"{e}", fg="red"), err=True)
        raise click.Abort()


@cli.group(name="config")
@click.pass_context
def config_group(ctx):
    """Manage application configuration."""
    pass

@config_group.command(name="set")
@click.argument('key', type=str)
@click.argument('value', type=str)
@click.pass_context
def set_config_value(ctx, key: str, value: str):
    """Sets a configuration value in the global config file.

    KEY: The configuration key to set (e.g., 'api_key', 'model', 'max_tokens').
    VALUE: The value for the configuration key.
    """
    try:
        service = AppService(ctx.obj['base_config'])
        service.set_global_config_value(key, value)
    except Exception as e:
        click.echo(click.style(f"❌ Error: {e}", fg="red"), err=True)
        if not isinstance(e, click.Abort):
            raise click.Abort()

@config_group.command(name="show")
@click.pass_context
def show_config(ctx):
    """Shows the path and content of the global configuration file."""
    click.echo(f"Global configuration file is expected at: {GLOBAL_CONFIG_FILE}")
    if GLOBAL_CONFIG_FILE.exists():
        try:
            with open(GLOBAL_CONFIG_FILE, "r", encoding="utf-8") as f:
                content = f.read()
                click.echo("\nCurrent content:")
                click.echo(content)
        except Exception as e:
            click.echo(click.style(f"Could not read global config file: {e}", fg="red"))
    else:
        click.echo("Global configuration file does not exist yet.")
        click.echo(f"You can create it and set values using: ai-code-reviewer-py config set <KEY> <VALUE>")


@cli.command(name="summarize")
@click.option('--since', 'since_date', type=click.DateTime(formats=["%Y-%m-%d"]), help="Only include reviews from this date (YYYY-MM-DD).")
@click.option('--min-score', type=int, help="Minimum review score to include in summary.")
@click.pass_context
def summarize_reviews_command(ctx, since_date: Optional[datetime], min_score: Optional[int]):
    """Generate a summary of saved review markdown files."""
    try:
        config = ctx.obj['base_config']
        service = AppService(config)
        asyncio.run(service.generate_review_summary(since_date, min_score))
    except Exception as e:
        click.echo(click.style(f"❌ Error: {e}", fg="red"), err=True)
        raise click.Abort()


if __name__ == '__main__':
    cli()