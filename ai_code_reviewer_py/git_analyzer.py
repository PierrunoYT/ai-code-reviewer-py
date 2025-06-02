import git
import re
from typing import List, Optional, TypedDict
from datetime import datetime
import tarfile
import io
import urllib.request
import urllib.parse
from git import Git
from ai_code_reviewer_py.models import FileDetails

class CommitInfo(TypedDict):
    hash: str
    message: str
    author_name: str
    author_email: str
    date: datetime
    body: str

class GitAnalyzer:
    def __init__(self, repo_path: str = '.'):
        try:
            self.repo = git.Repo(repo_path, search_parent_directories=True)
        except git.InvalidGitRepositoryError:
            raise ValueError(f"Invalid Git repository at {repo_path}")
        except Exception as e:
            raise RuntimeError(f"Error initializing Git repository: {e}")

    @staticmethod
    def _validate_commit_range(range_str: str) -> str:
        """Validate and sanitize commit range input."""
        range_str = range_str.strip().strip('\'"')
        
        # Allow only safe characters for git ranges
        if not re.match(r'^[a-zA-Z0-9_.^~/-]+$', range_str):
            raise ValueError(f"Invalid characters in commit range: {range_str}")
        
        # Prevent command injection patterns
        dangerous_patterns = [';', '|', '&', '$', '`', '(', ')', '<', '>', '\n', '\r']
        if any(pattern in range_str for pattern in dangerous_patterns):
            raise ValueError(f"Potentially dangerous commit range: {range_str}")
            
        return range_str

    @staticmethod
    def _validate_git_ref(ref: str) -> str:
        """Validate git reference."""
        ref = ref.strip().strip('\'"')
        
        if not re.match(r'^[a-zA-Z0-9_./-]+$', ref):
            raise ValueError(f"Invalid git reference: {ref}")
            
        dangerous_patterns = [';', '|', '&', '$', '`', '(', ')', '<', '>', '\n', '\r']
        if any(pattern in ref for pattern in dangerous_patterns):
            raise ValueError(f"Potentially dangerous git reference: {ref}")
            
        return ref

    def get_commits(self, range_str: str = 'HEAD~1..HEAD') -> List[CommitInfo]:
        try:
            range_str = self._validate_commit_range(range_str)
            
            if '..' not in range_str:
                if range_str == "HEAD":
                    commit_objects = [self.repo.head.commit]
                else:
                    commit_objects = [self.repo.commit(range_str)]
            else:
                commit_objects = list(self.repo.iter_commits(rev=range_str))

            commits_data: List[CommitInfo] = []
            for commit in commit_objects:
                commits_data.append(CommitInfo(
                    hash=commit.hexsha,
                    message=str(commit.message).strip().split('\n', 1)[0],
                    author_name=commit.author.name,
                    author_email=commit.author.email,
                    date=datetime.fromtimestamp(commit.authored_date),
                    body=str(commit.message).strip()
                ))
            return commits_data
        except git.GitCommandError as e:
            raise RuntimeError(f"Failed to get commits for range '{range_str}': {e}")
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred while getting commits: {e}")

    def get_commit_diff(self, commit_hash: str) -> str:
        try:
            commit_hash = self._validate_commit_range(commit_hash)
            
            commit = self.repo.commit(commit_hash)
            parent = commit.parents[0] if commit.parents else self.repo.tree()
            diff_output = self.repo.git.show(commit.hexsha, "--unified=3", "--pretty=format:")
            return diff_output
        except IndexError:
            raise ValueError(f"Commit {commit_hash} seems to have no parents and is not an initial commit, or is invalid.")
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred while getting diff for {commit_hash}: {e}")

    def get_staged_changes_diff(self) -> Optional[str]:
        try:
            diff_output = self.repo.git.diff("--cached", "--unified=3")
            return diff_output if diff_output.strip() else None
        except git.GitCommandError as e:
            raise RuntimeError(f"Failed to get staged changes: {e}")
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred while getting staged changes: {e}")

    def get_tracked_files(self) -> List[str]:
        """Returns a list of all files tracked by Git."""
        try:
            # ls-files shows tracked files, respecting .gitignore
            return self.repo.git.ls_files().splitlines()
        except git.GitCommandError as e:
            raise RuntimeError(f"Failed to list tracked files: {e}") from e

    @staticmethod
    def _is_github_url(repo_url: str) -> bool:
        """Check if the repository URL is from GitHub."""
        return 'github.com' in repo_url.lower()

    @staticmethod
    def _parse_github_url(repo_url: str) -> tuple[str, str]:
        """Parse GitHub URL to extract owner and repo name."""
        # Handle various GitHub URL formats
        patterns = [
            r'https://github\.com/([^/]+)/([^/]+)(?:\.git)?/?$',
            r'git@github\.com:([^/]+)/([^/]+)(?:\.git)?$',
            r'github\.com[:/]([^/]+)/([^/]+)(?:\.git)?/?$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, repo_url.strip())
            if match:
                owner, repo = match.groups()
                return owner, repo.rstrip('.git')
        
        raise ValueError(f"Could not parse GitHub URL: {repo_url}")

    @staticmethod
    def _validate_repo_url(repo_url: str) -> str:
        """Validate repository URL."""
        if not repo_url.startswith(('https://', 'git@', 'ssh://')):
            raise ValueError(f"Invalid repository URL protocol: {repo_url}")
        
        return repo_url

    @staticmethod
    def _download_github_archive(repo_url: str, ref: str = "HEAD") -> bytes:
        """Download repository archive from GitHub using HTTP."""
        owner, repo = GitAnalyzer._parse_github_url(repo_url)
        
        # Try different archive URL formats
        archive_urls = [
            f"https://github.com/{owner}/{repo}/archive/{ref}.tar.gz",
            f"https://github.com/{owner}/{repo}/archive/refs/heads/{ref}.tar.gz",
            f"https://github.com/{owner}/{repo}/archive/refs/tags/{ref}.tar.gz"
        ]
        
        last_error = None
        for url in archive_urls:
            try:
                with urllib.request.urlopen(url, timeout=60) as response:
                    if response.status == 200:
                        return response.read()
            except Exception as e:
                last_error = e
                continue
        
        raise RuntimeError(f"Failed to download archive from GitHub. Last error: {last_error}")

    @staticmethod
    def _extract_files_from_tar_gz(archive_bytes: bytes) -> List[FileDetails]:
        """Extract files from tar.gz archive bytes."""
        files_data: List[FileDetails] = []
        
        tar_stream = io.BytesIO(archive_bytes)
        with tarfile.open(fileobj=tar_stream, mode="r:gz") as tar:
            members = [m for m in tar.getmembers() if m.isfile() and m.name]
            
            for member in members:
                try:
                    extracted_file = tar.extractfile(member)
                    if extracted_file:
                        file_content_bytes = extracted_file.read()
                        file_content_str = file_content_bytes.decode('utf-8', errors='replace')
                        
                        # Remove the top-level directory from path (GitHub adds repo-ref/ prefix)
                        clean_path = '/'.join(member.name.split('/')[1:]) if '/' in member.name else member.name
                        if clean_path:  # Skip empty paths
                            files_data.append(FileDetails(
                                path=clean_path,
                                content=file_content_str
                            ))
                except UnicodeDecodeError:
                    print(f"Warning: Could not decode file {member.name} as UTF-8. Skipping.")
                except Exception as e:
                    print(f"Warning: Could not read file {member.name} from archive: {e}")
        
        return files_data

    @staticmethod
    def get_files_from_remote_archive(repo_url: str, ref: str = "HEAD") -> List[FileDetails]:
        """Get files from remote repository archive safely without executing any code."""
        try:
            repo_url = GitAnalyzer._validate_repo_url(repo_url)
            ref = GitAnalyzer._validate_git_ref(ref)
            
            if GitAnalyzer._is_github_url(repo_url):
                archive_bytes = GitAnalyzer._download_github_archive(repo_url, ref)
                return GitAnalyzer._extract_files_from_tar_gz(archive_bytes)
            else:
                # Fall back to git archive for other providers
                g = Git()
                tar_bytes = g.archive(remote=repo_url, format='tar', ref=ref, kill_after_timeout=120, stdout_as_bytes=True)
                
                files_data: List[FileDetails] = []
                tar_stream = io.BytesIO(tar_bytes)
                with tarfile.open(fileobj=tar_stream, mode="r|*") as tar:
                    for member in tar:
                        if member.isfile() and member.name: 
                            try:
                                extracted_file = tar.extractfile(member)
                                if extracted_file:
                                    file_content_bytes = extracted_file.read()
                                    file_content_str = file_content_bytes.decode('utf-8', errors='replace')
                                    files_data.append(FileDetails(
                                        path=member.name,
                                        content=file_content_str
                                    ))
                            except UnicodeDecodeError:
                                print(f"Warning: Could not decode file {member.name} as UTF-8. Skipping.")
                            except Exception as e:
                                print(f"Warning: Could not read file {member.name} from archive: {e}")
                return files_data
        except git.GitCommandError as e:
            error_message = f"Failed to fetch archive from '{repo_url}' (ref: {ref}). Git command failed: {e.stderr}"
            raise RuntimeError(error_message) from e
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"HTTP error downloading from '{repo_url}' (ref: {ref}): {e.code} {e.reason}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"Network error downloading from '{repo_url}': {e.reason}") from e
        except tarfile.TarError as e:
            raise RuntimeError(f"Failed to process tar archive from '{repo_url}': {e}") from e
        except Exception as e:
            raise RuntimeError(f"An unexpected error occurred while fetching remote archive: {e}") from e