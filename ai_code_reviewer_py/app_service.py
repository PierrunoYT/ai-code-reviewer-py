from pathlib import Path
import json

import re
from datetime import datetime
from typing import Optional, List, Union
from rich.console import Console
from rich.padding import Padding

from ai_code_reviewer_py.config_models import AppConfig
from ai_code_reviewer_py.git_analyzer import GitAnalyzer, CommitInfo
from ai_code_reviewer_py.ai_reviewer import AIReviewer
from ai_code_reviewer_py.constants import GLOBAL_CONFIG_FILE, GLOBAL_CONFIG_DIR
from ai_code_reviewer_py.enums import IssueSeverity
from ai_code_reviewer_py.models import AIReviewResponse, FileDetails, RepositorySummaryResponse

from pydantic import ValidationError

class AppService:
    def __init__(self, config: AppConfig):
        self.config = config
        self.git_analyzer = GitAnalyzer()
        self.ai_reviewer = AIReviewer(config)
        self.console = Console()

    async def review_commits_in_range(self, commit_range: str):
        self.console.print(f"🔍 Analyzing commits in range: [cyan]{commit_range}[/cyan]...")
        commits = self.git_analyzer.get_commits(commit_range)

        if not commits:
            self.console.print("[yellow]No commits found to review.[/yellow]")
            return

        self.console.print(f"Found {len(commits)} commit(s) to review.")

        diffs = [self.git_analyzer.get_commit_diff(c['hash']) for c in commits]
        
        review_results_or_errors = await self.ai_reviewer.review_multiple_commits(commits, diffs)

        for i, result_or_error in enumerate(review_results_or_errors):
            commit_info = commits[i]
            current_diff = diffs[i]
            self.console.rule(f"[bold blue]Reviewing commit: {commit_info['hash'][:8]} - {commit_info['message']}[/bold blue]")
            if isinstance(result_or_error, Exception):
                self.console.print(f"[bold red]❌ Review Failed for commit {commit_info['hash'][:8]}: {result_or_error}[/bold red]")
            else:
                self._display_review_to_console(result_or_error)
                if self.config.save_to_markdown:
                    self._save_commit_review_to_markdown(result_or_error, commit_info, current_diff)

    def _print_review_details_to_console(self, review: AIReviewResponse):
        """Helper method to print common review details to the console."""
        if not isinstance(review, dict) or review.get('score') is None: # Should ideally not happen with AIReviewResponse type
            self.console.print(f"[bold red]❌ Review data incomplete or malformed.[/bold red]\n\nSummary: {review.get('summary', 'N/A')}")
            return

        # Ensure score and confidence are numbers for comparisons
        score = review.get('score', 7)
        confidence = review.get('confidence', 5)
        if not isinstance(score, (int, float)):
            score = 7
        if not isinstance(confidence, (int, float)):
            confidence = 5

        score_color = "green" if score >= 8 else "yellow" if score >= 6 else "red"
        confidence_color = "green" if confidence >= 8 else "yellow" if confidence >= 6 else "red"

        self.console.print(f"📊 [bold {score_color}]Code Quality Score: {score}/10[/bold {score_color}]")
        self.console.print(f"🎯 [bold {confidence_color}]Confidence Level: {confidence}/10[/bold {confidence_color}]")
        self.console.print(f"\n📋 [bold]Summary:[/bold]\n{review['summary']}")

        if review['issues']:
            self.console.print("\n[bold red]⚠️ Issues Found:[/bold red]")
            for issue in review['issues']:
                severity_emoji_map = {
                    IssueSeverity.CRITICAL: '🚨',
                    IssueSeverity.HIGH: '🔥',
                    IssueSeverity.MEDIUM: '⚡',
                    IssueSeverity.LOW: 'ℹ️',
                }
                severity_enum = next((s for s in IssueSeverity if s.value == issue['severity']), None)
                severity_emoji = severity_emoji_map.get(severity_enum, '❓')
                self.console.print(Padding(
                    f"{severity_emoji} [bold magenta]{issue['severity'].upper()}:[/bold magenta] {issue['description']}\n"
                    f"   💡 [italic]Suggestion:[/italic] {issue['suggestion']}" +
                    (f"\n   📚 [italic]Citation:[/italic] {issue['citation']}" if issue.get('citation') else ""),
                    (1, 0, 0, 2)
                ))

        sections = {
            "💡 Suggestions": review.get('suggestions'),
            "🔒 Security Notes": review.get('security'),
            "⚡ Performance Notes": review.get('performance'),
            "♿ Accessibility Notes": review.get('accessibility'),
            "📦 Dependency Notes": review.get('dependencies'),
            "📚 Sources Consulted": review.get('sources')
        }

        for title, items in sections.items():
            if items:
                self.console.print(f"\n[bold blue]{title}:[/bold blue]")
                for item in items:
                    self.console.print(f"  - {item}")
        self.console.print("")

    def _display_review_to_console(self, review: AIReviewResponse):
        self._print_review_details_to_console(review)


    @staticmethod
    def _generate_markdown_filename(commit: CommitInfo) -> str:
        timestamp = commit['date'].strftime("%Y%m%d-%H%M%S")
        short_hash = commit['hash'][:8]
        sanitized_message = "".join(c if c.isalnum() or c in " -" else "" for c in commit['message']).replace(" ", "-")[:50]
        return f"{timestamp}-{short_hash}-{sanitized_message}.md"

    @staticmethod
    def _generate_common_ai_review_markdown_section(review: AIReviewResponse) -> str:
        """Generates common AI review sections (summary, score, issues) for markdown."""
        md_content = f"## AI Review Summary\n"
        md_content += f"- **Score:** {review['score']}/10\n"
        md_content += f"- **Confidence:** {review['confidence']}/10\n"
        md_content += f"- **Summary:** {review['summary']}\n\n"

        if review['issues']:
            md_content += "## Issues Found\n"
            for issue in review['issues']:
                md_content += f"- **[{issue['severity'].upper()}]** {issue['description']}\n"
                md_content += f"  - Suggestion: {issue['suggestion']}\n"
                if issue.get('citation'):
                    md_content += f"  - Citation: {issue['citation']}\n"
            md_content += "\n"
        return md_content

    def _generate_markdown_content(self, review: AIReviewResponse, commit: CommitInfo, diff: str) -> str:
        md_content = f"# Code Review for Commit {commit['hash'][:8]}\n\n"
        md_content += f"**Message:** {commit['message']}\n"
        md_content += f"**Author:** {commit['author_name']} <{commit['author_email']}>\n"
        md_content += f"**Date:** {commit['date'].isoformat()}\n\n"
        
        md_content += AppService._generate_common_ai_review_markdown_section(review)
        
        if self.config.include_diff_in_markdown and diff:
            md_content += "## Code Diff\n"
            md_content += f"```diff\n{diff}\n```\n\n"
        
        return md_content

    def _save_commit_review_to_markdown(self, review: AIReviewResponse, commit: CommitInfo, diff: str):
        filename = AppService._generate_markdown_filename(commit)
        output_dir_path = Path(self.config.markdown_output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)
        filepath = output_dir_path / filename

        markdown_content = self._generate_markdown_content(review, commit, diff)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            self.console.print(f"[green]💾 Review saved to: {filepath}[/green]")
        except Exception as e:
            self.console.print(f"[red]❌ Failed to save markdown file: {e}[/red]")

    def _load_or_create_global_config_data(self) -> tuple[dict, bool]:
        """
        Loads global config data if it exists, otherwise returns default AppConfig data.
        Returns a tuple of (config_data_dict, file_existed_boolean).
        """
        GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        if GLOBAL_CONFIG_FILE.exists():
            try:
                with open(GLOBAL_CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f), True
            except json.JSONDecodeError:
                self.console.print(f"[yellow]⚠️ Warning: Global config file {GLOBAL_CONFIG_FILE} is corrupted. Using defaults.[/yellow]")
            except Exception as e:
                self.console.print(f"[yellow]⚠️ Warning: Error reading global config file {GLOBAL_CONFIG_FILE}: {e}. Using defaults.[/yellow]")

        default_config_instance = AppConfig()
        return default_config_instance.model_dump(mode="json", by_alias=True, exclude_none=True), False

    @staticmethod
    def _is_sensitive_key(key: str) -> bool:
        """Check if a configuration key contains sensitive information that should be masked."""
        sensitive_keys = ['api_key', 'key', 'token', 'secret', 'password']
        key_lower = key.lower()
        return any(sensitive_word in key_lower for sensitive_word in sensitive_keys)

    @staticmethod
    def _mask_sensitive_value(value: any) -> str:
        """Mask sensitive values for display."""
        return "***HIDDEN***" if value and str(value).strip() else "***EMPTY***"

    @staticmethod
    def _find_matching_field(key_to_set: str) -> Optional[str]:
        """Find the actual field name that matches the user input."""
        # Direct match
        if key_to_set in AppConfig.model_fields:
            return key_to_set
        
        # Check aliases
        for field_name, field_info in AppConfig.model_fields.items():
            if field_info.alias == key_to_set:
                return field_name
        
        # Check partial matches (e.g., "provider" -> "ai_provider")
        for field_name in AppConfig.model_fields:
            if field_name.endswith(f"_{key_to_set}") or field_name.startswith(f"{key_to_set}_"):
                return field_name
        
        return None

    @staticmethod
    def _get_valid_enum_values(field_name: str) -> Optional[List[str]]:
        """Get valid enum values for a field if it's an enum type."""
        field_info = AppConfig.model_fields.get(field_name)
        if not field_info:
            return None
        
        # Handle Optional[Enum] types
        field_type = field_info.annotation
        if hasattr(field_type, '__origin__') and field_type.__origin__ is Union:
            # Extract non-None type from Optional
            for arg in field_type.__args__:
                if arg is not type(None):
                    field_type = arg
                    break
        
        # Check if it's an enum
        if hasattr(field_type, '__members__'):
            return [member.value for member in field_type.__members__.values()]
        
        return None

    def set_global_config_value(self, key_to_set: str, value_str: str):
        """
        Sets a specific key-value pair in the global configuration file.
        Creates the file with defaults if it doesn't exist, then applies the change.
        The key should match a field name or alias in AppConfig.
        """
        config_data, file_existed = self._load_or_create_global_config_data()

        target_field_name = self._find_matching_field(key_to_set)

        if not target_field_name:
            valid_keys = list(AppConfig.model_fields.keys())
            self.console.print(f"❌ [bold red]Error: Configuration key '{key_to_set}' is not recognized.[/bold red]")
            self.console.print(f"Valid configuration keys: {', '.join(valid_keys)}")
            return

        # Check if it's an enum field and validate the value
        valid_enum_values = self._get_valid_enum_values(target_field_name)
        if valid_enum_values and value_str not in valid_enum_values:
            self.console.print(f"❌ [bold red]Error: Invalid value '{value_str}' for '{target_field_name}'.[/bold red]")
            self.console.print(f"Valid values: {', '.join(valid_enum_values)}")
            return

        # Set the value
        config_data[target_field_name] = value_str
        
        # Show helpful message if user used a close match
        if key_to_set != target_field_name:
            self.console.print(f"ℹ️ [cyan]Note: Using field name '{target_field_name}' for your input '{key_to_set}'.[/cyan]")

        try:
            validated_config_instance = AppConfig(**config_data)

            data_to_save = validated_config_instance.model_dump(mode="json", by_alias=True, exclude_none=True)

            with open(GLOBAL_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, indent=2)

            final_key_in_json = target_field_name if target_field_name else key_to_set
            final_value_in_json = data_to_save.get(final_key_in_json)
            
            # Mask sensitive values in console output
            if self._is_sensitive_key(final_key_in_json):
                display_value = self._mask_sensitive_value(final_value_in_json)
            else:
                display_value = json.dumps(final_value_in_json)

            if not file_existed:
                self.console.print(f"✅ Global configuration file created at: [green]{GLOBAL_CONFIG_FILE}[/green]")
            else:
                self.console.print(f"✅ Global configuration file updated at: [green]{GLOBAL_CONFIG_FILE}[/green]")
            
            self.console.print(f"   Set [cyan]{final_key_in_json}[/cyan] to [yellow]{display_value}[/yellow].")

        except ValidationError as e:
            self.console.print(f"❌ [bold red]Error: The new value for '{key_to_set}' ('{value_str}') resulted in an invalid configuration:\n{e}[/bold red]")
            self.console.print(f"   Your changes were not saved. Please provide a valid value.")
        except Exception as e:
            self.console.print(f"❌ [bold red]Error creating global configuration file at {GLOBAL_CONFIG_FILE}: {e}[/bold red]")
            raise

    def _filter_and_limit_file_data(
        self,
        all_files_data: List[FileDetails],
        include_patterns: List[str],
        exclude_patterns: List[str],
        max_files: Optional[int],
    ) -> List[FileDetails]:
        filtered_files: List[FileDetails] = []
        for file_data in all_files_data:
            file_path = Path(file_data["path"])

            if any(file_path.full_match(pattern) for pattern in exclude_patterns):
                continue

            if not include_patterns or any(file_path.full_match(pattern) for pattern in include_patterns):
                filtered_files.append(file_data)

        if max_files is not None and len(filtered_files) > max_files:
            self.console.print(
                f"[yellow]Limiting to {max_files} files out of {len(filtered_files)} "
                f"found after pattern filtering.[/yellow]"
            )
            # Sort by path before slicing for deterministic output if limiting
            filtered_files.sort(key=lambda fd: fd["path"])
            return filtered_files[:max_files]
        return filtered_files

    def _display_file_review_to_console(self, review: AIReviewResponse, file_path: str):
        self.console.rule(f"[bold blue]Reviewing file: {file_path}[/bold blue]")
        self._print_review_details_to_console(review)

    def _display_repository_summary_to_console(self, summary: RepositorySummaryResponse, repo_info: str):
        self.console.rule(f"[bold green]📊 Repository Summary: {repo_info}[/bold green]")
        
        # Overall assessment
        score_color = "green" if summary['overall_score'] >= 8 else "yellow" if summary['overall_score'] >= 6 else "red"
        confidence_color = "green" if summary['confidence'] >= 8 else "yellow" if summary['confidence'] >= 6 else "red"
        
        self.console.print(f"🎯 [bold {score_color}]Overall Repository Score: {summary['overall_score']}/10[/bold {score_color}]")
        self.console.print(f"🔍 [bold {confidence_color}]Assessment Confidence: {summary['confidence']}/10[/bold {confidence_color}]")
        self.console.print(f"\n📋 [bold]Executive Summary:[/bold]\n{summary['executive_summary']}")
        
        # Security Assessment
        security = summary.get('security_assessment', {})
        if security:
            risk_level = security.get('risk_level', 'unknown')
            risk_emoji = {'low': '🟢', 'medium': '🟡', 'high': '🟠', 'critical': '🔴'}.get(risk_level, '❓')
            self.console.print(f"\n🔒 [bold red]Security Assessment:[/bold red] {risk_emoji} {risk_level.upper()} RISK")
            
            if security.get('potential_backdoors'):
                self.console.print("  🚨 [bold red]Potential Backdoors/Suspicious Patterns:[/bold red]")
                for backdoor in security['potential_backdoors']:
                    self.console.print(f"    - {backdoor}")
            
            if security.get('vulnerabilities_found'):
                self.console.print("  ⚠️ [bold yellow]Vulnerabilities Found:[/bold yellow]")
                for vuln in security['vulnerabilities_found']:
                    self.console.print(f"    - {vuln}")
        
        # Architecture Assessment
        arch = summary.get('architecture_assessment', {})
        if arch:
            self.console.print(f"\n🏗️ [bold blue]Architecture Assessment:[/bold blue]")
            if arch.get('patterns_used'):
                self.console.print(f"  📐 Design Patterns: {', '.join(arch['patterns_used'])}")
            if arch.get('modularity_score'):
                self.console.print(f"  🧩 Modularity Score: {arch['modularity_score']}/10")
        
        # Key sections
        sections = {
            "🔑 Key Findings": summary.get('key_findings'),
            "🚨 Immediate Actions Required": summary.get('immediate_actions'),
            "📈 Long-term Recommendations": summary.get('long_term_recommendations'),
            "📚 Sources Consulted": summary.get('sources')
        }
        
        for title, items in sections.items():
            if items:
                self.console.print(f"\n[bold blue]{title}:[/bold blue]")
                for item in items:
                    self.console.print(f"  - {item}")
        
        self.console.print("")

    @staticmethod
    def _generate_repository_summary_markdown_content(
        summary: RepositorySummaryResponse,
        repo_info: str,
        total_files: int,
        failed_reviews: int
    ) -> str:
        """Generate a repository summary markdown report."""
        md_content = f"# Repository Analysis Summary\n\n"
        md_content += f"**Repository:** {repo_info}\n"
        md_content += f"**Reviewed on:** {datetime.now().isoformat()}\n"
        md_content += f"**Total files reviewed:** {total_files}\n"
        md_content += f"**Failed reviews:** {failed_reviews}\n"
        md_content += f"**Overall Score:** {summary['overall_score']}/10\n"
        md_content += f"**Confidence:** {summary['confidence']}/10\n\n"
        
        md_content += f"## Executive Summary\n{summary['executive_summary']}\n\n"
        
        # Security Assessment
        security = summary.get('security_assessment', {})
        if security:
            risk_level = security.get('risk_level', 'unknown')
            md_content += f"## 🔒 Security Assessment\n"
            md_content += f"**Risk Level:** {risk_level.upper()}\n\n"
            
            if security.get('potential_backdoors'):
                md_content += f"### Potential Security Concerns\n"
                for concern in security['potential_backdoors']:
                    md_content += f"- {concern}\n"
                md_content += "\n"
            
            if security.get('vulnerabilities_found'):
                md_content += f"### Vulnerabilities Found\n"
                for vuln in security['vulnerabilities_found']:
                    md_content += f"- {vuln}\n"
                md_content += "\n"
        
        # Architecture Assessment
        arch = summary.get('architecture_assessment', {})
        if arch:
            md_content += f"## 🏗️ Architecture Assessment\n"
            if arch.get('patterns_used'):
                md_content += f"**Design Patterns:** {', '.join(arch['patterns_used'])}\n"
            if arch.get('structure_quality'):
                md_content += f"**Structure Quality:** {arch['structure_quality']}\n"
            if arch.get('modularity_score'):
                md_content += f"**Modularity Score:** {arch['modularity_score']}/10\n"
            md_content += "\n"
        
        # Key sections
        sections = {
            "🔑 Key Findings": summary.get('key_findings'),
            "🚨 Immediate Actions Required": summary.get('immediate_actions'),
            "📈 Long-term Recommendations": summary.get('long_term_recommendations')
        }
        
        for title, items in sections.items():
            if items:
                md_content += f"## {title}\n"
                for item in items:
                    md_content += f"- {item}\n"
                md_content += "\n"
        
        if summary.get('sources'):
            md_content += f"## 📚 Sources Consulted\n"
            for source in summary['sources']:
                md_content += f"- {source}\n"
            md_content += "\n"
        
        return md_content

    def _save_repository_summary_to_markdown(
        self, 
        summary: RepositorySummaryResponse,
        repo_info: str,
        total_files: int = 0,
        failed_reviews: int = 0
    ):
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        sanitized_repo_info = re.sub(r'[<>:"/\\|?*]', '_', repo_info)
        filename = f"repo-summary-{timestamp}-{sanitized_repo_info[:50]}.md"
        
        output_dir_path = Path(self.config.markdown_output_dir)
        output_dir_path.mkdir(parents=True, exist_ok=True)
        filepath = output_dir_path / filename

        markdown_content = self._generate_repository_summary_markdown_content(summary, repo_info, total_files, failed_reviews)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(markdown_content)
            self.console.print(f"[green]💾 Repository summary saved to: {filepath}[/green]")
        except Exception as e:
            self.console.print(f"[red]❌ Failed to save markdown file: {e}[/red]")

    async def _review_file_details_list_and_report(
        self,
        files_to_review: List[FileDetails],
        console_rule_prefix: str,
        repo_info: str
    ):
        """Helper to review a list of FileDetails, display, and save reports."""
        if not files_to_review:
            self.console.print("[yellow]No files to review.[/yellow]")
            return

        self.console.print(f"Found {len(files_to_review)} file(s) to review.")
        
        try:
            self.console.print("\n[bold cyan]🤖 Analyzing entire repository...[/bold cyan]")
            repo_summary = await self.ai_reviewer.review_entire_repository_with_retry(files_to_review, repo_info)
            
            if isinstance(repo_summary, Exception):
                self.console.print(f"[bold red]❌ Repository analysis failed: {repo_summary}[/bold red]")
                return
            
            self._display_repository_summary_to_console(repo_summary, repo_info)
            
            if self.config.save_to_markdown:
                self._save_repository_summary_to_markdown(repo_summary, repo_info, len(files_to_review), 0)
        except Exception as e:
            self.console.print(f"[yellow]⚠️ Failed to analyze repository: {e}[/yellow]")

    async def review_repository_files(
        self,
        include_patterns: List[str],
        exclude_patterns: List[str],
        max_files: Optional[int]
    ):
        self.console.print("🔍 Analyzing repository files...")
        
        repo_root = Path(self.git_analyzer.repo.working_dir)
        all_tracked_files_paths_str = self.git_analyzer.get_tracked_files()

        if not all_tracked_files_paths_str:
            self.console.print("[yellow]No tracked files found in the repository.[/yellow]")
            return

        selected_file_paths_str: List[str] = []
        for file_path_str in all_tracked_files_paths_str:

            file_path_obj = Path(file_path_str)

            if any(file_path_obj.full_match(pattern) for pattern in exclude_patterns):
                continue

            if not include_patterns or any(file_path_obj.full_match(pattern) for pattern in include_patterns):
                selected_file_paths_str.append(file_path_str)

        sorted_selected_file_paths_str = sorted(selected_file_paths_str)

        if max_files is not None and len(sorted_selected_file_paths_str) > max_files:
            self.console.print(
                f"[yellow]Limiting to {max_files} files out of {len(sorted_selected_file_paths_str)} found.[/yellow]"
            )
            final_file_paths_to_review_str = sorted_selected_file_paths_str[:max_files]
        else:
            final_file_paths_to_review_str = sorted_selected_file_paths_str

        if not final_file_paths_to_review_str:
            self.console.print("[yellow]No files found to review based on include/exclude patterns.[/yellow]")
            return

        await self._review_file_details_list_and_report(
            [{"path": fp_str, "content": (repo_root / fp_str).read_text(encoding='utf-8', errors='ignore')} 
             for fp_str in final_file_paths_to_review_str],
            "Reviewing file",
            f"Local Repository ({repo_root})"
        )

    async def review_external_repository(
        self,
        repo_url: str,
        ref: str,
        include_patterns: List[str],
        exclude_patterns: List[str],
        max_files: Optional[int]
    ):
        self.console.print(f"🔍 Fetching and analyzing remote repository: [cyan]{repo_url}[/cyan] (ref: [cyan]{ref}[/cyan])...")
        try:
            all_files_data = self.git_analyzer.get_files_from_remote_archive(repo_url, ref)
            self.console.print("[green]✅ Repository downloaded successfully[/green]")
        except RuntimeError as e:
            self.console.print(f"[bold red]❌ Failed to fetch or process remote repository: {e}[/bold red]")
            return
        
        # Sort files by path before filtering for consistent limiting if max_files is used
        all_files_data.sort(key=lambda fd: fd["path"])

        files_to_review = self._filter_and_limit_file_data(
            all_files_data, include_patterns, exclude_patterns, max_files
        )

        if not files_to_review:
            self.console.print("[yellow]No files found to review after applying include/exclude patterns and limits.[/yellow]")
            return

        await self._review_file_details_list_and_report(files_to_review, "Reviewing remote file", f"{repo_url} (ref: {ref})")

    async def generate_review_summary(self, since_date: Optional[datetime], min_score: Optional[int]):
        review_dir = Path(self.config.markdown_output_dir)
        if not review_dir.exists() or not review_dir.is_dir():
            self.console.print(
                f"[yellow]Review directory '{self.config.markdown_output_dir}' does not exist. No reviews to summarize.[/yellow]"
            )
            return

        review_files = list(review_dir.glob("*.md"))
        if not review_files:
            self.console.print("[yellow]No review files found.[/yellow]")
            return

        summaries = []
        for md_file in review_files:
            content = md_file.read_text(encoding="utf-8")
            
            date_match = re.search(r"\*\*Date:\*\* (.*?)\n", content)
            score_match = re.search(r"- \*\*Score:\*\* (\d+)/10", content)
            summary_match = re.search(r"- \*\*Summary:\*\* (.*?)\n", content, re.DOTALL)

            if not (date_match and score_match and summary_match):
                self.console.print(f"[yellow]Could not parse all required fields from '{md_file.name}'. Skipping.[/yellow]")
                continue

            try:
                # Handle 'Z' for UTC explicitly for wider compatibility
                review_date_str = date_match.group(1).strip()
                if review_date_str.endswith('Z'):
                    review_date = datetime.fromisoformat(review_date_str[:-1] + '+00:00')
                else:
                    review_date = datetime.fromisoformat(review_date_str)
                
                review_score = int(score_match.group(1))
                review_summary = summary_match.group(1).strip()
            except (ValueError, IndexError) as e:
                self.console.print(f"[yellow]Error parsing data from '{md_file.name}': {e}. Skipping.[/yellow]")
                continue

            if since_date and review_date < since_date:
                continue
            if min_score is not None and review_score < min_score:
                continue
            
            summaries.append({"file": md_file.name, "date": review_date, "score": review_score, "summary": review_summary})

        if not summaries:
            self.console.print("[yellow]No reviews match the specified criteria.[/yellow]")
            return

        self.console.print(f"\n[bold green]Review Summary ({len(summaries)} reviews matching criteria):[/bold green]")
        for summary_item in sorted(summaries, key=lambda s: s['date'], reverse=True):
            self.console.print(f"  📄 [cyan]{summary_item['file']}[/cyan] ({summary_item['date'].strftime('%Y-%m-%d')}) - Score: {summary_item['score']}/10")
            self.console.print(f"     [italic]{summary_item['summary']}[/italic]\n")