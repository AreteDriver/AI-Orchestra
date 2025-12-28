"""GitHub API client wrapper."""

from typing import Optional, List, Dict
from github import Github, GithubException

from test_ai.config import get_settings


class GitHubClient:
    """Wrapper for GitHub API."""

    def __init__(self):
        settings = get_settings()
        if settings.github_token:
            self.client = Github(settings.github_token)
        else:
            self.client = None

    def is_configured(self) -> bool:
        """Check if GitHub client is configured."""
        return self.client is not None

    def create_issue(
        self, repo_name: str, title: str, body: str, labels: Optional[List[str]] = None
    ) -> Optional[Dict]:
        """Create an issue in a GitHub repository."""
        if not self.is_configured():
            return None

        try:
            repo = self.client.get_repo(repo_name)
            issue = repo.create_issue(title=title, body=body, labels=labels or [])
            return {"number": issue.number, "url": issue.html_url, "title": issue.title}
        except GithubException as e:
            return {"error": str(e)}

    def commit_file(
        self,
        repo_name: str,
        file_path: str,
        content: str,
        message: str,
        branch: str = "main",
    ) -> Optional[Dict]:
        """Commit a file to a GitHub repository."""
        if not self.is_configured():
            return None

        try:
            repo = self.client.get_repo(repo_name)

            try:
                file = repo.get_contents(file_path, ref=branch)
                result = repo.update_file(
                    file_path, message, content, file.sha, branch=branch
                )
            except GithubException:
                result = repo.create_file(file_path, message, content, branch=branch)

            return {
                "commit_sha": result["commit"].sha,
                "url": result["content"].html_url,
            }
        except GithubException as e:
            return {"error": str(e)}

    def list_repositories(self) -> List[Dict]:
        """List user repositories."""
        if not self.is_configured():
            return []

        try:
            repos = self.client.get_user().get_repos()
            return [
                {
                    "name": repo.full_name,
                    "description": repo.description,
                    "url": repo.html_url,
                }
                for repo in repos[:20]
            ]
        except GithubException:
            return []
