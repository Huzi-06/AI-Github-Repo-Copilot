from __future__ import annotations

import asyncio
import base64
from typing import List

import httpx

# Binary/non-text extensions to skip
SKIP_EXTENSIONS = frozenset({
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp", ".bmp",
    ".pdf", ".zip", ".tar", ".gz", ".tgz", ".whl", ".egg", ".jar",
    ".pyc", ".pyo", ".pyd", ".so", ".dylib", ".dll", ".exe", ".bin",
    ".mp3", ".mp4", ".wav", ".avi", ".mov", ".mkv",
    ".ttf", ".woff", ".woff2", ".eot",
    ".DS_Store",
})

TEXT_EXTENSIONS = frozenset({
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rs",
    ".rb", ".php", ".swift", ".kt", ".cs", ".cpp", ".c", ".h", ".hpp",
    ".html", ".css", ".scss", ".sass", ".less",
    ".md", ".mdx", ".txt", ".rst",
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".env",
    ".sh", ".bash", ".zsh", ".fish", ".ps1",
    ".sql", ".graphql", ".gql", ".proto",
    ".xml", ".csv",
    ".gitignore", ".gitattributes", ".editorconfig",
    ".eslintrc", ".prettierrc", ".babelrc", ".npmrc",
})

MAX_FILE_BYTES = 80_000   
MAX_FILES = 120
MAX_CONCURRENT = 10       

SKIP_PATH_SEGMENTS = frozenset({
    "node_modules", "vendor", ".git", "__pycache__",
    "dist", "build", ".next", ".cache", ".venv", "venv",
    "env", ".tox", "coverage", ".nyc_output",
})


class GitHubClient:
    BASE = "https://api.github.com"

    def __init__(self, token: str | None = None):
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        self.client = httpx.AsyncClient(
            headers=headers,
            timeout=httpx.Timeout(30.0),
            follow_redirects=True,
        )

    def _parse_url(self, url: str) -> tuple[str, str]:
        for prefix in ("https://github.com/", "http://github.com/", "github.com/"):
            if url.startswith(prefix):
                url = url[len(prefix):]
        url = url.rstrip("/").removesuffix(".git")
        parts = url.split("/")
        if len(parts) < 2:
            raise ValueError(
                f"Invalid GitHub URL: {url!r}. Expected: https://github.com/owner/repo"
            )
        return parts[0], parts[1]

    def _is_fetchable(self, path: str, size: int) -> bool:
        if size > MAX_FILE_BYTES:
            return False
        segments = path.split("/")
        if any(seg in SKIP_PATH_SEGMENTS for seg in segments[:-1]):
            return False
        name = segments[-1].lower()
        if "." in name:
            ext = "." + name.rsplit(".", 1)[-1]
            if ext in SKIP_EXTENSIONS:
                return False
            if ext in TEXT_EXTENSIONS:
                return True
        # No extension: Makefile, Dockerfile, Procfile, etc.
        no_ext = {"makefile", "dockerfile", "rakefile", "gemfile", "procfile",
                  "vagrantfile", "jenkinsfile", "brewfile", "license", "readme"}
        return name in no_ext

    async def fetch_repo(self, repo_url: str) -> tuple[dict, list[dict]]:
        owner, repo = self._parse_url(repo_url)

        metadata, tree, commits, issues = await asyncio.gather(
            self._metadata(owner, repo),
            self._file_tree(owner, repo),
            self._commits(owner, repo),
            self._issues(owner, repo),
        )

        eligible = [
            item for item in tree
            if item["type"] == "blob"
            and self._is_fetchable(item["path"], item.get("size", 0))
        ]

        # Prioritize README > root configs > everything else
        def priority(item: dict) -> int:
            p = item["path"].lower()
            if "readme" in p:
                return 0
            if "/" not in p and p.split(".")[-1] in ("toml", "json", "py", "js", "ts", "go", "rb"):
                return 1
            if "/" not in p:
                return 2
            return 3

        eligible.sort(key=priority)
        eligible = eligible[:MAX_FILES]

        sem = asyncio.Semaphore(MAX_CONCURRENT)

        async def fetch(path: str) -> dict | None:
            async with sem:
                content = await self._file_content(owner, repo, path)
                return {"path": path, "content": content} if content else None

        results = await asyncio.gather(*[fetch(i["path"]) for i in eligible], return_exceptions=True)
        files = [r for r in results if isinstance(r, dict)]

        if commits:
            files.append({"path": "_commits.md", "content": self._fmt_commits(commits)})
        if issues:
            files.append({"path": "_issues.md", "content": self._fmt_issues(issues)})

        metadata["file_tree"] = "\n".join(i["path"] for i in tree if i["type"] == "blob")
        return metadata, files

    async def _metadata(self, owner: str, repo: str) -> dict:
        r = await self.client.get(f"{self.BASE}/repos/{owner}/{repo}")
        if r.status_code == 404:
            raise ValueError(f"Repository '{owner}/{repo}' not found or is private.")
        r.raise_for_status()
        d = r.json()
        return {
            "full_name": d["full_name"],
            "description": d.get("description") or "",
            "language": d.get("language") or "",
            "stars": d.get("stargazers_count", 0),
            "forks": d.get("forks_count", 0),
            "topics": d.get("topics", []),
            "default_branch": d.get("default_branch", "main"),
        }

    async def _file_tree(self, owner: str, repo: str) -> list[dict]:
        r = await self.client.get(
            f"{self.BASE}/repos/{owner}/{repo}/git/trees/HEAD",
            params={"recursive": "1"},
        )
        if r.status_code in (404, 409):
            return []
        r.raise_for_status()
        return r.json().get("tree", [])

    async def _file_content(self, owner: str, repo: str, path: str) -> str | None:
        try:
            r = await self.client.get(f"{self.BASE}/repos/{owner}/{repo}/contents/{path}")
            if r.status_code != 200:
                return None
            data = r.json()
            if isinstance(data, list):
                return None
            if data.get("encoding") == "base64":
                return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        except Exception:
            pass
        return None

    async def _commits(self, owner: str, repo: str) -> list[dict]:
        try:
            r = await self.client.get(
                f"{self.BASE}/repos/{owner}/{repo}/commits",
                params={"per_page": 30},
            )
            return r.json() if r.status_code == 200 else []
        except Exception:
            return []

    async def _issues(self, owner: str, repo: str) -> list[dict]:
        try:
            r = await self.client.get(
                f"{self.BASE}/repos/{owner}/{repo}/issues",
                params={"state": "all", "per_page": 20},
            )
            if r.status_code != 200:
                return []
            return [i for i in r.json() if "pull_request" not in i]
        except Exception:
            return []

    def _fmt_commits(self, commits: list[dict]) -> str:
        lines = ["# Recent Commits\n"]
        for c in commits:
            commit = c.get("commit", {})
            msg = commit.get("message", "").split("\n")[0]
            author = commit.get("author", {}).get("name", "unknown")
            date = commit.get("author", {}).get("date", "")[:10]
            sha = c.get("sha", "")[:7]
            lines.append(f"- `{sha}` [{date}] **{author}**: {msg}")
        return "\n".join(lines)

    def _fmt_issues(self, issues: list[dict]) -> str:
        lines = ["# Issues\n"]
        for issue in issues:
            state = issue.get("state", "").upper()
            title = issue.get("title", "")
            number = issue.get("number", "")
            body = (issue.get("body") or "")[:300]
            labels = ", ".join(l.get("name", "") for l in issue.get("labels", []))
            lines.append(f"## #{number} [{state}] {title}")
            if labels:
                lines.append(f"Labels: {labels}")
            if body:
                lines.append(body)
            lines.append("")
        return "\n".join(lines)
