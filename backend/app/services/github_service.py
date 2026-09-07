import re
import os
import httpx
import zipfile
import io
from typing import Tuple, Dict, Any
from backend.app.core.exceptions import AppException
from backend.app.services.zip_service import ZipService


class GitHubService:
    """Service for GitHub repository validation, metadata fetching, and archive import."""

    GITHUB_URL_REGEX = re.compile(
        r"^https://github\.com/([a-zA-Z0-9_.-]+)/([a-zA-Z0-9_.-]+?)(?:\.git|/)?$"
    )

    @classmethod
    def parse_github_url(cls, url: str) -> Tuple[str, str]:
        """Extract owner and repo name from GitHub URL."""
        match = cls.GITHUB_URL_REGEX.match(url.strip())
        if not match:
            raise AppException(
                message="Invalid GitHub repository URL format. Example: https://github.com/owner/repo",
                code="INVALID_GITHUB_URL"
            )
        owner, repo = match.groups()
        return owner, repo

    @classmethod
    async def fetch_repo_metadata(cls, owner: str, repo: str, access_token: str = None) -> Dict[str, Any]:
        """Fetch repository metadata using GitHub REST API with optional auth token for private repos."""
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        headers = {"User-Agent": "AICodeReviewPlatform/1.0"}
        if access_token:
            headers["Authorization"] = f"token {access_token}"
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(api_url, headers=headers)
            if response.status_code == 404:
                raise AppException(
                    message=f"GitHub repository '{owner}/{repo}' not found or is private.",
                    code="GITHUB_REPO_NOT_FOUND"
                )
            elif response.status_code == 403:
                raise AppException(
                    message="GitHub API rate limit exceeded or access forbidden.",
                    code="GITHUB_RATE_LIMIT"
                )
            elif response.status_code != 200:
                raise AppException(
                    message=f"Failed to fetch GitHub metadata (HTTP {response.status_code})",
                    code="GITHUB_API_ERROR"
                )
            
            data = response.json()
            return {
                "name": data.get("name"),
                "full_name": data.get("full_name"),
                "description": data.get("description"),
                "default_branch": data.get("default_branch", "main"),
                "stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
                "language": data.get("language")
            }

    @classmethod
    async def download_and_extract_repo(cls, owner: str, repo: str, extract_to_dir: str, access_token: str = None) -> str:
        """Download repository zip archive from GitHub and extract safely."""
        download_url = f"https://api.github.com/repos/{owner}/{repo}/zipball"
        headers = {"User-Agent": "AICodeReviewPlatform/1.0"}
        if access_token:
            headers["Authorization"] = f"token {access_token}"

        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.get(download_url, headers=headers)
            if response.status_code != 200:
                raise AppException(
                    message=f"Failed to download repository archive from GitHub (HTTP {response.status_code})",
                    code="GITHUB_DOWNLOAD_FAILED"
                )
            
            # Extract in memory zip
            try:
                zip_bytes = io.BytesIO(response.content)
                with zipfile.ZipFile(zip_bytes, "r") as zip_ref:
                    os.makedirs(extract_to_dir, exist_ok=True)
                    for member in zip_ref.infolist():
                        target_path = os.path.join(extract_to_dir, member.filename)
                        if not ZipService.is_safe_path(extract_to_dir, target_path):
                            raise AppException(
                                message="Path traversal risk detected in GitHub repository archive",
                                code="SECURITY_VIOLATION"
                            )
                        zip_ref.extract(member, extract_to_dir)
            except zipfile.BadZipFile:
                raise AppException(
                    message="Downloaded repository archive from GitHub is corrupt or invalid",
                    code="INVALID_ZIP"
                )

        return extract_to_dir
