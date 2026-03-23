from release_clean import (
    build_context,
    format_release_branch,
    is_valid_version,
    planned_commands,
)


def test_is_valid_version_accepts_supported_formats():
    assert is_valid_version("1.0.0")
    assert is_valid_version("2.100.1")
    assert is_valid_version("2.100.1-hotfix")


def test_is_valid_version_rejects_invalid_formats():
    assert not is_valid_version("")
    assert not is_valid_version("1.0")
    assert not is_valid_version("release/1.0.0")


def test_format_release_branch():
    assert format_release_branch("2.100.1") == "release/2.100.1"


def test_planned_commands_order():
    commands = planned_commands("release/2.100.1")
    assert commands[0] == "rm -rf ios"
    assert commands[-1] == "git pull origin release/2.100.1"


def test_build_context():
    ctx = build_context("1.0.0", "/tmp/repo")
    assert ctx.version == "1.0.0"
    assert ctx.release_branch == "release/1.0.0"
    assert ctx.repo_root == "/tmp/repo"
