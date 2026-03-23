from release_clean.cli import (
    build_context,
    format_release_branch,
    is_valid_version,
    planned_commands,
    supports_color,
)


def test_is_valid_version_accepts_supported_formats():
    assert is_valid_version("1.0.0")
    assert is_valid_version("2.100.1")
    assert is_valid_version("2.100.1-hotfix")
    assert is_valid_version("3.4.5-rc1")


def test_is_valid_version_rejects_invalid_formats():
    assert not is_valid_version("")
    assert not is_valid_version("1.0")
    assert not is_valid_version("release/1.0.0")
    assert not is_valid_version("v1.0.0")
    assert not is_valid_version("1.0.0/")
    assert not is_valid_version("abc")


def test_format_release_branch():
    assert format_release_branch("2.100.1") == "release/2.100.1"
    assert format_release_branch("2.100.1-hotfix") == "release/2.100.1-hotfix"


def test_planned_commands_returns_expected_order():
    release_branch = "release/2.100.1"
    commands = planned_commands(release_branch)

    assert commands == [
        "git clean -fdX -e node_modules/",
        "git checkout -- .",
        "git checkout main",
        "git pull",
        "git fetch --all",
        "git checkout release/2.100.1",
        "git checkout -- .",
        "git pull origin release/2.100.1",
    ]


def test_planned_commands_starts_with_git_clean_preserving_node_modules():
    commands = planned_commands("release/2.100.1")

    assert commands[0] == "git clean -fdX -e node_modules/"


def test_planned_commands_resets_after_release_checkout():
    release_branch = "release/2.100.1"
    commands = planned_commands(release_branch)

    checkout_index = commands.index(f"git checkout {release_branch}")
    assert commands[checkout_index + 1] == "git checkout -- ."


def test_planned_commands_ends_with_release_pull():
    commands = planned_commands("release/2.100.1")

    assert commands[-1] == "git pull origin release/2.100.1"


def test_build_context():
    ctx = build_context("1.0.0", "/tmp/repo")

    assert ctx.version == "1.0.0"
    assert ctx.release_branch == "release/1.0.0"
    assert ctx.repo_root == "/tmp/repo"
    assert isinstance(ctx.color_enabled, bool)


def test_supports_color_returns_bool():
    assert isinstance(supports_color(), bool)
