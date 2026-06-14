from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
UPDATER_PATH = ROOT / "scripts" / "update_github_actions.py"
spec = importlib.util.spec_from_file_location("update_github_actions", UPDATER_PATH)
assert spec is not None
assert spec.loader is not None
update_github_actions = importlib.util.module_from_spec(spec)
spec.loader.exec_module(update_github_actions)


def test_detects_unmanaged_workflow_action(tmp_path: Path) -> None:
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text(
        "name: ci\njobs:\n  ci:\n    steps:\n      - uses: example/not-managed@abc123\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="example/not-managed"):
        update_github_actions.verify_managed_actions(workflows)


def test_accepts_local_workflow_call(tmp_path: Path) -> None:
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "release.yml").write_text(
        "jobs:\n  regen:\n    uses: ./.github/workflows/regen.yml\n",
        encoding="utf-8",
    )

    update_github_actions.verify_managed_actions(workflows)


def test_accepts_quoted_managed_actions_and_local_workflows(tmp_path: Path) -> None:
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text(
        "jobs:\n"
        "  ci:\n"
        "    steps:\n"
        '      - uses: "actions/checkout@abc123"\n'
        "      - uses: './.github/workflows/regen.yml'\n",
        encoding="utf-8",
    )

    update_github_actions.verify_managed_actions(workflows)


def test_current_workflows_use_only_managed_actions() -> None:
    update_github_actions.verify_managed_actions()


def test_update_workflow_refs_updates_quoted_action_refs(tmp_path: Path) -> None:
    workflow = tmp_path / "ci.yml"
    workflow.write_text(
        "jobs:\n"
        "  ci:\n"
        "    steps:\n"
        '      - uses: "actions/checkout@oldoldoldoldoldoldoldoldoldoldoldoldoldoldoldoldold1"\n'
        "      - uses: 'astral-sh/setup-uv@oldoldoldoldoldoldoldoldoldoldoldoldoldoldoldoldold2'\n",
        encoding="utf-8",
    )
    releases = {
        "actions/checkout": update_github_actions.ActionRelease(tag="v-test", sha="a" * 40),
        "astral-sh/setup-uv": update_github_actions.ActionRelease(tag="v-test", sha="b" * 40),
    }

    assert update_github_actions.update_workflow_refs(workflow, releases=releases)
    text = workflow.read_text(encoding="utf-8")
    assert f'uses: "actions/checkout@{"a" * 40}"' in text
    assert f"uses: 'astral-sh/setup-uv@{'b' * 40}'" in text


def test_update_uv_version_refs_updates_quoted_setup_uv(tmp_path: Path) -> None:
    workflow = tmp_path / "ci.yml"
    workflow.write_text(
        "jobs:\n"
        "  ci:\n"
        "    steps:\n"
        '      - uses: "astral-sh/setup-uv@oldoldoldoldoldoldoldoldoldoldoldoldoldoldoldoldold2"\n'
        "        with:\n"
        '          version: "0.1.0"\n',
        encoding="utf-8",
    )

    assert update_github_actions.update_uv_version_refs(workflow, version="0.11.16")
    assert 'version: "0.11.16"' in workflow.read_text(encoding="utf-8")


def test_update_uv_version_refs_updates_quoted_setup_uv_with_inline_comment(tmp_path: Path) -> None:
    workflow = tmp_path / "ci.yml"
    workflow.write_text(
        "jobs:\n"
        "  ci:\n"
        "    steps:\n"
        '      - uses: "astral-sh/setup-uv@oldoldoldoldoldoldoldoldoldoldoldoldoldoldoldoldold2"  # v8.1.0\n'
        "        with:\n"
        '          version: "0.1.0"\n',
        encoding="utf-8",
    )

    assert update_github_actions.update_uv_version_refs(workflow, version="0.11.16")
    assert 'version: "0.11.16"' in workflow.read_text(encoding="utf-8")


def test_update_pyproject_uv_version_does_not_exist() -> None:
    """update_pyproject_uv_version must not exist — it was the source of the CI self-poison."""
    assert not hasattr(update_github_actions, "update_pyproject_uv_version"), (
        "update_pyproject_uv_version must be removed; it silently pinned "
        "required-version to the latest uv release, causing dep-refresh to "
        "fail its own version check on the next run."
    )


def test_update_github_actions_does_not_modify_pyproject(tmp_path: Path) -> None:
    """update_github_actions() must never touch pyproject.toml."""
    import json
    import subprocess

    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    setup_uv_sha = "c" * 40
    checkout_sha = "d" * 40
    (workflows / "ci.yml").write_text(
        "jobs:\n"
        "  ci:\n"
        "    steps:\n"
        f'      - uses: "actions/checkout@{checkout_sha}"\n'
        f'      - uses: "astral-sh/setup-uv@{setup_uv_sha}"\n'
        "        with:\n"
        '          version: "0.1.0"\n',
        encoding="utf-8",
    )
    pyproject = tmp_path / "pyproject.toml"
    original_content = '[tool.uv]\nrequired-version = ">=0.11.16"\n'
    pyproject.write_text(original_content, encoding="utf-8")

    def fake_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
        endpoint = command[-1]
        if "astral-sh/uv/releases/latest" in endpoint:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout=json.dumps({"tag_name": "0.99.99"}),
                stderr="",
            )
        if "releases/latest" in endpoint:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout=json.dumps({"tag_name": "v99.0.0"}),
                stderr="",
            )
        if "git/ref/tags" in endpoint:
            return subprocess.CompletedProcess(
                args=command,
                returncode=0,
                stdout=json.dumps({"object": {"type": "commit", "sha": "e" * 40}}),
                stderr="",
            )
        return subprocess.CompletedProcess(
            args=command, returncode=0, stdout=json.dumps({}), stderr=""
        )

    update_github_actions.update_github_actions(
        workflow_dir=workflows,
        runner=fake_runner,
    )

    assert pyproject.read_text(encoding="utf-8") == original_content, (
        "update_github_actions() must not modify pyproject.toml"
    )
