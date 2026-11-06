"""Read-only checks for the synthetic cross-host profile fixture."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

import yaml


CHILD_PATH = "enterprise-child"
CHILD_URL = (
    "https://github.qualcomm.com/zgeorge/"
    "profiles-cross-host-enterprise-fixture.git"
)
LINK_PATH = "skills/enterprise-marker"
LINK_TARGET = "../enterprise-child/skills/enterprise-marker"


def git(repo: Path, *arguments: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *arguments], text=True, stderr=subprocess.PIPE
    ).strip()


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def manifest(directory: Path) -> dict:
    path = directory / "qgenie-profile.yaml"
    check(path.is_file(), f"Missing manifest: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    check(isinstance(data, dict), f"Invalid manifest: {path}")
    profile = data.get("profile")
    check(isinstance(profile, dict), f"Missing profile mapping: {path}")
    for key in ("slug", "name", "version"):
        check(
            isinstance(profile.get(key), str) and bool(profile[key].strip()),
            f"Missing profile.{key}: {path}",
        )
    check(
        data.get("sync", {}).get("delete_removed_profiles") is False,
        f"Fixture must disable profile deletion: {path}",
    )
    return data


def verify(repo: Path) -> list[str]:
    modules = repo / ".gitmodules"
    check(modules.is_file(), "Missing .gitmodules; the cross-host fixture is incomplete.")
    url = git(
        repo, "config", "-f", str(modules), "--get",
        "submodule.enterprise-child.url",
    )
    check(url == CHILD_URL, f"Unexpected enterprise submodule URL: {url}")
    path = git(
        repo, "config", "-f", str(modules), "--get",
        "submodule.enterprise-child.path",
    )
    check(path == CHILD_PATH, f"Unexpected enterprise submodule path: {path}")

    staged = {}
    for line in git(repo, "ls-files", "--stage").splitlines():
        metadata, filename = line.split("\t", 1)
        mode, sha, stage = metadata.split()
        check(stage == "0", f"Unmerged index entry: {filename}")
        staged[filename] = (mode, sha)
    check(
        staged.get(CHILD_PATH, ("", ""))[0] == "160000",
        "Enterprise child is not a real pinned Git submodule (mode 160000).",
    )
    child = repo / CHILD_PATH
    check((child / ".git").exists(), "Initialize the enterprise submodule first.")
    pin = staged[CHILD_PATH][1]
    check(
        git(child, "rev-parse", "HEAD") == pin,
        "Enterprise checkout HEAD does not match the parent's pinned commit.",
    )
    check(not git(child, "status", "--porcelain"), "Enterprise checkout has uncommitted changes.")
    check(
        staged.get(LINK_PATH, ("", ""))[0] == "120000",
        "Shared enterprise skill is not a tracked Git symlink (mode 120000).",
    )
    check(
        git(repo, "cat-file", "blob", staged[LINK_PATH][1]) == LINK_TARGET,
        "Shared skill symlink does not point to the enterprise skill.",
    )

    root = manifest(repo)
    enterprise = manifest(child)
    check(
        root["profile"]["slug"] == "cross-host-submodule-test",
        "Unexpected root profile slug.",
    )
    check(
        enterprise["profile"]["slug"] == "cross-host-enterprise-child",
        "Unexpected enterprise profile slug.",
    )
    check(
        root["profile"]["subprofiles"] == [{
            "slug": enterprise["profile"]["slug"],
            "path": "./enterprise-child",
            "version": enterprise["profile"]["version"],
        }],
        "Root manifest must declare the enterprise child and its exact version.",
    )
    expected_skills = (
        (root, repo, "root-control", "ROOT_CONTROL_V1"),
        (root, repo, "review-ext", "PUBLIC_REVIEW_EXT_V1"),
        (enterprise, child, "enterprise-marker", "ENTERPRISE_MARKER_V1"),
    )
    for data, directory, slug, marker in expected_skills:
        entry = next((s for s in data.get("skills", []) if s.get("slug") == slug), None)
        check(entry is not None, f"Missing declared skill: {slug}")
        skill = directory / entry["dir"] / "SKILL.md"
        check(skill.is_file(), f"Missing skill content: {skill}")
        check(marker in skill.read_text(encoding="utf-8"), f"Missing marker: {marker}")
    check(
        {"slug": "enterprise-marker", "dir": "./skills/enterprise-marker"}
        in root.get("skills", []),
        "Root must declare the cross-host symlinked skill.",
    )
    return [
        "PASS: real HTTPS cross-host submodule with a pinned enterprise commit",
        f"PASS: enterprise commit {pin}",
        "PASS: matching root and enterprise profile declarations",
        "PASS: root control, public review, and enterprise marker skills",
        "PASS: tracked symlink to enterprise skill content",
        "PASS: profile deletion disabled in both manifests",
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        for message in verify(args.repo.resolve()):
            print(message)
    except (ValueError, OSError, subprocess.CalledProcessError, yaml.YAMLError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
