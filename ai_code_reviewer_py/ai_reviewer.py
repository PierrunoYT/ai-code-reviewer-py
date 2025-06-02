import json
import re
import asyncio
import os
from typing import Any, Dict, List, Optional, Union
from typing import cast

import litellm

from ai_code_reviewer_py.config_models import AppConfig
from ai_code_reviewer_py.git_analyzer import CommitInfo
from ai_code_reviewer_py.models import AIReviewResponse, CommitDetails, FileDetails, RepositorySummaryResponse
from ai_code_reviewer_py.exceptions import ReviewParsingError, ReviewGenerationError
from ai_code_reviewer_py.enums import AIProvider, AIModel


class AIReviewer:
    def __init__(self, config: AppConfig):
        self.config = config
        self.provider = config.ai_provider
        self.model = config.model or self._get_default_model()
        self.enable_extended_thinking = config.enable_extended_thinking
        self.enable_citations = config.enable_citations

    def _get_default_model(self) -> str:
        if self.provider == AIProvider.OPENAI:
            return AIModel.GPT_4_1_MINI
        elif self.provider == AIProvider.ANTHROPIC:
            return AIModel.CLAUDE_SONNET_4_20250514
        elif self.provider == AIProvider.GOOGLE:
            return AIModel.GEMINI_2_5_FLASH_PREVIEW_05_20
        return AIModel.GPT_4_1_MINI

    def _prepare_litellm_kwargs(self) -> Dict[str, Any]:
        kwargs = {}

        if self.provider == AIProvider.ANTHROPIC and self.enable_extended_thinking:
            max_tokens_budget = self.config.max_tokens or 64000
            budget_tokens = min(48000, int(max_tokens_budget * 0.75))
            kwargs["thinking"] = {"type": "enabled", "budget_tokens": budget_tokens}
        
        if self.provider == AIProvider.ANTHROPIC and self.config.enable_anthropic_web_search:
            supported_web_search_models = [
                AIModel.CLAUDE_SONNET_4_20250514,
                AIModel.CLAUDE_3_7_SONNET_20250219,
                AIModel.CLAUDE_3_5_SONNET_LATEST
            ]
            current_model_enum = None
            for model in AIModel:
                if model.value == self.model:
                    current_model_enum = model
            if current_model_enum in supported_web_search_models:
                kwargs["tools"] = [{
                    "type": "web_search_20250305", 
                    "name": "web_search"
                }]
            else:
                print(f"Warning: Anthropic web search is enabled but model '{self.model}' may not support it. Tool not added.")

        return kwargs

    def _build_prompt(self, diff: str, commit: CommitInfo) -> str:
        commit_details_for_prompt = CommitDetails(
            hash=commit['hash'],
            message=commit['message'],
            author=f"{commit['author_name']} <{commit['author_email']}>",
            date=commit['date'].isoformat()
        )

        citation_issue_field = '"citation": "<source URL or reference if applicable>",' if self.enable_citations else ''
        citation_sources_field = '"sources": ["<list of sources consulted>"],' if self.enable_citations else ''

        criteria_list = '\n'.join(f"{i+1}. {criterion.title()}" for i, criterion in enumerate(self.config.review_criteria))
        base_prompt = f"""You are an expert code reviewer. Please review the following git commit and provide feedback.

Commit Message: {commit_details_for_prompt['message']}
Author: {commit_details_for_prompt['author']}
Date: {commit_details_for_prompt['date']}

Code Changes:
{diff}

Please analyze this commit and provide a structured review focusing on:
{criteria_list}

{ 'Provide citations for any security recommendations or best practices you mention.' if self.enable_citations else ''}

Format your response as JSON with this structure:
{{
  "score": "<number 1-10>",
  "summary": "<brief summary>",
  "issues": [
    {{
      "severity": "low|medium|high|critical",
      "description": "<issue description>",
      "suggestion": "<how to fix>",
      "category": "security|performance|quality|style|testing|documentation",
      {citation_issue_field}
      "auto_fixable": "<boolean>"
    }}
  ],
  "suggestions": ["<general improvement suggestions>"],
  "security": ["<security-related notes>"],
  "performance": ["<performance-related notes>"],
  "dependencies": ["<dependency-related observations>"],
  "accessibility": ["<accessibility considerations>"],
  {citation_sources_field}
  "confidence": "<number 1-10 indicating confidence in the review>"
}}

Be constructive, specific, and provide actionable feedback. Focus on the most impactful improvements."""
        return base_prompt + "\n\nIMPORTANT: Respond ONLY with valid JSON. Do not wrap your response in markdown code blocks or add any explanation outside the JSON."

    def _build_repository_review_prompt(self, files_data: List[FileDetails], repo_info: str) -> str:
        citation_issue_field = '"citation": "<source URL or reference if applicable>",' if self.enable_citations else ''
        citation_sources_field = '"sources": ["<list of sources consulted>"],' if self.enable_citations else ''

        criteria_list = '\n'.join(f"{i+1}. {criterion.title()}" for i, criterion in enumerate(self.config.review_criteria))
        
        # Prepare the complete repository content
        repository_content = []
        for file_data in files_data:
            repository_content.append(f"=== FILE: {file_data['path']} ===")
            repository_content.append(file_data['content'])
            repository_content.append("=== END FILE ===\n")
        
        full_repo_text = "\n".join(repository_content)
        
        base_prompt = f"""You are a senior software architect conducting a comprehensive repository analysis. Please review the entire repository and provide detailed feedback.

Repository: {repo_info}
Total Files: {len(files_data)}

Complete Repository Content:
{full_repo_text}

Please analyze this entire repository and provide a structured review focusing on:
{criteria_list}
VERY IMPORTANT: Security Assessment (potential backdoors, vulnerabilities, insecure practices)
Architecture and Design Patterns
Code Quality and Consistency
Dependencies and Third-party Risk

{"Provide citations for security recommendations and architectural guidance." if self.enable_citations else ""}

Format your response as JSON with this structure:
{{
  "overall_score": "<number 1-10>",
  "executive_summary": "<comprehensive assessment in 3-4 sentences>",
  "architecture_assessment": {{
    "patterns_used": ["<list of design patterns identified>"],
    "structure_quality": "<detailed assessment of project structure>",
    "modularity_score": "<number 1-10>",
    "separation_of_concerns": "<assessment of how well concerns are separated>"
  }},
  "security_assessment": {{
    "risk_level": "low|medium|high|critical",
    "potential_backdoors": ["<list any suspicious code patterns or potential backdoors>"],
    "vulnerabilities_found": ["<detailed list of security issues found>"],
    "insecure_practices": ["<list of insecure coding practices>"],
    "data_handling": "<assessment of how sensitive data is handled>",
    "authentication_authorization": "<assessment of auth mechanisms if present>",
    "input_validation": "<assessment of input validation practices>",
    "recommendations": ["<detailed security improvement suggestions>"]
  }},
  "code_quality": {{
    "maintainability": "<detailed assessment>",
    "consistency": "<assessment of coding style and patterns>",
    "documentation_coverage": "<assessment of documentation quality>",
    "test_coverage_assessment": "<assessment of testing practices>",
    "error_handling": "<assessment of error handling patterns>",
    "performance_considerations": "<assessment of performance aspects>"
  }},
  "dependencies": {{
    "third_party_risk": "<detailed assessment>",
    "dependency_analysis": ["<analysis of dependencies used>"],
    "version_management": "<assessment of dependency versioning>",
    "security_implications": ["<security implications of dependencies>"],
    "recommendations": ["<dependency-related suggestions>"]
  }},
  "key_findings": ["<most important discoveries about the codebase>"],
  "architectural_strengths": ["<what the repository does well>"],
  "critical_issues": ["<urgent issues that need immediate attention>"],
  "improvement_opportunities": ["<areas for enhancement>"],
  "compliance_considerations": ["<any compliance or regulatory considerations>"],
  {citation_sources_field}
  "confidence": "<number 1-10 indicating confidence in the assessment>"
}}

Provide a thorough, professional analysis that considers the repository as a complete system. Focus on security, architecture, and overall code quality."""
        
        return base_prompt + "\n\nIMPORTANT: Respond ONLY with valid JSON. Do not wrap your response in markdown code blocks or add any explanation outside the JSON."

    async def _call_llm_with_litellm(self, prompt: str) -> str:
        litellm_model_name = self.model
        api_key = self.config.api_key.strip()

        messages = [
            {"role": "system", "content": "You are a senior software engineer providing code reviews. You MUST respond with valid JSON only. No markdown formatting, no code blocks, no explanations outside JSON. Be thorough and constructive in your analysis."},
            {"role": "user", "content": prompt}
        ]

        litellm_kwargs = self._prepare_litellm_kwargs()

        response = await litellm.acompletion(
            model=litellm_model_name,
            api_key=api_key,
            messages=messages,
            max_tokens=self.config.max_tokens or 4000,
            temperature=0.1,
            top_p=0.99,
            **litellm_kwargs
        )
        return response.choices[0].message.content

    @staticmethod
    def _parse_response(response_text: str) -> AIReviewResponse:
        try:
            cleaned_response = response_text.strip()
            
            # Try to extract JSON from markdown code blocks first
            markdown_json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned_response, re.DOTALL)
            if markdown_json_match:
                cleaned_response = markdown_json_match.group(1)
            
            # Look for JSON object boundaries
            json_match = re.search(r"\{[\s\S]*\}", cleaned_response)
            if json_match:
                json_content = json_match.group(0)
                try:
                    parsed_json = json.loads(json_content)
                except json.JSONDecodeError:
                    # Try to fix common JSON issues
                    json_content = json_content.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                    # Remove any trailing commas before closing braces/brackets
                    json_content = re.sub(r',(\s*[}\]])', r'\1', json_content)
                    parsed_json = json.loads(json_content)
            else:
                # Last resort: try parsing the entire cleaned response
                parsed_json = json.loads(cleaned_response)
            
            # Basic validation to ensure it's somewhat like AIReviewResponse
            if not isinstance(parsed_json, dict) or "score" not in parsed_json or "summary" not in parsed_json:
                raise ReviewParsingError(f"Parsed JSON does not match expected AIReviewResponse structure. Keys found: {list(parsed_json.keys()) if isinstance(parsed_json, dict) else 'Not a dict'}. Response: {response_text[:200]}...")
            
            # Ensure required fields exist with defaults
            parsed_json.setdefault('issues', [])
            parsed_json.setdefault('suggestions', [])
            parsed_json.setdefault('confidence', 5)

            # Ensure numeric fields are properly converted from strings if needed
            if 'score' in parsed_json and isinstance(parsed_json['score'], str):
                try:
                    parsed_json['score'] = int(parsed_json['score'])
                except (ValueError, TypeError):
                    parsed_json['score'] = 7  # Default fallback
            
            if 'confidence' in parsed_json and isinstance(parsed_json['confidence'], str):
                try:
                    parsed_json['confidence'] = int(parsed_json['confidence'])
                except (ValueError, TypeError):
                    parsed_json['confidence'] = 5  # Default fallback

            return AIReviewResponse(**parsed_json)
        except json.JSONDecodeError as e:
            raise ReviewParsingError(f"Failed to parse AI response as JSON: {e}. Response: {response_text[:200]}...") from e
        except Exception as e:
            raise ReviewParsingError(f"Unexpected error parsing AI response: {e}. Response: {response_text[:200]}...") from e

    @staticmethod
    def _parse_repository_summary_response(response_text: str) -> RepositorySummaryResponse:
        try:
            cleaned_response = response_text.strip()
            
            # Try to extract JSON from Markdown code blocks first
            markdown_json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned_response, re.DOTALL)
            if markdown_json_match:
                cleaned_response = markdown_json_match.group(1)
            
            # Look for JSON object boundaries
            json_match = re.search(r"\{[\s\S]*\}", cleaned_response)
            if json_match:
                json_content = json_match.group(0)
                try:
                    return RepositorySummaryResponse(**json.loads(json_content))
                except json.JSONDecodeError:
                    # Try to fix common JSON issues
                    json_content = json_content.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
                    json_content = re.sub(r',(\s*[}\]])', r'\1', json_content)
                    return RepositorySummaryResponse(**json.loads(json_content))
            else:
                return RepositorySummaryResponse(**json.loads(cleaned_response))
        except Exception as e:
            raise ReviewParsingError(f"Failed to parse repository summary response: {e}. Response: {response_text[:200]}...") from e

    async def review_code(self, diff: str, commit: CommitInfo) -> AIReviewResponse:
        prompt = self._build_prompt(diff, commit)
        
        try:
            raw_response_text = await self._call_llm_with_litellm(prompt)
            parsed_response = AIReviewer._parse_response(raw_response_text)
            return parsed_response
        except ReviewParsingError as e:
            raise
        except Exception as e:
            raise ReviewGenerationError(f"Failed to get review from AI for commit {commit['hash']}: {e}") from e

    async def review_entire_repository(self, files_data: List[FileDetails], repo_info: str) -> RepositorySummaryResponse:
        prompt = self._build_repository_review_prompt(files_data, repo_info)
        
        try:
            raw_response_text = await self._call_llm_with_litellm(prompt)
            parsed_response = AIReviewer._parse_repository_summary_response(raw_response_text)
            return parsed_response
        except Exception as e:
            raise ReviewGenerationError(f"Failed to get repository review from AI: {e}") from e

    async def review_entire_repository_with_retry(self, files_data: List[FileDetails], repo_info: str, max_retries: Optional[int] = None) -> RepositorySummaryResponse | Exception:
        retries = max_retries if max_retries is not None else self.config.retry_attempts
        for attempt in range(retries):
            try:
                return await self.review_entire_repository(files_data, repo_info)
            except Exception as e:
                print(f"Repository review attempt {attempt + 1} failed: {e}")
                if attempt == retries - 1:
                    print(f"All retry attempts failed for repository review. Using fallback.")
                    continue
                
                delay = (2 ** attempt)
                print(f"Retrying in {delay}s...")
                await asyncio.sleep(delay)
        
        return Exception(f"Unexpected end of retry loop for repository review.")

    async def review_code_with_retry(self, diff: str, commit: CommitInfo, max_retries: Optional[int] = None) -> AIReviewResponse | Exception:
        retries = max_retries if max_retries is not None else self.config.retry_attempts
        for attempt in range(retries):
            try:
                return await self.review_code(diff, commit)
            except Exception as e:
                print(f"Review attempt {attempt + 1} failed: {e}")
                if attempt == retries - 1:
                    print(f"All retry attempts failed for commit {commit['hash']}. Using fallback review.")
                    continue
                
                delay = (2 ** attempt)
                print(f"Retrying in {delay}s...")
                await asyncio.sleep(delay)
        
        return Exception(f"Unexpected end of retry loop for commit {commit['hash']}. Using fallback review.")

    async def review_file_content_with_retry(self, file_content: str, file_path: str, max_retries: Optional[int] = None) -> AIReviewResponse | Exception:
        retries = max_retries if max_retries is not None else self.config.retry_attempts
        for attempt in range(retries):
            try:
                return await self.review_file_content(file_content, file_path)
            except Exception as e:
                print(f"Review attempt {attempt + 1} for file {file_path} failed: {e}")
                if attempt == retries - 1:
                    print(f"All retry attempts failed for file {file_path}. Using fallback review.")
                    continue
                
                delay = (2 ** attempt)
                print(f"Retrying in {delay}s...")
                await asyncio.sleep(delay)
        return Exception(f"Unexpected end of retry loop for file {file_path}. Using fallback review.")

    async def review_multiple_commits(self, commits: List[CommitInfo], diffs: List[str]) -> List[Union[AIReviewResponse, Exception]]:
        if not self.config.enable_batch_processing:
            reviews: List[AIReviewResponse] = []
            for i, commit in enumerate(commits):
                review = await self.review_code_with_retry(diffs[i], commit)
                reviews.append(review)
            return reviews

        tasks = []
        for i, commit_info in enumerate(commits):
            tasks.append(self.review_code_with_retry(diffs[i], commit_info))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                print(f"Error reviewing commit {commits[i]['hash']}: {res}")
                processed_results.append(res)
            else:
                processed_results.append(res)
        return processed_results

    async def review_multiple_files(self, files_data: List[FileDetails]) -> List[Union[AIReviewResponse, Exception]]:
        # files_data is a list of dicts, each with "path" and "content"
        if not self.config.enable_batch_processing:
            reviews: List[Union[AIReviewResponse, Exception]] = []
            for file_data in files_data:
                review = await self.review_file_content_with_retry(file_data["content"], file_data["path"])
                reviews.append(review)
            return reviews

        tasks = []
        for file_data in files_data:
            tasks.append(self.review_file_content_with_retry(file_data["content"], file_data["path"]))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results