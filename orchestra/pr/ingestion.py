"""PR Ingestion pipeline: metadata retrieval, branch checkout, and noise filtering."""

from __future__ import annotations

import fnmatch
import json
import os
import re
import subprocess
from pathlib import Path
from typing import List, Optional

from orchestra.pr.models import ChangedFile, PRMetadata
from orchestra.pr.safety import GitConflictBlockerError


class PRIngestionError(Exception):
    """Raised when PR metadata retrieval, checkout, or diff parsing fails."""
    pass


class PRIngestionPipeline:
    """Manages non-interactive PR checkout, noise filtering, and high-signal diff preparation."""

    NOISE_PATTERNS = [
        # Package lockfiles
        "**/package-lock.json",
        "**/pnpm-lock.yaml",
        "**/yarn.lock",
        "**/poetry.lock",
        "**/Pipfile.lock",
        "**/Cargo.lock",
        "**/composer.lock",
        "**/Gemfile.lock",
        # Build outputs & minified assets
        "**/*.min.js",
        "**/*.min.css",
        "**/*.map",
        "**/dist/**",
        "**/build/**",
        "**/out/**",
        "**/.next/**",
        "**/.nuxt/**",
        # Binary & media
        "**/*.pdf",
        "**/*.png",
        "**/*.jpg",
        "**/*.jpeg",
        "**/*.gif",
        "**/*.ico",
        "**/*.svg",
        "**/*.wasm",
        "**/*.zip",
        "**/*.tar.gz",
        # Vendor & cache
        "**/vendor/**",
        "**/node_modules/**",
        "**/__pycache__/**",
        "**/*.pyc",
    ]

    def __init__(self, workspace_root: Optional[Path] = None):
        self.workspace_root = (workspace_root or Path.cwd()).resolve()

    def _get_clean_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env["GH_PAGER"] = "cat"
        env["GIT_PAGER"] = "cat"
        bin_dir = str(self.workspace_root / "bin")
        local_bin = str(Path.home() / ".local" / "bin")
        env["PATH"] = f"{bin_dir}:{local_bin}:{env.get('PATH', '')}"
        return env

    def fetch_metadata(self, pr_identifier: str | int) -> PRMetadata:
        """Fetches PR metadata from GitHub CLI in non-interactive mode."""
        cmd = [
            "gh",
            "pr",
            "view",
            str(pr_identifier),
            "--json",
            "number,title,body,author,baseRefName,headRefName,headRefOid,commits,files,additions,deletions,url",
        ]
        try:
            res = subprocess.run(
                cmd,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                check=False,
                env=self._get_clean_env(),
            )
            if res.returncode != 0:
                raise PRIngestionError(f"Failed to fetch PR #{pr_identifier} metadata: {res.stderr.strip()}")
            data = json.loads(res.stdout)
        except json.JSONDecodeError as e:
            raise PRIngestionError(f"Invalid JSON returned by gh pr view: {str(e)}")
        except Exception as e:
            raise PRIngestionError(f"Error executing gh pr view: {str(e)}")

        files: List[ChangedFile] = []
        for f in data.get("files", []):
            path = f.get("path", "")
            filtered, reason = self.is_noise_file(path)
            files.append(
                ChangedFile(
                    path=path,
                    status=f.get("status", "modified"),
                    additions=f.get("additions", 0),
                    deletions=f.get("deletions", 0),
                    is_filtered=filtered,
                    filter_reason=reason,
                )
            )

        author_data = data.get("author", {})
        author_name = author_data.get("login") or author_data.get("name") or "unknown"

        return PRMetadata(
            number=data.get("number", int(pr_identifier) if str(pr_identifier).isdigit() else 0),
            title=data.get("title", ""),
            body=data.get("body", ""),
            author=author_name,
            base_ref=data.get("baseRefName", "main"),
            head_ref=data.get("headRefName", ""),
            head_sha=data.get("headRefOid", ""),
            additions=data.get("additions", 0),
            deletions=data.get("deletions", 0),
            commits=data.get("commits", []),
            files=files,
            url=data.get("url", ""),
        )

    def checkout_pr(self, pr_identifier: str | int) -> None:
        """Checks out the PR branch into the local workspace using gh CLI."""
        cmd = ["gh", "pr", "checkout", str(pr_identifier)]
        try:
            res = subprocess.run(
                cmd,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                check=False,
                env=self._get_clean_env(),
            )
            if res.returncode != 0:
                err = res.stderr.strip()
                if "conflict" in err.lower() or "overwritten by checkout" in err.lower():
                    raise GitConflictBlockerError(f"Tier 1 Blocker: Checkout conflict on PR #{pr_identifier}: {err}")
                raise PRIngestionError(f"Failed to checkout PR #{pr_identifier}: {err}")
        except GitConflictBlockerError:
            raise
        except Exception as e:
            raise PRIngestionError(f"Error checking out PR: {str(e)}")

    def is_noise_file(self, path: str) -> tuple[bool, Optional[str]]:
        """Determines if a file should be excluded from LLM diff evaluation."""
        normalized = "/" + path.replace("\\", "/").lstrip("/")
        for pattern in self.NOISE_PATTERNS:
            if fnmatch.fnmatch(normalized, pattern) or fnmatch.fnmatch(path, pattern):
                return True, f"Matches noise pattern: {pattern}"
        return False, None

    def fetch_diff(self, pr_identifier: str | int, metadata: PRMetadata) -> List[ChangedFile]:
        """Fetches the unified diff using non-interactive git diff <BASE>...HEAD."""
        diff_text = ""
        # 1. Try local git diff base...HEAD if checked out
        base = metadata.base_ref or "main"
        try:
            cmd = ["git", "diff", f"{base}...HEAD"]
            res = subprocess.run(
                cmd,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                check=False,
                env=self._get_clean_env(),
            )
            if res.returncode == 0 and res.stdout.strip():
                diff_text = res.stdout
        except Exception:
            pass

        # 2. Fall back to gh pr diff
        if not diff_text:
            try:
                cmd = ["gh", "pr", "diff", str(pr_identifier)]
                res = subprocess.run(
                    cmd,
                    cwd=self.workspace_root,
                    capture_output=True,
                    text=True,
                    check=False,
                    env=self._get_clean_env(),
                )
                if res.returncode == 0:
                    diff_text = res.stdout
            except Exception:
                return metadata.files

        if not diff_text:
            return metadata.files

        # Split diff by file header: "diff --git a/... b/..."
        file_patches = re.split(r"(?=^diff --git a/)", diff_text, flags=re.MULTILINE)
        patch_map: dict[str, str] = {}
        for patch in file_patches:
            if not patch.strip():
                continue
            match = re.search(r"^\+\+\+ b/(.*)$", patch, re.MULTILINE)
            if match:
                fpath = match.group(1).strip()
                patch_map[fpath] = patch

        for file_obj in metadata.files:
            if not file_obj.is_filtered and file_obj.path in patch_map:
                file_obj.patch = patch_map[file_obj.path]

        return metadata.files
